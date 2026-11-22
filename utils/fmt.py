"""Formattazione all'italiana di numeri e date."""

from __future__ import annotations

import math

import pandas as pd

MESI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
MESI_LUNGHI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
               "agosto", "settembre", "ottobre", "novembre", "dicembre"]
GIORNI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]


def num(x: float | None, decimals: int = 2, sign: bool = False) -> str:
    """1234.5 -> '1.234,50' (separatore migliaia '.', decimali ',')."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n.d."
    s = f"{x:+,.{decimals}f}" if sign else f"{x:,.{decimals}f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    if s in ("-0", "+0", "-0,0", "+0,0", "-0,00", "+0,00"):
        s = s.replace("-", "+") if sign else s.replace("-", "")
    return s


def date_label(d: pd.Timestamp | None, freq: str = "D") -> str:
    """Data leggibile in base alla frequenza: 'ott 2026', 'T3 2026', '14/11/2026'."""
    if d is None or pd.isna(d):
        return "n.d."
    d = pd.Timestamp(d)
    if freq == "M":
        return f"{MESI[d.month - 1]} {d.year}"
    if freq == "Q":
        return f"T{(d.month - 1) // 3 + 1} {d.year}"
    return d.strftime("%d/%m/%Y")


def long_date(d: pd.Timestamp) -> str:
    d = pd.Timestamp(d)
    return f"{GIORNI[d.weekday()]} {d.day} {MESI_LUNGHI[d.month - 1]} {d.year}"


def ordinal_pct(p: float | None) -> str:
    return "n.d." if p is None else f"{p:.0f}°"
