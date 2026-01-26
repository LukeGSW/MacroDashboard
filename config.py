"""
FRED Macro Dashboard - Configuration
=====================================
Configurazione centralizzata di tutti gli indicatori FRED,
soglie per gauge, metadata e parametri di visualizzazione.
"""

# =============================================================================
# INDICATORI FRED PER SEZIONE
# =============================================================================

INDICATORS = {
    
    # -------------------------------------------------------------------------
    # SNAPSHOT - KPI Principali (8 indicatori chiave)
    # -------------------------------------------------------------------------
    "snapshot": {
        "CPIAUCSL": {
            "name": "CPI (Inflazione)",
            "description": "Consumer Price Index - All Urban Consumers",
            "frequency": "Monthly",
            "units": "% YoY",
            "transform": "yoy",  # Calcola Year-over-Year
            "gauge_range": [0, 10],
            "thresholds": {"green": [0, 2.5], "yellow": [2.5, 4], "red": [4, 10]},
            "target": 2.0,
            "invert": False  # False = alto è male, True = alto è bene
        },
        "PCEPILFE": {
            "name": "Core PCE",
            "description": "PCE Excluding Food and Energy (Fed's preferred)",
            "frequency": "Monthly",
            "units": "% YoY",
            "transform": "yoy",
            "gauge_range": [0, 8],
            "thresholds": {"green": [0, 2.5], "yellow": [2.5, 3.5], "red": [3.5, 8]},
            "target": 2.0,
            "invert": False
        },
        "FEDFUNDS": {
            "name": "Fed Funds Rate",
            "description": "Federal Funds Effective Rate",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "gauge_range": [0, 8],
            "thresholds": {"green": [0, 3], "yellow": [3, 5], "red": [5, 8]},
            "target": None,
            "invert": False
        },
        "UNRATE": {
            "name": "Disoccupazione",
            "description": "Unemployment Rate",
            "frequency": "Monthly",
            "units": "%",
            "transform": "level",
            "gauge_range": [0, 15],
            "thresholds": {"green": [0, 4.5], "yellow": [4.5, 6], "red": [6, 15]},
            "target": 4.0,
            "invert": False
        },
        "T10Y2Y": {
            "name": "Yield Curve 10Y-2Y",
            "description": "10-Year Treasury Minus 2-Year Treasury",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "gauge_range": [-3, 3],
            "thresholds": {"red": [-3, 0], "yellow": [0, 0.5], "green": [0.5, 3]},
            "target": 0,
            "invert": True  # Negativo = recessione warning
        },
        "UMCSENT": {
            "name": "Consumer Sentiment",
            "description": "University of Michigan Consumer Sentiment",
            "frequency": "Monthly",
            "units": "Index",
            "transform": "level",
            "gauge_range": [40, 120],
            "thresholds": {"red": [40, 60], "yellow": [60, 80], "green": [80, 120]},
            "target": 80,
            "invert": True
        },
        "BAMLH0A0HYM2": {
            "name": "HY Spread",
            "description": "ICE BofA US High Yield Option-Adjusted Spread",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "gauge_range": [0, 12],
            "thresholds": {"green": [0, 4], "yellow": [4, 6], "red": [6, 12]},
            "target": 3.5,
            "invert": False  # Alto spread = stress
        },
        "INDPRO": {
            "name": "Industrial Production",
            "description": "Industrial Production Index",
            "frequency": "Monthly",
            "units": "% YoY",
            "transform": "yoy",
            "gauge_range": [-15, 15],
            "thresholds": {"red": [-15, 0], "yellow": [0, 2], "green": [2, 15]},
            "target": 2.0,
            "invert": True
        }
    },
    
    # -------------------------------------------------------------------------
    # INFLAZIONE
    # -------------------------------------------------------------------------
    "inflazione": {
        "CPIAUCSL": {
            "name": "CPI All Items",
            "description": "Consumer Price Index for All Urban Consumers",
            "frequency": "Monthly",
            "units": "% YoY",
            "transform": "yoy",
            "color": "#1f77b4"
        },
        "CPILFESL": {
            "name": "Core CPI",
            "description": "CPI Excluding Food and Energy",
            "frequency": "Monthly",
            "units": "% YoY",
            "transform": "yoy",
            "color": "#ff7f0e"
        },
        "PCEPI": {
            "name": "PCE",
            "description": "Personal Consumption Expenditures Price Index",
            "frequency": "Monthly",
            "units": "% YoY",
            "transform": "yoy",
            "color": "#2ca02c"
        },
        "PCEPILFE": {
            "name": "Core PCE",
            "description": "PCE Excluding Food and Energy",
            "frequency": "Monthly",
            "units": "% YoY",
            "transform": "yoy",
            "color": "#d62728"
        },
        "PPIFIS": {
            "name": "PPI Final Demand",
            "description": "Producer Price Index - Final Demand",
            "frequency": "Monthly",
            "units": "% YoY",
            "transform": "yoy",
            "color": "#9467bd"
        },
        "T5YIE": {
            "name": "5Y Breakeven Inflation",
            "description": "5-Year Breakeven Inflation Rate",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#8c564b"
        },
        "T10YIE": {
            "name": "10Y Breakeven Inflation",
            "description": "10-Year Breakeven Inflation Rate",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#e377c2"
        }
    },
    
    # -------------------------------------------------------------------------
    # LAVORO
    # -------------------------------------------------------------------------
    "lavoro": {
        "UNRATE": {
            "name": "Unemployment Rate",
            "description": "Civilian Unemployment Rate",
            "frequency": "Monthly",
            "units": "%",
            "transform": "level",
            "color": "#1f77b4"
        },
        "U6RATE": {
            "name": "U6 Unemployment",
            "description": "Total Unemployed + Marginally Attached + Part-Time",
            "frequency": "Monthly",
            "units": "%",
            "transform": "level",
            "color": "#ff7f0e"
        },
        "ICSA": {
            "name": "Initial Claims",
            "description": "Initial Jobless Claims (Weekly)",
            "frequency": "Weekly",
            "units": "Thousands",
            "transform": "level",
            "color": "#2ca02c"
        },
        "CCSA": {
            "name": "Continuing Claims",
            "description": "Continued Claims (Insured Unemployment)",
            "frequency": "Weekly",
            "units": "Thousands",
            "transform": "level",
            "color": "#d62728"
        },
        "PAYEMS": {
            "name": "Nonfarm Payrolls",
            "description": "All Employees, Total Nonfarm",
            "frequency": "Monthly",
            "units": "MoM Change (K)",
            "transform": "mom_diff",
            "color": "#9467bd"
        },
        "CIVPART": {
            "name": "Labor Participation",
            "description": "Civilian Labor Force Participation Rate",
            "frequency": "Monthly",
            "units": "%",
            "transform": "level",
            "color": "#8c564b"
        }
    },
    
    # -------------------------------------------------------------------------
    # TASSI E YIELD CURVE
    # -------------------------------------------------------------------------
    "tassi": {
        "FEDFUNDS": {
            "name": "Fed Funds Rate",
            "description": "Federal Funds Effective Rate",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#1f77b4"
        },
        "DGS1": {
            "name": "Treasury 1Y",
            "description": "1-Year Treasury Constant Maturity",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#aec7e8"
        },
        "DGS2": {
            "name": "Treasury 2Y",
            "description": "2-Year Treasury Constant Maturity",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#ff7f0e"
        },
        "DGS5": {
            "name": "Treasury 5Y",
            "description": "5-Year Treasury Constant Maturity",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#2ca02c"
        },
        "DGS10": {
            "name": "Treasury 10Y",
            "description": "10-Year Treasury Constant Maturity",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#d62728"
        },
        "DGS30": {
            "name": "Treasury 30Y",
            "description": "30-Year Treasury Constant Maturity",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#9467bd"
        },
        "T10Y2Y": {
            "name": "Spread 10Y-2Y",
            "description": "10-Year Treasury Minus 2-Year Treasury",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#e377c2"
        },
        "T10Y3M": {
            "name": "Spread 10Y-3M",
            "description": "10-Year Treasury Minus 3-Month Treasury",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#bcbd22"
        }
    },
    
    # -------------------------------------------------------------------------
    # HOUSING
    # -------------------------------------------------------------------------
    "housing": {
        "HOUST": {
            "name": "Housing Starts",
            "description": "Housing Starts: Total (SAAR)",
            "frequency": "Monthly",
            "units": "Thousands",
            "transform": "level",
            "color": "#1f77b4"
        },
        "PERMIT": {
            "name": "Building Permits",
            "description": "New Private Housing Units Authorized",
            "frequency": "Monthly",
            "units": "Thousands",
            "transform": "level",
            "color": "#ff7f0e"
        },
        "CSUSHPINSA": {
            "name": "Case-Shiller Index",
            "description": "S&P/Case-Shiller U.S. National Home Price Index",
            "frequency": "Monthly",
            "units": "% YoY",
            "transform": "yoy",
            "color": "#2ca02c"
        },
        "MORTGAGE30US": {
            "name": "Mortgage 30Y",
            "description": "30-Year Fixed Rate Mortgage Average",
            "frequency": "Weekly",
            "units": "%",
            "transform": "level",
            "color": "#d62728"
        },
        "MSPUS": {
            "name": "Median Sale Price",
            "description": "Median Sales Price of Houses Sold",
            "frequency": "Quarterly",
            "units": "USD",
            "transform": "level",
            "color": "#9467bd"
        },
        "RRVRUSQ156N": {
            "name": "Rental Vacancy",
            "description": "Rental Vacancy Rate",
            "frequency": "Quarterly",
            "units": "%",
            "transform": "level",
            "color": "#8c564b"
        }
    },
    
    # -------------------------------------------------------------------------
    # SENTIMENT E FINANCIAL CONDITIONS
    # -------------------------------------------------------------------------
    "sentiment": {
        "UMCSENT": {
            "name": "Michigan Sentiment",
            "description": "University of Michigan Consumer Sentiment",
            "frequency": "Monthly",
            "units": "Index",
            "transform": "level",
            "color": "#1f77b4"
        },
        "PSAVERT": {
            "name": "Personal Savings Rate",
            "description": "Personal Saving Rate",
            "frequency": "Monthly",
            "units": "%",
            "transform": "level",
            "color": "#ff7f0e"
        },
        "BAMLH0A0HYM2": {
            "name": "HY Credit Spread",
            "description": "ICE BofA US High Yield OAS",
            "frequency": "Daily",
            "units": "%",
            "transform": "level",
            "color": "#d62728"
        },
        "STLFSI4": {
            "name": "Financial Stress Index",
            "description": "St. Louis Fed Financial Stress Index",
            "frequency": "Weekly",
            "units": "Index",
            "transform": "level",
            "color": "#2ca02c"
        },
        "DRTSCILM": {
            "name": "Bank Lending Standards",
            "description": "Net % Banks Tightening C&I Loans",
            "frequency": "Quarterly",
            "units": "%",
            "transform": "level",
            "color": "#9467bd"
        },
        "VIXCLS": {
            "name": "VIX",
            "description": "CBOE Volatility Index",
            "frequency": "Daily",
            "units": "Index",
            "transform": "level",
            "color": "#e377c2"
        }
    }
}


