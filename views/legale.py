"""Note legali, termini d'uso, privacy, fonti e licenze dei dati, soglie dei semafori."""

from datetime import date

import pandas as pd
import streamlit as st

from catalog import SERIES, SIGNALS
from config import (
    CACHE_TTL_HOURS, DISCLAIMER_FULL, FRED_NOTICE, FRED_NOTICE_IT, FRED_TOU_URL, HOSTING_PRIVACY_URL, LEVEL_NAME,
)
from utils import ui
from utils import signals as S

ui.page_title("Note legali e fonti", "Disclaimer, termini d'uso, privacy, fonti e licenze dei dati, soglie dei semafori.")

ui.section("Disclaimer")
st.markdown(DISCLAIMER_FULL)

ui.section("Termini d'uso")
st.markdown(f"""
Questa applicazione usa l'API FRED® della Federal Reserve Bank of St. Louis.

> {FRED_NOTICE}
>
> _{FRED_NOTICE_IT}_

**Usando questa applicazione accetti di essere vincolato dai
[Termini d'uso dell'API FRED®]({FRED_TOU_URL}).**

FRED® e ALFRED® sono marchi registrati della Federal Reserve Bank of St. Louis. Questa dashboard non è
affiliata, approvata o sponsorizzata dalla Federal Reserve Bank of St. Louis né da alcuna altra istituzione
del Federal Reserve System o dai fornitori dei dati.
""")

ui.section("Privacy")
st.markdown(f"""
La dashboard non richiede registrazione, non usa cookie propri e non raccoglie dati personali. È ospitata
su Streamlit Community Cloud (Snowflake Inc.), che può raccogliere dati tecnici e statistiche di utilizzo
secondo la propria [informativa sulla privacy]({HOSTING_PRIVACY_URL}). I link verso kriterionquant.it
contengono parametri UTM che indicano al sito che la visita arriva da questa dashboard.
""")

ui.section(
    "Fonti e licenze dei dati",
    help="Le serie con copyright possono essere mostrate citando la fonte (tag FRED 'copyrighted: citation "
         "required'); le relative note di copyright sono riportate anche sotto ogni grafico.",
)
today = date.today()
rows = []
for sid, meta in SERIES.items():
    rows.append({
        "Serie": sid,
        "Titolo (FRED®)": meta.title,
        "Fonte": meta.source,
        "Licenza": "Copyright, citazione obbligatoria" if meta.license == "citation" else "Pubblico dominio",
        "Nota di copyright": meta.copyright or "—",
        "Citazione": (f"{meta.source}, {meta.title} [{sid}], retrieved from FRED, Federal Reserve Bank of "
                      f"St. Louis; https://fred.stlouisfed.org/series/{sid}, {today:%B %d, %Y}."),
        "Pagina FRED®": f"https://fred.stlouisfed.org/series/{sid}",
    })
st.dataframe(
    pd.DataFrame(rows), hide_index=True, width="stretch", height=420,
    column_config={"Pagina FRED®": st.column_config.LinkColumn(display_text="Apri"),
                   "Citazione": st.column_config.TextColumn(width="large")},
)
st.markdown("""
**Serie escluse.** Lo S&P CoreLogic Case-Shiller Home Price Index e l'ICE BofA US High Yield Option-Adjusted
Spread non sono mostrati: i proprietari richiedono un'autorizzazione preventiva per l'uso pubblico (tag FRED
"copyrighted: pre-approval required"). Sono sostituiti dall'indice dei prezzi FHFA (pubblico dominio) e dallo
spread Moody's Baa - Treasury 10 anni.
""")
st.caption(f"Dati scaricati tramite l'API FRED® e conservati in cache per {CACHE_TTL_HOURS} ore.")

ui.section(
    "Soglie dei semafori",
    help="Tutte le soglie usate da gauge, tabelle e cruscotto, generate dalla stessa configurazione. Le soglie "
         "del Fed Funds e della disoccupazione si aggiornano con le ultime stime FOMC e CBO.",
)
d = ui.load(["FEDTARMDLR", "NROU"])
rows = []
for key, sig in SIGNALS.items():
    bands = S.resolve_bands(sig, d)
    if not bands:
        continue
    by_level = {"ok": [], "warn": [], "bad": []}
    for line in S.bands_text(sig, bands).splitlines():
        for level, name in LEVEL_NAME.items():
            if line.startswith(f"- {name}:") and level in by_level:
                by_level[level].append(line.split(":", 1)[1].strip())
    rows.append({
        "Indicatore": sig.label,
        "Verde": "  |  ".join(by_level["ok"]) or "—",
        "Giallo": "  |  ".join(by_level["warn"]) or "—",
        "Rosso": "  |  ".join(by_level["bad"]) or "—",
        "Origine delle soglie": sig.bands_note or "—",
    })
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=460)
