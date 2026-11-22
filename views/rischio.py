"""Rischio recessione: indicatori anticipatori e loro storico (successi e falsi allarmi)."""

import pandas as pd
import streamlit as st

from catalog import RECESSION_SERIES, signal_series_ids
from config import LEVEL_COLORS
from utils import fmt, ui
from utils import signals as S
from utils import transforms as T

KEYS = ["sahm", "t10y3m", "recprob", "claims_rise", "t10y2y", "baa10y", "nfci", "drtscilm"]

ui.page_title(
    "Rischio recessione",
    "Gli indicatori che in passato hanno anticipato o accompagnato le recessioni USA, "
    "con i loro successi e i loro falsi allarmi.",
)
d = ui.load(signal_series_ids(KEYS))

# --- Quadro sintetico -------------------------------------------------------------
readings = [r for r in (S.evaluate(k, d) for k in KEYS) if r is not None]
reds = [r for r in readings if r.level == "bad"]
yellows = [r for r in readings if r.level == "warn"]
greens = [r for r in readings if r.level == "ok"]
c1, c2, c3 = st.columns(3)
c1.metric("Segnali rossi", len(reds), border=True,
          help="Indicatori in zona di allarme secondo le soglie della ⓘ di ciascuno.")
c2.metric("Segnali gialli", len(yellows), border=True, help="Indicatori da monitorare.")
c3.metric("Segnali verdi", len(greens), border=True, help="Indicatori senza segnali di recessione.")
if reds:
    st.markdown(
        "In allarme: " + ", ".join(
            f"<b style='color:{LEVEL_COLORS['bad']}'>{r.signal.label}</b> ({S.value_text(r.signal, r.value)})"
            for r in reds),
        unsafe_allow_html=True,
    )
st.caption(
    "Nessun indicatore ha previsto tutte le recessioni senza falsi allarmi: vanno letti insieme. "
    "Le tabelle in fondo alla pagina mostrano lo storico dei segnali, calcolato sui dati FRED®."
)

# --- Gauge --------------------------------------------------------------------------
ui.section("Indicatori", help="Passa il mouse sulla ⓘ di ogni indicatore per definizione, soglie e fonte.")
for row in (KEYS[:4], KEYS[4:]):
    cols = st.columns(4, gap="medium")
    for col, key in zip(cols, row):
        with col:
            ui.gauge_block(key, d)
    st.space("medium")

# --- Grafici ------------------------------------------------------------------------
ui.section("Andamento storico")
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(
        ["t10y3m", "t10y2y"], d, title="Curva dei rendimenti: 10A-3M e 10A-2A",
        help=S.help_text("t10y3m", d), names={"t10y3m": "10 anni - 3 mesi", "t10y2y": "10 anni - 2 anni"},
        zero_line=True, hbands=[{"y0": -4, "y1": 0, "color": LEVEL_COLORS["bad"]}],
    )
with b:
    ui.signal_chart(
        ["sahm"], d, title="Regola di Sahm (tempo reale)", help=S.help_text("sahm", d),
        hlines=[{"y": 0.5, "label": "Soglia 0,5", "color": LEVEL_COLORS["bad"]}],
    )
a, b = st.columns(2, gap="large")
with a:
    ui.signal_chart(["recprob"], d, title="Probabilità di recessione (Chauvet-Piger)",
                    help=S.help_text("recprob", d))
with b:
    ui.signal_chart(
        ["claims_rise"], d, title="Richieste di sussidio: distanza dal minimo di 52 settimane",
        help=S.help_text("claims_rise", d),
        hlines=[{"y": 20, "label": "Soglia 20%", "color": LEVEL_COLORS["bad"]}],
    )

# --- Storico dei segnali ---------------------------------------------------------------
ui.section(
    "Storico dei segnali: quante volte hanno funzionato",
    help="Calcolato in tempo reale sui dati FRED®. Inversione = media mensile dello spread sotto zero; "
         "si considera 'seguita da recessione' se una recessione NBER inizia entro 24 mesi.",
)
rec_periods = T.recession_periods(d.get(RECESSION_SERIES))
rec_starts = [s for s, _ in rec_periods]
today = pd.Timestamp.today().normalize()


