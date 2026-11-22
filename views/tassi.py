"""Tassi e curva: Fed Funds, curva dei rendimenti completa, spread, tassi reali."""

import pandas as pd
import streamlit as st

from catalog import signal_series_ids
from config import LEVEL_COLORS, PALETTE
from utils import charts, fmt, ui
from utils import signals as S
from utils import transforms as T

KEYS = ["fedfunds", "real_ff_gap", "dgs2", "dgs10", "t10y2y", "t10y3m", "real10y"]
CURVE = [("DGS1MO", "1M"), ("DGS3MO", "3M"), ("DGS6MO", "6M"), ("DGS1", "1A"), ("DGS2", "2A"), ("DGS3", "3A"),
         ("DGS5", "5A"), ("DGS7", "7A"), ("DGS10", "10A"), ("DGS20", "20A"), ("DGS30", "30A")]

ui.page_title("Tassi e curva", "Politica monetaria della Fed, curva dei rendimenti dei Treasury e tassi reali.")
d = ui.load(signal_series_ids(KEYS) + [sid for sid, _ in CURVE] + ["DFEDTARU", "DFEDTARL"])

ui.section("Dati principali")
ui.kpi_row(["fedfunds", "dgs2", "dgs10", "t10y2y", "t10y3m"], d)

# --- Fed -------------------------------------------------------------------------------------
ui.section("Politica monetaria", help=S.help_text("fedfunds", d))
a, b = st.columns([1, 2], gap="large")
with a:
    ui.gauge_block("fedfunds", d)
    up, lo = T.clean(d.get("DFEDTARU")), T.clean(d.get("DFEDTARL"))
    neutral = S.resolve_target(S.SIGNALS["fedfunds"], d)
    if len(up) and len(lo):
        st.metric("Intervallo obiettivo Fed", f"{fmt.num(lo.iloc[-1])}% – {fmt.num(up.iloc[-1])}%", border=True,
                  help="Intervallo fissato dal FOMC per il tasso sui Fed Funds (serie DFEDTARL e DFEDTARU).")
    if neutral is not None:
        st.metric("Neutrale di lungo periodo (FOMC)", f"{fmt.num(neutral)}%", border=True,
                  help="Mediana delle proiezioni dei membri del FOMC per il tasso di lungo periodo (SEP, "
                       "serie FEDTARMDLR). Presuppone inflazione al 2%.")
    ui.kpi("real_ff_gap", d)
with b:
    yrs = ui.period_years()
    ff = T.window(T.clean(d.get("DFF")), yrs)
    traces = [{"series": ff, "name": "Fed Funds effettivo"}]
    neutral_s = T.window(T.clean(d.get("FEDTARMDLR")), yrs)
    if not neutral_s.empty:
        if not ff.empty and ff.index[-1] > neutral_s.index[-1]:
            neutral_s = pd.concat([neutral_s, pd.Series([neutral_s.iloc[-1]], index=[ff.index[-1]])])
        traces.append({"series": neutral_s.resample("D").ffill(), "name": "Neutrale FOMC (lungo periodo)",
                       "color": PALETTE["gold"], "dash": "dash", "width": 1.5})
    ui.chart_title("Fed Funds effettivo e neutrale FOMC")
    charts.show(charts.time_chart(traces, recessions=ui.recession_periods(d), suffix="%", height=420))
    ui.source_caption(["DFF", "FEDTARMDLR"], "Il neutrale FOMC è disponibile dal 2012.")

# --- Curva ------------------------------------------------------------------------------------
ui.section(
    "Curva dei rendimenti",
    help="Rendimenti dei Treasury per scadenza: oggi, un mese fa e un anno fa. Una curva inclinata "
         "positivamente (lunghi sopra i brevi) è la norma; una curva invertita segnala attese di tagli dei tassi.",
)
today = pd.Timestamp.today().normalize()


def curve_at(when: pd.Timestamp):
    xs, ys = [], []
    for sid, lab in CURVE:
        v = T.asof(d.get(sid), when)
        if v is not None:
            xs.append(lab)
            ys.append(v)
    return xs, ys


