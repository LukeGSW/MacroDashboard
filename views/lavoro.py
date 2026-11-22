"""Mercato del lavoro: disoccupazione, occupazione, sussidi, salari, JOLTS."""

import pandas as pd
import streamlit as st

from catalog import signal_series_ids
from config import LEVEL_COLORS, PALETTE
from utils import charts, fmt, ui
from utils import signals as S
from utils import transforms as T

KEYS = ["unrate", "u6", "epop_prime", "civpart", "payrolls_mom", "payrolls_3m", "claims", "claims_4w",
        "claims_rise", "ccsa", "sahm", "ahe_yoy", "openings_ratio", "quits"]

ui.page_title("Mercato del lavoro", "Disoccupazione, nuovi posti di lavoro, licenziamenti, salari e posti vacanti.")
d = ui.load(signal_series_ids(KEYS))

ui.section("Dati principali")
ui.kpi_row(["unrate", "payrolls_3m", "claims_4w", "ahe_yoy"], d)

st.space("small")
cols = st.columns(4)
for col, key in zip(cols, ["unrate", "u6", "epop_prime", "sahm"]):
    with col:
        ui.gauge_block(key, d)

# --- Disoccupazione ----------------------------------------------------------------------
ui.section("Disoccupazione", help=S.help_text("unrate", d))
nrou_now = S.resolve_target(S.SIGNALS["unrate"], d)
nrou_line = T.window(T.until_today(d.get("NROU")), ui.period_years())
traces = [
    {"series": T.window(S.compute("unrate", d), ui.period_years()), "name": "Disoccupazione U-3", "decimals": 1},
    {"series": T.window(S.compute("u6", d), ui.period_years()), "name": "Disoccupazione allargata U-6", "decimals": 1},
    {"series": nrou_line.resample("MS").ffill() if not nrou_line.empty else nrou_line,
     "name": "Tasso naturale (CBO)", "dash": "dash", "color": PALETTE["txt"], "width": 1.5, "decimals": 2},
]
ui.chart_title("U-3, U-6 e tasso naturale di disoccupazione")
charts.show(charts.time_chart(traces, recessions=ui.recession_periods(d), suffix="%", decimals=1, height=360))
ui.source_caption(["UNRATE", "U6RATE", "NROU"])

# --- Posti di lavoro ------------------------------------------------------------------------
ui.section("Nuovi posti di lavoro (Nonfarm Payrolls)", help=S.help_text("payrolls_3m", d))
a, b = st.columns([2, 1], gap="large")
with a:
    yrs = ui.period_years() if ui.period_years() is not None and ui.period_years() <= 5 else 5
    mom = T.window(S.compute("payrolls_mom", d), yrs)
    avg3 = T.window(S.compute("payrolls_3m", d), yrs)
    ui.chart_title(f"Variazione mensile e media a 3 mesi (migliaia, ultimi {yrs} anni)",
                   help="Barre: variazione del mese (verde positiva, rossa negativa). Linea: media a 3 mesi. "
                        "Il grafico è limitato a 5 anni perché il crollo del 2020 (-20 milioni) "
                        "schiaccerebbe la scala.")
    fig = charts.time_chart(
        [{"series": mom, "name": "Variazione mensile", "kind": "bar", "decimals": 0},
         {"series": avg3, "name": "Media 3 mesi", "color": PALETTE["gold"], "decimals": 0, "width": 2.5}],
        recessions=ui.recession_periods(d), zero_line=True, suffix=" mila", decimals=0, height=360,
    )
    charts.show(fig)
    ui.source_caption(["PAYEMS"])
with b:
    ui.kpi("payrolls_mom", d)
    ui.kpi("payrolls_3m", d)
    s = S.compute("payrolls_mom", d)
    if len(s) >= 12:
        st.metric("Media 12 mesi", f"{fmt.num(s.tail(12).mean(), 0, sign=True)} mila", border=True,
                  help="Media della variazione mensile degli occupati negli ultimi 12 mesi.")

