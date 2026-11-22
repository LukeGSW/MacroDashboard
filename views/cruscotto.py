"""Cruscotto: lo stato dell'economia USA in una schermata."""

import streamlit as st

from catalog import AREAS, SIGNALS, SNAPSHOT_GAUGES, signal_series_ids
from config import LEVEL_COLORS, LEVEL_NAME, LEVEL_SCORE
from utils import cal, ui
from utils import signals as S

ui.page_title(
    "Cruscotto macro USA",
    "Lo stato dell'economia americana in una schermata: semafori per area, indicatori chiave, "
    "ultimi dati usciti e prossime pubblicazioni.",
)

area_keys = [k for _, _, ks in AREAS for k in ks]
d = ui.load(signal_series_ids(area_keys + SNAPSHOT_GAUGES + cal.signals_for_releases()))

# --- Semaforo per area ---------------------------------------------------------
ui.section(
    "Semaforo per area",
    help="Ogni area riassume 2-5 indicatori. Ogni indicatore vale 2 punti se verde, 1 se giallo, "
         "0 se rosso; l'area è verde con una media di almeno 1,5, gialla da 0,75 a 1,5, rossa sotto "
         "0,75. È una sintesi descrittiva, non una previsione: passa il mouse sulla ⓘ dei singoli "
         "indicatori nelle pagine dedicate per vedere soglie e fonti.",
)

cards = []
for name, _icon, keys in AREAS:
    level, score, readings = S.area_status(keys, d)
    color = LEVEL_COLORS[level]
    greens = sum(1 for r in readings if r.level == "ok")
    scored = sum(1 for r in readings if r.level in LEVEL_SCORE)
    items = []
    for r in readings:
        sig = SIGNALS[r.key]
        items.append(
            f"<span class='kq-dot' style='background:{LEVEL_COLORS[r.level]};width:8px;height:8px'></span> "
            f"{sig.label}: <b>{S.value_text(sig, r.value)}</b> · {r.label or 'senza soglie'}"
        )
    badge = f"{LEVEL_NAME[level]} · {greens}/{scored} verdi" if scored else "n.d."
    cards.append(
        f"<div class='kq-area' style='--c:{color}'><div class='kq-area-head'>"
        f"<span class='kq-area-name'>{name}</span><span class='kq-area-badge'>{badge}</span></div>"
        f"<div class='kq-area-items'>{'<br>'.join(items)}</div></div>"
    )

for row_start in range(0, len(cards), 4):
    cols = st.columns(4)
    for col, card in zip(cols, cards[row_start:row_start + 4]):
        with col:
            st.markdown(card, unsafe_allow_html=True)
    st.space("small")

# --- Indicatori chiave -----------------------------------------------------------
ui.section(
    "Indicatori chiave",
    help="Gli 8 indicatori più seguiti. Lancetta = valore attuale; fasce colorate = soglie "
         "(dettagli nella ⓘ di ciascun indicatore); linea bianca = riferimento (obiettivo Fed, "
         "tasso neutrale, tasso naturale di disoccupazione o zero). Sotto il valore: variazione "
         "rispetto al dato precedente.",
)
for row in (SNAPSHOT_GAUGES[:4], SNAPSHOT_GAUGES[4:]):
    cols = st.columns(4, gap="medium")
    for col, key in zip(cols, row):
        with col:
            ui.gauge_block(key, d)
    st.space("medium")

# --- Ultimi dati e prossime uscite -----------------------------------------------
st.space("small")
left, right = st.columns(2, gap="large")
calendar = cal.get_calendar(days_back=10, days_ahead=14)
with left:
    ui.section("Ultimi dati usciti", help="Pubblicazioni degli ultimi 10 giorni con il valore più recente "
                                           "e quello precedente. Elenco completo nella pagina Calendario.")
    if calendar is None:
        cal.unavailable_note()
    else:
        st.markdown(cal.recent_html(calendar, d, max_items=8, min_importance=2), unsafe_allow_html=True)
with right:
    ui.section("Prossime uscite", help="Pubblicazioni importanti in programma nelle prossime due settimane "
                                        "(fonte: calendario FRED®). Le date possono cambiare.")
    if calendar is None:
        cal.unavailable_note()
    else:
        st.markdown(cal.upcoming_html(calendar, max_items=10, min_importance=2), unsafe_allow_html=True)

ui.guide("Come leggere colori e soglie", """
- **Verde**: valore in linea con un'economia in equilibrio o con condizioni finanziarie normali.
- **Giallo**: da monitorare; il valore si sta allontanando dalla normalità.
- **Rosso**: squilibrio o stress marcato (in un senso o nell'altro: ad esempio sia inflazione
  molto alta sia deflazione).
- **Senza soglie**: indicatori descrittivi, mostrati per contesto.

Le soglie sono ancorate a riferimenti pubblici (obiettivo di inflazione del 2% della Fed, tasso
neutrale indicato dal FOMC, tasso naturale di disoccupazione stimato dal CBO, soglie note in
letteratura come la regola di Sahm) oppure alla distribuzione storica dal 1990. Ogni soglia e la
sua origine sono scritte nella ⓘ dell'indicatore. I semafori descrivono la situazione: **non sono
segnali operativi né previsioni**.
""")
