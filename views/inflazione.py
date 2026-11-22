"""Inflazione: prezzi al consumo e alla produzione, momentum, componenti, aspettative."""

import streamlit as st

from catalog import signal_series_ids
from config import LEVEL_COLORS, PALETTE
from utils import ui
from utils import signals as S

KEYS = ["cpi_yoy", "core_cpi_yoy", "pce_yoy", "core_pce_yoy", "core_pce_3m", "core_pce_6m",
        "core_cpi_3m", "core_cpi_6m", "shelter_yoy", "supercore_yoy", "sticky_core", "be5", "be10", "ppi_yoy"]

ui.page_title("Inflazione", "Prezzi al consumo e alla produzione, direzione recente e aspettative di mercato.")
d = ui.load(signal_series_ids(KEYS))

ui.section("Dati principali", help="Variazioni sui 12 mesi. Il colore indica la distanza dall'obiettivo "
                                    "Fed del 2% (misurato sul PCE); dettagli nella ⓘ di ogni indicatore.")
ui.kpi_row(["cpi_yoy", "core_cpi_yoy", "pce_yoy", "core_pce_yoy"], d)

st.space("small")
cols = st.columns(4)
for col, key in zip(cols, ["core_pce_yoy", "core_pce_3m", "be5", "ppi_yoy"]):
    with col:
        ui.gauge_block(key, d)

# --- CPI e PCE ------------------------------------------------------------------------
ui.section("CPI e PCE", help="Fascia verde: valori compatibili con l'obiettivo della Fed. "
                             "Il CPI ha una fascia più alta perché corre in media 0,3-0,5 punti sopra il PCE.")
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["cpi_yoy", "core_cpi_yoy"], d, title="CPI e Core CPI (a/a)",
                    help=S.help_text("cpi_yoy", d), names={"cpi_yoy": "CPI", "core_cpi_yoy": "Core CPI"},
                    zero_line=True, hbands=ui.level_bands_for_chart("cpi_yoy", d))
with b:
    ui.signal_chart(["pce_yoy", "core_pce_yoy"], d, title="PCE e Core PCE (a/a)",
                    help=S.help_text("core_pce_yoy", d), names={"pce_yoy": "PCE", "core_pce_yoy": "Core PCE"},
                    zero_line=True, hbands=ui.level_bands_for_chart("core_pce_yoy", d),
                    hlines=[{"y": 2.0, "label": "Obiettivo Fed 2%", "color": PALETTE["txt"]}])

# --- Momentum -------------------------------------------------------------------------
ui.section(
    "Momentum: dove sta andando l'inflazione",
    help="Le variazioni annualizzate a 3 e 6 mesi mostrano la tendenza recente prima che si veda nel "
         "dato a 12 mesi. Se il 3 mesi è sotto il 12 mesi l'inflazione sta rallentando, se è sopra sta "
         "accelerando. Sono dati più rumorosi: conta la direzione, non il singolo mese.",
)
ui.kpi_row(["core_pce_3m", "core_pce_6m", "core_cpi_3m", "core_cpi_6m"], d)
ui.signal_chart(
    ["core_pce_yoy", "core_pce_6m", "core_pce_3m"], d, title="Core PCE: 12 mesi vs 6 e 3 mesi annualizzati",
    help=S.help_text("core_pce_3m", d), years=5,
    names={"core_pce_yoy": "12 mesi", "core_pce_6m": "6 mesi annualizzato", "core_pce_3m": "3 mesi annualizzato"},
    hbands=ui.level_bands_for_chart("core_pce_yoy", d),
    hlines=[{"y": 2.0, "label": "Obiettivo 2%", "color": PALETTE["txt"]}], extra_source="Ultimi 5 anni.",
    chart_key="momentum",
)

# --- Componenti -----------------------------------------------------------------------
ui.section(
    "Componenti persistenti",
    help="Le parti dell'inflazione che cambiano più lentamente e preoccupano di più la Fed: abitazione "
         "(circa un terzo del CPI), servizi esclusa abitazione ('supercore', legati ai salari) e prezzi "
         "'vischiosi' dell'Atlanta Fed. Sono indicatori descrittivi, senza semaforo.",
)
ui.kpi_row(["shelter_yoy", "supercore_yoy", "sticky_core"], d)
ui.signal_chart(["shelter_yoy", "supercore_yoy", "sticky_core"], d, title="Componenti persistenti (a/a)",
                names={"shelter_yoy": "Abitazione", "supercore_yoy": "Servizi esclusa abitazione",
                       "sticky_core": "Sticky core"}, zero_line=True)

# --- Aspettative -----------------------------------------------------------------------
ui.section(
    "Aspettative di inflazione del mercato",
    help="Breakeven = rendimento del Treasury nominale meno quello del TIPS (indicizzato all'inflazione) "
         "della stessa scadenza. È misurato sul CPI: valori tra 1,8% e 2,6% sono coerenti con il 2% sul PCE.",
)
a, b = st.columns([2, 1], gap="large")
with a:
    ui.signal_chart(["be5", "be10"], d, title="Breakeven 5 e 10 anni", help=S.help_text("be5", d),
                    names={"be5": "5 anni", "be10": "10 anni"}, hbands=ui.level_bands_for_chart("be5", d))
with b:
    ui.kpi("be5", d)
    ui.kpi("be10", d)

# --- PPI ---------------------------------------------------------------------------------
ui.section("Prezzi alla produzione", help=S.help_text("ppi_yoy", d))
a, b = st.columns([2, 1], gap="large")
with a:
    ui.signal_chart(["ppi_yoy"], d, title="PPI domanda finale (a/a)", zero_line=True,
                    hbands=ui.level_bands_for_chart("ppi_yoy", d))
with b:
    ui.kpi("ppi_yoy", d)
    st.caption("Indice disponibile da novembre 2009 (= 100): la variazione annua parte dal 2010.")

ui.section("Tabella riepilogativa")
ui.summary_table(KEYS, d, "inflazione")

ui.guide("Guida alla lettura", f"""
**CPI o PCE?** Il CPI (Bureau of Labor Statistics) è il dato più citato; il PCE (Bureau of Economic
Analysis) copre più spese e aggiorna i pesi quando i consumatori cambiano prodotti. La Fed fissa il suo
obiettivo del **2% sul PCE**. Poiché il CPI corre in media 0,3-0,5 punti sopra il PCE, la fascia verde del
CPI arriva al 3%, quella del PCE al 2,5%.

**Perché il 'core'?** Esclude alimentari ed energia, molto volatili, e mostra la tendenza di fondo.

**Perché il rosso anche quando l'inflazione è bassa?** Inflazione troppo bassa o deflazione sono a loro
volta squilibri (spesso legati a recessioni). Per questo le soglie sono simmetriche intorno all'obiettivo.

**Segnali da osservare**
- 3 mesi annualizzato stabilmente sotto il 12 mesi: disinflazione in corso.
- Abitazione e supercore in calo: la parte persistente si sta raffreddando.
- Breakeven sopra il 2,6-3%: il mercato teme che l'inflazione resti alta.
- PPI in forte accelerazione: possibili pressioni in arrivo sui prezzi al consumo.
""")
