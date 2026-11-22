"""Calendario delle pubblicazioni dei dati macro USA, con le date verificate in automatico."""

import pandas as pd
import streamlit as st

from catalog import DAILY_NOTE, RELEASES, SIGNALS
from utils import cal, fmt, ui

ui.page_title(
    "Calendario dati",
    "Quando escono i prossimi dati macro USA, a che ora in Italia e quali indicatori della dashboard "
    "aggiornano. Le date sono verificate in automatico sui calendari ufficiali.",
)

horizon = st.segmented_control(
    "Orizzonte", ["2 settimane", "1 mese", "2 mesi"], default="1 mese", required=True, key="cal_horizon",
)
days_ahead = {"2 settimane": 14, "1 mese": 31, "2 mesi": 62}[horizon]

with st.spinner("Verifico le date sui calendari ufficiali..."):
    calendar = cal.get_calendar()
if calendar is None:
    cal.unavailable_note()
    st.stop()

for w in calendar.warnings:
    st.warning(w, icon=":material/warning:")

ARRIVAL = {"ok": "✓ Dato arrivato", "attesa": "In arrivo su FRED®", "mancante": "⚠ Non risulta pubblicato"}


def _signals_text(key: str) -> str:
    keys = [k for k in RELEASES[key].signals if k in SIGNALS]
    return ", ".join(SIGNALS[k].label for k in keys) if keys else "—"


def _table(frame: pd.DataFrame, past: bool) -> pd.DataFrame:
    out = pd.DataFrame({
        "Data": [f"{fmt.GIORNI[x.weekday()]} {x:%d/%m/%Y}" for x in frame["day"]],
        "Ora (Italia)": frame["time"].tolist(),
        "Pubblicazione": frame["name"].tolist(),
        "Dettaglio": [x or "—" for x in frame["detail"]],
        "Importanza": [cal.IMPORTANCE[i].capitalize() for i in frame["importance"]],
    })
    if past:
        out["Stato"] = [ARRIVAL.get(a, "—") for a in frame["arrival"]]
    else:
        out["Verifica"] = [cal.BASIS_TEXT[b] if s == "ok" else f"⚠ Da confermare: {n}"
                           for s, n, b in zip(frame["status"], frame["note"], frame["basis"])]
    out["Fonte ufficiale"] = frame["source_url"].tolist()
    out["Indicatori aggiornati"] = [_signals_text(k) for k in frame["key"]]
    return out


COLUMNS = {
    "Fonte ufficiale": st.column_config.LinkColumn(display_text="Verifica ↗",
                                                   help="Apre la pagina ufficiale con la data dell'uscita."),
    "Importanza": st.column_config.TextColumn(
        help="Alta = dati che di solito muovono i mercati (FOMC, CPI, PCE, occupazione, PIL)."),
    "Verifica": st.column_config.TextColumn(
        help="Confermata da 2 fonti = la data coincide tra il calendario ufficiale dell'agenzia e il "
             "calendario FRED® (per l'FOMC: tra le due fonti della Fed). Calendario ufficiale = data "
             "oltre quelle già note a FRED®, da un calendario ufficiale che coincide con FRED® sulle date "
             "precedenti. Calendario FRED® = BLS e DOL, i cui siti non consentono la lettura automatica: "
             "dopo l'uscita si controlla che il dato sia arrivato. Da confermare = fonti non concordi o "
             "non raggiungibili."),
    "Stato": st.column_config.TextColumn(
        help="Controllo sull'arrivo del dato: la dashboard verifica che la serie su FRED® sia stata "
             "aggiornata dopo l'orario di uscita."),
}

tab_next, tab_past = st.tabs(["In arrivo", "Usciti di recente"])
with tab_next:
    nxt = cal.upcoming(calendar, days_ahead).sort_values(["when", "importance"], ascending=[True, False])
    if nxt.empty:
        st.info("Nessuna pubblicazione nel periodo selezionato.")
    else:
        st.dataframe(_table(nxt, past=False), hide_index=True, width="stretch", column_config=COLUMNS)
    note = cal.horizon_note(calendar, days_ahead)
    if note:
        st.caption(note)
with tab_past:
    past = cal.recent(calendar, 21).sort_values(["when", "importance"], ascending=[False, False])
    if past.empty:
        st.info("Nessuna pubblicazione nelle ultime tre settimane.")
    else:
        st.dataframe(_table(past, past=True), hide_index=True, width="stretch", column_config=COLUMNS)

st.caption(
    cal.sources_text(calendar)
    + " Orari in ora italiana, ricavati dagli orari ufficiali di New York (per BLS e DOL si usa "
      "l'orario abituale di pubblicazione). " + DAILY_NOTE
)
