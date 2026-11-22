"""Calcolo e valutazione degli indicatori definiti in ``catalog.SIGNALS``."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from catalog import SERIES, SIGNALS, Band, Signal
from config import LEVEL_NAME, LEVEL_SCORE, PERCENTILE_START
from utils import fmt
from utils import transforms as T


@dataclass
class Reading:
    key: str
    value: float
    date: pd.Timestamp
    prev_value: float | None
    prev_date: pd.Timestamp | None
    delta: float | None
    level: str          # ok | warn | bad | neutral
    label: str          # lettura della fascia ("Sopra l'obiettivo", ...)
    bands: list[Band]
    target: float | None
    pct: float | None   # percentile storico
    series: pd.Series

    @property
    def signal(self) -> Signal:
        return SIGNALS[self.key]


def freq_of(sig: Signal) -> str:
    if sig.freq:
        return sig.freq
    meta = SERIES.get(sig.series[0])
    return meta.freq if meta else "D"


def compute(key: str, data: dict[str, pd.Series]) -> pd.Series:
    try:
        s = SIGNALS[key].compute(data)
    except Exception:  # noqa: BLE001 - dati parziali: l'indicatore risulta non disponibile
        return pd.Series(dtype=float)
    return T.until_today(s)


def resolve_bands(sig: Signal, data: dict[str, pd.Series]) -> list[Band]:
    if sig.bands is None:
        return []
    return sig.bands(data) if callable(sig.bands) else list(sig.bands)


def resolve_target(sig: Signal, data: dict[str, pd.Series]) -> float | None:
    if sig.target is None:
        return None
    return sig.target(data) if callable(sig.target) else float(sig.target)


def classify(value: float | None, bands: list[Band]) -> tuple[str, str]:
    if value is None or not bands:
        return "neutral", ""
    for b in bands:
        lo = float("-inf") if b.lo is None else b.lo
        hi = float("inf") if b.hi is None else b.hi
        if lo <= value < hi:
            return b.level, b.label
    return "neutral", ""


def evaluate(key: str, data: dict[str, pd.Series]) -> Reading | None:
    sig = SIGNALS[key]
    s = compute(key, data)
    if s.empty:
        return None
    bands = resolve_bands(sig, data)
    value = float(s.iloc[-1])
    prev = float(s.iloc[-2]) if len(s) > 1 else None
    level, label = classify(value, bands)
    return Reading(
        key=key,
        value=value,
        date=s.index[-1],
        prev_value=prev,
        prev_date=s.index[-2] if len(s) > 1 else None,
        delta=(value - prev) if prev is not None else None,
        level=level,
        label=label,
        bands=bands,
        target=resolve_target(sig, data),
        pct=T.percentile_rank(s, value, PERCENTILE_START),
        series=s,
    )


# =============================================================================
# TESTI
# =============================================================================

def value_text(sig: Signal, v: float | None) -> str:
    return "n.d." if v is None else f"{fmt.num(v, sig.decimals)}{sig.suffix}"


def delta_text(sig: Signal, d: float | None) -> str | None:
    return None if d is None else f"{fmt.num(d, sig.decimals, sign=True)}{sig.delta_suffix}"


def bands_text(sig: Signal, bands: list[Band]) -> str:
    """Elenco leggibile delle soglie, per i tooltip."""
    if not bands:
        return ""
    def n(x: float) -> str:
        dec = 0 if abs(x) >= 100 or (abs(x) >= 10 and float(x).is_integer()) else (1 if abs(x) >= 10 else 2)
        return f"{fmt.num(x, dec)}{sig.suffix}"

    rows = []
    for b in bands:
        if b.lo is None:
            rng = f"sotto {n(b.hi)}"
        elif b.hi is None:
            rng = f"da {n(b.lo)} in su"
        else:
            rng = f"da {n(b.lo)} a {n(b.hi)}"
        rows.append(f"- {LEVEL_NAME[b.level]}: {rng} · {b.label}")
    return "\n".join(rows)


def help_text(key: str, data: dict[str, pd.Series] | None = None) -> str:
    """Tooltip completo: descrizione + soglie + origine delle soglie + fonte."""
    sig = SIGNALS[key]
    parts = [sig.help]
    bands = resolve_bands(sig, data or {}) if (data is not None or not callable(sig.bands)) else []
    if bands:
        parts.append("**Soglie dei colori**\n" + bands_text(sig, bands))
        if sig.bands_note:
            parts.append(f"_Origine delle soglie: {sig.bands_note}_")
    sources = sorted({SERIES[s].source for s in sig.series if s in SERIES})
    ids = ", ".join(sig.series)
    parts.append(f"Fonte: {'; '.join(sources)} (serie FRED® {ids}).")
    return "\n\n".join(parts)


def status_html(r: Reading) -> str:
    """Riga di stato sotto un gauge/metrica: pallino colorato + lettura + data + percentile."""
    from config import LEVEL_COLORS

    sig = r.signal
    color = LEVEL_COLORS[r.level]
    label = r.label or "Senza soglie"
    pct = f" · {fmt.ordinal_pct(r.pct)} percentile dal 1990" if r.pct is not None else ""
    return (
        f"<div class='kq-status'><span class='kq-dot' style='background:{color}'></span>"
        f"<span class='kq-status-label' style='color:{color}'>{label}</span>"
        f"<span class='kq-status-meta'>{fmt.date_label(r.date, freq_of(sig))}{pct}</span></div>"
    )


# =============================================================================
# AGGREGAZIONE PER AREA
# =============================================================================

def area_status(keys: list[str], data: dict[str, pd.Series]) -> tuple[str, float | None, list[Reading]]:
    """Stato di un'area = media dei punteggi (verde 2, giallo 1, rosso 0)."""
    readings = [r for r in (evaluate(k, data) for k in keys) if r is not None]
    scored = [LEVEL_SCORE[r.level] for r in readings if r.level in LEVEL_SCORE]
    if not scored:
        return "neutral", None, readings
    score = sum(scored) / len(scored)
    level = "ok" if score >= 1.5 else "warn" if score >= 0.75 else "bad"
    return level, score, readings
