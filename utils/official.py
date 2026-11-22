"""
Calendari ufficiali delle agenzie, letti in automatico
======================================================
Fonte principale delle date (e controllo del calendario FRED®) per le uscite
che le agenzie pubblicano in un formato leggibile da programma:

- Fed: pagina del calendario FOMC (anno in corso e successivo) e calendario JSON
  della Fed (anno in corso) per le decisioni FOMC; pagina della G.17 e calendario
  JSON per la produzione industriale.
- BEA: calendario ICS ufficiale (PIL, redditi e spese delle famiglie).
- Census: calendario degli indicatori economici (vendite al dettaglio, cantieri).

Il sito del BLS blocca la lettura automatica e il DOL non pubblica un calendario
annuale dei sussidi: per queste uscite si usa il solo calendario FRED®.

Ogni lettore restituisce una lista di ``Event`` o solleva ``SourceError`` se la
pagina non risponde o non ha la struttura attesa (in quel caso le date non
vengono inventate: il calendario le segnala come da confermare). Le letture
riuscite restano in memoria 6 ore; dopo un errore si riprova dopo 30 minuti e
nel frattempo si usa l'ultima lettura riuscita, se ha meno di 3 giorni.
"""

from __future__ import annotations

import html
import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Callable
from zoneinfo import ZoneInfo

import requests
import streamlit as st

log = logging.getLogger("macro_dashboard")

ET = ZoneInfo("America/New_York")

FOMC_PAGE = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
FED_JSON = "https://www.federalreserve.gov/json/calendar.json"
G17_PAGE = "https://www.federalreserve.gov/releases/g17/default.htm"
BEA_ICS = "https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics"
CENSUS_LIST = "https://www.census.gov/economic-indicators/calendar-listview{suffix}.html"

_HEADERS = {"User-Agent": "kq-macro-dashboard/2.0 (calendario delle uscite)"}
_TIMEOUT = 15
_OK_TTL = 6 * 3600
_FAIL_TTL = 30 * 60
_MAX_STALE = 3 * 86400

_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"]
_MONTH_NUM = {m: i for i, m in enumerate(_MONTHS, start=1)}
_MONTH3 = {m[:3]: i for m, i in _MONTH_NUM.items()}
_MONTHS_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto",
              "settembre", "ottobre", "novembre", "dicembre"]
SEP_DETAIL = "con proiezioni economiche (SEP)"


class SourceError(Exception):
    """Calendario ufficiale non raggiungibile o con struttura inattesa."""


@dataclass(frozen=True)
class Event:
    key: str            # uscita del catalogo (es. "gdp")
    when: datetime      # data e ora a New York (con fuso orario)
    detail: str = ""    # es. "seconda stima T3 2026", "ottobre 2026"


# =============================================================================
# SUPPORTO
# =============================================================================

def _get(url: str) -> str:
    try:
        r = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise SourceError(type(exc).__name__) from None
    if r.status_code != 200:
        raise SourceError(f"HTTP {r.status_code}")
    return r.content.decode("utf-8-sig", errors="replace")


def _text(fragment: str) -> str:
    """Testo semplice da un frammento HTML, con gli spazi normalizzati."""
    t = html.unescape(re.sub(r"<[^>]+>", " ", fragment)).replace("\xa0", " ")
    return re.sub(r"\s+", " ", t).strip()


def _et(y: int, m: int, d: int, hh: int, mm: int) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=ET)


def _clock(s: str, default: tuple[int, int]) -> tuple[int, int]:
    """'2:00 p.m.' / '8:30 AM' / 'noon' -> (ore, minuti); default se assente."""
    s = (s or "").strip().lower()
    if "noon" in s:
        return 12, 0
    m = re.match(r"(\d{1,2}):(\d{2})\s*([ap])\.?\s*m", s)
    if not m:
        return default
    hh, mm = int(m.group(1)) % 12, int(m.group(2))
    return (hh + 12 if m.group(3) == "p" else hh), mm


def month_it(text: str) -> str:
    """'October 2026' (anche dentro una frase) -> 'ottobre 2026'."""
    m = re.search(r"(" + "|".join(_MONTHS) + r") (\d{4})", text or "")
    return f"{_MONTHS_IT[_MONTH_NUM[m.group(1)] - 1]} {m.group(2)}" if m else ""


# =============================================================================
# LETTORI
# =============================================================================