def _months(a: pd.Timestamp, b: pd.Timestamp) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def curve_table(series_id: str, label: str) -> pd.DataFrame:
    s = T.clean(d.get(series_id))
    if s.empty:
        return pd.DataFrame()
    m = s.resample("MS").mean().dropna()
    rows = []
    for start in T.signal_episodes(m, lambda v: v < 0, min_gap_months=6):
        after = m[m.index > start]
        back = after[after >= 0]
        end = back.index.min() if not back.empty else None
        nxt = [r for r in rec_starts if r >= start]
        rec = nxt[0] if nxt else None
        lead = _months(start, rec) if rec is not None else None
        if rec is not None and lead <= 24:
            outcome = "Seguita da recessione"
        elif _months(start, today) < 24:
            outcome = "Esito non ancora noto"
        else:
            outcome = "Nessuna recessione entro 24 mesi"
        rows.append({
            "Inizio inversione": fmt.date_label(start, "M"),
            "Fine inversione": fmt.date_label(end, "M") if end is not None else "In corso",
            "Recessione successiva": fmt.date_label(rec, "M") if rec is not None and lead <= 36 else "—",
            "Mesi di anticipo": lead if rec is not None and lead <= 36 else None,
            "Esito": outcome,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Mesi di anticipo"] = pd.array(df["Mesi di anticipo"].tolist(), dtype="Int64")
    return df


def sahm_table() -> pd.DataFrame:
    s = T.clean(d.get("SAHMREALTIME"))
    rows = []
    for trig in T.signal_episodes(s, lambda v: v >= 0.5, min_gap_months=12):
        near = [r for r in rec_starts if -12 <= _months(r, trig) <= 12]
        rec = near[0] if near else None
        rows.append({
            "Attivazione": fmt.date_label(trig, "M"),
            "Inizio recessione più vicino": fmt.date_label(rec, "M") if rec is not None else "—",
            "Mesi dopo l'inizio": _months(rec, trig) if rec is not None else None,
            "Esito": "In linea con una recessione" if rec is not None else "Falso allarme",
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Mesi dopo l'inizio"] = pd.array(df["Mesi dopo l'inizio"].tolist(), dtype="Int64")
    return df


t1, t2, t3 = st.tabs(["Curva 10A-3M", "Curva 10A-2A", "Regola di Sahm"])
for tab, sid, lab in ((t1, "T10Y3M", "10A-3M"), (t2, "T10Y2Y", "10A-2A")):
    with tab:
        tbl = curve_table(sid, lab)
        if tbl.empty:
            st.info("Dati non disponibili.")
            continue
        st.dataframe(tbl, hide_index=True, width="stretch",
                     column_config={"Mesi di anticipo": st.column_config.NumberColumn(format="%d")})
        hits = (tbl["Esito"] == "Seguita da recessione").sum()
        misses = (tbl["Esito"] == "Nessuna recessione entro 24 mesi").sum()
        first_year = T.clean(d.get(sid)).index.min().year
        covered = [r for r in rec_starts if r.year >= first_year + 1]
        preceded = sum(1 for r in covered
                       if any(0 <= _months(pd.Timestamp(st_), r) <= 24
                              for st_ in T.signal_episodes(T.clean(d.get(sid)).resample("MS").mean().dropna(),
                                                           lambda v: v < 0, 6)))
        st.caption(
            f"Dal {first_year}: {hits} inversioni seguite da recessione, {misses} senza recessione entro "
            f"24 mesi; {preceded} recessioni su {len(covered)} precedute da un'inversione. "
            "L'anticipo è molto variabile e una recessione (2020) è stata causata da uno shock esterno."
        )
with t3:
    tbl = sahm_table()
    if tbl.empty:
        st.info("Dati non disponibili.")
    else:
        st.dataframe(tbl, hide_index=True, width="stretch",
                     column_config={"Mesi dopo l'inizio": st.column_config.NumberColumn(format="%d")})
        st.caption("La regola si attiva in genere a recessione già iniziata: è una conferma tempestiva più "
                   "che un anticipo. Un falso allarme è possibile quando la disoccupazione sale per un aumento "
                   "dell'offerta di lavoro (come nel 2024) invece che per licenziamenti.")

ui.summary_table(KEYS, d, "rischio_recessione")

ui.guide("Come leggere questa pagina", """
- **Curva dei rendimenti**: un'inversione (tassi a breve sopra quelli a lungo) segnala che il mercato
  si aspetta tagli dei tassi, spesso perché prevede un rallentamento. È l'indicatore anticipatore più
  noto, ma l'anticipo va da pochi mesi a due anni e l'inversione 2022-2024 non è stata seguita da una
  recessione entro 24 mesi.
- **Regola di Sahm**: segnala quando la disoccupazione sale rapidamente. Arriva quasi sempre a
  recessione appena iniziata.
- **Probabilità Chauvet-Piger**: modello statistico sui dati di attività; esce con ritardo e conferma
  le recessioni più che anticiparle.
- **Richieste di sussidio**: il dato più tempestivo (settimanale) sui licenziamenti.
- **Credito e condizioni finanziarie**: spread Baa, NFCI e standard bancari misurano quanto è difficile
  finanziarsi; il loro peggioramento ha accompagnato le recessioni passate.

Nessuno di questi indicatori è una previsione: servono a capire **quanti segnali di rischio sono accesi
contemporaneamente**.
""")