# --- Sussidi -------------------------------------------------------------------------------
ui.section("Richieste di sussidio di disoccupazione",
           help="Il dato più tempestivo sul mercato del lavoro (settimanale, ogni giovedì).")
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["claims", "claims_4w"], d, title="Richieste iniziali (migliaia)",
                    help=S.help_text("claims", d), names={"claims": "Settimanali", "claims_4w": "Media 4 settimane"})
with b:
    ui.signal_chart(["ccsa"], d, title="Richieste continuative (milioni)", help=S.help_text("ccsa", d))
ui.kpi_row(["claims_rise", "claims", "ccsa"], d)

# --- Salari e domanda di lavoro --------------------------------------------------------------
ui.section("Salari e domanda di lavoro")
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["ahe_yoy"], d, title="Salari orari medi (a/a)", help=S.help_text("ahe_yoy", d),
                    hbands=ui.level_bands_for_chart("ahe_yoy", d))
with b:
    ui.signal_chart(["openings_ratio"], d, title="Posti vacanti per disoccupato (JOLTS)",
                    help=S.help_text("openings_ratio", d), hbands=ui.level_bands_for_chart("openings_ratio", d),
                    hlines=[{"y": 1.0, "label": "1 posto per disoccupato", "color": PALETTE["mut"]}])
ui.kpi_row(["openings_ratio", "quits", "ahe_yoy"], d)

# --- Partecipazione ---------------------------------------------------------------------------
ui.section("Partecipazione e occupazione 25-54 anni", help=S.help_text("epop_prime", d))
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["epop_prime"], d, title="Occupati 25-54 anni (% della popolazione)",
                    hbands=ui.level_bands_for_chart("epop_prime", d))
with b:
    feb20 = T.asof(d.get("CIVPART"), pd.Timestamp("2020-02-01"))
    ui.signal_chart(["civpart"], d, title="Tasso di partecipazione", help=S.help_text("civpart", d),
                    hlines=[{"y": feb20, "label": f"Pre-COVID (feb 2020): {feb20:.1f}%".replace(".", ","),
                             "color": PALETTE["mut"]}] if feb20 else None)

ui.section("Tabella riepilogativa")
ui.summary_table(KEYS, d, "lavoro")

ui.guide("Guida alla lettura", """
**U-3 e U-6.** La U-3 è il tasso di disoccupazione ufficiale. La U-6 aggiunge scoraggiati e part-time
involontari: misura tutto il lavoro 'sprecato'.

**Tasso naturale.** Il riferimento per i colori è il tasso di disoccupazione 'naturale' stimato dal
Congressional Budget Office: il livello compatibile con un'inflazione stabile. Sotto di esso il mercato è
tirato, sopra ci sono risorse inutilizzate.

**Payrolls.** Il ritmo di nuovi posti 'di pareggio' (che tiene ferma la disoccupazione) dipende dalla
crescita della forza lavoro: con meno immigrazione è più basso che in passato. Per questo le soglie sono
volutamente prudenti (sotto zero = rosso, sotto 50 mila = giallo).

**Sussidi.** Le richieste iniziali misurano i nuovi licenziamenti, quelle continuative la difficoltà a
ritrovare lavoro. Più del livello conta la variazione: un rialzo del 20% dal minimo dell'anno ha spesso
accompagnato l'inizio delle recessioni, con falsi allarmi (2022-2023).

**Partecipazione.** Il tasso di partecipazione scende per l'invecchiamento della popolazione; per leggere
il ciclo è meglio la quota di occupati tra 25 e 54 anni, che non risente dei pensionamenti.

**Regola di Sahm.** Si attiva quando la media a 3 mesi della disoccupazione supera di 0,5 punti il minimo
dei 12 mesi precedenti. Storicamente ha coinciso con l'inizio delle recessioni; nel 2024 si è attivata
senza recessione.
""")
