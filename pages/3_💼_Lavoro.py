"""
FRED Macro Dashboard - Lavoro Page
===================================
Analisi del mercato del lavoro USA.
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
    page_title="Lavoro | FRED Macro Dashboard",
    page_icon="💼",
    layout="wide"
)


# =============================================================================
# HEADER
# =============================================================================

st.title("💼 Mercato del Lavoro")
st.markdown("*Monitoraggio occupazione, claims e dinamiche salariali USA*")
st.markdown(f"*Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")

st.markdown("---")


# =============================================================================
# KPI ROW
# =============================================================================

st.markdown("### 🎯 Indicatori Chiave")

labor_indicators = INDICATORS["lavoro"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    data = get_latest_value("UNRATE")
    if data["value"] is not None:
        st.metric(
            label="Unemployment Rate",
            value=f"{data['value']:.1f}%",
            delta=f"{data['change']:+.2f}%" if data['change'] else None,
            delta_color="inverse"  # Aumento disoccupazione = negativo
        )
        st.caption(f"📅 {data['date']}")

with col2:
    data = get_latest_value("ICSA")
    if data["value"] is not None:
        st.metric(
            label="Initial Claims",
            value=f"{data['value']/1000:.0f}K",
            delta=f"{data['change']/1000:+.0f}K" if data['change'] else None,
            delta_color="inverse"
        )
        st.caption(f"📅 {data['date']}")

with col3:
    data = get_latest_value("PAYEMS")
    if data["value"] is not None:
        st.metric(
            label="Nonfarm Payrolls",
            value=f"{data['value']:+.0f}K",
            delta=f"{data['change']:+.0f}K" if data['change'] else None,
            delta_color="normal"  # Aumento payrolls = positivo
        )
        st.caption(f"📅 {data['date']} (MoM)")

with col4:
    data = get_latest_value("CIVPART")
    if data["value"] is not None:
        st.metric(
            label="Participation Rate",
            value=f"{data['value']:.1f}%",
            delta=f"{data['change']:+.2f}%" if data['change'] else None,
            delta_color="normal"
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
    - **UNRATE**: Tasso disoccupazione U3
    - **U6**: Disoccupazione allargata
    - **ICSA**: Initial Jobless Claims
    - **CCSA**: Continuing Claims
    - **PAYEMS**: Nonfarm Payrolls
    - **CIVPART**: Labor Participation
    """)
    
    st.markdown("---")
    
    st.markdown("### 🎯 Benchmark")
    st.markdown("""
    - **Full Employment**: ~4%
    - **NAIRU**: ~4-4.5%
    - **Initial Claims sani**: <250K
    - **Payrolls sani**: >150K/mese
    """)


# =============================================================================
# UNEMPLOYMENT GAUGE
# =============================================================================

