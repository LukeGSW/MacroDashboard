"""
Accesso ai dati FRED®
=====================
- Una sola chiamata per serie (storia completa), condivisa tra pagine e utenti
  tramite una cache di processo con scadenza (``CACHE_TTL_HOURS``).
- Download in parallelo con limite di richieste al minuto (rispetto dei limiti
  dell'API FRED®) e nuovi tentativi in caso di errori temporanei.
- Se un aggiornamento fallisce si continua a mostrare l'ultimo dato valido.
- Calendario delle uscite dalle API ``release/dates``.

La chiave si legge da ``st.secrets["FRED_API_KEY"]`` o dalla variabile
d'ambiente ``FRED_API_KEY``. Solo per sviluppo locale senza chiave si può
impostare ``KQ_DEV_PUBLIC_CSV=1`` per leggere i CSV pubblici (niente calendario).
"""

from __future__ import annotations

import io
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

import pandas as pd
import requests
import streamlit as st

from config import CACHE_TTL_HOURS, CALENDAR_TTL_HOURS

log = logging.getLogger("macro_dashboard")

_API = "https://api.stlouisfed.org/fred"
_PUBLIC_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
_HEADERS = {"User-Agent": "kq-macro-dashboard/2.0"}
_MAX_WORKERS = 6


class DataUnavailable(Exception):
    """Dato non scaricabile (messaggio sempre privo della chiave API)."""


# =============================================================================
# CHIAVE E MODALITA'
# =============================================================================

def api_key() -> str | None:
    try:
        key = st.secrets["FRED_API_KEY"]
    except Exception:  # nessun secrets.toml o chiave assente
        key = None
    return key or os.environ.get("FRED_API_KEY")


def dev_public_mode() -> bool:
    return not api_key() and os.environ.get("KQ_DEV_PUBLIC_CSV") == "1"


# =============================================================================
# HTTP con limite di frequenza e nuovi tentativi
# =============================================================================

class _TokenBucket:
    """Max ~100 richieste/minuto (limite FRED: 120) con un picco iniziale consentito."""

    def __init__(self, per_minute: float = 100.0, capacity: int = 60) -> None:
        self.rate = per_minute / 60.0
        self.capacity = capacity
        self.tokens = float(capacity)
        self.stamp = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.stamp) * self.rate)
                self.stamp = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait = (1.0 - self.tokens) / self.rate
            time.sleep(wait)


_bucket = _TokenBucket()
_local = threading.local()


def _session() -> requests.Session:
    sess = getattr(_local, "session", None)
    if sess is None:
        sess = requests.Session()
        sess.headers.update(_HEADERS)
        _local.session = sess
    return sess


def _get(url: str, params: dict | None, what: str) -> requests.Response:
    last = "errore sconosciuto"
    for attempt in range(4):
        _bucket.acquire()
        try:
            r = _session().get(url, params=params, timeout=25)
        except requests.RequestException as exc:  # il testo può contenere l'URL con la chiave
            last = type(exc).__name__
        else:
            if r.status_code == 200:
                return r
            if r.status_code not in (429, 500, 502, 503, 504):
                raise DataUnavailable(f"{what}: risposta HTTP {r.status_code}")
            last = f"HTTP {r.status_code}"
        time.sleep(1.5 * (attempt + 1))
    raise DataUnavailable(f"{what}: {last}")


def _api_json(endpoint: str, params: dict, key: str, what: str) -> dict:
    full = {**params, "api_key": key, "file_type": "json"}
    return _get(f"{_API}/{endpoint}", full, what).json()


# =============================================================================
# SERIE
# =============================================================================

def _fetch_series(series_id: str, key: str | None, public: bool) -> pd.Series:
    if key:
        js = _api_json("series/observations", {"series_id": series_id}, key, series_id)
        obs = js.get("observations", [])
        dates = [o.get("date") for o in obs]
        values = [o.get("value") for o in obs]
    elif public:
        r = _get(_PUBLIC_CSV.format(series_id), None, series_id)
        df = pd.read_csv(io.StringIO(r.text))
        dates = df.iloc[:, 0].tolist()
        values = df.iloc[:, 1].tolist()
    else:
        raise DataUnavailable("FRED_API_KEY non configurata")
    s = pd.Series(pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(),
                  index=pd.to_datetime(pd.Series(dates)), name=series_id)
    s = s.dropna().sort_index()
    if s.empty:
        raise DataUnavailable(f"{series_id}: nessuna osservazione")
    return s


