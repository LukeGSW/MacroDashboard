"""
FRED Macro Dashboard - Chart Utilities
=======================================
Funzioni per creazione grafici Plotly: gauge, line charts, heatmaps.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from config import GAUGE_CONFIG, RECESSIONS


# =============================================================================
# GAUGE CHARTS
# =============================================================================

def create_gauge(
    value: float,
    title: str,
    gauge_range: List[float] = [0, 100],
    thresholds: Dict[str, List[float]] = None,
    target: Optional[float] = None,
    units: str = "",
    delta_reference: Optional[float] = None,
    invert: bool = False,
    height: int = None
) -> go.Figure:
    """
    Crea un gauge chart stile manometro.
    
    Args:
        value: Valore corrente da visualizzare
        title: Titolo del gauge
        gauge_range: [min, max] range del gauge
        thresholds: Dict con 'green', 'yellow', 'red' ranges
        target: Linea target opzionale
        units: Unità di misura per display
        delta_reference: Valore riferimento per delta
        invert: Se True, inverte logica colori (alto=bene)
        height: Altezza grafico
        
    Returns:
        Plotly Figure object
    """
    if height is None:
        height = GAUGE_CONFIG["height"]
    
    colors = GAUGE_CONFIG["colors"]
    
    # Default thresholds se non specificati
    if thresholds is None:
        range_span = gauge_range[1] - gauge_range[0]
        thresholds = {
            "green": [gauge_range[0], gauge_range[0] + range_span * 0.33],
            "yellow": [gauge_range[0] + range_span * 0.33, gauge_range[0] + range_span * 0.66],
            "red": [gauge_range[0] + range_span * 0.66, gauge_range[1]]
        }
    
    # Costruisci steps per il gauge
    steps = []
    color_order = ["green", "yellow", "red"] if not invert else ["red", "yellow", "green"]
    
    for color_name in color_order:
        if color_name in thresholds:
            steps.append({
                "range": thresholds[color_name],
                "color": colors[color_name]
            })
    
    # Ordina steps per range
    steps = sorted(steps, key=lambda x: x["range"][0])
    
    # Configura delta
    delta_config = None
    if delta_reference is not None:
        delta_config = {
            "reference": delta_reference,
            "position": "bottom",
            "relative": False,
            "valueformat": ".2f"
        }
    
    # Configura threshold line (target)
    threshold_config = None
    if target is not None:
        threshold_config = {
            "line": {"color": "white", "width": 3},
            "thickness": 0.8,
            "value": target
        }
    
    # Formatta valore per display
    if value is not None:
        number_format = {"suffix": f" {units}" if units else "", "valueformat": ".2f"}
    else:
        number_format = {}
        value = 0
    
    # Crea figura
    fig = go.Figure(go.Indicator(
        mode="gauge+number" + ("+delta" if delta_config else ""),
        value=value,
        number=number_format,
        delta=delta_config,
        title={"text": title, "font": {"size": 14, "color": "white"}},
        gauge={
            "axis": {
                "range": gauge_range,
                "tickcolor": "white",
                "tickfont": {"color": "white", "size": 10}
            },
            "bar": {"color": colors["bar"], "thickness": 0.3},
            "bgcolor": colors["background"],
            "borderwidth": 0,
            "steps": steps,
            "threshold": threshold_config
        }
    ))
    
    # Layout
    fig.update_layout(
        height=height,
        margin=GAUGE_CONFIG["margin"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"}
    )
    
    return fig


def create_gauge_row(
    indicators_data: List[Dict],
    columns: int = 4
) -> go.Figure:
    """
    Crea una riga di gauge multipli.
    
    Args:
        indicators_data: Lista di dict con dati per ogni gauge
        columns: Numero di colonne
        
    Returns:
        Plotly Figure con subplot di gauge
    """
    n_indicators = len(indicators_data)
    rows = (n_indicators + columns - 1) // columns
    
    fig = make_subplots(
        rows=rows,
        cols=columns,
        specs=[[{"type": "indicator"} for _ in range(columns)] for _ in range(rows)],
        vertical_spacing=0.15,
        horizontal_spacing=0.05
    )
    
    for i, data in enumerate(indicators_data):
        row = i // columns + 1
        col = i % columns + 1
        
        gauge = create_gauge(**data)
        
        for trace in gauge.data:
            fig.add_trace(trace, row=row, col=col)
    
    fig.update_layout(
        height=GAUGE_CONFIG["height"] * rows,
        margin={"t": 30, "b": 10, "l": 10, "r": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig


# =============================================================================
# LINE CHARTS
# =============================================================================

def create_line_chart(
    df: pd.DataFrame,
    title: str,
    y_label: str = "",
    color: str = "#1f77b4",
    show_recessions: bool = True,
    height: int = 400,
    show_zero_line: bool = False
) -> go.Figure:
    """
    Crea un line chart singolo.
    
    Args:
        df: DataFrame con colonne ['date', 'value']
        title: Titolo del grafico
        y_label: Label asse Y
        color: Colore linea
        show_recessions: Se mostrare bande recessioni
        height: Altezza grafico
        show_zero_line: Se mostrare linea zero
        
    Returns:
        Plotly Figure
    """
    fig = go.Figure()
    
    # Aggiungi recession bands se richiesto
    if show_recessions and not df.empty:
        min_date = df["date"].min()
        max_date = df["date"].max()
        
        for start, end in RECESSIONS:
            rec_start = pd.to_datetime(start)
            rec_end = pd.to_datetime(end)
            
            # Solo se overlap con range dati
            if rec_end >= min_date and rec_start <= max_date:
                fig.add_vrect(
                    x0=max(rec_start, min_date),
                    x1=min(rec_end, max_date),
                    fillcolor="rgba(128, 128, 128, 0.2)",
                    layer="below",
                    line_width=0
                )
    
    # Linea principale
    if not df.empty:
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["value"],
            mode="lines",
            name=title,
            line={"color": color, "width": 2},
            hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}<extra></extra>"
        ))
    
    # Zero line opzionale
    if show_zero_line:
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="rgba(255,255,255,0.5)",
            line_width=1
        )
    
    # Layout
    fig.update_layout(
        title={"text": title, "font": {"size": 16}},
        xaxis={"title": "", "gridcolor": "rgba(128,128,128,0.2)", "showgrid": True},
        yaxis={"title": y_label, "gridcolor": "rgba(128,128,128,0.2)", "showgrid": True},
        height=height,
        margin={"t": 50, "b": 40, "l": 60, "r": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        hovermode="x unified",
        showlegend=False
    )
    
    return fig


def create_multi_line_chart(
    data_dict: Dict[str, pd.DataFrame],
    title: str,
    y_label: str = "",
    colors: Dict[str, str] = None,
    show_recessions: bool = True,
    height: int = 450,
    show_zero_line: bool = False,
    show_legend: bool = True
) -> go.Figure:
    """
    Crea un line chart con multiple serie.
    
    Args:
        data_dict: Dict con chiave=nome serie, valore=DataFrame
        title: Titolo del grafico
        y_label: Label asse Y
        colors: Dict con colori per serie
        show_recessions: Se mostrare bande recessioni
        height: Altezza grafico
        show_zero_line: Se mostrare linea zero
        show_legend: Se mostrare legenda
        
    Returns:
        Plotly Figure
    """
    fig = go.Figure()
    
    # Default colors
    default_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
        "#9467bd", "#8c564b", "#e377c2", "#bcbd22"
    ]
    
    if colors is None:
        colors = {}
    
    # Trova range date complessivo
    all_dates = []
    for df in data_dict.values():
        if not df.empty:
            all_dates.extend(df["date"].tolist())
    
    # Recession bands
    if show_recessions and all_dates:
        min_date = min(all_dates)
        max_date = max(all_dates)
        
        for start, end in RECESSIONS:
            rec_start = pd.to_datetime(start)
            rec_end = pd.to_datetime(end)
            
            if rec_end >= min_date and rec_start <= max_date:
                fig.add_vrect(
                    x0=max(rec_start, min_date),
                    x1=min(rec_end, max_date),
                    fillcolor="rgba(128, 128, 128, 0.2)",
                    layer="below",
                    line_width=0
                )
    
    # Aggiungi ogni serie
    for i, (name, df) in enumerate(data_dict.items()):
        if df.empty:
            continue
        
        color = colors.get(name, default_colors[i % len(default_colors)])
        
        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["value"],
            mode="lines",
            name=name,
            line={"color": color, "width": 2},
            hovertemplate=f"{name}<br>%{{x|%Y-%m-%d}}<br>%{{y:.2f}}<extra></extra>"
        ))
    
    # Zero line opzionale
    if show_zero_line:
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="rgba(255,255,255,0.5)",
            line_width=1
        )
    
    # Layout
    fig.update_layout(
        title={"text": title, "font": {"size": 16}},
        xaxis={"title": "", "gridcolor": "rgba(128,128,128,0.2)", "showgrid": True},
        yaxis={"title": y_label, "gridcolor": "rgba(128,128,128,0.2)", "showgrid": True},
        height=height,
        margin={"t": 50, "b": 40, "l": 60, "r": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        hovermode="x unified",
        showlegend=show_legend,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1
        }
    )
    
    return fig


# =============================================================================
# YIELD CURVE CHART
# =============================================================================

def create_yield_curve(
    yields_data: Dict[str, float],
    title: str = "Yield Curve",
    height: int = 350
) -> go.Figure:
    """
    Crea grafico yield curve snapshot.
    
    Args:
        yields_data: Dict con maturity -> yield (es. {"1Y": 4.5, "2Y": 4.3, ...})
        title: Titolo grafico
        height: Altezza
        
    Returns:
        Plotly Figure
    """
    maturities = list(yields_data.keys())
    values = list(yields_data.values())
    
    # Determina colore basato su inversione
    if len(values) >= 2 and values[-1] < values[0]:
        color = "#ff4444"  # Invertita = rosso
    else:
        color = "#00cc66"  # Normale = verde
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=maturities,
        y=values,
        mode="lines+markers",
        line={"color": color, "width": 3},
        marker={"size": 10, "color": color},
        hovertemplate="%{x}: %{y:.2f}%<extra></extra>"
    ))
    
    fig.update_layout(
        title={"text": title, "font": {"size": 16}},
        xaxis={"title": "Maturity", "gridcolor": "rgba(128,128,128,0.2)"},
        yaxis={"title": "Yield %", "gridcolor": "rgba(128,128,128,0.2)"},
        height=height,
        margin={"t": 50, "b": 40, "l": 60, "r": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"}
    )
    
    return fig


# =============================================================================
# SPARKLINE (mini chart per tabelle)
# =============================================================================

def create_sparkline(
    values: List[float],
    width: int = 150,
    height: int = 40,
    color: str = "#1f77b4"
) -> go.Figure:
    """
    Crea mini sparkline chart.
    
    Args:
        values: Lista valori
        width: Larghezza
        height: Altezza
        color: Colore linea
        
    Returns:
        Plotly Figure
    """
    # Determina colore trend
    if len(values) >= 2:
        if values[-1] > values[0]:
            color = "#00cc66"
        elif values[-1] < values[0]:
            color = "#ff4444"
    
    fig = go.Figure(go.Scatter(
        y=values,
        mode="lines",
        line={"color": color, "width": 1.5},
        fill="tozeroy",
        fillcolor=f"rgba{tuple(list(bytes.fromhex(color[1:])) + [0.2])}"
    ))
    
    fig.update_layout(
        width=width,
        height=height,
        margin={"t": 0, "b": 0, "l": 0, "r": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
        showlegend=False
    )
    
    return fig


# =============================================================================
# HELPER: Metric Card HTML
# =============================================================================

def format_delta_color(delta: float, invert: bool = False) -> str:
    """Ritorna colore CSS per delta."""
    if delta is None:
        return "gray"
    
    if invert:
        return "#00cc66" if delta > 0 else "#ff4444" if delta < 0 else "gray"
    else:
        return "#ff4444" if delta > 0 else "#00cc66" if delta < 0 else "gray"


def format_value(value: float, decimals: int = 2) -> str:
    """Formatta valore numerico."""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"
