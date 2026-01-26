"""
FRED Macro Dashboard - Snapshot Page
=====================================
Overview rapida con gauge dei principali indicatori macro.
"""

import streamlit as st
from datetime import datetime

from config import INDICATORS
from utils.fred_api import get_latest_value, get_indicator_data
from utils.charts import create_gauge, create_line_chart


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Snapshot | FRED Macro Dashboard",
    page_icon="📊",
    layout="wide"
)


# =============================================================================
# HEADER
# =============================================================================

st.title("📊 Macro Snapshot")
st.markdown("*Vista rapida dei principali indicatori macroeconomici USA*")
st.markdown(f"*Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

st.markdown("---")


# =============================================================================
# GAUGE SECTION
# =============================================================================

st.markdown("### 🎯 Indicatori Chiave")

# Recupera configurazione indicatori snapshot
snapshot_indicators = INDICATORS["snapshot"]

# Prima riga: 4 gauge
row1_codes = ["CPIAUCSL", "PCEPILFE", "FEDFUNDS", "UNRATE"]
cols1 = st.columns(4)

for col, code in zip(cols1, row1_codes):
    with col:
        config = snapshot_indicators.get(code, {})
        data = get_latest_value(code)
        
        if data["value"] is not None:
            fig = create_gauge(
                value=data["value"],
                title=config.get("name", code),
                gauge_range=config.get("gauge_range", [0, 100]),
                thresholds=config.get("thresholds"),
                target=config.get("target"),
                units=config.get("units", ""),
                delta_reference=data.get("previous"),
                invert=config.get("invert", False)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Info sotto il gauge
            st.caption(f"📅 {data['date']} | Δ {data['change']:+.2f}")
        else:
            st.warning(f"Dati non disponibili per {code}")

# Seconda riga: 4 gauge
row2_codes = ["T10Y2Y", "UMCSENT", "BAMLH0A0HYM2", "INDPRO"]
cols2 = st.columns(4)

for col, code in zip(cols2, row2_codes):
    with col:
        config = snapshot_indicators.get(code, {})
        data = get_latest_value(code)
        
        if data["value"] is not None:
            fig = create_gauge(
                value=data["value"],
                title=config.get("name", code),
                gauge_range=config.get("gauge_range", [0, 100]),
                thresholds=config.get("thresholds"),
                target=config.get("target"),
                units=config.get("units", ""),
                delta_reference=data.get("previous"),
                invert=config.get("invert", False)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Info sotto il gauge
            st.caption(f"📅 {data['date']} | Δ {data['change']:+.2f}")
        else:
            st.warning(f"Dati non disponibili per {code}")

st.markdown("---")


# =============================================================================
# QUICK CHARTS
# =============================================================================

st.markdown("### 📈 Trend Recenti (1 Anno)")

# Selettore indicatore per chart dettagliato
chart_options = {code: config["name"] for code, config in snapshot_indicators.items()}
selected_code = st.selectbox(
    "Seleziona indicatore per dettaglio:",
    options=list(chart_options.keys()),
    format_func=lambda x: chart_options[x]
)

if selected_code:
    config = snapshot_indicators[selected_code]
    df = get_indicator_data(selected_code, years=1)
    
    if not df.empty:
        fig = create_line_chart(
            df=df,
            title=f"{config['name']} - Ultimo Anno",
            y_label=config.get("units", ""),
            color="#1f77b4",
            show_recessions=True,
            height=400,
            show_zero_line=(config.get("transform") == "yoy" or "Spread" in config["name"])
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats box
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Ultimo", f"{df['value'].iloc[-1]:.2f}")
        with col2:
            st.metric("Max 1Y", f"{df['value'].max():.2f}")
        with col3:
            st.metric("Min 1Y", f"{df['value'].min():.2f}")
        with col4:
            st.metric("Media 1Y", f"{df['value'].mean():.2f}")
    else:
        st.warning("Dati non disponibili per il grafico")

st.markdown("---")


# =============================================================================
# DATA TABLE
# =============================================================================

st.markdown("### 📋 Tabella Riepilogativa")

# Costruisci tabella dati
table_data = []

for code, config in snapshot_indicators.items():
    data = get_latest_value(code)
    
    if data["value"] is not None:
        # Determina status
        thresholds = config.get("thresholds", {})
        value = data["value"]
        invert = config.get("invert", False)
        
        status = "🟡"  # Default yellow
        
        if "green" in thresholds:
            if thresholds["green"][0] <= value <= thresholds["green"][1]:
                status = "🟢"
        if "red" in thresholds:
            if thresholds["red"][0] <= value <= thresholds["red"][1]:
                status = "🔴"
        
        table_data.append({
            "Status": status,
            "Indicatore": config["name"],
            "Valore": f"{data['value']:.2f}",
            "Unità": config.get("units", ""),
            "Variazione": f"{data['change']:+.2f}" if data['change'] else "N/A",
            "Data": data["date"],
            "Codice FRED": code
        })

if table_data:
    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("", width="small"),
            "Indicatore": st.column_config.TextColumn("Indicatore", width="medium"),
            "Valore": st.column_config.TextColumn("Valore", width="small"),
            "Unità": st.column_config.TextColumn("Unità", width="small"),
            "Variazione": st.column_config.TextColumn("Δ", width="small"),
            "Data": st.column_config.TextColumn("Data", width="medium"),
            "Codice FRED": st.column_config.TextColumn("FRED", width="medium")
        }
    )

st.markdown("---")


# =============================================================================
# INTERPRETATION GUIDE
# =============================================================================

with st.expander("📖 Guida all'Interpretazione"):
    st.markdown("""
    ### Come Leggere i Gauge
    
    Ogni gauge mostra un indicatore chiave con zone colorate:
    
    - 🟢 **Verde**: Valore in range ottimale/salutare
    - 🟡 **Giallo**: Valore da monitorare con attenzione
    - 🔴 **Rosso**: Valore critico/preoccupante
    
    ### Indicatori Spiegati
    
    | Indicatore | Cosa Misura | Target Fed |
    |------------|-------------|------------|
    | **CPI YoY** | Inflazione prezzi al consumo | ~2% |
    | **Core PCE** | Inflazione preferita dalla Fed (ex food/energy) | 2% |
    | **Fed Funds** | Tasso di interesse overnight | Varia |
    | **Disoccupazione** | % forza lavoro disoccupata | ~4% |
    | **Yield Curve 10Y-2Y** | Spread tra Treasury 10Y e 2Y | >0 (positivo) |
    | **Consumer Sentiment** | Fiducia consumatori Michigan | >80 |
    | **HY Spread** | Premio rischio obbligazioni high yield | <4% |
    | **Industrial Production** | Crescita produzione industriale | >2% YoY |
    
    ### Segnali di Warning
    
    - **Yield Curve negativa** (10Y-2Y < 0): Storicamente precede recessioni di 12-18 mesi
    - **HY Spread > 6%**: Indica stress nei mercati del credito
    - **Core PCE > 3%**: Fed probabilmente restrittiva
    - **Unemployment < 4%**: Mercato lavoro molto tight, pressioni salariali
    """)


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("💡 I dati sono aggiornati con cache di 4 ore. Fonte: FRED St. Louis Fed")
