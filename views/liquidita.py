"""Liquidità e Fed: bilancio della Fed, conto del Tesoro, reverse repo, riserve, M2, dollaro."""

import streamlit as st

from catalog import signal_series_ids
from config import PALETTE
from utils import charts, ui
from utils import signals as S
from utils import transforms as T

KEYS = ["netliq", "netliq_13w", "walcl", "reserves", "tga", "rrp", "m2_yoy", "dollar_yoy"]

ui.page_title(
    "Liquidità e Fed",
    "Quanta liquidità la Federal Reserve immette o drena dal sistema finanziario, e come cresce la moneta.",
)
d = ui.load(signal_series_ids(KEYS))

ui.section("Dati principali")
ui.kpi_row(["netliq", "walcl", "reserves", "m2_yoy"], d)

st.space("small")
cols = st.columns([1, 1, 2])
with cols[0]:
    ui.gauge_block("netliq_13w", d)
with cols[1]:
    ui.gauge_block("m2_yoy", d)
with cols[2]:
    st.markdown("**Come si calcola la liquidità netta**", help=S.help_text("netliq", d))
    st.markdown(
        """
Liquidità netta = **attivo della Fed** − **conto del Tesoro (TGA)** − **reverse repo overnight**

- L'**attivo della Fed** cresce con il quantitative easing (acquisti di titoli) e scende con il
  quantitative tightening.
- Il **conto del Tesoro** è la 'cassa' del governo presso la Fed: quando si riempie (emissioni di
  titoli, tasse) toglie liquidità alle banche.
- I **reverse repo** sono liquidità parcheggiata alla Fed da fondi monetari: quando scendono, quella
  liquidità torna sul mercato.

È una misura molto seguita dai trader, ma il suo legame con i mercati azionari **non è stabile**:
va letta come contesto, non come segnale.
        """
    )

# --- Liquidità netta e componenti --------------------------------------------------------------
ui.section("Liquidità netta e componenti", help=S.help_text("netliq", d))
yrs = ui.period_years()
traces = [
    {"series": T.window(S.compute("netliq", d), yrs), "name": "Liquidità netta", "color": PALETTE["teal"],
     "width": 2.8, "decimals": 0},
    {"series": T.window(S.compute("walcl", d), yrs), "name": "Attivo Fed", "color": PALETTE["blue"], "decimals": 0},
    {"series": T.window(S.compute("tga", d), yrs), "name": "Conto del Tesoro (TGA)", "color": PALETTE["gold"],
     "decimals": 0},
    {"series": T.window(S.compute("rrp", d), yrs), "name": "Reverse repo", "color": PALETTE["violet"], "decimals": 0},
]
ui.chart_title("Miliardi di dollari (dati settimanali; reverse repo giornalieri)")
charts.show(charts.time_chart(traces, recessions=ui.recession_periods(d), suffix=" mld $", decimals=0, height=420))
ui.source_caption(["WALCL", "WDTGAL", "RRPONTSYD"], "Serie disponibili dal 2002-2003.")

a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["netliq_13w"], d, title="Liquidità netta: variazione % su 13 settimane",
                    help=S.help_text("netliq_13w", d), zero_line=True)
with b:
    ui.signal_chart(["reserves"], d, title="Riserve bancarie presso la Fed (miliardi $)",
                    help=S.help_text("reserves", d))
ui.kpi_row(["tga", "rrp", "netliq_13w"], d)

# --- Moneta e dollaro -----------------------------------------------------------------------------
ui.section("Moneta e dollaro")
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["m2_yoy"], d, title="Moneta M2 (a/a)", help=S.help_text("m2_yoy", d), zero_line=True,
                    hbands=ui.level_bands_for_chart("m2_yoy", d))
with b:
    ui.signal_chart(["dollar_yoy"], d, title="Dollaro, indice ampio (a/a)", help=S.help_text("dollar_yoy", d),
                    zero_line=True)

ui.section("Tabella riepilogativa")
ui.summary_table(KEYS, d, "liquidita")

ui.guide("Guida alla lettura", """
**Perché la liquidità?** Quando la Fed compra titoli crea riserve bancarie: più liquidità nel sistema,
tassi di mercato più bassi, più propensione al rischio. Quando riduce il bilancio (QT) avviene il contrario.
Il Tesoro e i fondi monetari spostano grandi somme dentro e fuori dalla Fed, e per questo si sottraggono
il conto del Tesoro e i reverse repo.

**Limiti.** La relazione tra liquidità netta e mercati è stata forte in alcune fasi (2020-2022) e debole
in altre. È una variabile di contesto, non uno strumento di previsione.

**M2.** La moneta in senso ampio. Nel 2020-2021 è cresciuta oltre il 25% annuo, poi si è contratta per la
prima volta dal dopoguerra. Una crescita tra il 3% e l'8% è considerata normale.

**Dollaro.** Un dollaro in forte rafforzamento rende più care le esportazioni USA e più difficile il
finanziamento in dollari per il resto del mondo.
""")