def read_fomc_page() -> list[Event]:
    """Giorni delle decisioni FOMC dalla pagina ufficiale (anno in corso e successivo)."""
    page = _get(FOMC_PAGE)
    heads = list(re.finditer(r"(\d{4}) FOMC Meetings\s*</a>", page))
    events: list[Event] = []
    for i, h in enumerate(heads):
        year = int(h.group(1))
        end = heads[i + 1].start() if i + 1 < len(heads) else len(page)
        for row in re.split(r'class="[^"]*\brow fomc-meeting"', page[h.end():end])[1:]:
            mon = re.search(r"fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>", row)
            day = re.search(r"fomc-meeting__date[^>]*>([^<]+)<", row)
            if not (mon and day):
                continue
            days = day.group(1).strip()
            # esclusi: riunioni sulla strategia, voti senza riunione, riunioni straordinarie
            if "Strategy Meeting" in row or re.search(r"notation|unscheduled|cancel", days, re.I):
                continue
            nums = re.findall(r"\d+", days)
            month = _MONTH3.get(mon.group(1).split("/")[-1].strip()[:3])
            if len(nums) != 2 or month is None:
                continue
            # la decisione arriva il secondo giorno della riunione, alle 14:00 di New York
            events.append(Event("fomc", _et(year, month, int(nums[1]), 14, 0),
                                SEP_DETAIL if "*" in days else ""))
    this_year = [e for e in events if e.when.year == date.today().year]
    if len(this_year) < 6 or any(e.when.weekday() > 4 for e in events):
        raise SourceError("pagina FOMC con struttura inattesa")
    return events


def read_fed_json() -> list[Event]:
    """Riunioni FOMC e uscite G.17 dal calendario JSON della Fed (anno in corso)."""
    try:
        raw = json.loads(_get(FED_JSON))
    except json.JSONDecodeError:
        raise SourceError("calendario JSON della Fed non valido") from None
    events: list[Event] = []
    for e in raw.get("events", []):
        title, kind = (e.get("title") or "").strip(), e.get("type")
        if kind == "FOMC" and title == "FOMC Meeting":
            key, default = "fomc", (14, 0)
        elif kind == "Stat" and title.startswith("G.17"):
            key, default = "ip", (9, 15)
        else:
            continue
        try:
            y, m = (int(x) for x in str(e["month"]).split("-"))
            d = int(re.findall(r"\d+", str(e["days"]))[-1])
            events.append(Event(key, _et(y, m, d, *_clock(e.get("time", ""), default))))
        except (KeyError, ValueError, IndexError):
            continue
    if not any(ev.key == "fomc" for ev in events):
        raise SourceError("calendario JSON della Fed senza riunioni FOMC")
    return events


def read_g17_page() -> list[Event]:
    """Date della G.17 (anno in corso e successivo), compresa la revisione annuale."""
    text = _text(_get(G17_PAGE))
    start = text.find("following dates")
    if start < 0:
        raise SourceError("pagina G.17 con struttura inattesa")
    parts = re.split(r"\b(20\d\d):", text[start:start + 4000])
    events: list[Event] = []
    for year, body in zip(parts[1::2], parts[2::2]):
        for mon, dd, note in re.findall(r"([A-Z][a-z]+) (\d{1,2})(?: \(([^)]*)\))?", body.split(". ")[0]):
            if mon not in _MONTH_NUM:
                continue
            annual = "annual" in (note or "").lower()   # revisione annuale: alle 12:00
            hh, mm = (12, 0) if annual else (9, 15)
            events.append(Event("ip", _et(int(year), _MONTH_NUM[mon], int(dd), hh, mm),
                                "revisione annuale" if annual else ""))
    if sum(1 for e in events if e.when.year == date.today().year) < 10:
        raise SourceError("pagina G.17 con struttura inattesa")
    return events


_BEA_EST = {"advance": "stima preliminare", "second": "seconda stima", "third": "terza stima"}


def _gdp_detail(summary: str) -> str:
    est = re.search(r"(Advance|Second|Third) Estimate", summary)
    q = re.search(r"(\d)(?:st|nd|rd|th) Quarter(?: and Year)? (\d{4})", summary)
    parts = [_BEA_EST[est.group(1).lower()]] if est else []
    if q:
        parts.append(f"T{q.group(1)} {q.group(2)}")
    return " ".join(parts)


def read_bea_ics() -> list[Event]:
    """PIL e redditi/spese delle famiglie dal calendario ICS ufficiale della BEA."""
    ics = re.sub(r"\r?\n[ \t]", "", _get(BEA_ICS))  # righe spezzate (RFC 5545)
    events: list[Event] = []
    for block in ics.split("BEGIN:VEVENT")[1:]:
        s = re.search(r"^SUMMARY[^:\r\n]*:(.*?)\r?$", block, re.M)
        t = re.search(r"^DTSTART([^:\r\n]*):(\d{8}T\d{4,6})(Z?)", block, re.M)
        if not (s and t):
            continue
        summary = s.group(1).replace("\\,", ",").replace("\\;", ";").strip()
        try:
            when = datetime.strptime(t.group(2).ljust(15, "0"), "%Y%m%dT%H%M%S")
            if t.group(3) == "Z":
                when = when.replace(tzinfo=timezone.utc)
            else:
                tzid = re.search(r"TZID=([^;:]+)", t.group(1))
                when = when.replace(tzinfo=ZoneInfo(tzid.group(1)) if tzid else ET)
        except (ValueError, KeyError):
            continue
        when = when.astimezone(ET)
        if re.match(r"(GDP \(|Gross Domestic Product,)", summary):
            events.append(Event("gdp", when, _gdp_detail(summary)))
        elif summary.startswith("Personal Income and Outlays"):
            events.append(Event("pce", when, month_it(summary)))
    if not any(e.key == "gdp" for e in events) or not any(e.key == "pce" for e in events):
        raise SourceError("calendario BEA con struttura inattesa")
    return events


