"""
FRED Macro Dashboard - Sentiment Page
======================================
Analisi sentiment consumatori e condizioni finanziarie USA.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from config import INDICATORS
from utils.fred_api import get_latest_value, get_indicator_data
from utils.charts import create_gauge, create_line_chart, create_multi_line_chart


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Sentiment | FRED Macro Dashboard",
    page_icon="🌡️",
    layout="wide"
)


# =============================================================================
# HEADER
# =============================================================================

st.title("🌡️ Sentiment & Financial Conditions")
st.markdown("*Monitoraggio fiducia consumatori, stress finanziario e risk appetite*")
st.markdown(f"*Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

st.markdown("---")


# =============================================================================
# KPI ROW
# =============================================================================

st.markdown("### 🎯 Indicatori Chiave")

sentiment_indicators = INDICATORS["sentiment"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    data = get_latest_value("UMCSENT")
    if data["value"] is not None:
        st.metric(
            label="Michigan Sentiment",
            value=f"{data['value']:.1f}",
            delta=f"{data['change']:+.1f}" if data['change'] else None,
            delta_color="normal"
        )
        st.caption(f"📅 {data['date']}")

with col2:
    data = get_latest_value("PSAVERT")
    if data["value"] is not None:
        st.metric(
            label="Personal Savings Rate",
            value=f"{data['value']:.1f}%",
            delta=f"{data['change']:+.1f}%" if data['change'] else None,
            delta_color="off"
        )
        st.caption(f"📅 {data['date']}")

with col3:
    data = get_latest_value("BAMLH0A0HYM2")
    if data["value"] is not None:
        st.metric(
            label="HY Credit Spread",
            value=f"{data['value']:.2f}%",
            delta=f"{data['change']:+.2f}%" if data['change'] else None,
            delta_color="inverse"  # Spread in aumento = negativo
        )
        st.caption(f"📅 {data['date']}")

with col4:
    data = get_latest_value("VIXCLS")
    if data["value"] is not None:
        st.metric(
            label="VIX",
            value=f"{data['value']:.1f}",
            delta=f"{data['change']:+.1f}" if data['change'] else None,
            delta_color="inverse"  # VIX in aumento = negativo
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
        max_value=30,
        value=10,
        step=1
    )
    
    show_recessions = st.checkbox("Mostra recessioni", value=True)
    
    st.markdown("---")
    
    st.markdown("### 📖 Legenda")
    st.markdown("""
    - **UMCSENT**: Michigan Consumer Sentiment
    - **PSAVERT**: Personal Savings Rate
    - **HY Spread**: High Yield Bond Spread
    - **STLFSI**: St. Louis Financial Stress
    - **DRTSCILM**: Bank Lending Standards
    - **VIX**: Volatility Index
    """)
    
    st.markdown("---")
    
    st.markdown("### 🎯 Soglie Chiave")
    st.markdown("""
    **Michigan Sentiment:**
    - \\> 90: Ottimismo
    - 70-90: Neutrale
    - < 70: Pessimismo
    
    **HY Spread:**
    - < 4%: Risk-on
    - 4-6%: Neutrale
    - \\> 6%: Stress
    
    **VIX:**
    - < 15: Complacency
    - 15-25: Normale
    - \\> 25: Paura
    """)


# =============================================================================
# SENTIMENT GAUGES
# =============================================================================

st.markdown("### 📊 Dashboard Sentiment")

col1, col2, col3 = st.columns(3)

with col1:
    umcsent_data = get_latest_value("UMCSENT")
    if umcsent_data["value"]:
        fig = create_gauge(
            value=umcsent_data["value"],
            title="Consumer Sentiment",
            gauge_range=[40, 120],
            thresholds={
                "red": [40, 60],
                "yellow": [60, 80],
                "green": [80, 120]
            },
            target=80,
            units="",
            delta_reference=umcsent_data.get("previous"),
            invert=True  # Alto = positivo
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    hy_data = get_latest_value("BAMLH0A0HYM2")
    if hy_data["value"]:
        fig = create_gauge(
            value=hy_data["value"],
            title="HY Credit Spread",
            gauge_range=[0, 12],
            thresholds={
                "green": [0, 4],
                "yellow": [4, 6],
                "red": [6, 12]
            },
            target=3.5,
            units="%",
            delta_reference=hy_data.get("previous"),
            invert=False  # Basso = positivo
        )
        st.plotly_chart(fig, use_container_width=True)

with col3:
    vix_data = get_latest_value("VIXCLS")
    if vix_data["value"]:
        fig = create_gauge(
            value=vix_data["value"],
            title="VIX (Fear Index)",
            gauge_range=[0, 50],
            thresholds={
                "green": [0, 18],
                "yellow": [18, 28],
                "red": [28, 50]
            },
            target=18,
            units="",
            delta_reference=vix_data.get("previous"),
            invert=False  # Basso = positivo
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# =============================================================================
# MARKET REGIME INDICATOR
# =============================================================================

st.markdown("### 🚦 Market Regime Indicator")

# Calcola regime basato su indicatori
vix_val = vix_data["value"] if vix_data and vix_data["value"] else None
hy_val = hy_data["value"] if hy_data and hy_data["value"] else None
sent_val = umcsent_data["value"] if umcsent_data and umcsent_data["value"] else None

col1, col2 = st.columns([1, 2])

with col1:
    # Scoring system
    score = 0
    max_score = 0
    
    if vix_val:
        max_score += 2
        if vix_val < 18:
            score += 2
        elif vix_val < 25:
            score += 1
    
    if hy_val:
        max_score += 2
        if hy_val < 4:
            score += 2
        elif hy_val < 6:
            score += 1
    
    if sent_val:
        max_score += 2
        if sent_val > 80:
            score += 2
        elif sent_val > 65:
            score += 1
    
    if max_score > 0:
        regime_pct = score / max_score * 100
        
        if regime_pct >= 70:
            regime = "🟢 RISK-ON"
            regime_color = "green"
            regime_desc = "Condizioni favorevoli per asset rischiosi"
        elif regime_pct >= 40:
            regime = "🟡 NEUTRALE"
            regime_color = "yellow"
            regime_desc = "Condizioni miste, cautela consigliata"
        else:
            regime = "🔴 RISK-OFF"
            regime_color = "red"
            regime_desc = "Condizioni di stress, preferire asset difensivi"
        
        st.markdown(f"""
        <div style="
            background-color: #262730;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            border-left: 5px solid {'#00cc66' if regime_color == 'green' else '#ffcc00' if regime_color == 'yellow' else '#ff4444'};
        ">
            <h2 style="margin: 0;">{regime}</h2>
            <p style="color: #b0b0b0; margin-top: 10px;">{regime_desc}</p>
            <p style="font-size: 24px; margin-top: 15px;"><strong>Score: {score}/{max_score}</strong></p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("#### 📋 Componenti del Regime")
    
    components = []
    
    if vix_val:
        vix_status = "🟢" if vix_val < 18 else "🟡" if vix_val < 25 else "🔴"
        components.append({
            "Indicatore": "VIX",
            "Valore": f"{vix_val:.1f}",
            "Status": vix_status,
            "Segnale": "Risk-on" if vix_val < 18 else "Neutrale" if vix_val < 25 else "Risk-off"
        })
    
    if hy_val:
        hy_status = "🟢" if hy_val < 4 else "🟡" if hy_val < 6 else "🔴"
        components.append({
            "Indicatore": "HY Spread",
            "Valore": f"{hy_val:.2f}%",
            "Status": hy_status,
            "Segnale": "Risk-on" if hy_val < 4 else "Neutrale" if hy_val < 6 else "Risk-off"
        })
    
    if sent_val:
        sent_status = "🟢" if sent_val > 80 else "🟡" if sent_val > 65 else "🔴"
        components.append({
            "Indicatore": "Consumer Sentiment",
            "Valore": f"{sent_val:.1f}",
            "Status": sent_status,
            "Segnale": "Ottimista" if sent_val > 80 else "Neutrale" if sent_val > 65 else "Pessimista"
        })
    
    if components:
        st.dataframe(components, use_container_width=True, hide_index=True)

