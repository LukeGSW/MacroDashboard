"""
FRED Macro Dashboard - Inflazione Page
=======================================
Analisi dettagliata degli indicatori di inflazione USA.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from config import INDICATORS
from utils.fred_api import get_latest_value, get_indicator_data, fetch_fred_series
from utils.charts import create_gauge, create_line_chart, create_multi_line_chart


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Inflazione | FRED Macro Dashboard",
    page_icon="📈",
    layout="wide"
)


# =============================================================================
# HEADER
# =============================================================================

st.title("📈 Inflazione")
st.markdown("*Monitoraggio completo delle dinamiche inflazionistiche USA*")
st.markdown(f"*Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

st.markdown("---")


# =============================================================================
# KPI ROW
# =============================================================================

st.markdown("### 🎯 Indicatori Chiave")

inflation_indicators = INDICATORS["inflazione"]

col1, col2, col3, col4 = st.columns(4)

kpi_codes = ["CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE"]

for col, code in zip([col1, col2, col3, col4], kpi_codes):
    with col:
        config = inflation_indicators.get(code, {})
        data = get_latest_value(code)
        
        if data["value"] is not None:
            # Determina colore delta (per inflazione, aumento = negativo)
            delta_color = "inverse"
            
            st.metric(
                label=config.get("name", code),
                value=f"{data['value']:.2f}%",
                delta=f"{data['change']:+.2f}%" if data['change'] else None,
                delta_color=delta_color
            )
            st.caption(f"📅 {data['date']}")
        else:
            st.metric(label=config.get("name", code), value="N/A")

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
    - **CPI**: Consumer Price Index
    - **Core**: Esclude food & energy
    - **PCE**: Personal Consumption Expenditures
    - **PPI**: Producer Price Index
    - **Breakeven**: Aspettative inflazione mercato
    """)


# =============================================================================
# CPI vs PCE COMPARISON
# =============================================================================