# =============================================================================
# CONFIGURAZIONE GAUGE DEFAULT
# =============================================================================

GAUGE_CONFIG = {
    "height": 250,
    "margin": {"t": 50, "b": 20, "l": 30, "r": 30},
    "colors": {
        "green": "#00cc66",
        "yellow": "#ffcc00",
        "red": "#ff4444",
        "bar": "#1f77b4",
        "background": "#262730"
    }
}


# =============================================================================
# PARAMETRI TEMPORALI
# =============================================================================

TIME_CONFIG = {
    "default_years": 10,
    "max_years": 50,
    "cache_ttl_hours": 4
}


# =============================================================================
# RECESSION PERIODS (per shading nei grafici)
# =============================================================================

RECESSIONS = [
    ("1980-01-01", "1980-07-01"),
    ("1981-07-01", "1982-11-01"),
    ("1990-07-01", "1991-03-01"),
    ("2001-03-01", "2001-11-01"),
    ("2007-12-01", "2009-06-01"),
    ("2020-02-01", "2020-04-01")
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_section_indicators(section: str) -> dict:
    """Ritorna gli indicatori per una sezione specifica."""
    return INDICATORS.get(section, {})


def get_all_indicator_codes() -> list:
    """Ritorna lista unica di tutti i codici FRED."""
    codes = set()
    for section in INDICATORS.values():
        codes.update(section.keys())
    return list(codes)


def get_indicator_config(code: str) -> dict:
    """Cerca la configurazione di un indicatore in tutte le sezioni."""
    for section in INDICATORS.values():
        if code in section:
            return section[code]
    return {}