class _SeriesStore:
    """Cache di processo condivisa da tutte le sessioni."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, pd.Series]] = {}
        self._errors: dict[str, str] = {}
        self._lock = threading.Lock()

    def get_many(self, ids: list[str]) -> dict[str, pd.Series]:
        ttl = CACHE_TTL_HOURS * 3600
        now = time.time()
        with self._lock:
            stale = [i for i in ids if i not in self._data or now - self._data[i][0] > ttl]
        if stale:
            key = api_key()
            public = dev_public_mode()
            with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
                futures = {i: pool.submit(_fetch_series, i, key, public) for i in stale}
            for i, fut in futures.items():
                try:
                    s = fut.result()
                except Exception as exc:  # noqa: BLE001 - si mantiene l'ultimo dato valido
                    msg = str(exc) if isinstance(exc, DataUnavailable) else type(exc).__name__
                    log.warning("Serie %s non aggiornata: %s", i, msg)
                    with self._lock:
                        self._errors[i] = msg
                    continue
                with self._lock:
                    self._data[i] = (time.time(), s)
                    self._errors.pop(i, None)
        with self._lock:
            return {i: (self._data[i][1] if i in self._data else pd.Series(dtype=float, name=i))
                    for i in ids}

    def fetched_at(self, ids: list[str]) -> datetime | None:
        with self._lock:
            stamps = [self._data[i][0] for i in ids if i in self._data]
        return datetime.fromtimestamp(min(stamps)) if stamps else None

    def errors(self, ids: list[str]) -> dict[str, str]:
        with self._lock:
            return {i: self._errors[i] for i in ids if i in self._errors and i not in self._data}


@st.cache_resource(show_spinner=False)
def _store() -> _SeriesStore:
    return _SeriesStore()


def load(ids) -> dict[str, pd.Series]:
    """Storia completa delle serie richieste (dict id -> pd.Series)."""
    ids = list(dict.fromkeys(ids))
    return _store().get_many(ids)


def fetched_at(ids) -> datetime | None:
    return _store().fetched_at(list(ids))


def missing(ids) -> dict[str, str]:
    """Serie mai scaricate con il relativo errore."""
    return _store().errors(list(ids))


# =============================================================================
# CALENDARIO USCITE
# =============================================================================

@st.cache_data(ttl=timedelta(hours=CALENDAR_TTL_HOURS), show_spinner=False)
def release_dates(release_ids: tuple[int, ...], days_back: int, days_ahead: int) -> pd.DataFrame:
    """Date di pubblicazione (passate e programmate) delle release indicate.

    Restituisce un DataFrame con colonne ``release_id`` e ``date``.
    """
    key = api_key()
    if not key:
        raise DataUnavailable("Calendario disponibile solo con FRED_API_KEY")
    start = (date.today() - timedelta(days=days_back)).isoformat()
    end = (date.today() + timedelta(days=days_ahead)).isoformat()

    def one(rid: int) -> list[tuple[int, str]]:
        try:
            js = _api_json(
                "release/dates",
                {
                    "release_id": rid,
                    "realtime_start": start,
                    "realtime_end": end,
                    "include_release_dates_with_no_data": "true",
                    "sort_order": "asc",
                    "limit": 1000,
                },
                key,
                f"release {rid}",
            )
        except DataUnavailable as exc:
            log.warning("Calendario release %s non disponibile: %s", rid, exc)
            return []
        return [(rid, d["date"]) for d in js.get("release_dates", [])]

    rows: list[tuple[int, str]] = []
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        for res in pool.map(one, release_ids):
            rows.extend(res)
    if not rows:
        raise DataUnavailable("Calendario non disponibile")
    df = pd.DataFrame(rows, columns=["release_id", "date"])
    df["date"] = pd.to_datetime(df["date"])
    df = df[(df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))]
    return df.drop_duplicates().sort_values(["date", "release_id"]).reset_index(drop=True)
