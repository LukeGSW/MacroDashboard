"""
FRED Macro Dashboard - FRED API Client
=======================================
Gestione connessione API FRED con caching Streamlit.
"""

import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fredapi import Fred

from config import TIME_CONFIG, get_indicator_config


# =============================================================================
# FRED CLIENT CLASS
# =============================================================================

class FredClient:
    """Client per accesso API FRED con caching."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inizializza il client FRED.
        
        Args:
            api_key: API key FRED. Se None, cerca in secrets o env.
        """
        self.api_key = api_key or self._get_api_key()
        self.fred = Fred(api_key=self.api_key)
    
    def _get_api_key(self) -> str:
        """Recupera API key da Streamlit secrets o environment."""
        # Prima prova Streamlit secrets
        try:
            return st.secrets["FRED_API_KEY"]
        except (KeyError, FileNotFoundError):
            pass
        
        # Poi prova environment variable
        api_key = os.environ.get("FRED_API_KEY")
        if api_key:
            return api_key
        
        # Se non trovata, solleva errore
        raise ValueError(
            "FRED_API_KEY non trovata. "
            "Configura in .streamlit/secrets.toml o come variabile d'ambiente."
        )
    
    def get_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.Series:
        """
        Recupera una serie FRED.
        
        Args:
            series_id: Codice serie FRED (es. 'CPIAUCSL')
            start_date: Data inizio (YYYY-MM-DD)
            end_date: Data fine (YYYY-MM-DD)
            
        Returns:
            pd.Series con dati della serie
        """
        try:
            data = self.fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )
            return data.dropna()
        except Exception as e:
            st.error(f"Errore fetch {series_id}: {str(e)}")
            return pd.Series(dtype=float)
    
    def get_series_info(self, series_id: str) -> dict:
        """Recupera metadati di una serie FRED."""
        try:
            info = self.fred.get_series_info(series_id)
            return info.to_dict()
        except Exception as e:
            return {"error": str(e)}


# =============================================================================
# CACHED DATA FETCHING
# =============================================================================

