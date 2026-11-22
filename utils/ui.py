"""
Componenti di interfaccia condivisi
===================================
Stile, header con link, footer legale, titoli di sezione con tooltip,
blocchi gauge/metriche, tabelle riepilogative, fonti e download.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from catalog import RECESSION_SERIES, SERIES, SIGNALS
from config import (
    APP_NAME, DEFAULT_PERIOD, DISCLAIMER_SHORT, FRED_NOTICE, FRED_TOU_URL, HEADER_LINKS,
    LEVEL_COLORS, LEVEL_EMOJI, PALETTE, PERIOD_OPTIONS,
)
from utils import charts, data, fmt
from utils import signals as S
from utils import transforms as T

# =============================================================================
# STILE
# =============================================================================

_CSS = f"""
<style>
:root {{
  --kq-bg: {PALETTE['bg']}; --kq-card: {PALETTE['card']}; --kq-card2: {PALETTE['card2']};
  --kq-line: {PALETTE['line']}; --kq-line2: {PALETTE['line2']}; --kq-txt: {PALETTE['txt']};
  --kq-mut: {PALETTE['mut']}; --kq-teal: {PALETTE['teal']}; --kq-teal2: {PALETTE['teal2']};
}}
[data-testid="stMainBlockContainer"] {{ padding-top: 3.4rem; padding-bottom: 2rem; max-width: 1400px; }}
[data-testid="stSidebar"] {{ background: {PALETTE['bg2']}; border-right: 1px solid var(--kq-line); }}
h1, h2, h3 {{ letter-spacing: -0.01em; }}
[data-testid="stMetric"] {{ background: var(--kq-card); border-radius: 12px; }}
[data-testid="stMetricLabel"] p {{ color: var(--kq-mut); }}

/* Header con link */
.kq-header {{ display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap;
  padding: 10px 16px; margin: 0 0 18px 0; background: var(--kq-card); border:1px solid var(--kq-line);
  border-radius: 14px; }}
.kq-brand {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }}
.kq-logo {{ font-weight: 800; font-size: 1.25rem; color: var(--kq-txt); letter-spacing:-0.02em; }}
.kq-logo span {{ background: linear-gradient(135deg, {PALETTE['teal']}, {PALETTE['teal2']});
  -webkit-background-clip: text; background-clip: text; color: transparent; }}
.kq-sub {{ color: var(--kq-mut); font-size: 0.9rem; }}
.kq-links {{ display:flex; gap:8px; flex-wrap:wrap; }}
.kq-links a {{ text-decoration:none !important; color: var(--kq-txt) !important; font-weight:600; font-size:0.9rem;
  padding: 7px 14px; border-radius: 999px; border:1px solid var(--kq-line2); background: var(--kq-card2);
  transition: border-color .15s ease, color .15s ease; }}
.kq-links a:hover {{ border-color: var(--kq-teal); color: var(--kq-teal) !important; }}

/* Titolo pagina */
.kq-page-title {{ margin: 0 0 2px 0; font-size: 1.9rem; font-weight: 800; }}
.kq-page-sub {{ color: var(--kq-mut); margin: 0 0 14px 0; }}

/* Riga di stato sotto gauge e metriche */
.kq-status {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:0.86rem; margin-top:-18px; }}
[data-testid="stMetric"] + div .kq-status, .stElementContainer:has([data-testid="stMetric"]) + .stElementContainer .kq-status {{ margin-top: -6px; }}
.kq-dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; flex:0 0 auto; }}
.kq-status-label {{ font-weight:700; }}
.kq-status-meta {{ color: var(--kq-mut); }}

/* Card delle aree */
.kq-area {{ background: var(--kq-card); border:1px solid var(--kq-line); border-left: 4px solid var(--c);
  border-radius: 12px; padding: 12px 14px; height: 100%; }}
