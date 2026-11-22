"""
Grafici Plotly con lo stile Kriterion Quant
===========================================
Template unico, numeri all'italiana, bande di recessione NBER, watermark.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from catalog import Band
from config import BRAND, LEVEL_COLORS, PALETTE, SERIES_COLORS

TEMPLATE = "kq"
FONT = '-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
PLOTLY_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}
_DAY_MS = 86_400_000


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def register_template() -> None:
    if TEMPLATE in pio.templates:
        return
    axis = dict(
        gridcolor=PALETTE["line"], linecolor=PALETTE["line2"], zerolinecolor=PALETTE["line2"],
        tickfont=dict(color=PALETTE["mut"], size=11), title=dict(font=dict(color=PALETTE["mut"], size=12)),
        automargin=True,
    )
    t = go.layout.Template()
    t.layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=PALETTE["txt"], size=13),
        colorway=SERIES_COLORS,
        separators=",.",
        xaxis=axis,
        yaxis=axis,
        hoverlabel=dict(bgcolor=PALETTE["card"], bordercolor=PALETTE["line2"],
                        font=dict(family=FONT, color=PALETTE["txt"], size=12)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(color=PALETTE["mut"], size=12)),
        margin=dict(t=36, b=24, l=8, r=8),
        hovermode="x unified",
    )
    pio.templates[TEMPLATE] = t


register_template()


def show(fig: go.Figure, key: str | None = None) -> None:
    st.plotly_chart(fig, width="stretch", theme=None, config=PLOTLY_CONFIG, key=key)


def _watermark(fig: go.Figure) -> None:
    fig.add_annotation(
        text=BRAND, xref="paper", yref="paper", x=0.995, y=0.03, xanchor="right", yanchor="bottom",
        showarrow=False, font=dict(size=11, color=_rgba(PALETTE["txt"], 0.22)),
    )


def _date_axis(fig: go.Figure) -> None:
    fig.update_xaxes(
        type="date",
        hoverformat="%d/%m/%Y",
        tickformatstops=[
            dict(dtickrange=[None, 40 * _DAY_MS], value="%d/%m/%y"),
            dict(dtickrange=[40 * _DAY_MS, 300 * _DAY_MS], value="%m/%Y"),
            dict(dtickrange=[300 * _DAY_MS, None], value="%Y"),
        ],
    )


def add_recessions(fig: go.Figure, periods, x_min: pd.Timestamp, x_max: pd.Timestamp) -> None:
    for start, end in periods or []:
        if end < x_min or start > x_max:
            continue
        fig.add_vrect(x0=max(start, x_min), x1=min(end, x_max),
                      fillcolor=_rgba(PALETTE["mut"], 0.14), line_width=0, layer="below")


def time_chart(
    traces: list[dict],
    *,
    title: str | None = None,
    y_title: str | None = None,
    height: int = 360,
    recessions=None,
    zero_line: bool = False,
    hlines: list[dict] | None = None,
    hbands: list[dict] | None = None,
    suffix: str = "",
    decimals: int = 2,
    clip_outliers: bool = True,
) -> go.Figure:
    """Grafico temporale.

    ``traces``: dict con ``series`` (pd.Series), ``name`` e opzionali ``color``,
    ``kind`` ('line' | 'bar'), ``dash``, ``width``, ``fill`` (bool), ``colors`` (per barre).
    ``hlines``: dict con ``y``, ``label``, ``color``. ``hbands``: dict con ``y0``, ``y1``, ``color``.
    """
    fig = go.Figure()
    x_min, x_max = None, None
    for i, tr in enumerate(traces):
        s: pd.Series = tr["series"]
        if s is None or s.empty:
            continue
        x_min = s.index.min() if x_min is None else min(x_min, s.index.min())
        x_max = s.index.max() if x_max is None else max(x_max, s.index.max())
        color = tr.get("color", SERIES_COLORS[i % len(SERIES_COLORS)])
        dec = tr.get("decimals", decimals)
        suf = tr.get("suffix", suffix)
        hover = f"{tr['name']}: %{{y:,.{dec}f}}{suf}<extra></extra>"
        if tr.get("kind") == "bar":
            colors = tr.get("colors")
            if colors is None:
                colors = [PALETTE["teal"] if v >= 0 else PALETTE["coral"] for v in s.to_numpy()]
            fig.add_trace(go.Bar(x=s.index, y=s.to_numpy(), name=tr["name"], marker_color=colors,
                                 marker_line_width=0, hovertemplate=hover, opacity=0.9))
        else:
            fig.add_trace(go.Scatter(
                x=s.index, y=s.to_numpy(), name=tr["name"], mode="lines",
                line=dict(color=color, width=tr.get("width", 2), dash=tr.get("dash")),
                fill="tozeroy" if tr.get("fill") else None,
                fillcolor=_rgba(color, 0.10) if tr.get("fill") else None,
                hovertemplate=hover,
            ))
    shown = [tr["series"] for tr in traces if tr.get("series") is not None and not tr["series"].empty]
    if shown and hbands:
        all_vals = pd.concat(shown)
        v_min, v_max = float(all_vals.min()), float(all_vals.max())
        margin = 0.06 * ((v_max - v_min) or 1.0)
        for band in hbands:
            # la fascia non deve allargare l'asse oltre i dati mostrati
            y0 = max(band["y0"], v_min - margin)
            y1 = min(band["y1"], v_max + margin)
            if y1 > y0:
                fig.add_hrect(y0=y0, y1=y1, fillcolor=_rgba(band.get("color", PALETTE["mut"]), 0.08),
                              line_width=0, layer="below")
    if zero_line:
        fig.add_hline(y=0, line_color=_rgba(PALETTE["txt"], 0.35), line_width=1)
    for hl in hlines or []:
        fig.add_hline(
            y=hl["y"], line_dash=hl.get("dash", "dash"), line_width=1.2,
            line_color=hl.get("color", _rgba(PALETTE["txt"], 0.6)),
            annotation_text=hl.get("label"), annotation_position=hl.get("position", "top left"),
            annotation_font=dict(size=11, color=hl.get("color", PALETTE["mut"])),
        )
    if x_min is not None and recessions:
        add_recessions(fig, recessions, x_min, x_max)
    fig.update_layout(
        template=TEMPLATE, height=height, showlegend=len(traces) > 1, bargap=0.15,
        title=dict(text=title, font=dict(size=15, color=PALETTE["txt"]), x=0, xanchor="left") if title else None,
        margin=dict(t=48 if (title or len(traces) > 1) else 16, b=24, l=8, r=8),
    )
    fig.update_yaxes(title_text=y_title, ticksuffix=suffix.strip() if suffix.strip() in ("%",) else "")
    if clip_outliers:
        _clip_outliers(fig, traces, hlines or [])
    _date_axis(fig)
    _watermark(fig)
    return fig


def _clip_outliers(fig: go.Figure, traces: list[dict], hlines: list[dict]) -> None:
    """Limita l'asse Y quando pochi valori estremi (es. 2020) schiaccerebbero il grafico."""
    series = [tr["series"] for tr in traces if tr.get("series") is not None and not tr["series"].empty]
    if not series:
        return
    values = pd.concat(series)
    if len(values) < 40:
        return
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    iqr = q3 - q1
    if iqr <= 0:
        return
    fence_hi, fence_lo = q3 + 8 * iqr, q1 - 8 * iqr
    too_high = values.max() > fence_hi
    too_low = values.min() < fence_lo
    if not (too_high or too_low):
        return
    inside = values[(values >= fence_lo) & (values <= fence_hi)]
    pad = 0.08 * (inside.max() - inside.min() or iqr)
    lo = inside.min() - pad
    hi = inside.max() + pad
    for hl in hlines:
        lo, hi = min(lo, hl["y"] - pad), max(hi, hl["y"] + pad)
    if any(tr.get("kind") == "bar" for tr in traces):
        lo, hi = min(lo, 0), max(hi, 0)
    fig.update_yaxes(range=[lo, hi])
    fig.update_xaxes(title=dict(text="Scala verticale limitata: alcuni valori estremi (es. 2020) sono fuori grafico",
                                font=dict(size=10, color=PALETTE["mut"]), standoff=6))


