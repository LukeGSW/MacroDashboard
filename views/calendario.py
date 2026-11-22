"""Calendario delle pubblicazioni dei dati macro USA."""

from datetime import date

import pandas as pd
import streamlit as st

from catalog import DAILY_NOTE, RELEASES, SIGNALS
from utils import cal, fmt, ui

ui.page_title(
    "Calendario dati",
    "Quando escono i prossimi dati macro USA e quali indicatori della dashboard aggiornano.",
)

c1, c2 = st.columns([1, 1])
with c1:
    scope = st.segmented_control(
        "Pubblicazioni", ["Principali", "Tutte"], default="Principali", required=True, key="cal_scope",
        help="Principali = importanza alta e media (inflazione, lavoro, PIL, Fed, consumi, attività). "
             "Tutte = include anche dati settimanali e trimestrali minori.",
    )
with c2:
    horizon = st.segmented_control(
        "Orizzonte", ["2 settimane", "1 mese", "2 mesi"], default="1 mese", required=True, key="cal_horizon",
    )
days_ahead = {"2 settimane": 14, "1 mese": 31, "2 mesi": 62}[horizon]
min_imp = 2 if scope == "Principali" else 1

df = cal.get_calendar(days_back=21, days_ahead=62)
if df is None:
    cal.unavailable_note()
    st.stop()

today = pd.Timestamp(date.today())
df = df[df["importance"] >= min_imp]


def _signals_text(rid: int) -> str:
    keys = [k for k in RELEASES[rid].signals if k in SIGNALS]
    return ", ".join(SIGNALS[k].label for k in keys) if keys else "—"


def _table(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Data": [f"{fmt.GIORNI[x.weekday()]} {x:%d/%m/%Y}" for x in frame["date"]],
        "Pubblicazione": frame["name"].tolist(),
        "Importanza": [cal.IMPORTANCE[i].capitalize() for i in frame["importance"]],
        "Indicatori aggiornati": [_signals_text(r) for r in frame["release_id"]],
    })


tab_next, tab_past = st.tabs(["In arrivo", "Usciti di recente"])
with tab_next:
    nxt = df[(df["date"] >= today) & (df["date"] <= today + pd.Timedelta(days=days_ahead))]
    nxt = nxt.sort_values(["date", "importance"], ascending=[True, False])
    if nxt.empty:
        st.info("Nessuna pubblicazione nel periodo selezionato.")
    else:
        st.dataframe(_table(nxt), hide_index=True, width="stretch",
                     column_config={"Importanza": st.column_config.TextColumn(
                         help="Alta = dati che di solito muovono i mercati (CPI, PCE, occupazione, PIL, FOMC).")})
with tab_past:
    past = df[(df["date"] < today)].sort_values(["date", "importance"], ascending=[False, False])
    if past.empty:
        st.info("Nessuna pubblicazione nelle ultime tre settimane.")
    else:
        st.dataframe(_table(past), hide_index=True, width="stretch")

st.caption(
    "Fonti: calendario delle release FRED® e, per le decisioni FOMC, calendario ufficiale della "
    "Federal Reserve. Le date sono quelle programmate e possono cambiare; "
    "FRED® non indica l'orario: i dati principali USA escono in genere alle 8:30 di New York "
    "(14:30 in Italia), le decisioni FOMC alle 14:00 di New York (20:00 in Italia). "
    + DAILY_NOTE
)