def read_census() -> list[Event]:
    """Vendite al dettaglio e cantieri dal calendario degli indicatori Census."""
    year = date.today().year
    found: dict[tuple[str, datetime], list[str]] = {}
    pages_ok = 0
    for suffix in ("", f"-{year - 1}", f"-{year}", f"-{year + 1}"):
        try:
            page = _get(CENSUS_LIST.format(suffix=suffix))
        except SourceError:
            continue  # gli anni non ancora pubblicati non esistono
        pages_ok += 1
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
            cells = [_text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
            if len(cells) < 3:
                continue
            if cells[0].startswith("Advance Monthly Sales for Retail"):
                key = "retail"
            elif cells[0].startswith("New Residential Construction"):
                key = "housing"
            else:
                continue
            try:
                d = datetime.strptime(cells[1], "%B %d, %Y")
            except ValueError:
                continue
            when = _et(d.year, d.month, d.day, *_clock(cells[2], (8, 30)))
            period = month_it(cells[3]) if len(cells) > 3 else ""
            # a volte un'uscita copre due mesi (es. dopo lo shutdown del 2025)
            details = found.setdefault((key, when), [])
            if period and period not in details:
                details.append(period)
    events = [Event(k, w, " e ".join(p)) for (k, w), p in found.items()]
    if not pages_ok or not any(e.key == "retail" for e in events) \
            or not any(e.key == "housing" for e in events):
        raise SourceError("calendario Census con struttura inattesa")
    return events


READERS: dict[str, Callable[[], list[Event]]] = {
    "fomc_page": read_fomc_page,
    "fed_json": read_fed_json,
    "g17_page": read_g17_page,
    "bea": read_bea_ics,
    "census": read_census,
}

SOURCE_LABELS = {
    "fomc_page": "Fed, calendario FOMC",
    "fed_json": "Fed, calendario JSON",
    "g17_page": "Fed, calendario G.17",
    "bea": "BEA, calendario ICS",
    "census": "Census, calendario indicatori",
}


# =============================================================================
# MEMORIA CONDIVISA
# =============================================================================

@dataclass(frozen=True)
class SourceStatus:
    ok: bool                 # dati disponibili (lettura recente o ultima copia valida)
    read_at: float | None    # ora dell'ultima lettura riuscita (epoch)
    error: str | None        # errore dell'ultimo tentativo, se fallito
    stale: bool = False      # si sta usando una copia precedente all'ultimo tentativo


class _Store:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._good: dict[str, tuple[float, list[Event]]] = {}
        self._fail: dict[str, tuple[float, str]] = {}

    def _due(self, name: str, now: float) -> bool:
        good, fail = self._good.get(name), self._fail.get(name)
        if good and now - good[0] < _OK_TTL:
            return False
        if fail and now - fail[0] < _FAIL_TTL:
            return False
        return True

    def get_all(self) -> tuple[dict[str, list[Event]], dict[str, SourceStatus]]:
        now = time.time()
        with self._lock:
            due = [n for n in READERS if self._due(n, now)]
        if due:
            with ThreadPoolExecutor(max_workers=len(due)) as pool:
                futures = {n: pool.submit(READERS[n]) for n in due}
            for n, fut in futures.items():
                try:
                    events = fut.result()
                except Exception as exc:  # noqa: BLE001 - si segnala, non si inventano date
                    msg = str(exc) if isinstance(exc, SourceError) else type(exc).__name__
                    log.warning("Calendario ufficiale %s non letto: %s", n, msg)
                    with self._lock:
                        self._fail[n] = (time.time(), msg)
                    continue
                with self._lock:
                    self._good[n] = (time.time(), events)
                    self._fail.pop(n, None)
        events_by_source: dict[str, list[Event]] = {}
        status: dict[str, SourceStatus] = {}
        with self._lock:
            for n in READERS:
                good, fail = self._good.get(n), self._fail.get(n)
                usable = good is not None and now - good[0] < _MAX_STALE
                if usable:
                    events_by_source[n] = good[1]
                status[n] = SourceStatus(
                    ok=usable,
                    read_at=good[0] if good else None,
                    error=fail[1] if fail else None,
                    stale=bool(usable and fail and fail[0] > good[0]),
                )
        return events_by_source, status


@st.cache_resource(show_spinner=False)
def _store() -> _Store:
    return _Store()


def official_events() -> tuple[dict[str, list[Event]], dict[str, SourceStatus]]:
    """Eventi per calendario ufficiale (solo quelli disponibili) e stato di ogni fonte."""
    return _store().get_all()
