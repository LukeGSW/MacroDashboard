"""Calendario delle uscite dei dati (condiviso da Cruscotto e Calendario)."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from catalog import RELEASES, SIGNALS
from config import LEVEL_COLORS
from utils import data, fmt
from utils import signals as S

IMPORTANCE = {3: "alta", 2: "media", 1: "bassa"}


def get_calendar(days_back: int, days_ahead: int) -> pd.DataFrame | None:
    """Release del catalogo nel periodo indicato, o None se non disponibile."""
    try:
        df = data.release_dates(tuple(sorted(RELEASES)), days_back, days_ahead)
    except data.DataUnavailable:
        return None
    except Exception:  # noqa: BLE001
        return None
    df = df.copy()
    df["name"] = df["release_id"].map(lambda r: RELEASES[r].name)
    df["importance"] = df["release_id"].map(lambda r: RELEASES[r].importance)
    return df


def unavailable_note() -> None:
    if not data.api_key():
        st.info("Il calendario delle uscite richiede la chiave FRED® (`FRED_API_KEY`).",
                icon=":material/event_busy:")
    else:
        st.info("Calendario momentaneamente non disponibile: verrà riprovato a breve.",
                icon=":material/event_busy:")


def _imp_badge(imp: int) -> str:
    label = IMPORTANCE[imp]
    cls = "kq-imp alta" if imp == 3 else "kq-imp"
    return f"<span class='{cls}'>{label}</span>"


def upcoming_html(df: pd.DataFrame, max_items: int | None = None, min_importance: int = 1) -> str:
    today = pd.Timestamp(date.today())
    up = df[(df["date"] >= today) & (df["importance"] >= min_importance)].sort_values(["date", "importance"],
                                                                                     ascending=[True, False])
    if max_items:
        up = up.head(max_items)
    if up.empty:
        return "<div class='kq-list-body'><small>Nessuna uscita in programma nel periodo.</small></div>"
    rows = []
    for _, r in up.iterrows():
        when = "Oggi" if r["date"] == today else f"{fmt.GIORNI[r['date'].weekday()]} {r['date']:%d/%m}"
        rows.append(f"<div class='kq-list-item'><div class='kq-list-date'>{when}</div>"
                    f"<div class='kq-list-body'>{r['name']}{_imp_badge(r['importance'])}</div></div>")
    return "".join(rows)


def recent_html(df: pd.DataFrame, d: dict[str, pd.Series], max_items: int | None = None,
                min_importance: int = 1) -> str:
    today = pd.Timestamp(date.today())
    past = df[(df["date"] <= today) & (df["importance"] >= min_importance)]
    past = past.sort_values(["date", "importance"], ascending=[False, False])
    # una riga per release (l'uscita più recente)
    past = past.drop_duplicates("release_id")
    if max_items:
        past = past.head(max_items)
    if past.empty:
        return "<div class='kq-list-body'><small>Nessuna uscita recente.</small></div>"
    rows = []
    for _, r in past.iterrows():
        rel = RELEASES[r["release_id"]]
        details = []
        for key in rel.signals:
            if key not in SIGNALS:
                continue
            rd = S.evaluate(key, d)
            if rd is None:
                continue
            sig = SIGNALS[key]
            color = LEVEL_COLORS[rd.level]
            prev = f" (prec. {S.value_text(sig, rd.prev_value)})" if rd.prev_value is not None else ""
            details.append(
                f"<span class='kq-dot' style='background:{color};width:8px;height:8px'></span> "
                f"{sig.label}: <b>{S.value_text(sig, rd.value)}</b>{prev}"
                f" · {fmt.date_label(rd.date, S.freq_of(sig))}"
            )
        body = "<br>".join(details) if details else ""
        when = "Oggi" if r["date"] == today else f"{fmt.GIORNI[r['date'].weekday()]} {r['date']:%d/%m}"
        rows.append(f"<div class='kq-list-item'><div class='kq-list-date'>{when}</div>"
                    f"<div class='kq-list-body'>{rel.name}{_imp_badge(rel.importance)}"
                    f"{'<br><small>' + body + '</small>' if body else ''}</div></div>")
    return "".join(rows)


def signals_for_releases() -> list[str]:
    keys: list[str] = []
    for rel in RELEASES.values():
        keys.extend(k for k in rel.signals if k in SIGNALS)
    return list(dict.fromkeys(keys))
