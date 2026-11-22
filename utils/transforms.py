"""
Trasformazioni delle serie storiche (funzioni pure su pandas).

Tutte le funzioni ricevono e restituiscono ``pd.Series`` con indice di date
ordinato e senza valori mancanti.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd


def clean(s: pd.Series | None) -> pd.Series:
    """Serie ordinata, numerica, senza NaN (vuota se None)."""
    if s is None or len(s) == 0:
        return pd.Series(dtype=float)
    return pd.to_numeric(s, errors="coerce").dropna().sort_index()


def until_today(s: pd.Series) -> pd.Series:
    """Esclude osservazioni future (es. proiezioni CBO della NROU)."""
    s = clean(s)
    return s[s.index <= pd.Timestamp(date.today())]


def asof(s: pd.Series, when: pd.Timestamp) -> float | None:
    """Ultimo valore disponibile alla data ``when`` (o prima)."""
    s = clean(s)
    s = s[s.index <= when]
    return float(s.iloc[-1]) if len(s) else None


def yoy(s: pd.Series) -> pd.Series:
    """Variazione % su 12 mesi, allineata per data (vale per ogni frequenza)."""
    s = clean(s)
    if s.empty:
        return s
    left = pd.DataFrame({"date": s.index - pd.DateOffset(years=1)})
    right = pd.DataFrame({"date": s.index, "prev": s.to_numpy()})
    m = pd.merge_asof(left, right, on="date", direction="backward",
                      tolerance=pd.Timedelta(days=10))
    out = pd.Series((s.to_numpy() / m["prev"].to_numpy() - 1.0) * 100.0, index=s.index)
    return out.replace([np.inf, -np.inf], np.nan).dropna()


def monthly(s: pd.Series) -> pd.Series:
    """Serie mensile su calendario completo: i mesi mancanti diventano NaN.

    Evita confronti sbagliati quando un dato non è stato pubblicato (es. CPI di
    ottobre 2025, non raccolto durante lo shutdown federale).
    """
    s = clean(s)
    if s.empty:
        return s
    return s.asfreq("MS")


def annualized(s: pd.Series, months: int) -> pd.Series:
    """Variazione % annualizzata su ``months`` mesi (serie mensili)."""
    m = monthly(s)
    if m.count() <= months:
        return pd.Series(dtype=float)
    out = ((m / m.shift(months)) ** (12.0 / months) - 1.0) * 100.0
    return out.dropna()


def diff(s: pd.Series, monthly_calendar: bool = False) -> pd.Series:
    """Differenza rispetto all'osservazione precedente (o al mese precedente)."""
    base = monthly(s) if monthly_calendar else clean(s)
    return base.diff().dropna()


def rolling_mean(s: pd.Series, n: int) -> pd.Series:
    return clean(s).rolling(n).mean().dropna()


def pct_above_rolling_min(s: pd.Series, window: int) -> pd.Series:
    """Distanza % dal minimo mobile (es. claims vs minimo di 52 settimane)."""
    s = clean(s)
    return ((s / s.rolling(window).min() - 1.0) * 100.0).dropna()


def scale(s: pd.Series, factor: float) -> pd.Series:
    return clean(s) * factor


def align_asof(target_index: pd.DatetimeIndex, s: pd.Series) -> pd.Series:
    """Riporta ``s`` sulle date di ``target_index`` usando l'ultimo valore disponibile."""
    s = clean(s)
    if s.empty:
        return pd.Series(np.nan, index=target_index)
    return s.reindex(s.index.union(target_index)).ffill().reindex(target_index)


def net_liquidity(walcl: pd.Series, tga: pd.Series, rrp: pd.Series) -> pd.Series:
    """Liquidità netta Fed in miliardi di $: attivo Fed - conto del Tesoro - reverse repo.

    WALCL e WDTGAL sono in milioni (livello del mercoledì), RRPONTSYD in miliardi
    (giornaliero): si allinea tutto alle date settimanali del bilancio Fed.
    """
    walcl = clean(walcl) / 1000.0
    if walcl.empty:
        return walcl
    tga_b = align_asof(walcl.index, clean(tga) / 1000.0)
    rrp_b = align_asof(walcl.index, clean(rrp)).fillna(0.0)
    return (walcl - tga_b - rrp_b).dropna()


def window(s: pd.Series, years: int | None) -> pd.Series:
    """Ultimi ``years`` anni della serie (tutta la storia se None)."""
    s = clean(s)
    if years is None or s.empty:
        return s
    start = pd.Timestamp(date.today()) - pd.DateOffset(years=years)
    return s[s.index >= start]


def percentile_rank(s: pd.Series, value: float, since: str | None = None) -> float | None:
    """Percentuale delle osservazioni storiche inferiori a ``value``."""
    s = clean(s)
    if since:
        s = s[s.index >= pd.Timestamp(since)]
    if len(s) < 24:
        return None
    return float((s < value).mean() * 100.0)


def recession_periods(usrec: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Periodi di recessione NBER (inizio mese del picco, fine mese del minimo)."""
    s = clean(usrec)
    periods: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    start = None
    prev_date = None
    for d, v in s.items():
        if v >= 0.5 and start is None:
            start = d
        elif v < 0.5 and start is not None:
            periods.append((start, d))
            start = None
        prev_date = d
    if start is not None and prev_date is not None:
        periods.append((start, prev_date + pd.offsets.MonthBegin(1)))
    return periods


def signal_episodes(s: pd.Series, trigger, min_gap_months: int = 6) -> list[pd.Timestamp]:
    """Date in cui ``trigger(valore)`` diventa vero, ignorando ritorni entro ``min_gap_months``."""
    s = clean(s)
    starts: list[pd.Timestamp] = []
    active = False
    last_off = None
    for d, v in s.items():
        on = bool(trigger(v))
        if on and not active:
            if last_off is None or (d - last_off).days > min_gap_months * 30.5 or not starts:
                starts.append(d)
            active = True
        elif not on and active:
            active = False
            last_off = d
    return starts