st.markdown("### 📊 CPI vs PCE - Confronto")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Consumer Price Index (CPI)")
    
    # Fetch data
    cpi_data = get_indicator_data("CPIAUCSL", years=years_range)
    core_cpi_data = get_indicator_data("CPILFESL", years=years_range)
    
    if not cpi_data.empty and not core_cpi_data.empty:
        fig = create_multi_line_chart(
            data_dict={
                "CPI All Items": cpi_data,
                "Core CPI": core_cpi_data
            },
            title="CPI vs Core CPI (YoY %)",
            y_label="% YoY",
            colors={
                "CPI All Items": inflation_indicators["CPIAUCSL"]["color"],
                "Core CPI": inflation_indicators["CPILFESL"]["color"]
            },
            show_recessions=show_recessions,
            height=400,
            show_zero_line=True
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Personal Consumption Expenditures (PCE)")
    
    # Fetch data
    pce_data = get_indicator_data("PCEPI", years=years_range)
    core_pce_data = get_indicator_data("PCEPILFE", years=years_range)
    
    if not pce_data.empty and not core_pce_data.empty:
        fig = create_multi_line_chart(
            data_dict={
                "PCE": pce_data,
                "Core PCE": core_pce_data
            },
            title="PCE vs Core PCE (YoY %)",
            y_label="% YoY",
            colors={
                "PCE": inflation_indicators["PCEPI"]["color"],
                "Core PCE": inflation_indicators["PCEPILFE"]["color"]
            },
            show_recessions=show_recessions,
            height=400,
            show_zero_line=True
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# =============================================================================
# ALL INFLATION METRICS
# =============================================================================

st.markdown("### 📈 Tutti gli Indicatori di Inflazione")

# Fetch all inflation data
all_inflation_data = {}
colors_dict = {}

for code, config in inflation_indicators.items():
    df = get_indicator_data(code, years=years_range)
    if not df.empty:
        all_inflation_data[config["name"]] = df
        colors_dict[config["name"]] = config.get("color", "#1f77b4")

if all_inflation_data:
    fig = create_multi_line_chart(
        data_dict=all_inflation_data,
        title="Panoramica Completa Inflazione",
        y_label="%",
        colors=colors_dict,
        show_recessions=show_recessions,
        height=500,
        show_zero_line=True
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# =============================================================================
# BREAKEVEN INFLATION
# =============================================================================

st.markdown("### 💹 Breakeven Inflation (Aspettative di Mercato)")

col1, col2 = st.columns([2, 1])

with col1:
    # Fetch breakeven data
    t5y_data = get_indicator_data("T5YIE", years=years_range)
    t10y_data = get_indicator_data("T10YIE", years=years_range)
    
    if not t5y_data.empty and not t10y_data.empty:
        fig = create_multi_line_chart(
            data_dict={
                "5Y Breakeven": t5y_data,
                "10Y Breakeven": t10y_data
            },
            title="Breakeven Inflation Rates",
            y_label="%",
            colors={
                "5Y Breakeven": inflation_indicators["T5YIE"]["color"],
                "10Y Breakeven": inflation_indicators["T10YIE"]["color"]
            },
            show_recessions=show_recessions,
            height=400,
            show_zero_line=False
        )
        
        # Aggiungi linea target Fed al 2%
        fig.add_hline(
            y=2.0,
            line_dash="dash",
            line_color="rgba(255,255,255,0.7)",
            annotation_text="Target Fed 2%",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 📊 Valori Attuali")
    
    t5y_latest = get_latest_value("T5YIE")
    t10y_latest = get_latest_value("T10YIE")
    
    if t5y_latest["value"]:
        st.metric(
            "5Y Breakeven",
            f"{t5y_latest['value']:.2f}%",
            delta=f"{t5y_latest['change']:+.2f}%" if t5y_latest['change'] else None
        )
    
    if t10y_latest["value"]:
        st.metric(
            "10Y Breakeven",
            f"{t10y_latest['value']:.2f}%",
            delta=f"{t10y_latest['change']:+.2f}%" if t10y_latest['change'] else None
        )
    
    st.markdown("---")
    
    st.markdown("""
    **Interpretazione:**
    
    Il breakeven inflation è la differenza tra Treasury nominali e TIPS. 
    Rappresenta le aspettative di inflazione del mercato.
    
    - **> 2.5%**: Mercato vede inflazione persistente
    - **2.0-2.5%**: In linea con target Fed
    - **< 2.0%**: Rischio deflazione/rallentamento
    """)

st.markdown("---")


# =============================================================================
# PPI - PRODUCER PRICES
# =============================================================================

st.markdown("### 🏭 Producer Price Index (PPI)")

col1, col2 = st.columns([2, 1])

with col1:
    ppi_data = get_indicator_data("PPIFIS", years=years_range)
    
    if not ppi_data.empty:
        fig = create_line_chart(
            df=ppi_data,
            title="PPI Final Demand (YoY %)",
            y_label="% YoY",
            color=inflation_indicators["PPIFIS"]["color"],
            show_recessions=show_recessions,
            height=350,
            show_zero_line=True
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    ppi_latest = get_latest_value("PPIFIS")
    
    if ppi_latest["value"]:
        # Gauge per PPI
        fig = create_gauge(
            value=ppi_latest["value"],
            title="PPI YoY",
            gauge_range=[-5, 15],
            thresholds={
                "green": [-5, 3],
                "yellow": [3, 6],
                "red": [6, 15]
            },
            units="%",
            delta_reference=ppi_latest.get("previous"),
            invert=False
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"📅 Ultimo dato: {ppi_latest['date']}")

st.markdown("---")


# =============================================================================
# DATA TABLE
# =============================================================================

st.markdown("### 📋 Tabella Dati")

table_data = []

for code, config in inflation_indicators.items():
    data = get_latest_value(code)
    
    if data["value"] is not None:
        # Status basato su distanza dal target 2%
        value = data["value"]
        if abs(value - 2.0) <= 0.5:
            status = "🟢"
        elif abs(value - 2.0) <= 1.5:
            status = "🟡"
        else:
            status = "🔴"
        
        table_data.append({
            "Status": status,
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

# Export CSV
if table_data:
    df_export = pd.DataFrame(table_data)
    csv = df_export.to_csv(index=False)
    
    st.download_button(
        label="📥 Scarica CSV",
        data=csv,
        file_name=f"inflazione_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")


# =============================================================================
# INTERPRETATION GUIDE
# =============================================================================

with st.expander("📖 Guida all'Interpretazione"):
    st.markdown("""
    ### CPI vs PCE: Quale Usare?
    
    | Aspetto | CPI | PCE |
    |---------|-----|-----|
    | **Calcolato da** | Bureau of Labor Statistics | Bureau of Economic Analysis |
    | **Usato dalla Fed** | No | ✅ Sì (preferito) |
    | **Paniere** | Fisso | Variabile (sostituzioni) |
    | **Peso Housing** | ~33% | ~15% |
    | **Copertura** | Urbani | Tutti i consumatori |
    
    ### Perché il Core?
    
    Gli indicatori "Core" escludono alimentari ed energia perché:
    - Sono molto volatili
    - Non riflettono trend di fondo
    - La Fed guarda al Core PCE per decisioni di policy
    
    ### Segnali da Monitorare
    
    - **CPI > PCE**: Housing sta trainando inflazione
    - **Core stabile, Headline volatile**: Shock temporanei energia/food
    - **Breakeven in calo**: Mercato vede rallentamento
    - **PPI > CPI**: Pressioni in arrivo sui prezzi al consumo
    
    ### Target Fed
    
    La Federal Reserve ha un target di inflazione del **2% annuo** misurato sul **Core PCE**.
    Questo è considerato compatibile con massima occupazione e stabilità prezzi.
    """)


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("💡 La Fed usa il Core PCE come indicatore preferito per le decisioni di politica monetaria. Fonte: FRED St. Louis Fed")
