"""
Macro Dashboard USA - Kriterion Quant
=====================================
Entrypoint dell'app: configurazione pagina, stile, navigazione, controlli
globali, header con link e footer legale comuni a tutte le pagine.

Avvio locale:  streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from config import APP_NAME, BRAND, DEFAULT_PERIOD, PERIOD_OPTIONS
from utils import ui

ROOT = Path(__file__).parent

st.set_page_config(
    page_title=f"{APP_NAME} · {BRAND}",
    page_icon=str(ROOT / "assets" / "icon.png"),
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={"About": f"**{APP_NAME}** di {BRAND}. Dati macroeconomici USA tramite l'API FRED®."},
)

ui.inject_css()
st.logo(str(ROOT / "assets" / "logo.svg"), icon_image=str(ROOT / "assets" / "icon.png"), size="large")

# --- Pagine -------------------------------------------------------------------
V = ROOT / "views"
cruscotto = st.Page(V / "cruscotto.py", title="Cruscotto", icon=":material/dashboard:", default=True)
calendario = st.Page(V / "calendario.py", title="Calendario dati", icon=":material/calendar_month:",
                     url_path="Calendario")
rischio = st.Page(V / "rischio.py", title="Rischio recessione", icon=":material/crisis_alert:",
                  url_path="Rischio")
inflazione = st.Page(V / "inflazione.py", title="Inflazione", icon=":material/local_fire_department:",
                     url_path="Inflazione")
lavoro = st.Page(V / "lavoro.py", title="Lavoro", icon=":material/work:", url_path="Lavoro")
crescita = st.Page(V / "crescita.py", title="Crescita", icon=":material/factory:", url_path="Crescita")
tassi = st.Page(V / "tassi.py", title="Tassi e curva", icon=":material/account_balance:", url_path="Tassi")
liquidita = st.Page(V / "liquidita.py", title="Liquidità e Fed", icon=":material/water_drop:",
                    url_path="Liquidita")
housing = st.Page(V / "housing.py", title="Housing", icon=":material/home:", url_path="Housing")
sentiment = st.Page(V / "sentiment.py", title="Sentiment e stress", icon=":material/thermostat:",
                    url_path="Sentiment")
legale = st.Page(V / "legale.py", title="Note legali e fonti", icon=":material/gavel:", url_path="Note-legali")

pg = st.navigation({
    "Panoramica": [cruscotto, calendario, rischio],
    "Indicatori": [inflazione, lavoro, crescita, tassi, liquidita],
    "Mercati e settori": [housing, sentiment],
    "Informazioni": [legale],
})

# --- Controlli globali (validi per tutte le pagine) ------------------------------
with st.sidebar:
    st.segmented_control(
        "Periodo dei grafici",
        options=list(PERIOD_OPTIONS),
        default=DEFAULT_PERIOD,
        key="period",
        required=True,
        help="Finestra temporale dei grafici storici, uguale per tutte le pagine. "
             "I valori attuali, i semafori e i percentili non cambiano.",
    )
    st.toggle(
        "Evidenzia le recessioni",
        value=True,
        key="show_rec",
        help="Aree grigie nei grafici: recessioni USA datate dal NBER (serie FRED® USREC).",
    )

ui.header()
pg.run()
ui.footer(legale)