@st.cache_data(ttl=timedelta(hours=TIME_CONFIG["cache_ttl_hours"]))
def fetch_fred_series(
    series_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch singola serie FRED con caching.
    
    Args:
        series_id: Codice serie FRED
        start_date: Data inizio
        end_date: Data fine
        api_key: API key (opzionale se in secrets)
        
    Returns:
        DataFrame con colonne ['date', 'value']
    """
    client = FredClient(api_key)
    series = client.get_series(series_id, start_date, end_date)
    
    if series.empty:
        return pd.DataFrame(columns=["date", "value"])
    
    df = pd.DataFrame({
        "date": series.index,
        "value": series.values
    })
    df["date"] = pd.to_datetime(df["date"])
    
    return df


@st.cache_data(ttl=timedelta(hours=TIME_CONFIG["cache_ttl_hours"]))
def fetch_multiple_series(
    series_ids: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """
    Fetch multiple serie FRED con caching.
    
    Args:
        series_ids: Lista codici serie FRED
        start_date: Data inizio
        end_date: Data fine
        api_key: API key
        
    Returns:
        Dict con chiave=series_id, valore=DataFrame
    """
    results = {}
    
    for series_id in series_ids:
        df = fetch_fred_series(series_id, start_date, end_date, api_key)
        results[series_id] = df
    
    return results


# =============================================================================
# DATA TRANSFORMATIONS
# =============================================================================

def calculate_yoy(df: pd.DataFrame, periods: int = 12) -> pd.DataFrame:
    """
    Calcola variazione Year-over-Year percentuale.
    
    Args:
        df: DataFrame con colonne ['date', 'value']
        periods: Numero di periodi per YoY (12 per monthly, 252 per daily)
        
    Returns:
        DataFrame con colonna 'value' trasformata in % YoY
    """
    if df.empty or len(df) < periods + 1:
        return df
    
    df = df.copy()
    df["value"] = df["value"].pct_change(periods=periods) * 100
    df = df.dropna()
    
    return df


def calculate_mom_diff(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola differenza Month-over-Month.
    
    Args:
        df: DataFrame con colonne ['date', 'value']
        
    Returns:
        DataFrame con variazione assoluta MoM
    """
    if df.empty or len(df) < 2:
        return df
    
    df = df.copy()
    df["value"] = df["value"].diff()
    df = df.dropna()
    
    return df


def transform_series(df: pd.DataFrame, transform: str) -> pd.DataFrame:
    """
    Applica trasformazione alla serie.
    
    Args:
        df: DataFrame originale
        transform: Tipo trasformazione ('level', 'yoy', 'mom_diff')
        
    Returns:
        DataFrame trasformato
    """
    if df.empty:
        return df
    
    if transform == "yoy":
        # Stima periodi basata su frequenza dati
        if len(df) > 1:
            avg_days = (df["date"].iloc[-1] - df["date"].iloc[0]).days / len(df)
            if avg_days < 5:  # Daily
                periods = 252
            elif avg_days < 10:  # Weekly
                periods = 52
            else:  # Monthly o meno frequente
                periods = 12
        else:
            periods = 12
        return calculate_yoy(df, periods)
    
    elif transform == "mom_diff":
        return calculate_mom_diff(df)
    
    else:  # 'level' o default
        return df


# =============================================================================
# DATA RETRIEVAL WITH TRANSFORM
# =============================================================================

def get_indicator_data(
    series_id: str,
    years: int = None,
    apply_transform: bool = True
) -> pd.DataFrame:
    """
    Recupera dati indicatore con trasformazione automatica.
    
    Args:
        series_id: Codice FRED
        years: Numero anni di storia (default da config)
        apply_transform: Se applicare trasformazione da config
        
    Returns:
        DataFrame pronto per visualizzazione
    """
    if years is None:
        years = TIME_CONFIG["default_years"]
    
    # Recupera config per questo indicatore
    config = get_indicator_config(series_id)
    transform = config.get("transform", "level")
    
    # Se serve YoY, chiedi 1 anno extra di dati per il calcolo
    extra_years = 0
    if apply_transform and transform == "yoy":
        extra_years = 2  # Buffer extra per sicurezza
    
    # Calcola date range
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=(years + extra_years) * 365)).strftime("%Y-%m-%d")
    
    # Fetch dati
    df = fetch_fred_series(series_id, start_date, end_date)
    
    if df.empty:
        return df
    
    # Applica trasformazione se richiesto
    if apply_transform:
        df = transform_series(df, transform)
    
    # Filtra per mantenere solo il periodo richiesto dall'utente
    if not df.empty and extra_years > 0:
        cutoff_date = datetime.now() - timedelta(days=years * 365)
        df = df[df["date"] >= cutoff_date].copy()
    
    return df


def get_latest_value(series_id: str, apply_transform: bool = True) -> dict:
    """
    Recupera ultimo valore di un indicatore.
    
    Args:
        series_id: Codice FRED
        apply_transform: Se applicare trasformazione
        
    Returns:
        Dict con 'value', 'date', 'previous', 'change'
    """
    df = get_indicator_data(series_id, years=3, apply_transform=apply_transform)
    
    if df.empty or len(df) < 2:
        return {
            "value": None,
            "date": None,
            "previous": None,
            "change": None
        }
    
    current = df.iloc[-1]
    previous = df.iloc[-2]
    
    return {
        "value": round(current["value"], 2),
        "date": current["date"].strftime("%Y-%m-%d"),
        "previous": round(previous["value"], 2),
        "change": round(current["value"] - previous["value"], 2)
    }


# =============================================================================
# SINGLETON CLIENT
# =============================================================================

@st.cache_resource
def get_fred_client() -> FredClient:
    """Ritorna istanza singleton del client FRED."""
    return FredClient()