.kq-area-head {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
.kq-area-name {{ font-weight: 800; font-size: 1.02rem; }}
.kq-area-badge {{ font-size: 0.78rem; font-weight: 800; color: var(--c); border:1px solid var(--c);
  padding: 2px 8px; border-radius: 999px; white-space:nowrap; }}
.kq-area-items {{ margin-top: 8px; font-size: 0.84rem; color: var(--kq-mut); line-height: 1.55; }}
.kq-area-items b {{ color: var(--kq-txt); font-weight: 600; }}

/* Liste calendario / ultimi dati */
.kq-list-item {{ display:flex; gap:10px; align-items:flex-start; padding: 8px 0; border-bottom: 1px solid var(--kq-line); }}
.kq-list-date {{ min-width: 92px; color: var(--kq-mut); font-size: 0.85rem; }}
.kq-list-body {{ font-size: 0.9rem; }}
.kq-list-body small {{ color: var(--kq-mut); }}
.kq-imp {{ font-size:0.72rem; font-weight:800; padding:1px 7px; border-radius:999px; margin-left:6px;
  border:1px solid var(--kq-line2); color: var(--kq-mut); }}
.kq-imp.alta {{ color: {PALETTE['gold']}; border-color: {PALETTE['gold']}; }}

/* Footer */
.kq-footer {{ margin-top: 28px; padding-top: 14px; border-top: 1px solid var(--kq-line);
  color: var(--kq-mut); font-size: 0.8rem; line-height: 1.6; }}
.kq-footer a {{ color: var(--kq-mut) !important; }}
.kq-source {{ color: var(--kq-mut); font-size: 0.76rem; margin-top: -8px; margin-bottom: 10px; }}

@media (max-width: 640px) {{
  .kq-page-title {{ font-size: 1.5rem; }}
  .kq-header {{ padding: 10px 12px; }}
  .kq-logo {{ font-size: 1.1rem; }}
}}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


# =============================================================================
# HEADER, TITOLI, FOOTER
# =============================================================================

def header() -> None:
    links = "".join(
        f'<a href="{url}" target="_blank" rel="noopener">{label}</a>' for label, url in HEADER_LINKS
    )
    st.markdown(
        f"""<div class="kq-header">
              <div class="kq-brand"><span class="kq-logo">Kriterion<span>Quant</span></span>
              <span class="kq-sub">{APP_NAME} · dati macroeconomici in tempo reale</span></div>
              <nav class="kq-links">{links}</nav>
            </div>""",
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str) -> None:
    st.markdown(f"<h1 class='kq-page-title'>{title}</h1><p class='kq-page-sub'>{subtitle}</p>",
                unsafe_allow_html=True)


def section(title: str, help: str | None = None) -> None:
    st.subheader(title, help=help, anchor=False)


def footer(legal_page=None) -> None:
    st.markdown(
        f"""<div class="kq-footer">
        <b>Disclaimer.</b> {DISCLAIMER_SHORT}<br>
        {FRED_NOTICE}<br>
        Usando questa applicazione accetti i <a href="{FRED_TOU_URL}" target="_blank" rel="noopener">
        Termini d'uso dell'API FRED®</a>. Fonti, licenze, note di copyright e privacy nella pagina
        «Note legali e fonti».
        </div>""",
        unsafe_allow_html=True,
    )
    if legal_page is not None:
        st.page_link(legal_page, label="Note legali e fonti", icon=":material/gavel:")


# =============================================================================
# CONTROLLI GLOBALI
# =============================================================================

def period_years() -> int | None:
    label = st.session_state.get("period") or DEFAULT_PERIOD
    return PERIOD_OPTIONS.get(label, 10)


def period_label() -> str:
    label = st.session_state.get("period") or DEFAULT_PERIOD
    return "tutta la storia" if label == "Max" else f"ultimi {PERIOD_OPTIONS[label]} anni"


def recessions_enabled() -> bool:
    return bool(st.session_state.get("show_rec", True))


def recession_periods(d: dict[str, pd.Series]):
    if not recessions_enabled():
        return None
    return T.recession_periods(d.get(RECESSION_SERIES))


# =============================================================================
# DATI
# =============================================================================

def load(ids) -> dict[str, pd.Series]:
    """Scarica le serie (con la serie delle recessioni) mostrando uno spinner."""
    ids = list(dict.fromkeys(list(ids) + [RECESSION_SERIES]))
    with st.spinner("Carico i dati FRED®..."):
        d = data.load(ids)
    miss = data.missing(ids)
    if miss:
        if not data.api_key() and not data.dev_public_mode():
            st.error("Chiave FRED® non configurata: imposta `FRED_API_KEY` nei secrets dell'app.")
            st.stop()
        st.warning(
            "Alcuni dati non sono al momento disponibili e verranno riprovati: "
            + ", ".join(sorted(miss)), icon=":material/cloud_off:",
        )
    return d


def load_signals(keys) -> dict[str, pd.Series]:
    from catalog import signal_series_ids
    return load(signal_series_ids(keys))


# =============================================================================
# BLOCCHI
# =============================================================================

def gauge_block(key: str, d: dict[str, pd.Series], height: int = 200) -> None:
    sig = SIGNALS[key]
    st.markdown(f"**{sig.label}**", help=S.help_text(key, d))
    r = S.evaluate(key, d)
    if r is None or sig.gauge_range is None:
        st.info("Dato non disponibile", icon=":material/hourglass_empty:")
        return
    fig = charts.gauge(r.value, r.bands, sig.gauge_range, suffix=sig.suffix, decimals=sig.decimals,
                       target=r.target, reference=r.prev_value, delta_color=sig.delta_color, height=height)
    charts.show(fig, key=f"gauge_{key}")
    st.markdown(S.status_html(r), unsafe_allow_html=True)


def kpi(key: str, d: dict[str, pd.Series], label: str | None = None, spark_points: int = 24) -> None:
    sig = SIGNALS[key]
    r = S.evaluate(key, d)
    if r is None:
        st.metric(label or sig.label, "n.d.", help=S.help_text(key, d), border=True)
        return
    spark = r.series.tail(spark_points).round(4).tolist()
    st.metric(
        label or sig.label,
        S.value_text(sig, r.value),
        delta=S.delta_text(sig, r.delta),
        delta_color=sig.delta_color,
        help=S.help_text(key, d),
        border=True,
        chart_data=spark if len(spark) > 2 else None,
        chart_type="line",
    )
    st.markdown(S.status_html(r), unsafe_allow_html=True)


def kpi_row(keys: list[str], d: dict[str, pd.Series], labels: dict[str, str] | None = None) -> None:
    cols = st.columns(len(keys))
    for col, key in zip(cols, keys):
        with col:
            kpi(key, d, (labels or {}).get(key))


def source_caption(series_ids, extra: str = "", time_chart: bool = True) -> None:
    """Fonte del grafico + eventuali note di copyright (obbligatorie per alcune serie)."""
    ids = [s for s in dict.fromkeys(series_ids) if s in SERIES and s != RECESSION_SERIES]
    sources = list(dict.fromkeys(SERIES[s].source for s in ids))
    text = f"Fonte: {'; '.join(sources)}, tramite FRED® (serie {', '.join(ids)})."
    notices = [SERIES[s].copyright for s in ids if SERIES[s].copyright]
    if notices:
        text += " " + " ".join(dict.fromkeys(notices))
    if time_chart and recessions_enabled():
        text += " Aree grigie: recessioni USA (NBER, via FRED®)."
    if extra:
        text += " " + extra
    st.markdown(f"<div class='kq-source'>{text}</div>", unsafe_allow_html=True)


def chart_title(title: str, help: str | None = None) -> None:
    st.markdown(f"**{title}**", help=help)


def signal_chart(
    keys: list[str],
    d: dict[str, pd.Series],
    *,
    title: str,
    help: str | None = None,
    names: dict[str, str] | None = None,
    years: int | None = -1,
    height: int = 340,
    zero_line: bool = False,
    hlines: list[dict] | None = None,
    hbands: list[dict] | None = None,
    bars: set[str] | None = None,
    colors: dict[str, str] | None = None,
    extra_source: str = "",
    chart_key: str | None = None,
) -> dict[str, pd.Series]:
    """Grafico temporale di uno o più indicatori + fonte. Restituisce le serie mostrate."""
    yrs = period_years() if years == -1 else years
    chart_title(title, help)
    traces, shown = [], {}
    for key in keys:
        sig = SIGNALS[key]
        s = T.window(S.compute(key, d), yrs)
        name = (names or {}).get(key, sig.label)
        shown[name] = s
        traces.append({
            "series": s, "name": name, "decimals": sig.decimals, "suffix": sig.suffix,
            "kind": "bar" if bars and key in bars else "line",
            **({"color": colors[key]} if colors and key in colors else {}),
        })
    if all(tr["series"].empty for tr in traces):
        st.caption("Dati non disponibili al momento: verranno riprovati al prossimo aggiornamento.")
        return shown
    first = SIGNALS[keys[0]]
    fig = charts.time_chart(traces, height=height, recessions=recession_periods(d), zero_line=zero_line,
                            hlines=hlines, hbands=hbands, suffix=first.suffix, decimals=first.decimals)
    # chiave esplicita: grafici con parametri uguali non devono collidere
    charts.show(fig, key=chart_key or f"chart_{'_'.join(keys)}_{title}")
    ids = [sid for k in keys for sid in SIGNALS[k].series]
    source_caption(ids, extra_source)
    return shown


def level_bands_for_chart(key: str, d: dict[str, pd.Series], alpha_levels=("ok",)) -> list[dict]:
    """Fasce orizzontali colorate (es. la fascia verde) da sovrapporre a un grafico."""
    sig = SIGNALS[key]
    out = []
    for b in S.resolve_bands(sig, d):
        if b.level in alpha_levels and b.lo is not None and b.hi is not None:
            out.append({"y0": b.lo, "y1": b.hi, "color": LEVEL_COLORS[b.level]})
    return out


def summary_table(keys: list[str], d: dict[str, pd.Series], file_stub: str) -> None:
    """Tabella riepilogativa con stato, valore, variazione e percentile + download CSV."""
    rows = []
    for key in keys:
        sig = SIGNALS[key]
        r = S.evaluate(key, d)
        if r is None:
            continue
        rows.append({
            "Stato": LEVEL_EMOJI[r.level],
            "Indicatore": sig.label,
            "Valore": S.value_text(sig, r.value),
            "Variazione": S.delta_text(sig, r.delta) or "",
            "Lettura": r.label or "—",
            "Percentile dal 1990": fmt.ordinal_pct(r.pct),
            "Dato del": fmt.date_label(r.date, S.freq_of(sig)),
            "Serie FRED®": ", ".join(s for s in sig.series),
        })
    if not rows:
        return
    st.dataframe(
        pd.DataFrame(rows), hide_index=True, width="stretch",
        column_config={
            "Stato": st.column_config.TextColumn("", width="small",
                                                 help="Verde = equilibrio, giallo = da monitorare, rosso = squilibrio/stress, bianco = senza soglie"),
            "Variazione": st.column_config.TextColumn("Variazione", help="Rispetto all'osservazione precedente"),
            "Percentile dal 1990": st.column_config.TextColumn(
                "Percentile", help="Percentuale delle osservazioni dal 1990 inferiori al valore attuale"),
        },
    )
    download_signals(keys, d, file_stub)


def download_signals(keys: list[str], d: dict[str, pd.Series], file_stub: str) -> None:
    yrs = period_years()
    frames = {}
    for key in keys:
        s = T.window(S.compute(key, d), yrs)
        if not s.empty:
            frames[SIGNALS[key].label] = s
    if not frames:
        return
    df = pd.concat(frames, axis=1).sort_index()
    df.index.name = "data"
    csv = df.to_csv(sep=";", decimal=",", float_format="%.4f").encode("utf-8-sig")
    st.download_button(
        "Scarica le serie (CSV)", csv, file_name=f"{file_stub}_{date.today():%Y%m%d}.csv",
        mime="text/csv", icon=":material/download:",
        help=f"Serie storiche degli indicatori della tabella, {period_label()}. "
             "Formato CSV con separatore ';' e decimali con la virgola (si apre in Excel).",
    )


def guide(title: str, body: str) -> None:
    with st.expander(title, icon=":material/menu_book:"):
        st.markdown(body)
