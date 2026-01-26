"""
FRED Macro Dashboard - Tassi Page
==================================
Analisi tassi di interesse e yield curve USA.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from config import INDICATORS
from utils.fred_api import get_latest_value, get_indicator_data
from utils.charts import create_gauge, create_line_chart, create_multi_line_chart, create_yield_curve


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Tassi | FRED Macro Dashboard",
    page_icon="🏦",
    layout="wide"
)


# =============================================================================
# HEADER
# =============================================================================

st.title("🏦 Tassi di Interesse")
st.markdown("*Monitoraggio Fed Funds, Treasury e Yield Curve*")
st.markdown(f"*Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

st.markdown("---")


# =============================================================================
# KPI ROW
# =============================================================================

st.markdown("### 🎯 Tassi Chiave")

tassi_indicators = INDICATORS["tassi"]

col1, col2, col3, col4, col5 = st.columns(5)

kpi_data = [
    ("FEDFUNDS", "Fed Funds"),
    ("DGS2", "Treasury 2Y"),
    ("DGS10", "Treasury 10Y"),
    ("T10Y2Y", "Spread 10Y-2Y"),
    ("T10Y3M", "Spread 10Y-3M")
]

for col, (code, label) in zip([col1, col2, col3, col4, col5], kpi_data):
    with col:
        data = get_latest_value(code)
        if data["value"] is not None:
            # Per gli spread, inversione = warning
            if "Spread" in label:
                delta_color = "normal" if data.get("change", 0) >= 0 else "inverse"
            else:
                delta_color = "off"
            
            st.metric(
                label=label,
                value=f"{data['value']:.2f}%",
                delta=f"{data['change']:+.2f}%" if data['change'] else None,
                delta_color=delta_color
            )
            st.caption(f"📅 {data['date']}")

st.markdown("---")


# =============================================================================
# SIDEBAR CONTROLS
# =============================================================================

with st.sidebar:
    st.markdown("### ⚙️ Controlli")
    
    years_range = st.slider(
        "Periodo storico (anni)",
        min_value=1,
        max_value=40,
        value=10,
        step=1
    )
    
    show_recessions = st.checkbox("Mostra recessioni", value=True)
    
    st.markdown("---")
    
    st.markdown("### 📖 Legenda")
    st.markdown("""
    - **Fed Funds**: Tasso overnight interbancario
    - **DGS**: Treasury Constant Maturity
    - **T10Y2Y**: Spread 10Y minus 2Y
    - **T10Y3M**: Spread 10Y minus 3M
    """)
    
    st.markdown("---")
    
    st.markdown("### ⚠️ Segnali")
    st.markdown("""
    **Yield Curve Invertita:**
    - 10Y-2Y < 0: Warning
    - 10Y-3M < 0: Forte warning
    - Storicamente precede recessioni di 12-18 mesi
    """)


# =============================================================================
# YIELD CURVE SNAPSHOT
# =============================================================================

st.markdown("### 📐 Yield Curve Attuale")

col1, col2 = st.columns([2, 1])

with col1:
    # Fetch current yields
    maturities = ["DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]
    maturity_labels = ["1Y", "2Y", "5Y", "10Y", "30Y"]
    
    yields_data = {}
    for code, label in zip(maturities, maturity_labels):
        data = get_latest_value(code)
        if data["value"] is not None:
            yields_data[label] = data["value"]
    
    if yields_data:
        fig = create_yield_curve(
            yields_data=yields_data,
            title="Treasury Yield Curve",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 📊 Analisi Curva")
    
    # Spread analysis
    t10y2y = get_latest_value("T10Y2Y")
    t10y3m = get_latest_value("T10Y3M")
    
    if t10y2y["value"] is not None:
        if t10y2y["value"] < 0:
            st.error(f"🔴 **Curva Invertita (10Y-2Y)**")
            st.markdown(f"Spread: **{t10y2y['value']:.2f}%**")
            st.markdown("⚠️ Segnale recessione storico")
        elif t10y2y["value"] < 0.5:
            st.warning(f"🟡 **Curva Piatta (10Y-2Y)**")
            st.markdown(f"Spread: **{t10y2y['value']:.2f}%**")
            st.markdown("👀 Monitorare attentamente")
        else:
            st.success(f"🟢 **Curva Normale (10Y-2Y)**")
            st.markdown(f"Spread: **{t10y2y['value']:.2f}%**")
    
    st.markdown("---")
    
    if t10y3m["value"] is not None:
        if t10y3m["value"] < 0:
            st.error(f"🔴 **10Y-3M Invertito: {t10y3m['value']:.2f}%**")
        elif t10y3m["value"] < 0.5:
            st.warning(f"🟡 **10Y-3M Piatto: {t10y3m['value']:.2f}%**")
        else:
            st.success(f"🟢 **10Y-3M Normale: {t10y3m['value']:.2f}%**")
    
    st.markdown("---")
    
    # Steepness
    if yields_data:
        steepness_2_10 = yields_data.get("10Y", 0) - yields_data.get("2Y", 0)
        steepness_2_30 = yields_data.get("30Y", 0) - yields_data.get("2Y", 0)
        
        st.markdown("**Steepness:**")
        st.markdown(f"- 2Y → 10Y: {steepness_2_10:.2f}%")
        st.markdown(f"- 2Y → 30Y: {steepness_2_30:.2f}%")

st.markdown("---")


# =============================================================================
# FED FUNDS & POLICY
# =============================================================================

st.markdown("### 🏛️ Federal Funds Rate")

col1, col2 = st.columns([2, 1])

with col1:
    fedfunds_df = get_indicator_data("FEDFUNDS", years=years_range)
    
    if not fedfunds_df.empty:
        fig = create_line_chart(
            df=fedfunds_df,
            title="Federal Funds Effective Rate",
            y_label="%",
            color="#1f77b4",
            show_recessions=show_recessions,
            height=400,
            show_zero_line=True
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    fedfunds_data = get_latest_value("FEDFUNDS")
    
    if fedfunds_data["value"]:
        fig = create_gauge(
            value=fedfunds_data["value"],
            title="Fed Funds Rate",
            gauge_range=[0, 8],
            thresholds={
                "green": [0, 3],
                "yellow": [3, 5],
                "red": [5, 8]
            },
            units="%",
            delta_reference=fedfunds_data.get("previous"),
            invert=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### 📋 Policy Stance")
    
    if fedfunds_data["value"]:
        rate = fedfunds_data["value"]
        if rate < 2:
            st.success("🕊️ **Accommodativa**")
            st.markdown("Politica monetaria espansiva")
        elif rate < 4:
            st.info("⚖️ **Neutrale**")
            st.markdown("Politica monetaria bilanciata")
        else:
            st.warning("🦅 **Restrittiva**")
            st.markdown("Politica monetaria hawkish")

st.markdown("---")


# =============================================================================
# TREASURY YIELDS
# =============================================================================

st.markdown("### 📈 Treasury Yields Storici")

# Fetch all treasury data
treasury_codes = ["DGS1", "DGS2", "DGS5", "DGS10", "DGS30"]
treasury_data = {}
treasury_colors = {}

for code in treasury_codes:
    config = tassi_indicators.get(code, {})
    df = get_indicator_data(code, years=years_range)
    if not df.empty:
        treasury_data[config.get("name", code)] = df
        treasury_colors[config.get("name", code)] = config.get("color", "#1f77b4")

if treasury_data:
    fig = create_multi_line_chart(
        data_dict=treasury_data,
        title="Treasury Yields per Maturity",
        y_label="%",
        colors=treasury_colors,
        show_recessions=show_recessions,
        height=450,
        show_zero_line=True
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# =============================================================================
# YIELD CURVE SPREADS
# =============================================================================

st.markdown("### 📉 Yield Curve Spreads (Indicatori Recessione)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Spread 10Y - 2Y")
    
    t10y2y_df = get_indicator_data("T10Y2Y", years=years_range)
    
    if not t10y2y_df.empty:
        fig = create_line_chart(
            df=t10y2y_df,
            title="10-Year Treasury Minus 2-Year Treasury",
            y_label="%",
            color="#e377c2",
            show_recessions=show_recessions,
            height=350,
            show_zero_line=True
        )
        
        # Evidenzia zona inversione
        fig.add_hrect(
            y0=-3, y1=0,
            fillcolor="rgba(255, 68, 68, 0.1)",
            line_width=0,
            annotation_text="Inversione",
            annotation_position="bottom right"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        if len(t10y2y_df) > 0:
            days_inverted = (t10y2y_df["value"] < 0).sum()
            pct_inverted = days_inverted / len(t10y2y_df) * 100
            st.caption(f"📊 Giorni in inversione (periodo selezionato): {days_inverted} ({pct_inverted:.1f}%)")

with col2:
    st.markdown("#### Spread 10Y - 3M")
    
    t10y3m_df = get_indicator_data("T10Y3M", years=years_range)
    
    if not t10y3m_df.empty:
        fig = create_line_chart(
            df=t10y3m_df,
            title="10-Year Treasury Minus 3-Month Treasury",
            y_label="%",
            color="#bcbd22",
            show_recessions=show_recessions,
            height=350,
            show_zero_line=True
        )
        
        # Evidenzia zona inversione
        fig.add_hrect(
            y0=-3, y1=0,
            fillcolor="rgba(255, 68, 68, 0.1)",
            line_width=0,
            annotation_text="Inversione",
            annotation_position="bottom right"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        if len(t10y3m_df) > 0:
            days_inverted = (t10y3m_df["value"] < 0).sum()
            pct_inverted = days_inverted / len(t10y3m_df) * 100
            st.caption(f"📊 Giorni in inversione (periodo selezionato): {days_inverted} ({pct_inverted:.1f}%)")

st.markdown("---")


# =============================================================================
# REAL RATES (Optional section)
# =============================================================================

st.markdown("### 💰 Tassi Reali (Nominali - Inflazione)")

col1, col2, col3 = st.columns(3)

# Calculate real rates
dgs10_data = get_latest_value("DGS10")
t10yie_data = get_latest_value("T10YIE")

if dgs10_data["value"] and t10yie_data["value"]:
    real_10y = dgs10_data["value"] - t10yie_data["value"]
    
    with col1:
        st.metric(
            "Treasury 10Y Nominale",
            f"{dgs10_data['value']:.2f}%"
        )
    
    with col2:
        st.metric(
            "Breakeven Inflation 10Y",
            f"{t10yie_data['value']:.2f}%"
        )
    
    with col3:
        st.metric(
            "Tasso Reale 10Y",
            f"{real_10y:.2f}%",
            delta=f"{'Positivo' if real_10y > 0 else 'Negativo'}",
            delta_color="normal" if real_10y > 0 else "inverse"
        )
    
    st.markdown("""
    > **Interpretazione**: Un tasso reale positivo indica che i rendimenti superano l'inflazione attesa. 
    > Tassi reali negativi tendono a essere stimolativi per l'economia e i mercati azionari.
    """)

st.markdown("---")


# =============================================================================
# DATA TABLE
# =============================================================================

st.markdown("### 📋 Tabella Riepilogativa")

table_data = []

for code, config in tassi_indicators.items():
    data = get_latest_value(code)
    
    if data["value"] is not None:
        table_data.append({
            "Indicatore": config["name"],
            "Valore": f"{data['value']:.2f}%",
            "Variazione": f"{data['change']:+.2f}%" if data['change'] else "N/A",
            "Data": data["date"],
            "Frequenza": config.get("frequency", "N/A"),
            "Codice FRED": code
        })

if table_data:
    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True
    )
    
    # Export
    df_export = pd.DataFrame(table_data)
    csv = df_export.to_csv(index=False)
    
    st.download_button(
        label="📥 Scarica CSV",
        data=csv,
        file_name=f"tassi_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")


# =============================================================================
# INTERPRETATION GUIDE
# =============================================================================

with st.expander("📖 Guida all'Interpretazione"):
    st.markdown("""
    ### Federal Funds Rate
    
    Il tasso a cui le banche si prestano denaro overnight. È lo strumento principale della Fed.
    
    | Livello | Interpretazione |
    |---------|-----------------|
    | 0-2% | Politica accomodante, stimolo economia |
    | 2-4% | Politica neutrale |
    | >4% | Politica restrittiva, contrasto inflazione |
    
    ### Treasury Yields
    
    Rendimenti dei titoli di stato USA per diverse scadenze.
    
    - **Short-term (1Y-2Y)**: Più sensibili alle decisioni Fed
    - **Medium-term (5Y)**: Bilanciano aspettative breve/lungo
    - **Long-term (10Y-30Y)**: Riflettono aspettative crescita/inflazione lungo periodo
    
    ### Yield Curve
    
    **Curva Normale (inclinata positivamente):**
    - Tassi lungo termine > tassi breve termine
    - Economia in espansione attesa
    
    **Curva Piatta:**
    - Spread ridotti tra scadenze
    - Incertezza sulle prospettive
    
    **Curva Invertita:**
    - Tassi breve termine > lungo termine
    - Storicamente precede recessioni (lead time 12-18 mesi)
    - Affidabilità storica: ~80% negli ultimi 50 anni
    
    ### Spread 10Y-2Y vs 10Y-3M
    
    - **10Y-2Y**: Più usato dai mercati
    - **10Y-3M**: Preferito dalla Fed (più "puro", 3M = quasi risk-free)
    - Entrambi sono indicatori di recessione, ma il 10Y-3M ha storicamente maggiore precisione
    
    ### Tassi Reali
    
    Tasso Reale = Tasso Nominale - Inflazione Attesa
    
    - **Positivo**: Rendimento sopra inflazione → risparmio premiato
    - **Negativo**: Rendimento sotto inflazione → incentivo a spendere/investire
    """)


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("💡 La yield curve invertita ha predetto 7 delle ultime 8 recessioni USA. Fonte: FRED St. Louis Fed")
