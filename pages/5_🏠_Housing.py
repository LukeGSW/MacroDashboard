"""
FRED Macro Dashboard - Housing Page
=====================================
Analisi del mercato immobiliare USA.
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
    page_title="Housing | FRED Macro Dashboard",
    page_icon="🏠",
    layout="wide"
)


# =============================================================================
# HEADER
# =============================================================================

st.title("🏠 Mercato Immobiliare")
st.markdown("*Monitoraggio housing starts, prezzi e mutui USA*")
st.markdown(f"*Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

st.markdown("---")


# =============================================================================
# KPI ROW
# =============================================================================

st.markdown("### 🎯 Indicatori Chiave")

housing_indicators = INDICATORS["housing"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    data = get_latest_value("HOUST")
    if data["value"] is not None:
        st.metric(
            label="Housing Starts",
            value=f"{data['value']/1000:.2f}M",
            delta=f"{data['change']/1000:+.2f}M" if data['change'] else None,
            delta_color="normal"
        )
        st.caption(f"📅 {data['date']} (SAAR)")

with col2:
    data = get_latest_value("PERMIT")
    if data["value"] is not None:
        st.metric(
            label="Building Permits",
            value=f"{data['value']/1000:.2f}M",
            delta=f"{data['change']/1000:+.2f}M" if data['change'] else None,
            delta_color="normal"
        )
        st.caption(f"📅 {data['date']} (SAAR)")

with col3:
    data = get_latest_value("CSUSHPINSA")
    if data["value"] is not None:
        st.metric(
            label="Case-Shiller YoY",
            value=f"{data['value']:.1f}%",
            delta=f"{data['change']:+.1f}%" if data['change'] else None,
            delta_color="off"
        )
        st.caption(f"📅 {data['date']}")

with col4:
    data = get_latest_value("MORTGAGE30US")
    if data["value"] is not None:
        st.metric(
            label="Mortgage 30Y",
            value=f"{data['value']:.2f}%",
            delta=f"{data['change']:+.2f}%" if data['change'] else None,
            delta_color="inverse"  # Tassi più bassi = positivo
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
        value=15,
        step=1
    )
    
    show_recessions = st.checkbox("Mostra recessioni", value=True)
    
    st.markdown("---")
    
    st.markdown("### 📖 Legenda")
    st.markdown("""
    - **HOUST**: Housing Starts (nuove costruzioni)
    - **PERMIT**: Building Permits (permessi)
    - **Case-Shiller**: Indice prezzi case
    - **MORTGAGE30US**: Tasso mutuo 30 anni
    - **MSPUS**: Prezzo mediano vendite
    - **RRVRUSQ156N**: Vacancy rate affitti
    """)
    
    st.markdown("---")
    
    st.markdown("### 🎯 Benchmark")
    st.markdown("""
    - **Housing Starts sani**: 1.4-1.6M
    - **Mortgage "normale"**: 4-6%
    - **Case-Shiller YoY sano**: 3-5%
    """)


# =============================================================================
# HOUSING ACTIVITY GAUGES
# =============================================================================

st.markdown("### 📊 Dashboard Attività Edilizia")

col1, col2, col3 = st.columns(3)

with col1:
    houst_data = get_latest_value("HOUST")
    if houst_data["value"]:
        fig = create_gauge(
            value=houst_data["value"],
            title="Housing Starts (K)",
            gauge_range=[500, 2000],
            thresholds={
                "red": [500, 1000],
                "yellow": [1000, 1400],
                "green": [1400, 2000]
            },
            target=1500,
            units="K",
            delta_reference=houst_data.get("previous"),
            invert=True
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    permit_data = get_latest_value("PERMIT")
    if permit_data["value"]:
        fig = create_gauge(
            value=permit_data["value"],
            title="Building Permits (K)",
            gauge_range=[500, 2000],
            thresholds={
                "red": [500, 1000],
                "yellow": [1000, 1400],
                "green": [1400, 2000]
            },
            target=1500,
            units="K",
            delta_reference=permit_data.get("previous"),
            invert=True
        )
        st.plotly_chart(fig, use_container_width=True)

with col3:
    mortgage_data = get_latest_value("MORTGAGE30US")
    if mortgage_data["value"]:
        fig = create_gauge(
            value=mortgage_data["value"],
            title="Mortgage Rate 30Y",
            gauge_range=[2, 10],
            thresholds={
                "green": [2, 5],
                "yellow": [5, 7],
                "red": [7, 10]
            },
            target=5.0,
            units="%",
            delta_reference=mortgage_data.get("previous"),
            invert=False  # Tassi bassi = bene
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# =============================================================================
# HOUSING STARTS & PERMITS
# =============================================================================

st.markdown("### 🏗️ Attività Edilizia")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Housing Starts vs Permits")
    
    houst_df = get_indicator_data("HOUST", years=years_range)
    permit_df = get_indicator_data("PERMIT", years=years_range)
    
    if not houst_df.empty and not permit_df.empty:
        fig = create_multi_line_chart(
            data_dict={
                "Housing Starts": houst_df,
                "Building Permits": permit_df
            },
            title="Nuove Costruzioni vs Permessi (SAAR)",
            y_label="Migliaia di unità",
            colors={
                "Housing Starts": "#1f77b4",
                "Building Permits": "#ff7f0e"
            },
            show_recessions=show_recessions,
            height=400,
            show_zero_line=False
        )
        
        # Linea benchmark
        fig.add_hline(
            y=1500,
            line_dash="dash",
            line_color="rgba(0, 204, 102, 0.7)",
            annotation_text="Livello sano ~1.5M",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Analisi Trend")
    
    if not houst_df.empty and not permit_df.empty:
        # Calcola medie mobili
        houst_current = houst_df['value'].iloc[-1]
        houst_avg_6m = houst_df['value'].tail(6).mean()
        houst_avg_12m = houst_df['value'].tail(12).mean()
        
        permit_current = permit_df['value'].iloc[-1]
        permit_avg_6m = permit_df['value'].tail(6).mean()
        
        # Metrics
        st.metric("Housing Starts (Ultimo)", f"{houst_current/1000:.2f}M")
        st.metric("Housing Starts (Media 6M)", f"{houst_avg_6m/1000:.2f}M")
        st.metric("Building Permits (Ultimo)", f"{permit_current/1000:.2f}M")
        
        st.markdown("---")
        
        # Permits lead indicator
        permits_vs_starts = permit_current - houst_current
        
        if permits_vs_starts > 50:
            st.success(f"📈 **Permits > Starts** (+{permits_vs_starts:.0f}K)")
            st.markdown("Segnale positivo: pipeline in crescita")
        elif permits_vs_starts < -50:
            st.warning(f"📉 **Permits < Starts** ({permits_vs_starts:.0f}K)")
            st.markdown("Segnale cautela: pipeline in calo")
        else:
            st.info(f"⚖️ **Permits ≈ Starts** ({permits_vs_starts:+.0f}K)")
            st.markdown("Mercato in equilibrio")

st.markdown("---")


# =============================================================================
# HOME PRICES
# =============================================================================

st.markdown("### 💰 Prezzi Immobiliari")

col1, col2 = st.columns([2, 1])

with col1:
    cs_df = get_indicator_data("CSUSHPINSA", years=years_range)
    
    if not cs_df.empty:
        fig = create_line_chart(
            df=cs_df,
            title="S&P/Case-Shiller U.S. National Home Price Index (YoY %)",
            y_label="% YoY",
            color="#2ca02c",
            show_recessions=show_recessions,
            height=400,
            show_zero_line=True
        )
        
        # Zona bolla
        fig.add_hrect(
            y0=10, y1=25,
            fillcolor="rgba(255, 204, 0, 0.1)",
            line_width=0,
            annotation_text="Zona surriscaldamento",
            annotation_position="top right"
        )
        
        # Zona deflazione
        fig.add_hrect(
            y0=-20, y1=0,
            fillcolor="rgba(255, 68, 68, 0.1)",
            line_width=0,
            annotation_text="Deflazione prezzi",
            annotation_position="bottom right"
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 📊 Statistiche Prezzi")
    
    cs_data = get_latest_value("CSUSHPINSA")
    mspus_data = get_latest_value("MSPUS")
    
    if cs_data["value"]:
        st.metric(
            "Case-Shiller YoY",
            f"{cs_data['value']:.1f}%",
            delta=f"{cs_data['change']:+.1f}%" if cs_data['change'] else None
        )
    
    if mspus_data["value"]:
        st.metric(
            "Prezzo Mediano Vendite",
            f"${mspus_data['value']/1000:.0f}K",
            delta=f"${mspus_data['change']/1000:+.0f}K" if mspus_data['change'] else None
        )
    
    st.markdown("---")
    
    # Assessment
    if cs_data["value"]:
        yoy = cs_data["value"]
        if yoy > 10:
            st.warning("🔥 **Mercato surriscaldato**")
            st.markdown("Crescita prezzi insostenibile")
        elif yoy > 5:
            st.success("📈 **Mercato forte**")
            st.markdown("Crescita sopra media storica")
        elif yoy > 0:
            st.info("➡️ **Mercato stabile**")
            st.markdown("Crescita moderata")
        else:
            st.error("📉 **Prezzi in calo**")
            st.markdown("Possibile correzione in corso")

st.markdown("---")


# =============================================================================
# MORTGAGE RATES
# =============================================================================

st.markdown("### 🏦 Tassi Mutui")

col1, col2 = st.columns([2, 1])

with col1:
    mortgage_df = get_indicator_data("MORTGAGE30US", years=years_range)
    
    if not mortgage_df.empty:
        fig = create_line_chart(
            df=mortgage_df,
            title="30-Year Fixed Rate Mortgage Average",
            y_label="%",
            color="#d62728",
            show_recessions=show_recessions,
            height=400,
            show_zero_line=False
        )
        
        # Zone di riferimento
        fig.add_hline(
            y=7,
            line_dash="dash",
            line_color="rgba(255, 68, 68, 0.7)",
            annotation_text="Soglia stress 7%",
            annotation_position="right"
        )
        
        fig.add_hline(
            y=4,
            line_dash="dash",
            line_color="rgba(0, 204, 102, 0.7)",
            annotation_text="Livello favorevole 4%",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 💳 Affordability Impact")
    
    if mortgage_df.empty:
        st.warning("Dati mutui non disponibili")
    else:
        current_rate = mortgage_df['value'].iloc[-1]
        min_rate = mortgage_df['value'].min()
        max_rate = mortgage_df['value'].max()
        avg_rate = mortgage_df['value'].mean()
        
        st.metric("Tasso Attuale", f"{current_rate:.2f}%")
        st.metric("Media Periodo", f"{avg_rate:.2f}%")
        st.metric("Range", f"{min_rate:.2f}% - {max_rate:.2f}%")
        
        st.markdown("---")
        
        # Calcolo esempio pagamento
        st.markdown("**Esempio Pagamento Mensile**")
        st.markdown("*(Mutuo $400K, 30 anni)*")
        
        # Formula pagamento mensile
        principal = 400000
        monthly_rate = current_rate / 100 / 12
        n_payments = 360
        
        if monthly_rate > 0:
            payment = principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
            st.metric("Rata Mensile", f"${payment:,.0f}")
            
            # Confronto con tasso 4%
            rate_4 = 0.04 / 12
            payment_4 = principal * (rate_4 * (1 + rate_4)**n_payments) / ((1 + rate_4)**n_payments - 1)
            diff = payment - payment_4
            
            st.caption(f"vs tasso 4%: +${diff:,.0f}/mese")

st.markdown("---")


# =============================================================================
# RENTAL MARKET
# =============================================================================

st.markdown("### 🔑 Mercato Affitti")

col1, col2 = st.columns(2)

with col1:
    vacancy_df = get_indicator_data("RRVRUSQ156N", years=years_range)
    
    if not vacancy_df.empty:
        fig = create_line_chart(
            df=vacancy_df,
            title="Rental Vacancy Rate",
            y_label="%",
            color="#8c564b",
            show_recessions=show_recessions,
            height=350,
            show_zero_line=False
        )
        
        # Media storica
        avg_vacancy = vacancy_df['value'].mean()
        fig.add_hline(
            y=avg_vacancy,
            line_dash="dash",
            line_color="rgba(255, 255, 255, 0.5)",
            annotation_text=f"Media: {avg_vacancy:.1f}%",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 📊 Analisi Vacancy")
    
    vacancy_data = get_latest_value("RRVRUSQ156N")
    
    if vacancy_data["value"]:
        st.metric(
            "Vacancy Rate Attuale",
            f"{vacancy_data['value']:.1f}%",
            delta=f"{vacancy_data['change']:+.1f}%" if vacancy_data['change'] else None
        )
        
        st.markdown("---")
        
        # Interpretazione
        vacancy = vacancy_data["value"]
        
        if vacancy < 5:
            st.error("🔴 **Mercato molto tight**")
            st.markdown("Bassa disponibilità → pressione rialzista affitti")
        elif vacancy < 7:
            st.warning("🟡 **Mercato equilibrato**")
            st.markdown("Domanda e offerta bilanciate")
        else:
            st.success("🟢 **Mercato rilassato**")
            st.markdown("Buona disponibilità → affitti stabili/in calo")
        
        st.markdown("---")
        
        st.markdown("""
        **Nota:** Il vacancy rate è un indicatore chiave per:
        - Pressioni inflazionistiche (shelter CPI)
        - Rendimenti investimenti immobiliari
        - Dinamiche domanda/offerta housing
        """)

st.markdown("---")


# =============================================================================
# DATA TABLE
# =============================================================================

st.markdown("### 📋 Tabella Riepilogativa")

table_data = []

for code, config in housing_indicators.items():
    data = get_latest_value(code)
    
    if data["value"] is not None:
        # Format based on indicator
        if code in ["HOUST", "PERMIT"]:
            value_str = f"{data['value']/1000:.2f}M"
            change_str = f"{data['change']/1000:+.2f}M" if data['change'] else "N/A"
        elif code == "MSPUS":
            value_str = f"${data['value']/1000:.0f}K"
            change_str = f"${data['change']/1000:+.0f}K" if data['change'] else "N/A"
        elif code in ["CSUSHPINSA"]:
            value_str = f"{data['value']:.1f}%"
            change_str = f"{data['change']:+.1f}%" if data['change'] else "N/A"
        else:
            value_str = f"{data['value']:.2f}%"
            change_str = f"{data['change']:+.2f}%" if data['change'] else "N/A"
        
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
        file_name=f"housing_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")


# =============================================================================
# INTERPRETATION GUIDE
# =============================================================================

with st.expander("📖 Guida all'Interpretazione"):
    st.markdown("""
    ### Housing Starts vs Building Permits
    
    | Indicatore | Significato | Lead/Lag |
    |------------|-------------|----------|
    | **Building Permits** | Autorizzazioni rilasciate | Leading (1-2 mesi) |
    | **Housing Starts** | Costruzioni effettivamente iniziate | Coincident |
    
    **Interpretazione:**
    - Permits > Starts: Pipeline in crescita, outlook positivo
    - Permits < Starts: Pipeline in calo, possibile rallentamento
    
    ### Case-Shiller Index
    
    Indice più affidabile per i prezzi immobiliari USA:
    - Metodologia repeat-sales (stesse case nel tempo)
    - Lag di ~2 mesi rispetto al mercato
    - National vs City indices disponibili
    
    **Range storici YoY:**
    - > 10%: Mercato surriscaldato / possibile bolla
    - 3-5%: Crescita sana e sostenibile
    - 0-3%: Mercato debole
    - < 0%: Correzione / crisi
    
    ### Mortgage Rates
    
    Il tasso mutuo 30Y è cruciale per l'affordability:
    
    | Tasso | Impatto |
    |-------|---------|
    | < 4% | Molto favorevole, stimola domanda |
    | 4-6% | Range "normale" storico |
    | 6-7% | Stress affordability moderato |
    | > 7% | Forte stress, domanda in calo |
    
    ### Relazione Housing-Economia
    
    Il settore housing è un leading indicator dell'economia:
    1. **Fed alza tassi** → Mutui più cari
    2. **Affordability cala** → Domanda scende
    3. **Costruzioni rallentano** → Occupazione settore cala
    4. **Effetto ricchezza negativo** → Consumi calano
    5. **Economia rallenta**
    
    Il ciclo housing tipicamente anticipa le recessioni di 12-18 mesi.
    
    ### Vacancy Rate e Inflazione
    
    Il rental vacancy rate influenza direttamente la componente "shelter" del CPI:
    - Vacancy basso → Affitti in aumento → CPI shelter sale
    - Shelter rappresenta ~33% del CPI
    - Lag di 12-18 mesi tra mercato affitti e CPI
    """)


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("💡 Il settore immobiliare rappresenta ~15-18% del PIL USA ed è un leading indicator del ciclo economico. Fonte: FRED St. Louis Fed")
