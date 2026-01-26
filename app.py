"""
FRED Macro Dashboard - Main Application
========================================
Dashboard macroeconomica con dati FRED per il mercato USA.

Autore: KriterionQuant
Repository: github.com/[username]/fred-macro-dashboard
"""

import streamlit as st
from datetime import datetime

from config import INDICATORS, TIME_CONFIG
from utils.fred_api import get_latest_value, get_fred_client
from utils.charts import create_gauge, format_value


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="FRED Macro Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #fafafa;
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #262730;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #404040;
    }
    
    div[data-testid="metric-container"] label {
        color: #b0b0b0;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #262730;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    
    /* Status indicator */
    .status-ok { color: #00cc66; }
    .status-warning { color: #ffcc00; }
    .status-danger { color: #ff4444; }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #808080;
        padding: 20px;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.image("https://fred.stlouisfed.org/images/fred-logo-2x.png", width=150)
    st.markdown("---")
    
    st.markdown("### ⚙️ Impostazioni")
    
    # Test connessione API
    try:
        client = get_fred_client()
        st.success("✅ API FRED connessa")
    except Exception as e:
        st.error(f"❌ Errore API: {str(e)}")
    
    st.markdown("---")
    
    # Info
    st.markdown("### ℹ️ Informazioni")
    st.markdown(f"""
    **Ultimo aggiornamento:**  
    {datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    **Cache TTL:** {TIME_CONFIG['cache_ttl_hours']} ore
    
    **Fonte dati:**  
    [FRED St. Louis Fed](https://fred.stlouisfed.org/)
    """)
    
    st.markdown("---")
    
    # Link navigazione
    st.markdown("### 📑 Sezioni")
    st.markdown("""
    - 📊 **Snapshot** - Overview KPI
    - 📈 **Inflazione** - CPI, PCE, PPI
    - 💼 **Lavoro** - Unemployment, Claims
    - 🏦 **Tassi** - Treasury, Yield Curve
    - 🏠 **Housing** - Starts, Prices
    - 🌡️ **Sentiment** - Consumer, Financial
    """)


# =============================================================================
# MAIN CONTENT
# =============================================================================

# Header
st.title("📊 FRED Macro Dashboard")
st.markdown("*Monitoraggio macroeconomico del mercato USA in tempo reale*")

st.markdown("---")

# Quick Stats Row
st.markdown("### 🎯 Quick Stats")

col1, col2, col3, col4 = st.columns(4)

# Fetch quick stats
quick_indicators = [
    ("FEDFUNDS", "Fed Funds", "%", False),
    ("UNRATE", "Disoccupazione", "%", False),
    ("CPIAUCSL", "CPI YoY", "%", False),
    ("T10Y2Y", "Yield Curve 10Y-2Y", "%", True)
]

for col, (code, name, unit, invert) in zip([col1, col2, col3, col4], quick_indicators):
    with col:
        data = get_latest_value(code)
        
        if data["value"] is not None:
            delta_color = "normal" if not invert else "inverse"
            st.metric(
                label=name,
                value=f"{data['value']:.2f}{unit}",
                delta=f"{data['change']:+.2f}" if data['change'] else None,
                delta_color=delta_color
            )
        else:
            st.metric(label=name, value="N/A")

st.markdown("---")

# Dashboard Overview
st.markdown("### 📋 Overview Dashboard")

st.markdown("""
<div class="info-box">
<h4>🎯 Benvenuto nella FRED Macro Dashboard</h4>
<p>Questa dashboard fornisce una visione completa dei principali indicatori macroeconomici USA, 
utilizzando i dati della Federal Reserve Bank of St. Louis (FRED).</p>

<p><strong>Naviga tra le sezioni usando il menu laterale:</strong></p>
<ul>
<li><strong>Snapshot:</strong> Vista rapida con gauge dei KPI principali</li>
<li><strong>Inflazione:</strong> CPI, PCE, PPI e breakeven inflation</li>
<li><strong>Lavoro:</strong> Disoccupazione, claims settimanali, payrolls</li>
<li><strong>Tassi:</strong> Fed Funds, Treasury yields, yield curve</li>
<li><strong>Housing:</strong> Housing starts, permits, prezzi immobiliari</li>
<li><strong>Sentiment:</strong> Consumer confidence, financial stress</li>
</ul>
</div>
""", unsafe_allow_html=True)

# Indicatori disponibili
st.markdown("### 📊 Indicatori Monitorati")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **📈 Inflazione**
    - CPI All Items & Core
    - PCE & Core PCE
    - PPI Final Demand
    - Breakeven Inflation 5Y/10Y
    """)

with col2:
    st.markdown("""
    **💼 Mercato del Lavoro**
    - Unemployment Rate (U3, U6)
    - Initial & Continuing Claims
    - Nonfarm Payrolls
    - Labor Force Participation
    """)

with col3:
    st.markdown("""
    **🏦 Tassi & Obbligazioni**
    - Federal Funds Rate
    - Treasury 1Y, 2Y, 5Y, 10Y, 30Y
    - Yield Curve Spreads
    - High Yield Credit Spread
    """)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    **🏠 Housing**
    - Housing Starts
    - Building Permits
    - Case-Shiller Home Price
    - Mortgage Rate 30Y
    """)

with col5:
    st.markdown("""
    **🌡️ Sentiment & Stress**
    - Michigan Consumer Sentiment
    - Personal Savings Rate
    - Financial Stress Index
    - VIX Volatility Index
    """)

with col6:
    st.markdown("""
    **⚡ Attività Economica**
    - Industrial Production
    - Capacity Utilization
    - Retail Sales
    - Bank Lending Standards
    """)

st.markdown("---")

# Market Status Summary
st.markdown("### 🚦 Market Status")

status_col1, status_col2, status_col3 = st.columns(3)

# Fetch status indicators
inflation_data = get_latest_value("PCEPILFE")
labor_data = get_latest_value("UNRATE")
curve_data = get_latest_value("T10Y2Y")

with status_col1:
    if inflation_data["value"]:
        if inflation_data["value"] <= 2.5:
            status = "🟢 Sotto controllo"
            status_class = "status-ok"
        elif inflation_data["value"] <= 4:
            status = "🟡 Elevata"
            status_class = "status-warning"
        else:
            status = "🔴 Critica"
            status_class = "status-danger"
        
        st.markdown(f"""
        **Inflazione (Core PCE)**  
        <span class="{status_class}">{status}</span>  
        Valore: {inflation_data['value']:.2f}%
        """, unsafe_allow_html=True)

with status_col2:
    if labor_data["value"]:
        if labor_data["value"] <= 4.5:
            status = "🟢 Piena occupazione"
            status_class = "status-ok"
        elif labor_data["value"] <= 6:
            status = "🟡 Moderata"
            status_class = "status-warning"
        else:
            status = "🔴 Elevata"
            status_class = "status-danger"
        
        st.markdown(f"""
        **Disoccupazione**  
        <span class="{status_class}">{status}</span>  
        Valore: {labor_data['value']:.2f}%
        """, unsafe_allow_html=True)

with status_col3:
    if curve_data["value"]:
        if curve_data["value"] > 0.5:
            status = "🟢 Normale"
            status_class = "status-ok"
        elif curve_data["value"] > 0:
            status = "🟡 Piatta"
            status_class = "status-warning"
        else:
            status = "🔴 Invertita"
            status_class = "status-danger"
        
        st.markdown(f"""
        **Yield Curve 10Y-2Y**  
        <span class="{status_class}">{status}</span>  
        Spread: {curve_data['value']:.2f}%
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <p>📊 FRED Macro Dashboard | Dati: Federal Reserve Bank of St. Louis | 
    Sviluppato con ❤️ da KriterionQuant</p>
    <p>I dati vengono aggiornati con un ritardo di 4 ore per limitare le chiamate API.</p>
</div>
""", unsafe_allow_html=True)
