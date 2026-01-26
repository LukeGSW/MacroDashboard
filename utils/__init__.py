"""
FRED Macro Dashboard - Utils Package
=====================================
Moduli di utilità per fetch dati e visualizzazioni.
"""

from utils.fred_api import FredClient, get_fred_client
from utils.charts import create_gauge, create_line_chart, create_multi_line_chart

__all__ = [
    "FredClient",
    "get_fred_client", 
    "create_gauge",
    "create_line_chart",
    "create_multi_line_chart"
]