def gauge(
    value: float,
    bands: list[Band],
    rng: tuple[float, float],
    *,
    suffix: str = "",
    decimals: int = 2,
    target: float | None = None,
    reference: float | None = None,
    delta_color: str = "off",
    height: int = 200,
) -> go.Figure:
    lo, hi = rng
    steps = []
    for b in bands:
        b_lo = lo if b.lo is None else max(b.lo, lo)
        b_hi = hi if b.hi is None else min(b.hi, hi)
        if b_hi > b_lo:
            steps.append({"range": [b_lo, b_hi], "color": _rgba(LEVEL_COLORS[b.level], 0.82)})
    up, down = PALETTE["teal"], PALETTE["coral"]
    if delta_color == "inverse":
        up, down = down, up
    elif delta_color == "off":
        up = down = PALETTE["mut"]
    indicator = go.Indicator(
        mode="gauge+number" + ("+delta" if reference is not None else ""),
        value=value,
        number={"suffix": suffix, "valueformat": f",.{decimals}f",
                "font": {"size": 30, "color": PALETTE["txt"], "family": FONT}},
        delta={"reference": reference, "valueformat": f"+,.{decimals}f", "position": "bottom",
               "increasing": {"color": up, "symbol": "▲ "}, "decreasing": {"color": down, "symbol": "▼ "},
               "font": {"size": 13}} if reference is not None else None,
        gauge={
            "shape": "angular",
            "axis": {"range": [lo, hi], "tickcolor": PALETTE["line2"], "tickwidth": 1,
                     "tickfont": {"color": PALETTE["mut"], "size": 10}, "nticks": 6},
            "bar": {"color": PALETTE["txt"], "thickness": 0.22},
            "bgcolor": PALETTE["card2"],
            "borderwidth": 0,
            "steps": steps,
            "threshold": ({"line": {"color": "#FFFFFF", "width": 3}, "thickness": 0.9, "value": target}
                          if target is not None else None),
        },
    )
    fig = go.Figure(indicator)
    fig.update_layout(template=TEMPLATE, height=height, margin=dict(t=18, b=6, l=26, r=26))
    return fig


def yield_curve(curves: list[dict], height: int = 380) -> go.Figure:
    """``curves``: dict con ``name``, ``x`` (scadenze), ``y`` (rendimenti), ``color``, ``dash``."""
    fig = go.Figure()
    for c in curves:
        fig.add_trace(go.Scatter(
            x=c["x"], y=c["y"], name=c["name"], mode="lines+markers",
            line=dict(color=c["color"], width=c.get("width", 2.5), dash=c.get("dash")),
            marker=dict(size=c.get("marker", 8), color=c["color"]),
            hovertemplate=f"{c['name']}: %{{y:,.2f}}%<extra></extra>",
        ))
    fig.update_layout(template=TEMPLATE, height=height, hovermode="x unified",
                      margin=dict(t=40, b=24, l=8, r=8))
    fig.update_yaxes(ticksuffix="%")
    fig.update_xaxes(type="category", title_text="Scadenza")
    _watermark(fig)
    return fig