st.markdown("### 📊 Unemployment Dashboard")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    unrate_data = get_latest_value("UNRATE")
    if unrate_data["value"]:
        fig = create_gauge(
            value=unrate_data["value"],
            title="Unemployment Rate (U3)",
            gauge_range=[0, 15],
            thresholds={
                "green": [0, 4.5],
                "yellow": [4.5, 6],
                "red": [6, 15]
            },
            target=4.0,
            units="%",
            delta_reference=unrate_data.get("previous"),
            invert=False
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    u6_data = get_latest_value("U6RATE")
    if u6_data["value"]:
        fig = create_gauge(
            value=u6_data["value"],
            title="Unemployment Rate (U6)",
            gauge_range=[0, 25],
            thresholds={
                "green": [0, 8],
                "yellow": [8, 12],
                "red": [12, 25]
            },
            target=7.0,
            units="%",
            delta_reference=u6_data.get("previous"),
            invert=False
        )
        st.plotly_chart(fig, use_container_width=True)

with col3:
    civpart_data = get_latest_value("CIVPART")
    if civpart_data["value"]:
        fig = create_gauge(
            value=civpart_data["value"],
            title="Labor Participation",
            gauge_range=[58, 68],
            thresholds={
                "red": [58, 61],
                "yellow": [61, 63],
                "green": [63, 68]
            },
            target=63.0,
            units="%",
            delta_reference=civpart_data.get("previous"),
            invert=True  # Alto è positivo
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# =============================================================================
# UNEMPLOYMENT CHART
# =============================================================================

st.markdown("### 📈 Disoccupazione Storica")

# Fetch data
unrate_df = get_indicator_data("UNRATE", years=years_range)
u6_df = get_indicator_data("U6RATE", years=years_range)

if not unrate_df.empty:
    fig = create_multi_line_chart(
        data_dict={
            "Unemployment (U3)": unrate_df,
            "Unemployment (U6)": u6_df if not u6_df.empty else pd.DataFrame()
        },
        title="Unemployment Rate: U3 vs U6",
        y_label="%",
        colors={
            "Unemployment (U3)": "#1f77b4",
            "Unemployment (U6)": "#ff7f0e"
        },
        show_recessions=show_recessions,
        height=400,
        show_zero_line=False
    )
    
    # Aggiungi linea NAIRU
    fig.add_hline(
        y=4.0,
        line_dash="dash",
        line_color="rgba(0, 204, 102, 0.7)",
        annotation_text="NAIRU ~4%",
        annotation_position="right"
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# =============================================================================
# JOBLESS CLAIMS
# =============================================================================

st.markdown("### 📉 Jobless Claims")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Initial Claims (Settimanali)")
    
    icsa_df = get_indicator_data("ICSA", years=years_range)
    
    if not icsa_df.empty:
        fig = create_line_chart(
            df=icsa_df,
            title="Initial Jobless Claims",
            y_label="Thousands",
            color="#2ca02c",
            show_recessions=show_recessions,
            height=350,
            show_zero_line=False
        )
        
        # Linea soglia 300K
        fig.add_hline(
            y=300,
            line_dash="dash",
            line_color="rgba(255, 204, 0, 0.7)",
            annotation_text="Soglia attenzione 300K",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Ultimo", f"{icsa_df['value'].iloc[-1]/1000:.0f}K")
        with col_b:
            st.metric("Media 4 sett.", f"{icsa_df['value'].tail(4).mean()/1000:.0f}K")
        with col_c:
            st.metric("Max 1Y", f"{icsa_df['value'].max()/1000:.0f}K")

with col2:
    st.markdown("#### Continuing Claims")
    
    ccsa_df = get_indicator_data("CCSA", years=years_range)
    
    if not ccsa_df.empty:
        fig = create_line_chart(
            df=ccsa_df,
            title="Continuing Claims",
            y_label="Thousands",
            color="#d62728",
            show_recessions=show_recessions,
            height=350,
            show_zero_line=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Stats
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Ultimo", f"{ccsa_df['value'].iloc[-1]/1000:.1f}M")
        with col_b:
            st.metric("Media 4 sett.", f"{ccsa_df['value'].tail(4).mean()/1000:.1f}M")
        with col_c:
            st.metric("Max 1Y", f"{ccsa_df['value'].max()/1000:.1f}M")

st.markdown("---")


# =============================================================================
# NONFARM PAYROLLS
# =============================================================================

st.markdown("### 👷 Nonfarm Payrolls")

col1, col2 = st.columns([2, 1])

with col1:
    payems_df = get_indicator_data("PAYEMS", years=years_range)
    
    if not payems_df.empty:
        fig = create_line_chart(
            df=payems_df,
            title="Nonfarm Payrolls - Variazione Mensile",
            y_label="Migliaia (MoM)",
            color="#9467bd",
            show_recessions=show_recessions,
            height=400,
            show_zero_line=True
        )
        
        # Linea benchmark 150K
        fig.add_hline(
            y=150,
            line_dash="dash",
            line_color="rgba(0, 204, 102, 0.7)",
            annotation_text="Benchmark 150K",
            annotation_position="right"
        )
        
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### 📊 Statistiche")
    
    if not payems_df.empty:
        last_value = payems_df['value'].iloc[-1]
        avg_3m = payems_df['value'].tail(3).mean()
        avg_6m = payems_df['value'].tail(6).mean()
        avg_12m = payems_df['value'].tail(12).mean()
        
        st.metric("Ultimo Mese", f"{last_value:+.0f}K")
        st.metric("Media 3 Mesi", f"{avg_3m:+.0f}K")
        st.metric("Media 6 Mesi", f"{avg_6m:+.0f}K")
        st.metric("Media 12 Mesi", f"{avg_12m:+.0f}K")
        
        st.markdown("---")
        
        # Trend assessment
        if avg_3m > 200:
            st.success("🟢 Mercato lavoro forte")
        elif avg_3m > 100:
            st.warning("🟡 Crescita moderata")
        elif avg_3m > 0:
            st.warning("🟠 Rallentamento in corso")
        else:
            st.error("🔴 Mercato in contrazione")

st.markdown("---")


# =============================================================================
# LABOR PARTICIPATION
# =============================================================================

st.markdown("### 👥 Labor Force Participation")

civpart_df = get_indicator_data("CIVPART", years=years_range)

if not civpart_df.empty:
    fig = create_line_chart(
        df=civpart_df,
        title="Labor Force Participation Rate",
        y_label="%",
        color="#8c564b",
        show_recessions=show_recessions,
        height=350,
        show_zero_line=False
    )
    
    # Linea pre-COVID
    fig.add_hline(
        y=63.3,
        line_dash="dash",
        line_color="rgba(255, 255, 255, 0.5)",
        annotation_text="Pre-COVID (Feb 2020): 63.3%",
        annotation_position="right"
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# =============================================================================
# DATA TABLE
# =============================================================================

st.markdown("### 📋 Tabella Riepilogativa")

table_data = []

for code, config in labor_indicators.items():
    data = get_latest_value(code)
    
    if data["value"] is not None:
        # Format value based on indicator
        if code in ["ICSA", "CCSA"]:
            value_str = f"{data['value']/1000:.0f}K"
            change_str = f"{data['change']/1000:+.0f}K" if data['change'] else "N/A"
        elif code == "PAYEMS":
            value_str = f"{data['value']:+.0f}K"
            change_str = f"{data['change']:+.0f}K" if data['change'] else "N/A"
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
        file_name=f"lavoro_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.markdown("---")


# =============================================================================
# INTERPRETATION GUIDE
# =============================================================================

with st.expander("📖 Guida all'Interpretazione"):
    st.markdown("""
    ### Tipi di Disoccupazione
    
    | Misura | Definizione | Livello "Sano" |
    |--------|-------------|----------------|
    | **U3** | Disoccupati attivamente in cerca | ~4% |
    | **U6** | U3 + scoraggiati + part-time involontari | ~7-8% |
    
    ### Initial vs Continuing Claims
    
    - **Initial Claims**: Nuove richieste sussidio → indica licenziamenti recenti
    - **Continuing Claims**: Persone che continuano a ricevere sussidio → indica difficoltà a trovare lavoro
    
    **Soglie di attenzione:**
    - Initial Claims > 300K: Segnale di stress
    - Initial Claims > 400K: Recessione probabile
    
    ### Nonfarm Payrolls
    
    Indica i nuovi posti di lavoro creati (escluso settore agricolo).
    
    - **> 200K/mese**: Economia forte
    - **100-200K/mese**: Crescita moderata
    - **< 100K/mese**: Rallentamento
    - **Negativo**: Recessione/contrazione
    
    ### Labor Participation
    
    % della popolazione in età lavorativa che lavora o cerca lavoro.
    
    - Pre-COVID era ~63.3%
    - Calo può indicare: invecchiamento popolazione, scoraggiamento, pensionamenti anticipati
    - Recovery lento post-COVID è segnale di cambiamenti strutturali
    
    ### Sahm Rule
    
    Se la media mobile a 3 mesi del tasso di disoccupazione sale di 0.5% rispetto al minimo dei 12 mesi precedenti, indica l'inizio di una recessione.
    """)


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("💡 Il mercato del lavoro è un indicatore lagging - reagisce con ritardo al ciclo economico. Fonte: FRED St. Louis Fed")
