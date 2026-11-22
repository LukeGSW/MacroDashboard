"""Crescita: PIL, GDPNow, produzione industriale, consumi e redditi reali."""

import pandas as pd
import streamlit as st

from catalog import signal_series_ids
from config import PALETTE
from utils import charts, ui
from utils import signals as S
from utils import transforms as T

KEYS = ["gdp_qoq", "gdpnow", "ip_yoy", "tcu", "retail_real_yoy", "pce_real_yoy", "income_real_yoy"]

ui.page_title("Crescita", "PIL, stima in tempo reale del trimestre in corso, industria, consumi e redditi reali.")
d = ui.load(signal_series_ids(KEYS))

ui.section("Dati principali")
ui.kpi_row(["gdp_qoq", "gdpnow", "retail_real_yoy", "income_real_yoy"], d)

st.space("small")
cols = st.columns(4)
for col, key in zip(cols, ["gdp_qoq", "gdpnow", "ip_yoy", "tcu"]):
    with col:
        ui.gauge_block(key, d)

# --- PIL ------------------------------------------------------------------------------------
ui.section("PIL reale e GDPNow", help=S.help_text("gdp_qoq", d))
yrs = ui.period_years()
gdp = T.window(S.compute("gdp_qoq", d), yrs)
now = S.compute("gdpnow", d)
traces = [{"series": gdp, "name": "PIL reale (trim. annualizzato)", "kind": "bar", "decimals": 1}]
last_gdp_date = gdp.index.max() if not gdp.empty else None
if not now.empty and (last_gdp_date is None or now.index[-1] > last_gdp_date):
    traces.append({"series": now.tail(1), "name": "GDPNow (trimestre in corso)", "kind": "bar",
                   "colors": [PALETTE["gold"]], "decimals": 1})
ui.chart_title("Crescita trimestrale annualizzata",
               help="Barre verdi/rosse: PIL reale ufficiale (BEA). Barra oro: stima GDPNow dell'Atlanta Fed per "
                    "il trimestre non ancora pubblicato. La linea tratteggiata indica il 2%, vicino al "
                    "potenziale di lungo periodo.")
charts.show(charts.time_chart(traces, recessions=ui.recession_periods(d), zero_line=True, suffix="%", decimals=1,
                              hlines=[{"y": 2.0, "label": "≈ potenziale 2%", "color": PALETTE["mut"]}], height=360))
ui.source_caption(["A191RL1Q225SBEA", "GDPNOW"])

# --- Industria --------------------------------------------------------------------------------
ui.section("Industria")
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["ip_yoy"], d, title="Produzione industriale (a/a)", help=S.help_text("ip_yoy", d),
                    zero_line=True)
with b:
    ui.signal_chart(["tcu"], d, title="Utilizzo della capacità produttiva", help=S.help_text("tcu", d),
                    hbands=ui.level_bands_for_chart("tcu", d))

# --- Consumi e redditi -----------------------------------------------------------------------------
ui.section("Consumi e redditi reali",
           help="Valori corretti per l'inflazione. I consumi sono circa due terzi del PIL USA; il reddito "
                "reale esclusi i trasferimenti è uno degli indicatori con cui il NBER data le recessioni.")
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["retail_real_yoy", "pce_real_yoy"], d, title="Vendite al dettaglio e consumi reali (a/a)",
                    help=S.help_text("retail_real_yoy", d),
                    names={"retail_real_yoy": "Vendite al dettaglio reali", "pce_real_yoy": "Consumi reali (PCE)"},
                    zero_line=True)
with b:
    ui.signal_chart(["income_real_yoy"], d, title="Reddito reale esclusi trasferimenti (a/a)",
                    help=S.help_text("income_real_yoy", d), zero_line=True)

ui.section("Tabella riepilogativa")
ui.summary_table(KEYS, d, "crescita")

ui.guide("Guida alla lettura", """
**PIL.** Il BEA comunica la crescita trimestrale 'annualizzata': un +0,5% nel trimestre diventa circa
+2% annuo. La prima stima esce circa un mese dopo la fine del trimestre e viene rivista due volte.

**GDPNow.** È un modello dell'Atlanta Fed che aggiorna la stima del PIL del trimestre in corso a ogni
nuovo dato. È utile per capire la direzione, ma all'inizio del trimestre può discostarsi molto dal dato finale.

**Produzione industriale e capacità.** L'industria pesa meno del 20% dell'economia USA ma è molto ciclica:
spesso rallenta prima del resto. L'utilizzo della capacità sopra l'82% indica possibili pressioni sui prezzi.

**Consumi e redditi.** Se i redditi reali rallentano mentre i consumi tengono, le famiglie stanno usando
risparmi o credito: una situazione che di solito non dura a lungo.
""")