curves = []
for label, when, color, dash, width in (
    ("Un anno fa", today - pd.DateOffset(years=1), PALETTE["mut"], "dot", 1.8),
    ("Un mese fa", today - pd.DateOffset(months=1), PALETTE["blue"], "dash", 2.0),
    ("Oggi", today, PALETTE["teal"], None, 3.0),
):
    xs, ys = curve_at(when)
    if xs:
        ten = T.clean(d.get("DGS10"))
        ten = ten[ten.index <= when]
        last_date = ten.index[-1] if len(ten) else when
        curves.append({"name": f"{label} ({last_date:%d/%m/%Y})", "x": xs, "y": ys, "color": color, "dash": dash,
                       "width": width})
a, b = st.columns([2, 1], gap="large")
with a:
    charts.show(charts.yield_curve(curves, height=400))
    ui.source_caption([sid for sid, _ in CURVE], time_chart=False)
with b:
    for key in ("t10y3m", "t10y2y"):
        ui.kpi(key, d)
    xs, ys = curve_at(today)
    if xs:
        pairs = dict(zip(xs, ys))
        if "2A" in pairs and "30A" in pairs:
            st.metric("Pendenza 2A → 30A", f"{fmt.num(pairs['30A'] - pairs['2A'], 2, sign=True)} pp", border=True,
                      help="Differenza tra il rendimento a 30 anni e quello a 2 anni.")

# --- Storico rendimenti e spread -------------------------------------------------------------------
ui.section("Rendimenti e spread nel tempo")
yrs = ui.period_years()
traces = []
for sid, lab, color in (("DGS3MO", "3 mesi", PALETTE["mut"]), ("DGS2", "2 anni", PALETTE["blue"]),
                        ("DGS10", "10 anni", PALETTE["teal"]), ("DGS30", "30 anni", PALETTE["violet"])):
    traces.append({"series": T.window(T.clean(d.get(sid)), yrs), "name": lab, "color": color})
ui.chart_title("Treasury per scadenza")
charts.show(charts.time_chart(traces, recessions=ui.recession_periods(d), suffix="%", height=380))
ui.source_caption(["DGS3MO", "DGS2", "DGS10", "DGS30"])

a, b = st.columns(2, gap="large")
for col, key in ((a, "t10y2y"), (b, "t10y3m")):
    with col:
        shown = ui.signal_chart([key], d, title=S.SIGNALS[key].label, help=S.help_text(key, d), zero_line=True,
                                hbands=[{"y0": -4, "y1": 0, "color": LEVEL_COLORS["bad"]}])
        s = next(iter(shown.values()))
        if len(s):
            inv = (s < 0).mean() * 100
            st.caption(f"Giorni con curva invertita nel periodo mostrato: {fmt.num(inv, 1)}%.")

# --- Tassi reali --------------------------------------------------------------------------------------
ui.section("Tassi reali", help=S.help_text("real10y", d))
a, b = st.columns([2, 1], gap="large")
with a:
    ui.signal_chart(["real10y"], d, title="Rendimento reale del Treasury 10 anni (TIPS)", zero_line=True,
                    hbands=ui.level_bands_for_chart("real10y", d))
with b:
    ui.kpi("real10y", d)
    st.caption("Il tasso reale a 10 anni coincide, per costruzione, con il rendimento nominale meno il "
               "breakeven di inflazione a 10 anni.")

ui.section("Tabella riepilogativa")
ui.summary_table(KEYS, d, "tassi")

ui.guide("Guida alla lettura", """
**Fed Funds e neutrale.** Il tasso 'neutrale' è quello che né stimola né frena l'economia. Il FOMC ne
pubblica una stima di lungo periodo (mediana delle proiezioni dei membri, aggiornata 4 volte l'anno). Qui
la stance è misurata come distanza da quel valore: entro ±0,5 punti la politica è considerata vicina al
neutrale. La stima presuppone inflazione al 2%: quando l'inflazione è più alta conta anche il tasso reale.

**Curva dei rendimenti.** Normalmente i tassi a lungo termine sono più alti di quelli a breve. Quando la
curva si inverte il mercato si aspetta tagli dei tassi, spesso perché prevede un rallentamento. Lo storico
delle inversioni, con successi e falsi allarmi, è nella pagina **Rischio recessione**.

**Tassi reali.** Il rendimento dei TIPS è il costo del denaro al netto dell'inflazione attesa. Tassi reali
alti rendono più costoso finanziarsi e pesano sulle valutazioni degli asset rischiosi.
""")