st.markdown("---")


# =============================================================================
# CONSUMER SENTIMENT
# =============================================================================

st.markdown("### 😊 Consumer Sentiment")

col1, col2 = st.columns([2, 1])

with col1:
    umcsent_df = get_indicator_data("UMCSENT", years=years_range)
    
    if not umcsent_df.empty:
        fig = create_line_chart(
            df=umcsent_df,
            title="University of Michigan Consumer Sentiment Index",
            y_label="Index",
            color="#1f77b4",
            show_recessions=show_recessions,
            height=400,
            show_zero_line=False
        )
        
        # Zone di riferimento
        fig.add_hrect(
            y0=80, y1=120,
            fillcolor="rgba(0, 204, 102, 0.1)",
            line_width=0
        )
        
        fig.add_hrect(
            y0=40, y1=65,
            fillcolor="rgba(255, 68, 68, 0.1)",
            line_width=0
        )
        
        # Media storica
        avg_sent = umcsent_df['value'].mean()
        fig.add_hline(
            y=avg_sent,
            line_dash="dash",
            line_color="rgba(255, 255, 255, 0.5)",
            annotation_text=f"Media: {avg_sent:.1f}",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 📊 Statistiche")
    
    if not umcsent_df.empty:
        current = umcsent_df['value'].iloc[-1]
        avg = umcsent_df['value'].mean()
        min_val = umcsent_df['value'].min()
        max_val = umcsent_df['value'].max()
        
        st.metric("Attuale", f"{current:.1f}")
        st.metric("Media Periodo", f"{avg:.1f}")
        st.metric("Range", f"{min_val:.1f} - {max_val:.1f}")
        
        st.markdown("---")
        
        # Percentile
        percentile = (umcsent_df['value'] < current).mean() * 100
        st.metric("Percentile", f"{percentile:.0f}°")
        
        st.markdown("---")
        
        # Trend
        mom_change = current - umcsent_df['value'].iloc[-2] if len(umcsent_df) > 1 else 0
        yoy_idx = -12 if len(umcsent_df) > 12 else 0
        yoy_change = current - umcsent_df['value'].iloc[yoy_idx] if len(umcsent_df) > 1 else 0
        
        st.markdown("**Trend:**")
        st.markdown(f"- MoM: {mom_change:+.1f}")
        st.markdown(f"- YoY: {yoy_change:+.1f}")

st.markdown("---")


# =============================================================================
# FINANCIAL STRESS
# =============================================================================

st.markdown("### 📉 Financial Stress & Credit Conditions")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### St. Louis Financial Stress Index")
    
    stlfsi_df = get_indicator_data("STLFSI4", years=years_range)
    
    if not stlfsi_df.empty:
        fig = create_line_chart(
            df=stlfsi_df,
            title="St. Louis Fed Financial Stress Index",
            y_label="Index (0 = Normal)",
            color="#d62728",
            show_recessions=show_recessions,
            height=350,
            show_zero_line=True
        )
        
        # Zona stress
        fig.add_hrect(
            y0=1, y1=5,
            fillcolor="rgba(255, 68, 68, 0.1)",
            line_width=0,
            annotation_text="Elevated Stress",
            annotation_position="top right"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretazione
        stlfsi_data = get_latest_value("STLFSI4")
        if stlfsi_data["value"]:
            val = stlfsi_data["value"]
            if val < 0:
                st.success(f"🟢 **Below Average Stress** ({val:.2f})")
            elif val < 1:
                st.info(f"🟡 **Normal Stress** ({val:.2f})")
            else:
                st.error(f"🔴 **Elevated Stress** ({val:.2f})")

with col2:
    st.markdown("#### High Yield Credit Spread")
    
    hy_df = get_indicator_data("BAMLH0A0HYM2", years=years_range)
    
    if not hy_df.empty:
        fig = create_line_chart(
            df=hy_df,
            title="ICE BofA US High Yield OAS",
            y_label="%",
            color="#ff7f0e",
            show_recessions=show_recessions,
            height=350,
            show_zero_line=False
        )
        
        # Soglie
        fig.add_hline(
            y=6,
            line_dash="dash",
            line_color="rgba(255, 68, 68, 0.7)",
            annotation_text="Stress Threshold 6%",
            annotation_position="right"
        )
        
        fig.add_hline(
            y=4,
            line_dash="dash",
            line_color="rgba(0, 204, 102, 0.7)",
            annotation_text="Healthy < 4%",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        if not hy_df.empty:
            current_hy = hy_df['value'].iloc[-1]
            avg_hy = hy_df['value'].mean()
            st.caption(f"📊 Attuale: {current_hy:.2f}% | Media: {avg_hy:.2f}%")

st.markdown("---")


# =============================================================================
# SAVINGS & LENDING
# =============================================================================

st.markdown("### 💰 Savings & Bank Lending")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Personal Savings Rate")
    
    savings_df = get_indicator_data("PSAVERT", years=years_range)
    
    if not savings_df.empty:
        fig = create_line_chart(
            df=savings_df,
            title="Personal Saving Rate",
            y_label="%",
            color="#2ca02c",
            show_recessions=show_recessions,
            height=350,
            show_zero_line=False
        )
        
        # Media pre-COVID
        fig.add_hline(
            y=7.5,
            line_dash="dash",
            line_color="rgba(255, 255, 255, 0.5)",
            annotation_text="Pre-COVID avg ~7.5%",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretazione
        savings_data = get_latest_value("PSAVERT")
        if savings_data["value"]:
            val = savings_data["value"]
            if val < 5:
                st.warning(f"⚠️ **Savings rate basso** ({val:.1f}%)")
                st.caption("Consumatori potrebbero essere sotto stress")
            elif val > 10:
                st.info(f"📈 **Savings rate elevato** ({val:.1f}%)")
                st.caption("Possibile cautela/incertezza consumatori")
            else:
                st.success(f"✅ **Savings rate normale** ({val:.1f}%)")

with col2:
    st.markdown("#### Bank Lending Standards")
    
    lending_df = get_indicator_data("DRTSCILM", years=years_range)
    
    if not lending_df.empty:
        fig = create_line_chart(
            df=lending_df,
            title="Net % Banks Tightening C&I Loans",
            y_label="Net % Tightening",
            color="#9467bd",
            show_recessions=show_recessions,
            height=350,
            show_zero_line=True
        )
        
        # Zona tightening
        fig.add_hrect(
            y0=20, y1=100,
            fillcolor="rgba(255, 68, 68, 0.1)",
            line_width=0
        )
        
        # Zona easing
        fig.add_hrect(
            y0=-100, y1=-20,
            fillcolor="rgba(0, 204, 102, 0.1)",
            line_width=0
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretazione
        lending_data = get_latest_value("DRTSCILM")
        if lending_data["value"]:
            val = lending_data["value"]
            if val > 20:
                st.error(f"🔴 **Banks tightening** (+{val:.1f}%)")
                st.caption("Credit crunch risk - negativo per economia")
            elif val < -20:
                st.success(f"🟢 **Banks easing** ({val:.1f}%)")
                st.caption("Credito più accessibile")
            else:
                st.info(f"🟡 **Standards stabili** ({val:+.1f}%)")

st.markdown("---")


# =============================================================================
# VIX ANALYSIS
# =============================================================================

st.markdown("### 😱 VIX - Volatility Index")

col1, col2 = st.columns([2, 1])

with col1:
    vix_df = get_indicator_data("VIXCLS", years=years_range)
    
    if not vix_df.empty:
        fig = create_line_chart(
            df=vix_df,
            title="CBOE Volatility Index (VIX)",
            y_label="Index",
            color="#e377c2",
            show_recessions=show_recessions,
            height=400,
            show_zero_line=False
        )
        
        # Zone
        fig.add_hrect(
            y0=0, y1=15,
            fillcolor="rgba(0, 204, 102, 0.1)",
            line_width=0
        )
        
        fig.add_hrect(
            y0=25, y1=80,
            fillcolor="rgba(255, 68, 68, 0.1)",
            line_width=0
        )
        
        fig.add_hline(
            y=20,
            line_dash="dash",
            line_color="rgba(255, 255, 255, 0.5)",
            annotation_text="Long-term avg ~20",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 📊 VIX Analysis")
    
    if not vix_df.empty:
        current_vix = vix_df['value'].iloc[-1]
        avg_vix = vix_df['value'].mean()
        percentile = (vix_df['value'] < current_vix).mean() * 100
        
        st.metric("VIX Attuale", f"{current_vix:.1f}")
        st.metric("Media Periodo", f"{avg_vix:.1f}")
        st.metric("Percentile", f"{percentile:.0f}°")
        
        st.markdown("---")
        
        st.markdown("**Interpretazione:**")
        
        if current_vix < 15:
            st.success("😌 **Complacency**")
            st.markdown("Mercato molto tranquillo. Attenzione a possibili sorprese.")
        elif current_vix < 20:
            st.success("😊 **Low Fear**")
            st.markdown("Volatilità sotto media. Condizioni favorevoli.")
        elif current_vix < 25:
            st.info("😐 **Normal**")
            st.markdown("Volatilità nella norma storica.")
        elif current_vix < 35:
            st.warning("😟 **Elevated Fear**")
            st.markdown("Mercato nervoso. Cautela consigliata.")
        else:
            st.error("😱 **Extreme Fear**")
            st.markdown("Panico. Possibili opportunità contrarian.")

st.markdown("---")


# =============================================================================
# DATA TABLE
# =============================================================================

st.markdown("### 📋 Tabella Riepilogativa")

table_data = []

for code, config in sentiment_indicators.items():
    data = get_latest_value(code)
    
    if data["value"] is not None:
        # Format based on indicator
        if code in ["BAMLH0A0HYM2", "PSAVERT", "DRTSCILM"]:
            value_str = f"{data['value']:.2f}%"
            change_str = f"{data['change']:+.2f}%" if data['change'] else "N/A"
        else:
            value_str = f"{data['value']:.1f}"
            change_str = f"{data['change']:+.1f}" if data['change'] else "N/A"
        
        table_data.append({
            "Indicatore": config["name"],
            "Valore": value_str,
            "Variazione": change_str,
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
        file_name=f"sentiment_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")


# =============================================================================
# INTERPRETATION GUIDE
# =============================================================================

with st.expander("📖 Guida all'Interpretazione"):
    st.markdown("""
    ### Michigan Consumer Sentiment
    
    Sondaggio mensile che misura la fiducia dei consumatori USA.
    
    | Livello | Interpretazione |
    |---------|-----------------|
    | > 100 | Ottimismo forte |
    | 80-100 | Ottimismo moderato |
    | 60-80 | Neutralità/cautela |
    | < 60 | Pessimismo |
    
    **Utilizzo:** Leading indicator per consumi e retail sales.
    
    ### High Yield Credit Spread
    
    Differenza tra rendimento obbligazioni high yield e Treasury.
    
    | Spread | Interpretazione |
    |--------|-----------------|
    | < 3% | Risk appetite elevato, possibile complacency |
    | 3-4.5% | Condizioni normali |
    | 4.5-6% | Stress moderato |
    | > 6% | Stress elevato, risk-off |
    | > 8% | Crisi/panico |
    
    **Utilizzo:** Leading indicator per recessioni e crisi finanziarie.
    
    ### St. Louis Financial Stress Index
    
    Indice composito che misura lo stress nel sistema finanziario USA.
    
    - **0** = condizioni normali (media storica)
    - **< 0** = stress sotto media (condizioni rilassate)
    - **> 0** = stress sopra media
    - **> 1.5** = stress significativo
    
    ### VIX - Fear Index
    
    Misura la volatilità implicita delle opzioni S&P 500 a 30 giorni.
    
    | VIX | Interpretazione |
    |-----|-----------------|
    | < 12 | Complacency estrema |
    | 12-18 | Bassa volatilità |
    | 18-25 | Normale |
    | 25-35 | Paura elevata |
    | > 35 | Panico |
    
    **Nota:** VIX molto basso può essere segnale contrarian (complacency).
    
    ### Personal Savings Rate
    
    % del reddito disponibile risparmiato.
    
    - **Alto (> 10%)**: Consumatori cauti, possibile rallentamento consumi
    - **Normale (5-8%)**: Equilibrio tra consumo e risparmio
    - **Basso (< 5%)**: Consumatori ottimisti ma vulnerabili a shock
    
    ### Bank Lending Standards
    
    Survey trimestrale Fed su quanto le banche stanno stringendo/allentando credito.
    
    - **Positivo**: Net tightening (più banche stringono)
    - **Negativo**: Net easing (più banche allentano)
    - **> 40%**: Credit crunch, forte segnale recessione
    
    **Utilizzo:** Leading indicator 2-4 trimestri per ciclo economico.
    """)


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("💡 Gli indicatori di sentiment sono leading indicators e tendono ad anticipare i turning point economici. Fonte: FRED St. Louis Fed")
