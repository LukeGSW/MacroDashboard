"""
Calendario delle uscite (condiviso da Cruscotto e Calendario)
=============================================================
Ogni data viene confrontata tra due fonti indipendenti, dove possibile:
- il calendario ufficiale dell'agenzia, letto in automatico (utils/official.py);
- il calendario delle release FRED® (API release/dates).

Uscite con calendario ufficiale leggibile (Fed, BEA, Census):
- data in entrambe le fonti                                 -> confermata;
- solo nel calendario ufficiale, dove FRED® ha già le date  -> da confermare;
- solo nel calendario ufficiale, oltre le date FRED®        -> confermata, se il
  calendario ufficiale coincide con FRED® sulle date già note;
- solo in FRED®, dove il calendario ufficiale ha le date    -> scartata (non è
  un'uscita ufficiale: es. aggiornamenti secondari della release FRED®);
- solo in FRED®, oltre le date ufficiali                     -> da confermare.
Se il calendario ufficiale non è leggibile o non coincide con FRED® sulle date
già note, le date vengono dal solo FRED® e risultano da confermare.

Decisioni FOMC: confronto tra la pagina FOMC e il calendario JSON della Fed,
più le date FRED® delle proiezioni economiche (SEP).
BLS e DOL: solo calendario FRED® (i siti non consentono la lettura automatica).

Dopo ogni uscita si verifica che il dato sia arrivato su FRED®: se manca da più
di 24 ore l'uscita risulta "non pubblicata" e le date successive della stessa
agenzia diventano da confermare (es. uno shutdown). Se il dato è arrivato dopo
l'ultimo download, le serie collegate vengono riscaricate.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from datetime import date, datetime, time as dtime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from catalog import RELEASES, SIGNALS, signal_series_ids
from config import LEVEL_COLORS
from utils import data, fmt, official
from utils import signals as S

ROME = ZoneInfo("Europe/Rome")
ET = official.ET
IMPORTANCE = {3: "alta", 2: "media", 1: "bassa"}
_FRED_BACK, _FRED_AHEAD = 150, 80      # giorni chiesti a FRED® (stessa cache per tutte le pagine)
_LATE = timedelta(hours=24)            # oltre questo ritardo un'uscita risulta non pubblicata
_TOLERANCE = timedelta(minutes=10)
_COLUMNS = ["key", "name", "detail", "importance", "agency", "when", "day", "time",
            "status", "note", "basis", "source_url", "past", "arrival"]
# basis: "doppia" = due fonti concordi, "ufficiale" = solo calendario ufficiale (verificato
# sulle date già note), "fred" = solo calendario FRED® (BLS e DOL, o fonte ufficiale assente)
BASIS_TEXT = {"doppia": "✓ Confermata da 2 fonti", "ufficiale": "✓ Calendario ufficiale",
              "fred": "Calendario FRED®"}


@dataclass
class Calendar:
    df: pd.DataFrame                                  # una riga per uscita
    sources: dict[str, official.SourceStatus]         # stato dei calendari ufficiali
    now: datetime                                     # ora di Roma del calcolo
    warnings: list[str] = field(default_factory=list)
    fred_until: date | None = None                    # ultima data nota a FRED® per BLS e DOL

    @property
    def today(self) -> date:
        return self.now.date()


# =============================================================================
# COSTRUZIONE
# =============================================================================

def _fred_dates() -> dict[int, set[date]]:
    """Date del calendario FRED® per release (solleva un'eccezione senza chiave)."""
    ids = tuple(sorted({r.fred_id for r in RELEASES.values() if r.fred_id}))
    df = data.release_dates(ids, _FRED_BACK, _FRED_AHEAD)
    df = df[df["date"].dt.weekday < 5]  # nessun dato USA esce nel fine settimana
    counts = df.groupby("release_id")["date"].nunique()
    daily = set(counts[counts > (_FRED_BACK + _FRED_AHEAD) / 2].index)  # serie giornaliere
    return {int(rid): {ts.date() for ts in grp["date"]}
            for rid, grp in df.groupby("release_id") if rid not in daily}


def _at(key: str, d: date) -> datetime:
    """Data senza orario (FRED®) all'orario abituale dell'uscita, a New York."""
    hh, mm = (int(x) for x in RELEASES[key].time_et.split(":"))
    return datetime.combine(d, dtime(hh, mm), tzinfo=ET)


def _row(key: str, when_et: datetime, detail: str, status: str, note: str = "",
         basis: str = "fred") -> dict:
    rel = RELEASES[key]
    when = when_et.astimezone(ROME)
    return {"key": key, "name": rel.name, "detail": detail, "importance": rel.importance,
            "agency": rel.agency, "when": when, "day": when.date(), "time": when.strftime("%H:%M"),
            "status": status, "note": note, "basis": basis, "source_url": rel.source_url}


def _official_for(key: str, events: dict[str, list[official.Event]]) -> dict[date, official.Event] | None:
    """Date ufficiali dell'uscita; None se nessun calendario ufficiale è disponibile."""
    out: dict[date, official.Event] = {}
    for name in RELEASES[key].official:  # il primo calendario dell'elenco ha la precedenza
        for e in events.get(name, []):
            if e.key == key:
                out.setdefault(e.when.date(), e)
    return out or None


def _release_rows(key: str, fred: set[date], off: dict[date, official.Event] | None,
                  today: date) -> list[dict]:
    rel = RELEASES[key]
    if not rel.official:  # BLS e DOL: solo calendario FRED®
        rows = []
        for d in sorted(fred):
            status, note = "ok", ""
            if key == "claims" and d.weekday() not in (2, 3):
                status, note = "check", "Giorno insolito: i sussidi escono di norma il giovedì."
            rows.append(_row(key, _at(key, d), "", status, note))
        return rows
    if not off:
        return [_row(key, _at(key, d), "", "check",
                     "Calendario ufficiale non raggiungibile: data dal solo calendario FRED®.")
                for d in sorted(fred)]
    if not fred:
        return [_row(key, e.when, e.detail, "check", "Calendario FRED® non disponibile per il confronto.",
                     "ufficiale") for e in off.values()]
    fred_start, fred_end, off_end = min(fred), max(fred), max(off)
    # confronto solo sul periodo coperto da entrambe le fonti
    known = {d for d in off if fred_start <= d <= fred_end}
    confirmed = known & fred
    if not confirmed or len(confirmed) < len(known) / 2:
        return [_row(key, _at(key, d), "", "check",
                     "Calendario ufficiale e FRED® non coincidono: verifica la data sul sito ufficiale.")
                for d in sorted(fred)]
    rows = []
    for d, e in sorted(off.items()):
        if d in fred:
            rows.append(_row(key, e.when, e.detail, "ok", basis="doppia"))
        elif d > fred_end:
            rows.append(_row(key, e.when, e.detail, "ok", basis="ufficiale"))
        else:
            rows.append(_row(key, e.when, e.detail, "check", "Data non confermata dal calendario FRED®.",
                             "ufficiale"))
    for d in sorted(fred - set(off)):
        if d > off_end:
            rows.append(_row(key, _at(key, d), "", "check", "Data non ancora nel calendario ufficiale."))
        # le altre date solo FRED® non sono uscite ufficiali (aggiornamenti secondari)
    return rows


def _fomc_rows(sep: set[date], events: dict[str, list[official.Event]], today: date) -> list[dict]:
    page = {e.when.date(): e for e in events.get("fomc_page", []) if e.key == "fomc"}
    js = {e.when.date(): e for e in events.get("fed_json", []) if e.key == "fomc"}
    if not page and not js:
        return []
    # confronto tra le due fonti Fed sulle riunioni recenti e future dell'anno in corso
    lo, hi = today - timedelta(days=30), date(today.year, 12, 31)
    page_cmp = {d for d in page if lo <= d <= hi}
    js_cmp = {d for d in js if lo <= d <= hi}
    compared = bool(page_cmp and js_cmp)
    agree = page_cmp == js_cmp if compared else None
    # le riunioni con proiezioni (SEP) note a FRED® devono comparire nei calendari Fed
    sep_ok = all(d in page or d in js for d in sep)
    trusted = agree if agree is not None else sep_ok
    rows = []
    for d in sorted(set(page) | set(js)):
        e = page.get(d) or js[d]
        detail = e.detail or (official.SEP_DETAIL if d in sep else "")
        if compared and lo <= d <= hi:
            ok = d in page_cmp and d in js_cmp
            note = "" if ok else "Le due fonti della Fed non coincidono su questa data."
            basis = "doppia" if ok else "ufficiale"
        else:
            ok = bool(trusted)
            note = "" if ok else "Data presente in una sola fonte della Fed: verificala sul sito."
            basis = "doppia" if (d in sep or (d in page and d in js)) else "ufficiale"
        rows.append(_row("fomc", e.when, detail, "ok" if ok else "check", note, basis))
    return rows


def _check_arrivals(df: pd.DataFrame, now: datetime) -> pd.DataFrame:
    """Per le uscite passate verifica che il dato sia arrivato su FRED®."""
    df["past"] = df["when"] <= now
    df["arrival"] = ""
    recent = df[df["past"] & (df["when"] >= now - timedelta(days=12))]
    series = sorted({RELEASES[k].check_series for k in recent["key"] if RELEASES[k].check_series})
    updated = data.series_last_updated(tuple(series)) if series else {}
    if not updated:
        return df  # senza chiave o con l'API non raggiungibile il controllo non è disponibile
    all_ids = signal_series_ids({s for k in recent["key"] for s in RELEASES[k].signals})
    fetched = data.fetched_each(all_ids)
    stale: set[str] = set()
    for idx, r in recent.iterrows():
        rel = RELEASES[r["key"]]
        last = updated.get(rel.check_series) if rel.check_series else None
        if last is None:
            continue
        if last >= r["when"].astimezone(timezone.utc) - _TOLERANCE:
            df.at[idx, "arrival"] = "ok"
            ids = signal_series_ids(rel.signals)
            if any(fetched.get(i) is not None and fetched[i] < last for i in ids):
                stale.update(ids)  # il dato in memoria è precedente all'uscita
        elif now - r["when"] < _LATE:
            df.at[idx, "arrival"] = "attesa"
        else:
            df.at[idx, "arrival"] = "mancante"
    if stale:
        data.mark_stale(sorted(stale))
    return df


def get_calendar() -> Calendar | None:
    """Calendario verificato, o None se il calendario FRED® non è disponibile."""
    try:
        fred = _fred_dates()
    except Exception:  # noqa: BLE001 - chiave assente o API non raggiungibile
        return None
    events, sources = official.official_events()
    now = datetime.now(ROME)
    today = now.date()
    rows: list[dict] = []
    for key, rel in RELEASES.items():
        f_dates = fred.get(rel.fred_id, set()) if rel.fred_id else set()
        if key == "fomc":
            rows += _fomc_rows(f_dates, events, today)
        else:
            rows += _release_rows(key, f_dates, _official_for(key, events), today)
    df = pd.DataFrame(rows, columns=_COLUMNS[:-2])
    df = df.drop_duplicates(["key", "when"]).sort_values(["when", "importance"], ascending=[True, False])
    df = _check_arrivals(df.reset_index(drop=True), now)

    warnings = []
    for agency, grp in df[df["arrival"] == "mancante"].groupby("agency"):
        last = max(grp["day"])
        mask = (~df["past"]) & (df["agency"] == agency)
        df.loc[mask, "status"] = "check"
        df.loc[mask, "note"] = (f"{agency}: l'uscita del {last:%d/%m} non risulta pubblicata "
                                "(possibile rinvio o shutdown). Date da confermare.")
        warnings.append(df.loc[mask, "note"].iloc[0] if mask.any() else
                        f"{agency}: l'uscita del {last:%d/%m} non risulta pubblicata.")
    fed_down = not sources["fomc_page"].ok and not sources["fed_json"].ok
    if fed_down:
        warnings.append("Date FOMC non verificabili: i calendari della Fed non sono raggiungibili.")
    fred_only = [fred.get(r.fred_id, set()) for r in RELEASES.values() if not r.official and r.fred_id]
    fred_until = max((max(s) for s in fred_only if s), default=None)
    return Calendar(df, sources, now, warnings, fred_until)


def horizon_note(cal: Calendar, days_ahead: int) -> str | None:
    """Avviso se il periodo mostrato va oltre le date note a FRED® per BLS e DOL."""
    if cal.fred_until is None or cal.today + timedelta(days=days_ahead) <= cal.fred_until:
        return None
    return (f"CPI, PPI, occupazione, JOLTS e sussidi: il calendario FRED® arriva al "
            f"{cal.fred_until:%d/%m/%Y}. Le uscite successive compariranno appena FRED® le pubblica.")


# =============================================================================
# PRESENTAZIONE
# =============================================================================

def unavailable_note() -> None:
    if not data.api_key():
        st.info("Il calendario delle uscite richiede la chiave FRED® (`FRED_API_KEY`).",
                icon=":material/event_busy:")
    else:
        st.info("Calendario momentaneamente non disponibile: verrà riprovato a breve.",
                icon=":material/event_busy:")


def day_label(d: date, today: date) -> str:
    if d == today:
        return "Oggi"
    if d == today + timedelta(days=1):
        return "Domani"
    return f"{fmt.GIORNI[d.weekday()]} {d:%d/%m}"


def _imp_badge(imp: int) -> str:
    cls = "kq-imp alta" if imp == 3 else "kq-imp"
    return f"<span class='{cls}'>{IMPORTANCE[imp]}</span>"


def _check_badge(note: str) -> str:
    return f"<span class='kq-check' title='{html.escape(note, quote=True)}'>⚠ da confermare</span>"


def _source_link(url: str) -> str:
    return (f"<a class='kq-src' href='{html.escape(url, quote=True)}' target='_blank' rel='noopener' "
            f"title='Verifica la data sul sito ufficiale'>fonte ↗</a>")


def _item(day_html: str, body: str) -> str:
    return (f"<div class='kq-list-item'><div class='kq-list-date'>{day_html}</div>"
            f"<div class='kq-list-body'>{body}</div></div>")


def _warnings_html(cal: Calendar) -> str:
    return "".join(_item("<span class='kq-warn'>⚠</span>", f"<small class='kq-warn'>{html.escape(w)}</small>")
                   for w in cal.warnings)


def upcoming(cal: Calendar, days_ahead: int) -> pd.DataFrame:
    df = cal.df
    return df[(~df["past"]) & (df["day"] <= cal.today + timedelta(days=days_ahead))]


def recent(cal: Calendar, days_back: int) -> pd.DataFrame:
    df = cal.df
    return df[df["past"] & (df["day"] >= cal.today - timedelta(days=days_back))]


def upcoming_html(cal: Calendar, days_ahead: int, max_items: int | None = None) -> str:
    up = upcoming(cal, days_ahead).sort_values(["when", "importance"], ascending=[True, False])
    if max_items:
        up = up.head(max_items)
    out = [_warnings_html(cal)]
    if up.empty:
        out.append("<div class='kq-list-body'><small>Nessuna uscita in programma nel periodo.</small></div>")
    for _, r in up.iterrows():
        check = r["status"] == "check"
        body = (f"{html.escape(r['name'])}{_imp_badge(r['importance'])}"
                f"{_check_badge(r['note']) if check else ''} {_source_link(r['source_url'])}")
        if r["detail"]:
            body += f"<br><small>{html.escape(r['detail'])}</small>"
        if check:
            body += f"<br><small class='kq-warn'>{html.escape(r['note'])}</small>"
        out.append(_item(f"{day_label(r['day'], cal.today)}<br><span class='kq-time'>{r['time']}</span>", body))
    note = horizon_note(cal, days_ahead)
    if note:
        out.append(f"<div class='kq-list-body' style='padding-top:8px'><small>{html.escape(note)}</small></div>")
    return "".join(out)


def recent_html(cal: Calendar, d: dict[str, pd.Series], days_back: int, max_items: int | None = None) -> str:
    past = recent(cal, days_back).sort_values(["when", "importance"], ascending=[False, False])
    past = past.drop_duplicates("key")  # una riga per uscita (la più recente)
    if max_items:
        past = past.head(max_items)
    if past.empty:
        return "<div class='kq-list-body'><small>Nessuna uscita recente.</small></div>"
    out = []
    for _, r in past.iterrows():
        rel = RELEASES[r["key"]]
        head = f"{html.escape(rel.name)}{_imp_badge(rel.importance)} {_source_link(r['source_url'])}"
        if r["detail"]:
            head += f"<br><small>{html.escape(r['detail'])}</small>"
        if r["arrival"] == "attesa":
            body = "<small>Dato in arrivo su FRED®: verrà mostrato appena disponibile.</small>"
        elif r["arrival"] == "mancante":
            body = "<small class='kq-warn'>⚠ Il dato non risulta pubblicato: possibile rinvio.</small>"
        else:
            body = "<small>" + "<br>".join(_values(rel, d)) + "</small>"
        out.append(_item(f"{day_label(r['day'], cal.today)}<br><span class='kq-time'>{r['time']}</span>",
                         f"{head}<br>{body}"))
    return "".join(out)


def _values(rel, d: dict[str, pd.Series]) -> list[str]:
    lines = []
    for key in rel.signals:
        if key not in SIGNALS:
            continue
        rd = S.evaluate(key, d)
        if rd is None:
            continue
        sig = SIGNALS[key]
        prev = f" (prec. {S.value_text(sig, rd.prev_value)})" if rd.prev_value is not None else ""
        lines.append(
            f"<span class='kq-dot' style='background:{LEVEL_COLORS[rd.level]};width:8px;height:8px'></span> "
            f"{sig.label}: <b>{S.value_text(sig, rd.value)}</b>{prev}"
            f" · {fmt.date_label(rd.date, S.freq_of(sig))}"
        )
    return lines


def sources_text(cal: Calendar) -> str:
    """Riepilogo delle verifiche, per la didascalia della pagina Calendario."""
    text = (f"Verifica automatica delle date alle {cal.now:%H:%M} (ora italiana): i calendari ufficiali "
            "di Fed (FOMC e produzione industriale), BEA (PIL, PCE) e Census (vendite al dettaglio, "
            "cantieri) sono confrontati con il calendario FRED®. Per CPI, PPI, occupazione e JOLTS "
            "(BLS) e per i sussidi (DOL) la fonte è il solo calendario FRED®, perché i loro siti non "
            "consentono la lettura automatica; dopo ogni uscita si controlla che il dato sia arrivato.")
    down = [official.SOURCE_LABELS[n] for n, s in cal.sources.items() if not s.ok]
    if down:
        text += (" Non raggiungibili in questo momento: " + ", ".join(down)
                 + ". Le date collegate sono segnate come da confermare.")
    return text


def signals_for_releases() -> list[str]:
    keys: list[str] = []
    for rel in RELEASES.values():
        keys.extend(k for k in rel.signals if k in SIGNALS)
    return list(dict.fromkeys(keys))
