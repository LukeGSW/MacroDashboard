"""Housing: cantieri, permessi, prezzi, mutui, affitti."""

import streamlit as st

from catalog import signal_series_ids
from config import LEVEL_COLORS, PALETTE
from utils import fmt, ui
from utils import signals as S
from utils import transforms as T

KEYS = ["houst", "permit", "hpi_yoy", "mortgage30", "mspus", "rental_vac"]

ui.page_title("Housing", "Mercato immobiliare USA: nuove costruzioni, prezzi, mutui e affitti.")
d = ui.load(signal_series_ids(KEYS))

ui.section("Dati principali")
ui.kpi_row(["houst", "permit", "hpi_yoy", "mortgage30"], d)

st.space("small")
cols = st.columns(4)
for col, key in zip(cols, ["houst", "permit", "mortgage30", "hpi_yoy"]):
    with col:
        ui.gauge_block(key, d)

# --- Attività edilizia ----------------------------------------------------------------------------
ui.section("Attività edilizia", help=S.help_text("houst", d))
a, b = st.columns([2, 1], gap="large")
with a:
    ui.signal_chart(["houst", "permit"], d, title="Cantieri e permessi (milioni, annualizzati)",
                    names={"houst": "Cantieri avviati", "permit": "Permessi"},
                    hbands=ui.level_bands_for_chart("houst", d))
with b:
    h, p = S.evaluate("houst", d), S.evaluate("permit", d)
    if h and p:
        gap = (p.value - h.value) * 1000
        st.metric("Permessi meno cantieri", f"{fmt.num(gap, 0, sign=True)} mila", border=True,
                  help="Se i permessi superano i cantieri la pipeline di nuove costruzioni è in crescita; "
                       "se sono inferiori, l'attività tende a rallentare nei mesi successivi. "
                       "Differenze entro ±50 mila sono rumore statistico.")
        if gap > 50:
            st.success("Pipeline in crescita: più permessi che cantieri.", icon=":material/trending_up:")
        elif gap < -50:
            st.warning("Pipeline in calo: meno permessi che cantieri.", icon=":material/trending_down:")
        else:
            st.info("Permessi e cantieri in equilibrio.", icon=":material/trending_flat:")

# --- Prezzi ------------------------------------------------------------------------------------------
ui.section("Prezzi delle abitazioni", help=S.help_text("hpi_yoy", d))
a, b = st.columns([2, 1], gap="large")
with a:
    ui.signal_chart(["hpi_yoy"], d, title="Prezzi delle case FHFA (a/a)", zero_line=True,
                    hbands=ui.level_bands_for_chart("hpi_yoy", d))
with b:
    ui.kpi("hpi_yoy", d)
    ui.kpi("mspus", d)

# --- Mutui -----------------------------------------------------------------------------------------
ui.section("Tassi sui mutui", help=S.help_text("mortgage30", d))
a, b = st.columns([2, 1], gap="large")
with a:
    ui.signal_chart(["mortgage30"], d, title="Mutuo a tasso fisso 30 anni",
                    hlines=[{"y": 7.0, "label": "7%: forte stress", "color": LEVEL_COLORS["bad"]},
                            {"y": 5.0, "label": "5%: favorevole sotto questa soglia", "color": LEVEL_COLORS["ok"]}])
with b:
    m = S.evaluate("mortgage30", d)
    st.markdown("**Esempio di rata**", help="Mutuo da 400.000 $ a 30 anni con rata costante (ammortamento "
                                             "alla francese), al tasso medio attuale e a confronto con il 4%.")
    if m:
        principal, n = 400_000, 360

        def rata(rate_pct: float) -> float:
            i = rate_pct / 100 / 12
            return principal * i * (1 + i) ** n / ((1 + i) ** n - 1)

        st.metric(f"Rata mensile al {fmt.num(m.value)}%", f"{fmt.num(rata(m.value), 0)} $",
                  delta=f"{fmt.num(rata(m.value) - rata(4.0), 0, sign=True)} $ rispetto al 4%",
                  delta_color="inverse", border=True)

# --- Affitti ---------------------------------------------------------------------------------------
ui.section("Affitti", help=S.help_text("rental_vac", d))
a, b = st.columns([2, 1], gap="large")
with a:
    ui.signal_chart(["rental_vac"], d, title="Sfitto negli affitti", hbands=ui.level_bands_for_chart("rental_vac", d))
with b:
    ui.kpi("rental_vac", d)
    st.caption("Lo sfitto influenza la componente abitazione del CPI con 12-18 mesi di ritardo.")

ui.section("Tabella riepilogativa")
ui.summary_table(KEYS, d, "housing")

ui.guide("Guida alla lettura", """
**Permessi e cantieri.** I permessi anticipano i cantieri di 1-2 mesi. Il settore immobiliare reagisce
presto ai tassi: storicamente ha rallentato prima delle recessioni.

**Prezzi.** Si usa l'indice FHFA (compravendite di abitazioni unifamiliari con mutuo conforme,
destagionalizzato). Il Case-Shiller, più noto, non è usato perché S&P richiede un'autorizzazione
preventiva per mostrarlo pubblicamente.

**Mutui.** Il tasso fisso a 30 anni segue il Treasury a 10 anni più uno spread. Con i prezzi delle case
ai massimi, tassi sopra il 7% mettono sotto forte pressione l'accessibilità.

**Affitti.** Uno sfitto basso indica un mercato teso, con affitti in aumento che si trasmettono con ritardo
all'inflazione. Uno sfitto alto indica eccesso di offerta.
""")
