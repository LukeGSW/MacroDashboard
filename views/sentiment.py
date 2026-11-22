"""Sentiment e stress: fiducia dei consumatori, risparmio, credito, condizioni finanziarie, VIX."""

import streamlit as st

from catalog import SIGNALS, signal_series_ids
from config import LEVEL_COLORS, LEVEL_EMOJI, LEVEL_SCORE, PALETTE
from utils import ui
from utils import signals as S

KEYS = ["umcsent", "psavert", "baa10y", "stlfsi", "nfci", "drtscilm", "vix"]
CLIMATE = ["vix", "baa10y", "nfci", "stlfsi", "umcsent"]

ui.page_title("Sentiment e stress", "Fiducia delle famiglie, condizioni del credito e tensione sui mercati finanziari.")
d = ui.load(signal_series_ids(KEYS))

ui.section("Dati principali")
ui.kpi_row(["umcsent", "baa10y", "nfci", "vix"], d)

st.space("small")
cols = st.columns(4)
for col, key in zip(cols, ["umcsent", "baa10y", "stlfsi", "vix"]):
    with col:
        ui.gauge_block(key, d)

# --- Clima finanziario --------------------------------------------------------------------------
ui.section(
    "Clima finanziario",
    help="Sintesi di 5 indicatori (VIX, spread Baa, NFCI, indice di stress St. Louis Fed, fiducia dei "
         "consumatori): 2 punti per ogni verde, 1 per ogni giallo, 0 per ogni rosso. Descrive le condizioni "
         "attuali, non è un segnale operativo.",
)
level, score, readings = S.area_status(CLIMATE, d)
a, b = st.columns([1, 2], gap="large")
with a:
    if score is not None:
        title = {"ok": "Condizioni distese", "warn": "Condizioni miste", "bad": "Condizioni di stress"}.get(level, "n.d.")
        desc = {
            "ok": "Volatilità, spread e condizioni finanziarie nella norma.",
            "warn": "Alcuni indicatori segnalano tensione: il quadro non è univoco.",
            "bad": "Più indicatori segnalano stress finanziario o pessimismo marcato.",
        }.get(level, "")
        pts = sum(LEVEL_SCORE[r.level] for r in readings if r.level in LEVEL_SCORE)
        max_pts = 2 * sum(1 for r in readings if r.level in LEVEL_SCORE)
        color = LEVEL_COLORS[level]
        st.markdown(
            f"<div class='kq-area' style='--c:{color};text-align:center;padding:22px 16px'>"
            f"<div style='font-size:1.5rem;font-weight:800;color:{color}'>{title}</div>"
            f"<div style='color:var(--kq-mut);margin-top:8px'>{desc}</div>"
            f"<div style='font-size:1.25rem;font-weight:700;margin-top:12px'>Punteggio {pts}/{max_pts}</div></div>",
            unsafe_allow_html=True,
        )
with b:
    rows = [{"": LEVEL_EMOJI[r.level], "Indicatore": SIGNALS[r.key].label,
             "Valore": S.value_text(SIGNALS[r.key], r.value), "Lettura": r.label or "—"} for r in readings]
    st.dataframe(rows, hide_index=True, width="stretch")

# --- Consumatori -----------------------------------------------------------------------------------
ui.section("Famiglie")
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["umcsent"], d, title="Fiducia dei consumatori (Università del Michigan)",
                    help=S.help_text("umcsent", d), hbands=ui.level_bands_for_chart("umcsent", d))
with b:
    ui.signal_chart(["psavert"], d, title="Tasso di risparmio delle famiglie", help=S.help_text("psavert", d),
                    hbands=ui.level_bands_for_chart("psavert", d))
ui.kpi_row(["umcsent", "psavert"], d)

# --- Credito e condizioni finanziarie -------------------------------------------------------------------
ui.section("Credito e condizioni finanziarie")
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["baa10y"], d, title="Spread creditizio Baa - Treasury 10 anni", help=S.help_text("baa10y", d),
                    hlines=[{"y": 3.25, "label": "Soglia stress 3,25", "color": LEVEL_COLORS["bad"]}])
with b:
    ui.signal_chart(["stlfsi", "nfci"], d, title="Indici di stress e condizioni finanziarie",
                    help=S.help_text("nfci", d), names={"stlfsi": "Stress St. Louis Fed", "nfci": "NFCI Chicago Fed"},
                    zero_line=True)
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["drtscilm"], d, title="Banche che irrigidiscono il credito alle imprese (saldo %)",
                    help=S.help_text("drtscilm", d), zero_line=True,
                    hlines=[{"y": 30, "label": "Irrigidimento marcato", "color": LEVEL_COLORS["bad"]}])
with b:
    ui.signal_chart(["vix"], d, title="VIX", help=S.help_text("vix", d),
                    hlines=[{"y": 20, "label": "20", "color": LEVEL_COLORS["warn"]},
                            {"y": 30, "label": "30", "color": LEVEL_COLORS["bad"]}])

ui.section("Tabella riepilogativa")
ui.summary_table(KEYS, d, "sentiment_stress")

ui.guide("Guida alla lettura", """
**Fiducia dei consumatori.** L'indice dell'Università del Michigan riflette soprattutto inflazione percepita,
redditi e prezzi dei carburanti. Negli ultimi anni è rimasto basso anche con consumi solidi: va letto insieme
ai dati di spesa (pagina Crescita).

**Spread creditizio.** Il premio che le imprese pagano rispetto allo Stato per finanziarsi. Si usa lo spread
delle obbligazioni Baa di Moody's: lo spread High Yield ICE BofA non è mostrato perché il proprietario dei
dati richiede un'autorizzazione preventiva.

**NFCI e indice di stress St. Louis Fed.** Indici compositi costruiti in modo che zero sia la media storica:
valori positivi indicano condizioni più tese della norma.

**Standard del credito bancario.** Sondaggio trimestrale della Fed presso le banche: quando molte banche
stringono i criteri, imprese e famiglie fanno più fatica a finanziarsi.

**VIX.** Volatilità attesa dell'S&P 500. Livelli molto bassi possono indicare compiacenza, livelli molto
alti panico: nessuno dei due è, da solo, un segnale di acquisto o di vendita.
""")
