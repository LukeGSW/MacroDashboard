"""
Macro Dashboard USA - Configurazione generale
==============================================
Brand, link, parametri dell'app e testi legali. Gli indicatori, le soglie e
i tooltip stanno in ``catalog.py``.
"""

from __future__ import annotations

# =============================================================================
# BRAND (palette presa dalle variabili CSS di kriterionquant.it)
# =============================================================================

APP_NAME = "Macro Dashboard USA"
BRAND = "Kriterion Quant"

PALETTE = {
    "bg": "#090C12",
    "bg2": "#0D121C",
    "card": "#121A27",
    "card2": "#0F1622",
    "line": "#222C3C",
    "line2": "#2C3A50",
    "txt": "#EAF0F8",
    "mut": "#8B97AA",
    "teal": "#00E5A0",
    "teal2": "#16C8C8",
    "coral": "#FF5470",
    "gold": "#FFC24B",
    "violet": "#C77DFF",
    "blue": "#4F9DFF",
}

# Colori dei semafori: verde = equilibrio, giallo = da monitorare, rosso = squilibrio/stress
LEVEL_COLORS = {
    "ok": PALETTE["teal"],
    "warn": PALETTE["gold"],
    "bad": PALETTE["coral"],
    "neutral": PALETTE["mut"],
}
LEVEL_EMOJI = {"ok": "🟢", "warn": "🟡", "bad": "🔴", "neutral": "⚪"}
LEVEL_NAME = {"ok": "Verde", "warn": "Giallo", "bad": "Rosso", "neutral": "Neutro"}
LEVEL_SCORE = {"ok": 2, "warn": 1, "bad": 0}

# Colori delle serie nei grafici (ordine di utilizzo)
SERIES_COLORS = [
    PALETTE["teal"],
    PALETTE["blue"],
    PALETTE["gold"],
    PALETTE["violet"],
    PALETTE["teal2"],
    PALETTE["coral"],
    "#9AA7BD",
]

# =============================================================================
# LINK IN TESTA ALLA DASHBOARD
# =============================================================================

_UTM = "utm_source=macro-dashboard&utm_medium=referral&utm_campaign=header"
HEADER_LINKS = [
    ("Blog", f"https://kriterionquant.it/blog/?{_UTM}"),
    ("Chi sono", f"https://kriterionquant.it/chi-sono.html?{_UTM}"),
]

# =============================================================================
# PARAMETRI APP
# =============================================================================

CACHE_TTL_HOURS = 4          # validita' della cache delle serie FRED
CALENDAR_TTL_HOURS = 6       # validita' della cache del calendario uscite
PERCENTILE_START = "1990-01-01"  # base storica per i percentili
PERIOD_OPTIONS = {"1A": 1, "3A": 3, "5A": 5, "10A": 10, "20A": 20, "Max": None}
DEFAULT_PERIOD = "10A"

# =============================================================================
# TESTI LEGALI
# =============================================================================

FRED_NOTICE = (
    "This product uses the FRED® API but is not endorsed or certified by "
    "the Federal Reserve Bank of St. Louis."
)
FRED_NOTICE_IT = (
    "Questo prodotto usa l'API FRED® ma non è approvato né certificato "
    "dalla Federal Reserve Bank of St. Louis."
)
FRED_TOU_URL = "https://fred.stlouisfed.org/docs/api/terms_of_use.html"
HOSTING_PRIVACY_URL = "https://streamlit.io/privacy-policy"

DISCLAIMER_SHORT = (
    "Contenuti a solo scopo informativo ed educativo: non costituiscono consulenza "
    "finanziaria né sollecitazione all'investimento. Soglie e semafori sono "
    "convenzioni indicative, non segnali operativi."
)

DISCLAIMER_FULL = """
**Natura dei contenuti.** Questa dashboard ha finalità esclusivamente informative ed
educative. Nulla di quanto mostrato costituisce consulenza in materia di investimenti,
raccomandazione personalizzata, ricerca in materia di investimenti, offerta o
sollecitazione all'acquisto o alla vendita di strumenti finanziari.

**Soglie e semafori.** I colori (verde, giallo, rosso) e le etichette sono convenzioni
indicative costruite su riferimenti pubblici (obiettivi della Federal Reserve, stime
ufficiali, distribuzioni storiche). Non sono segnali operativi e non prevedono
l'andamento dei mercati. Ogni soglia è indicata nel tooltip ⓘ del relativo indicatore.

**Dati.** I dati provengono da fonti pubbliche tramite l'API FRED® e possono contenere
errori, ritardi o revisioni successive. L'autore non garantisce completezza,
accuratezza o aggiornamento dei dati e non risponde di decisioni prese sulla base
di questa dashboard. I risultati passati non sono indicativi di quelli futuri.
"""
