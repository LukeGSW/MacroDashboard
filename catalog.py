"""
Catalogo degli indicatori
=========================
Unica fonte di verità per:
- serie FRED® usate (titolo, fonte, licenza, eventuale nota di copyright);
- indicatori derivati ("segnali"): calcolo, unità, soglie dei semafori, tooltip;
- release del calendario.

Logica dei colori (uguale per tutta la dashboard):
    verde  = in linea con un'economia in equilibrio / condizioni normali
    giallo = da monitorare
    rosso  = squilibrio o stress marcato
Le soglie sono ancorate a riferimenti pubblici (obiettivo di inflazione della Fed,
stime FOMC/CBO, soglie della letteratura) o alla distribuzione storica dal 1990.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from utils import transforms as T

# =============================================================================
# SERIE FRED
# =============================================================================

BLS = "U.S. Bureau of Labor Statistics"
BEA = "U.S. Bureau of Economic Analysis"
FRB = "Board of Governors of the Federal Reserve System (US)"
STL = "Federal Reserve Bank of St. Louis"
CENSUS = "U.S. Census Bureau"
CENSUS_HUD = "U.S. Census Bureau and U.S. Department of Housing and Urban Development"


@dataclass(frozen=True)
class SeriesMeta:
    title: str            # titolo originale FRED (per la citazione)
    source: str           # proprietario / fonte del dato
    freq: str             # D, W, M, Q
    license: str          # "public" = pubblico dominio, "citation" = copyright, citazione obbligatoria
    copyright: str = ""   # nota di copyright da riportare integralmente


SERIES: dict[str, SeriesMeta] = {
    # --- Inflazione
    "CPIAUCSL": SeriesMeta("Consumer Price Index for All Urban Consumers: All Items in U.S. City Average", BLS, "M", "public"),
    "CPILFESL": SeriesMeta("Consumer Price Index for All Urban Consumers: All Items Less Food and Energy in U.S. City Average", BLS, "M", "public"),
    "PCEPI": SeriesMeta("Personal Consumption Expenditures: Chain-type Price Index", BEA, "M", "public"),
    "PCEPILFE": SeriesMeta("Personal Consumption Expenditures Excluding Food and Energy (Chain-Type Price Index)", BEA, "M", "public"),
    "PPIFIS": SeriesMeta("Producer Price Index by Commodity: Final Demand", BLS, "M", "public"),
    "T5YIE": SeriesMeta("5-Year Breakeven Inflation Rate", STL, "D", "citation"),
    "T10YIE": SeriesMeta("10-Year Breakeven Inflation Rate", STL, "D", "citation"),
    "CUSR0000SAH1": SeriesMeta("Consumer Price Index for All Urban Consumers: Shelter in U.S. City Average", BLS, "M", "public"),
    "CUSR0000SASL2RS": SeriesMeta("Consumer Price Index for All Urban Consumers: Services Less Rent of Shelter in U.S. City Average", BLS, "M", "public"),
    "CORESTICKM159SFRBATL": SeriesMeta("Sticky Price Consumer Price Index less Food and Energy", "Federal Reserve Bank of Atlanta", "M", "citation"),
    # --- Lavoro
    "UNRATE": SeriesMeta("Unemployment Rate", BLS, "M", "public"),
    "U6RATE": SeriesMeta("Total Unemployed, Plus All Persons Marginally Attached to the Labor Force, Plus Total Employed Part Time for Economic Reasons, as a Percent of the Civilian Labor Force Plus All Persons Marginally Attached to the Labor Force (U-6)", BLS, "M", "public"),
    "NROU": SeriesMeta("Noncyclical Rate of Unemployment", "U.S. Congressional Budget Office", "Q", "public"),
    "ICSA": SeriesMeta("Initial Claims", "U.S. Employment and Training Administration", "W", "public"),
    "IC4WSA": SeriesMeta("4-Week Moving Average of Initial Claims", "U.S. Employment and Training Administration", "W", "public"),
    "CCSA": SeriesMeta("Continued Claims (Insured Unemployment)", "U.S. Employment and Training Administration", "W", "public"),
    "PAYEMS": SeriesMeta("All Employees, Total Nonfarm", BLS, "M", "public"),
    "CIVPART": SeriesMeta("Labor Force Participation Rate", BLS, "M", "public"),
    "LNS12300060": SeriesMeta("Employment-Population Ratio - 25-54 Yrs.", BLS, "M", "public"),
    "CES0500000003": SeriesMeta("Average Hourly Earnings of All Employees, Total Private", BLS, "M", "public"),
    "JTSJOL": SeriesMeta("Job Openings: Total Nonfarm", BLS, "M", "public"),
    "JTSQUR": SeriesMeta("Quits: Total Nonfarm (rate)", BLS, "M", "public"),
    "UNEMPLOY": SeriesMeta("Unemployment Level", BLS, "M", "public"),
    "SAHMREALTIME": SeriesMeta("Real-time Sahm Rule Recession Indicator", "Claudia Sahm", "M", "public"),
    # --- Crescita
    "A191RL1Q225SBEA": SeriesMeta("Real Gross Domestic Product (percent change from preceding period, SAAR)", BEA, "Q", "public"),
    "GDPNOW": SeriesMeta("GDPNow", "Federal Reserve Bank of Atlanta", "Q", "citation"),
    "INDPRO": SeriesMeta("Industrial Production: Total Index", FRB, "M", "public"),
    "TCU": SeriesMeta("Capacity Utilization: Total Index", FRB, "M", "public"),
    "RRSFS": SeriesMeta("Advance Real Retail and Food Services Sales", STL, "M", "citation"),
    "PCEC96": SeriesMeta("Real Personal Consumption Expenditures", BEA, "M", "public"),
    "W875RX1": SeriesMeta("Real personal income excluding current transfer receipts", BEA, "M", "public"),
    # --- Tassi
    "DFF": SeriesMeta("Federal Funds Effective Rate", FRB, "D", "public"),
    "DFEDTARU": SeriesMeta("Federal Funds Target Range - Upper Limit", FRB, "D", "public"),
    "DFEDTARL": SeriesMeta("Federal Funds Target Range - Lower Limit", FRB, "D", "public"),
    "FEDTARMDLR": SeriesMeta("Longer Run FOMC Summary of Economic Projections for the Fed Funds Rate, Median", FRB, "Q", "public"),
    "DGS1MO": SeriesMeta("Market Yield on U.S. Treasury Securities at 1-Month Constant Maturity", FRB, "D", "public"),
    "DGS3MO": SeriesMeta("Market Yield on U.S. Treasury Securities at 3-Month Constant Maturity", FRB, "D", "public"),
    "DGS6MO": SeriesMeta("Market Yield on U.S. Treasury Securities at 6-Month Constant Maturity", FRB, "D", "public"),
    "DGS1": SeriesMeta("Market Yield on U.S. Treasury Securities at 1-Year Constant Maturity", FRB, "D", "public"),
    "DGS2": SeriesMeta("Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity", FRB, "D", "public"),
    "DGS3": SeriesMeta("Market Yield on U.S. Treasury Securities at 3-Year Constant Maturity", FRB, "D", "public"),
    "DGS5": SeriesMeta("Market Yield on U.S. Treasury Securities at 5-Year Constant Maturity", FRB, "D", "public"),
    "DGS7": SeriesMeta("Market Yield on U.S. Treasury Securities at 7-Year Constant Maturity", FRB, "D", "public"),
    "DGS10": SeriesMeta("Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity", FRB, "D", "public"),
    "DGS20": SeriesMeta("Market Yield on U.S. Treasury Securities at 20-Year Constant Maturity", FRB, "D", "public"),
    "DGS30": SeriesMeta("Market Yield on U.S. Treasury Securities at 30-Year Constant Maturity", FRB, "D", "public"),
    "T10Y2Y": SeriesMeta("10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity", STL, "D", "citation"),
    "T10Y3M": SeriesMeta("10-Year Treasury Constant Maturity Minus 3-Month Treasury Constant Maturity", STL, "D", "citation"),
    "DFII10": SeriesMeta("Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Inflation-Indexed", FRB, "D", "public"),
    # --- Liquidità
    "WALCL": SeriesMeta("Assets: Total Assets: Total Assets (Less Eliminations from Consolidation): Wednesday Level", FRB, "W", "public"),
    "WDTGAL": SeriesMeta("Liabilities and Capital: Liabilities: Deposits with F.R. Banks, Other Than Reserve Balances: U.S. Treasury, General Account: Wednesday Level", FRB, "W", "public"),
    "RRPONTSYD": SeriesMeta("Overnight Reverse Repurchase Agreements: Treasury Securities Sold by the Federal Reserve in the Temporary Open Market Operations", "Federal Reserve Bank of New York", "D", "citation"),
    "WRESBAL": SeriesMeta("Liabilities and Capital: Other Factors Draining Reserve Balances: Reserve Balances with Federal Reserve Banks: Week Average", FRB, "W", "public"),
    "M2SL": SeriesMeta("M2", FRB, "M", "public"),
    "DTWEXBGS": SeriesMeta("Nominal Broad U.S. Dollar Index", FRB, "D", "public"),
    # --- Housing
    "HOUST": SeriesMeta("New Privately-Owned Housing Units Started: Total Units", CENSUS_HUD, "M", "public"),
    "PERMIT": SeriesMeta("New Privately-Owned Housing Units Authorized in Permit-Issuing Places: Total Units", CENSUS_HUD, "M", "public"),
    "HPIPONM226S": SeriesMeta("Purchase Only House Price Index for the United States", "U.S. Federal Housing Finance Agency", "M", "public"),
    "MORTGAGE30US": SeriesMeta("30-Year Fixed Rate Mortgage Average in the United States", "Freddie Mac", "W", "citation",
                               "Copyright, 2016, Freddie Mac. Reprinted with permission."),
    "MSPUS": SeriesMeta("Median Sales Price of Houses Sold for the United States", CENSUS_HUD, "Q", "public"),
    "RRVRUSQ156N": SeriesMeta("Rental Vacancy Rate in the United States", CENSUS, "Q", "public"),
    # --- Sentiment, credito e stress
    "UMCSENT": SeriesMeta("University of Michigan: Consumer Sentiment", "Surveys of Consumers, University of Michigan", "M", "citation",
                          "Copyright, 2016, Surveys of Consumers, University of Michigan. Reprinted with permission."),
    "PSAVERT": SeriesMeta("Personal Saving Rate", BEA, "M", "public"),
    "BAA10Y": SeriesMeta("Moody's Seasoned Baa Corporate Bond Yield Relative to Yield on 10-Year Treasury Constant Maturity", STL, "D", "citation"),
    "STLFSI4": SeriesMeta("St. Louis Fed Financial Stress Index", STL, "W", "citation"),
    "NFCI": SeriesMeta("Chicago Fed National Financial Conditions Index", "Federal Reserve Bank of Chicago", "W", "citation"),
    "DRTSCILM": SeriesMeta("Net Percentage of Domestic Banks Tightening Standards for Commercial and Industrial Loans to Large and Middle-Market Firms", FRB, "Q", "public"),
    "VIXCLS": SeriesMeta("CBOE Volatility Index: VIX", "Chicago Board Options Exchange", "D", "citation",
                         "Copyright, 2016, Chicago Board Options Exchange, Inc. Reprinted with permission."),
    # --- Ciclo
    "USREC": SeriesMeta("NBER based Recession Indicators for the United States from the Period following the Peak through the Trough", STL, "M", "citation"),
    "RECPROUSM156N": SeriesMeta("Smoothed U.S. Recession Probabilities", "Piger, Jeremy Max; Chauvet, Marcelle", "M", "public"),
}

# Serie rimosse perché i proprietari richiedono un'autorizzazione preventiva
# (tag FRED "copyrighted: pre-approval required"): CSUSHPINSA (S&P Case-Shiller),
# BAMLH0A0HYM2 (ICE BofA High Yield). Sostituite da HPIPONM226S (FHFA) e BAA10Y.

RECESSION_SERIES = "USREC"

# =============================================================================
# SEGNALI (indicatori derivati con soglie)
# =============================================================================


@dataclass(frozen=True)
class Band:
    lo: float | None   # None = -infinito
    hi: float | None   # None = +infinito
    level: str         # ok | warn | bad
    label: str         # lettura breve mostrata accanto al valore


@dataclass
class Signal:
    key: str
    label: str
    series: tuple[str, ...]
    compute: Callable[[dict[str, pd.Series]], pd.Series]
    help: str
    suffix: str = "%"            # unità mostrata dopo il valore
    delta_suffix: str = " pp"    # unità della variazione
    decimals: int = 2
    bands: list[Band] | Callable[[dict[str, pd.Series]], list[Band]] | None = None
    gauge_range: tuple[float, float] | None = None
    target: float | Callable[[dict[str, pd.Series]], float | None] | None = None
    target_label: str = ""
    delta_color: str = "off"     # normal | inverse | off (colore della variazione)
    freq: str | None = None      # se None si usa la frequenza della prima serie
    bands_note: str = ""         # da dove vengono le soglie


def _bands_fixed(*spec) -> list[Band]:
    return [Band(*b) for b in spec]


def _s(sid: str):
    return lambda d: T.clean(d.get(sid))


# --- soglie dinamiche --------------------------------------------------------

def _neutral_rate(d: dict[str, pd.Series]) -> float | None:
    s = T.clean(d.get("FEDTARMDLR"))
    return float(s.iloc[-1]) if len(s) else None


def _fed_bands(d: dict[str, pd.Series]) -> list[Band]:
    n = _neutral_rate(d)
    if n is None:
        return []
    return _bands_fixed(
        (None, n - 1.5, "bad", "Molto accomodante (condizioni eccezionali)"),
        (n - 1.5, n - 0.5, "warn", "Accomodante"),
        (n - 0.5, n + 0.5, "ok", "Vicina al neutrale"),
        (n + 0.5, n + 1.5, "warn", "Restrittiva"),
        (n + 1.5, None, "bad", "Molto restrittiva"),
    )


def _nrou(d: dict[str, pd.Series]) -> float | None:
    return T.asof(d.get("NROU"), pd.Timestamp.today().normalize())


def _unrate_bands(d: dict[str, pd.Series]) -> list[Band]:
    n = _nrou(d)
    if n is None:
        return []
    return _bands_fixed(
        (None, n - 1.0, "warn", "Molto sotto il livello naturale: possibile surriscaldamento"),
        (n - 1.0, n + 0.5, "ok", "Vicina al pieno impiego"),
        (n + 0.5, n + 1.5, "warn", "Sopra il livello naturale"),
        (n + 1.5, None, "bad", "Debolezza marcata"),
    )


def _real_ff_gap(d: dict[str, pd.Series]) -> pd.Series:
    ff = T.clean(d.get("DFF"))
    core = T.yoy(d.get("PCEPILFE"))
    neutral = T.clean(d.get("FEDTARMDLR"))
    if ff.empty or core.empty or neutral.empty:
        return pd.Series(dtype=float)
    monthly_ff = ff.resample("MS").mean()
    idx = core.index
    real = T.align_asof(idx, monthly_ff) - core
    rstar = T.align_asof(idx, neutral) - 2.0
    return (real - rstar).dropna()


def _openings_ratio(d: dict[str, pd.Series]) -> pd.Series:
    jo = T.clean(d.get("JTSJOL"))
    un = T.clean(d.get("UNEMPLOY"))
    if jo.empty or un.empty:
        return pd.Series(dtype=float)
    return (jo / un.reindex(jo.index)).dropna()


def _netliq(d: dict[str, pd.Series]) -> pd.Series:
    return T.net_liquidity(d.get("WALCL"), d.get("WDTGAL"), d.get("RRPONTSYD"))


def _netliq_13w(d: dict[str, pd.Series]) -> pd.Series:
    s = _netliq(d)
    return ((s / s.shift(13) - 1.0) * 100.0).dropna()


# --- testi ricorrenti --------------------------------------------------------

_TARGET_NOTE = ("L'obiettivo della Fed è un'inflazione del 2% misurata sul PCE; il CPI tende a "
                "correre 0,3-0,5 punti sopra il PCE, per questo la fascia verde del CPI è più alta.")

SIGNALS: dict[str, Signal] = {}


def _add(sig: Signal) -> None:
    SIGNALS[sig.key] = sig


# ----------------------------------------------------------------- INFLAZIONE
_add(Signal(
    "cpi_yoy", "CPI (inflazione, a/a)", ("CPIAUCSL",), lambda d: T.yoy(d.get("CPIAUCSL")),
    "Variazione dei prezzi al consumo negli ultimi 12 mesi (paniere completo, incluse "
    "energia e alimentari). È il dato di inflazione più citato. " + _TARGET_NOTE,
    bands=_bands_fixed((None, 0.0, "bad", "Deflazione"), (0.0, 1.5, "warn", "Sotto l'obiettivo"),
                       (1.5, 3.0, "ok", "Compatibile con l'obiettivo"), (3.0, 4.0, "warn", "Sopra l'obiettivo"),
                       (4.0, None, "bad", "Molto sopra l'obiettivo")),
    gauge_range=(-2, 10), delta_color="inverse",
    bands_note="Ancorate all'obiettivo Fed del 2% (PCE) più il divario medio CPI-PCE.",
))
_add(Signal(
    "core_cpi_yoy", "Core CPI (a/a)", ("CPILFESL",), lambda d: T.yoy(d.get("CPILFESL")),
    "Inflazione al consumo esclusi alimentari ed energia, le componenti più volatili: "
    "misura la tendenza di fondo dei prezzi. " + _TARGET_NOTE,
    bands=_bands_fixed((None, 0.5, "bad", "Molto bassa"), (0.5, 1.5, "warn", "Sotto l'obiettivo"),
                       (1.5, 3.0, "ok", "Compatibile con l'obiettivo"), (3.0, 4.0, "warn", "Sopra l'obiettivo"),
                       (4.0, None, "bad", "Molto sopra l'obiettivo")),
    gauge_range=(0, 8), delta_color="inverse",
    bands_note="Ancorate all'obiettivo Fed del 2% (PCE) più il divario medio CPI-PCE.",
))
_add(Signal(
    "pce_yoy", "PCE (a/a)", ("PCEPI",), lambda d: T.yoy(d.get("PCEPI")),
    "Indice dei prezzi della spesa per consumi (BEA): copre più beni e servizi del CPI e "
    "aggiorna i pesi quando i consumatori sostituiscono i prodotti. È la misura su cui "
    "la Fed fissa l'obiettivo del 2%.",
    bands=_bands_fixed((None, 0.0, "bad", "Deflazione"), (0.0, 1.5, "warn", "Sotto l'obiettivo"),
                       (1.5, 2.5, "ok", "In linea con l'obiettivo"), (2.5, 3.5, "warn", "Sopra l'obiettivo"),
                       (3.5, None, "bad", "Molto sopra l'obiettivo")),
    gauge_range=(-1, 8), target=2.0, target_label="Obiettivo Fed 2%", delta_color="inverse",
    bands_note="Fascia verde: obiettivo Fed 2% ± 0,5 punti.",
))
_add(Signal(
    "core_pce_yoy", "Core PCE (a/a)", ("PCEPILFE",), lambda d: T.yoy(d.get("PCEPILFE")),
    "Inflazione PCE esclusi alimentari ed energia: è l'indicatore preferito dalla Fed per "
    "giudicare se l'inflazione sta convergendo verso l'obiettivo del 2%.",
    bands=_bands_fixed((None, 1.0, "bad", "Troppo bassa"), (1.0, 1.5, "warn", "Sotto l'obiettivo"),
                       (1.5, 2.5, "ok", "In linea con l'obiettivo"), (2.5, 3.5, "warn", "Sopra l'obiettivo"),
                       (3.5, None, "bad", "Molto sopra l'obiettivo")),
    gauge_range=(0, 7), target=2.0, target_label="Obiettivo Fed 2%", delta_color="inverse",
    bands_note="Fascia verde: obiettivo Fed 2% ± 0,5 punti.",
))
for _sid, _name, _m in (("PCEPILFE", "Core PCE", 3), ("PCEPILFE", "Core PCE", 6),
                        ("CPILFESL", "Core CPI", 3), ("CPILFESL", "Core CPI", 6)):
    _base = SIGNALS["core_pce_yoy" if _sid == "PCEPILFE" else "core_cpi_yoy"]
    _add(Signal(
        f"{'core_pce' if _sid == 'PCEPILFE' else 'core_cpi'}_{_m}m", f"{_name} annualizzato {_m} mesi",
        (_sid,), (lambda d, sid=_sid, m=_m: T.annualized(d.get(sid), m)),
        f"Variazione degli ultimi {_m} mesi riportata su base annua: mostra la direzione "
        "recente dell'inflazione prima che emerga nel dato a 12 mesi. È più rumoroso. "
        "Usa le stesse soglie del dato annuale.",
        bands=_base.bands, gauge_range=_base.gauge_range, target=_base.target,
        target_label=_base.target_label, delta_color="inverse", bands_note=_base.bands_note,
    ))
_add(Signal(
    "ppi_yoy", "PPI domanda finale (a/a)", ("PPIFIS",), lambda d: T.yoy(d.get("PPIFIS")),
    "Prezzi alla produzione (domanda finale): misurano i prezzi incassati dalle imprese. "
    "Spesso anticipano le pressioni sui prezzi al consumo.",
    bands=_bands_fixed((None, -1.0, "bad", "Deflazione alla produzione"), (-1.0, 1.0, "warn", "Pressioni deboli"),
                       (1.0, 3.5, "ok", "Pressioni moderate"), (3.5, 6.0, "warn", "Pressioni elevate"),
                       (6.0, None, "bad", "Pressioni molto elevate")),
    gauge_range=(-5, 12), delta_color="inverse",
    bands_note="Storia disponibile dal 2010: mediana 2,1%, 90° percentile 6,5%.",
))
_add(Signal(
    "be5", "Breakeven inflazione 5 anni", ("T5YIE",), _s("T5YIE"),
    "Inflazione media attesa dal mercato nei prossimi 5 anni: differenza tra il rendimento "
    "del Treasury nominale e quello indicizzato all'inflazione (TIPS). È misurata sul CPI, "
    "quindi un valore intorno al 2,2-2,5% è coerente con l'obiettivo Fed del 2% sul PCE.",
    bands=_bands_fixed((None, 1.5, "bad", "Rischio disinflazione"), (1.5, 1.8, "warn", "Sotto l'obiettivo"),
                       (1.8, 2.6, "ok", "Aspettative ancorate"), (2.6, 3.0, "warn", "Aspettative in salita"),
                       (3.0, None, "bad", "Aspettative disancorate")),
    gauge_range=(0, 4), delta_color="inverse",
    bands_note="Fascia verde coerente con il 2% sul PCE (breakeven calcolato sul CPI).",
))
_add(Signal(
    "be10", "Breakeven inflazione 10 anni", ("T10YIE",), _s("T10YIE"),
    "Inflazione media attesa dal mercato nei prossimi 10 anni (Treasury nominale meno TIPS). "
    "Misurata sul CPI.",
    bands=SIGNALS["be5"].bands, gauge_range=(0, 4), delta_color="inverse",
    bands_note=SIGNALS["be5"].bands_note,
))
_add(Signal(
    "shelter_yoy", "CPI abitazione (a/a)", ("CUSR0000SAH1",), lambda d: T.yoy(d.get("CUSR0000SAH1")),
    "Componente abitazione del CPI (affitti e affitti figurativi dei proprietari): pesa circa un "
    "terzo del CPI e segue gli affitti di mercato con 12-18 mesi di ritardo.",
))
_add(Signal(
    "supercore_yoy", "CPI servizi esclusa abitazione (a/a)", ("CUSR0000SASL2RS",),
    lambda d: T.yoy(d.get("CUSR0000SASL2RS")),
    "Il cosiddetto 'supercore': prezzi dei servizi escluse le abitazioni. Dipende molto dai "
    "salari ed è seguito dalla Fed come misura dell'inflazione più persistente.",
))
_add(Signal(
    "sticky_core", "Sticky core CPI (a/a)", ("CORESTICKM159SFRBATL",), _s("CORESTICKM159SFRBATL"),
    "Indice dell'Atlanta Fed costruito con i prezzi che cambiano raramente (affitti, "
    "assicurazioni, servizi): incorpora le aspettative di inflazione e cambia direzione lentamente.",
))

# --------------------------------------------------------------------- LAVORO
_add(Signal(
    "unrate", "Tasso di disoccupazione", ("UNRATE", "NROU"), _s("UNRATE"),
    "Percentuale della forza lavoro senza impiego e in cerca di lavoro (U-3). Il riferimento è "
    "il tasso 'naturale' stimato dal CBO (NROU): sotto di esso il mercato del lavoro è tirato, "
    "sopra ci sono risorse inutilizzate.",
    bands=_unrate_bands, gauge_range=(2, 12), target=_nrou, target_label="Tasso naturale (CBO)",
    delta_color="inverse",
    bands_note="Ancorate al tasso naturale di disoccupazione stimato dal CBO (serie NROU).",
))
_add(Signal(
    "u6", "Disoccupazione allargata U-6", ("U6RATE",), _s("U6RATE"),
    "Misura ampia di sottoutilizzo: disoccupati, scoraggiati e lavoratori part-time che "
    "vorrebbero un impiego a tempo pieno. Corre circa 3,5-4 punti sopra la U-3.",
    bands=_bands_fixed((None, 9.0, "ok", "Sottoutilizzo contenuto"), (9.0, 11.0, "warn", "Sottoutilizzo in aumento"),
                       (11.0, None, "bad", "Sottoutilizzo elevato")),
    gauge_range=(5, 20), delta_color="inverse",
    bands_note="Equivalenti delle soglie della U-3 (U-6 ≈ U-3 + 4 punti).",
))
_add(Signal(
    "epop_prime", "Occupati 25-54 anni (% popolazione)", ("LNS12300060",), _s("LNS12300060"),
    "Quota di persone tra 25 e 54 anni che hanno un lavoro. È meno influenzata "
    "dall'invecchiamento della popolazione rispetto al tasso di partecipazione e per questo "
    "è una buona misura ciclica della salute del mercato del lavoro.",
    bands=_bands_fixed((None, 77.5, "bad", "Occupazione debole"), (77.5, 79.5, "warn", "Nella media"),
                       (79.5, None, "ok", "Occupazione elevata")),
    gauge_range=(70, 84), delta_color="normal",
    bands_note="Percentili storici dal 1990: 25° = 78,0%, mediana = 79,3%.",
))
_add(Signal(
    "civpart", "Tasso di partecipazione", ("CIVPART",), _s("CIVPART"),
    "Percentuale della popolazione in età lavorativa che lavora o cerca lavoro. È in calo "
    "strutturale per l'invecchiamento della popolazione: per il ciclo guarda agli occupati 25-54 anni.",
    delta_color="normal",
))
_add(Signal(
    "payrolls_mom", "Nuovi posti di lavoro (mese)", ("PAYEMS",),
    lambda d: T.diff(d.get("PAYEMS"), monthly_calendar=True),
    "Variazione mensile degli occupati non agricoli (Nonfarm Payrolls), in migliaia. "
    "Il dato del mese è rumoroso e viene rivisto: conta la media degli ultimi 3 mesi.",
    suffix=" mila", delta_suffix=" mila", decimals=0, delta_color="normal",
))
_add(Signal(
    "payrolls_3m", "Nuovi posti di lavoro (media 3 mesi)", ("PAYEMS",),
    lambda d: T.diff(d.get("PAYEMS"), monthly_calendar=True).asfreq("MS").rolling(3).mean().dropna(),
    "Media degli ultimi 3 mesi della variazione degli occupati non agricoli, in migliaia. "
    "Il ritmo di 'pareggio' che tiene stabile la disoccupazione dipende dalla crescita "
    "della forza lavoro ed è sceso rispetto al passato: le soglie sono indicative.",
    suffix=" mila", delta_suffix=" mila", decimals=0,
    bands=_bands_fixed((None, 0.0, "bad", "Occupazione in calo"), (0.0, 50.0, "warn", "Crescita debole"),
                       (50.0, None, "ok", "Crescita in corso")),
    gauge_range=(-200, 400), delta_color="normal",
    bands_note="Soglie indicative: sotto zero si perdono posti di lavoro.",
))
_add(Signal(
    "claims", "Richieste iniziali di sussidio", ("ICSA",), lambda d: T.scale(d.get("ICSA"), 1 / 1000),
    "Nuove domande settimanali di sussidio di disoccupazione, in migliaia: è il dato più "
    "tempestivo sui licenziamenti.",
    suffix=" mila", delta_suffix=" mila", decimals=0, delta_color="inverse",
))
_add(Signal(
    "claims_4w", "Richieste iniziali (media 4 settimane)", ("IC4WSA",), lambda d: T.scale(d.get("IC4WSA"), 1 / 1000),
    "Media mobile di 4 settimane delle nuove richieste di sussidio, in migliaia: filtra il "
    "rumore settimanale.",
    suffix=" mila", delta_suffix=" mila", decimals=0, delta_color="inverse",
))
_add(Signal(
    "claims_rise", "Richieste di sussidio vs minimo 52 settimane", ("ICSA",),
    lambda d: T.pct_above_rolling_min(T.rolling_mean(d.get("ICSA"), 4), 52),
    "Di quanto la media a 4 settimane delle nuove richieste di sussidio è sopra il minimo "
    "dell'ultimo anno. Rialzi del 20% o più hanno accompagnato l'avvio delle recessioni, ma "
    "ci sono stati falsi allarmi (es. 2022-2023).",
    suffix="%", delta_suffix=" pp", decimals=1,
    bands=_bands_fixed((None, 10.0, "ok", "Licenziamenti stabili"), (10.0, 20.0, "warn", "Licenziamenti in aumento"),
                       (20.0, None, "bad", "Aumento marcato")),
    gauge_range=(0, 40), delta_color="inverse",
    bands_note="Dal 1990: mediana 4%, 90° percentile 27%; media nelle recessioni oltre il 100%.",
))
_add(Signal(
    "ccsa", "Richieste continuative di sussidio", ("CCSA",), lambda d: T.scale(d.get("CCSA"), 1 / 1e6),
    "Persone che continuano a ricevere il sussidio, in milioni: se salgono, chi perde il "
    "lavoro fatica a trovarne un altro.",
    suffix=" mln", delta_suffix=" mln", decimals=2, delta_color="inverse",
))
_add(Signal(
    "sahm", "Regola di Sahm", ("SAHMREALTIME",), _s("SAHMREALTIME"),
    "Differenza tra la media a 3 mesi della disoccupazione e il suo minimo dei 12 mesi "
    "precedenti. Quando supera 0,5 punti la regola si 'attiva': storicamente è successo "
    "all'inizio delle recessioni, ma nel 2024 si è attivata senza recessione.",
    suffix=" pp", delta_suffix=" pp", decimals=2,
    bands=_bands_fixed((None, 0.3, "ok", "Nessun segnale"), (0.3, 0.5, "warn", "Vicina alla soglia"),
                       (0.5, None, "bad", "Regola attivata")),
    gauge_range=(-0.5, 1.5), target=0.5, target_label="Soglia 0,5", delta_color="inverse",
    bands_note="Soglia di attivazione 0,5 punti (Sahm, 2019).",
))
_add(Signal(
    "ahe_yoy", "Salari orari (a/a)", ("CES0500000003",), lambda d: T.yoy(d.get("CES0500000003")),
    "Crescita annua della retribuzione oraria media nel settore privato. Con una produttività "
    "intorno all'1-1,5% annuo, salari tra 3 e 3,5% sono compatibili con inflazione al 2%.",
    bands=_bands_fixed((None, 1.5, "bad", "Salari molto deboli"), (1.5, 2.5, "warn", "Crescita debole"),
                       (2.5, 3.75, "ok", "Compatibile con inflazione al 2%"), (3.75, 4.75, "warn", "Pressioni salariali"),
                       (4.75, None, "bad", "Pressioni salariali forti")),
    gauge_range=(0, 8), delta_color="off",
    bands_note="Obiettivo inflazione 2% + produttività 1-1,5%.",
))
_add(Signal(
    "openings_ratio", "Posti vacanti per disoccupato", ("JTSJOL", "UNEMPLOY"), _openings_ratio,
    "Numero di posti di lavoro vacanti per ogni disoccupato (JOLTS). Sopra 1 ci sono più "
    "posizioni aperte che persone in cerca: mercato tirato, pressioni salariali.",
    suffix="", delta_suffix="", decimals=2,
    bands=_bands_fixed((None, 0.5, "bad", "Molta manodopera inutilizzata"), (0.5, 0.8, "warn", "Mercato debole"),
                       (0.8, 1.4, "ok", "Mercato equilibrato"), (1.4, None, "warn", "Mercato surriscaldato")),
    gauge_range=(0, 2.2), delta_color="off",
    bands_note="Dal 2001: mediana 0,64, 75° percentile 1,0; picco 2,0 nel 2022.",
))
_add(Signal(
    "quits", "Tasso di dimissioni", ("JTSQUR",), _s("JTSQUR"),
    "Percentuale di lavoratori che si dimettono ogni mese: cresce quando è facile trovare un "
    "nuovo impiego, scende quando i lavoratori sono prudenti.",
    delta_color="normal",
))

# ------------------------------------------------------------------- CRESCITA
_GROWTH_BANDS = _bands_fixed((None, 0.0, "bad", "Contrazione"), (0.0, 1.5, "warn", "Crescita debole"),
                             (1.5, None, "ok", "Crescita solida"))
_add(Signal(
    "gdp_qoq", "PIL reale (trim. annualizzato)", ("A191RL1Q225SBEA",), _s("A191RL1Q225SBEA"),
    "Crescita del prodotto interno lordo reale nel trimestre, riportata su base annua (come "
    "la comunica il BEA). Il potenziale di lungo periodo degli USA è intorno al 2%.",
    bands=_GROWTH_BANDS, gauge_range=(-4, 8), delta_color="normal",
    bands_note="Sotto zero contrazione; fino a 1,5% crescita inferiore al potenziale.",
))
_add(Signal(
    "gdpnow", "GDPNow (stima PIL trimestre in corso)", ("GDPNOW",), _s("GDPNOW"),
    "Stima in tempo reale della crescita del PIL del trimestre in corso, calcolata "
    "dall'Atlanta Fed con i dati via via pubblicati. Non è una previsione ufficiale e può "
    "cambiare molto nel corso del trimestre.",
    bands=_GROWTH_BANDS, gauge_range=(-4, 8), delta_color="normal",
    bands_note="Stesse soglie del PIL reale.",
))
_add(Signal(
    "ip_yoy", "Produzione industriale (a/a)", ("INDPRO",), lambda d: T.yoy(d.get("INDPRO")),
    "Variazione annua della produzione di industria, miniere e utility. È ciclica e "
    "sensibile a tassi, dollaro ed energia.",
    bands=_bands_fixed((None, -1.0, "bad", "Contrazione"), (-1.0, 1.0, "warn", "Stagnazione"),
                       (1.0, None, "ok", "Espansione")),
    gauge_range=(-10, 10), delta_color="normal",
    bands_note="Dal 1990: mediana 2,2%, media nelle recessioni -5%.",
))
_add(Signal(
    "tcu", "Utilizzo della capacità produttiva", ("TCU",), _s("TCU"),
    "Percentuale della capacità produttiva industriale effettivamente utilizzata. Valori "
    "bassi indicano capacità inutilizzata; sopra l'82% emergono pressioni sui prezzi.",
    bands=_bands_fixed((None, 74.0, "bad", "Molta capacità inutilizzata"), (74.0, 76.0, "warn", "Sotto la media"),
                       (76.0, 82.0, "ok", "Normale"), (82.0, None, "warn", "Vicino ai limiti")),
    gauge_range=(64, 88), delta_color="normal",
    bands_note="Dal 1990: 25° percentile 76,2%, 90° percentile 83,3%.",
))
_add(Signal(
    "retail_real_yoy", "Vendite al dettaglio reali (a/a)", ("RRSFS",), lambda d: T.yoy(d.get("RRSFS")),
    "Vendite al dettaglio e ristorazione corrette per l'inflazione, variazione annua: "
    "misura tempestiva dei consumi delle famiglie.",
    bands=_GROWTH_BANDS, gauge_range=(-10, 10), delta_color="normal",
    bands_note="Sotto zero i consumi reali si contraggono.",
))
_add(Signal(
    "pce_real_yoy", "Consumi reali (a/a)", ("PCEC96",), lambda d: T.yoy(d.get("PCEC96")),
    "Spesa per consumi personali corretta per l'inflazione, variazione annua: i consumi "
    "pesano circa il 68% del PIL USA.",
    bands=_GROWTH_BANDS, gauge_range=(-6, 8), delta_color="normal",
    bands_note="Sotto zero i consumi reali si contraggono.",
))
_add(Signal(
    "income_real_yoy", "Reddito reale esclusi trasferimenti (a/a)", ("W875RX1",),
    lambda d: T.yoy(d.get("W875RX1")),
    "Reddito personale reale esclusi i sussidi pubblici, variazione annua: è uno degli "
    "indicatori usati dal NBER per datare le recessioni.",
    bands=_GROWTH_BANDS, gauge_range=(-6, 8), delta_color="normal",
    bands_note="Dal 1990: mediana 2,8%, media nelle recessioni -0,8%.",
))

# ---------------------------------------------------------------------- TASSI
_add(Signal(
    "fedfunds", "Fed Funds effettivo", ("DFF", "FEDTARMDLR"), _s("DFF"),
    "Tasso overnight a cui le banche si prestano le riserve: è lo strumento principale della "
    "Fed. I colori misurano la distanza dal tasso 'neutrale' di lungo periodo indicato dal "
    "FOMC (mediana delle proiezioni SEP): sopra il neutrale la politica frena l'economia, "
    "sotto la sostiene. Il neutrale FOMC presuppone inflazione al 2%: con inflazione più alta "
    "la politica è meno restrittiva di quanto sembri (vedi il tasso reale).",
    bands=_fed_bands, gauge_range=(0, 8), target=_neutral_rate, target_label="Neutrale FOMC",
    delta_color="off",
    bands_note="Neutrale = mediana FOMC di lungo periodo (FEDTARMDLR) ± 0,5 / 1,5 punti.",
))
_add(Signal(
    "real_ff_gap", "Fed Funds reale vs neutrale reale", ("DFF", "PCEPILFE", "FEDTARMDLR"), _real_ff_gap,
    "Fed Funds meno inflazione core PCE annua, confrontato con il tasso neutrale reale "
    "(neutrale FOMC meno 2%). Positivo = politica restrittiva in termini reali.",
    suffix=" pp", delta_suffix=" pp",
    bands=_bands_fixed((None, -1.5, "bad", "Molto accomodante"), (-1.5, -0.5, "warn", "Accomodante"),
                       (-0.5, 0.5, "ok", "Vicina al neutrale"), (0.5, 1.5, "warn", "Restrittiva"),
                       (1.5, None, "bad", "Molto restrittiva")),
    gauge_range=(-5, 5), delta_color="off", freq="M",
    bands_note="Stesse distanze usate per il Fed Funds nominale.",
))
_add(Signal(
    "t10y2y", "Curva 10 anni - 2 anni", ("T10Y2Y",), _s("T10Y2Y"),
    "Differenza tra il rendimento del Treasury a 10 anni e quello a 2 anni. Quando è negativa "
    "(curva invertita) il mercato si aspetta tagli dei tassi: è successo prima di quasi tutte "
    "le recessioni dal 1976, ma con anticipi variabili (6-24 mesi) e almeno un falso segnale "
    "lungo (2022-2024). La recessione è spesso iniziata quando la curva tornava positiva.",
    bands=_bands_fixed((None, 0.0, "bad", "Invertita"), (0.0, 0.5, "warn", "Piatta"),
                       (0.5, None, "ok", "Inclinata positivamente")),
    gauge_range=(-3, 3), target=0.0, target_label="Zero", delta_color="normal", suffix=" pp",
    bands_note="Inversione sotto zero; sotto 0,5 punti la curva è considerata piatta.",
))
_add(Signal(
    "t10y3m", "Curva 10 anni - 3 mesi", ("T10Y3M",), _s("T10Y3M"),
    "Differenza tra il rendimento del Treasury a 10 anni e quello a 3 mesi: è la versione "
    "della curva preferita da molti studi della Fed come indicatore di recessione.",
    bands=SIGNALS["t10y2y"].bands, gauge_range=(-3, 4), target=0.0, target_label="Zero",
    delta_color="normal", suffix=" pp",
    bands_note=SIGNALS["t10y2y"].bands_note,
))
_add(Signal(
    "real10y", "Tasso reale 10 anni (TIPS)", ("DFII10",), _s("DFII10"),
    "Rendimento del Treasury a 10 anni indicizzato all'inflazione: il costo del denaro al "
    "netto dell'inflazione attesa. Valori alti rendono più restrittive le condizioni "
    "finanziarie per imprese, famiglie e valutazioni azionarie.",
    bands=_bands_fixed((None, 0.0, "warn", "Negativo: condizioni molto espansive"), (0.0, 1.5, "ok", "Moderato"),
                       (1.5, 2.5, "warn", "Elevato"), (2.5, None, "bad", "Molto elevato")),
    gauge_range=(-2, 4), delta_color="inverse",
    bands_note="Dal 2003: mediana 1,1%, 90° percentile 2,2%.",
))
_add(Signal(
    "dgs2", "Treasury 2 anni", ("DGS2",), _s("DGS2"),
    "Rendimento del Treasury a 2 anni: riflette soprattutto le attese sul percorso dei tassi Fed.",
))
_add(Signal(
    "dgs10", "Treasury 10 anni", ("DGS10",), _s("DGS10"),
    "Rendimento del Treasury a 10 anni: riferimento per mutui e valutazioni; riflette attese "
    "su crescita, inflazione e premio a termine.",
))

# ----------------------------------------------------------------- LIQUIDITA'
_add(Signal(
    "netliq", "Liquidità netta Fed", ("WALCL", "WDTGAL", "RRPONTSYD"), _netliq,
    "Attivo di bilancio della Fed meno il conto del Tesoro presso la Fed (TGA) meno i reverse "
    "repo overnight, in miliardi di dollari. È una stima della liquidità disponibile nel "
    "sistema finanziario; il legame con i mercati è dibattuto e non stabile nel tempo.",
    suffix=" mld $", delta_suffix=" mld $", decimals=0, delta_color="normal", freq="W",
))
_add(Signal(
    "netliq_13w", "Liquidità netta: variazione 13 settimane", ("WALCL", "WDTGAL", "RRPONTSYD"), _netliq_13w,
    "Variazione percentuale della liquidità netta Fed negli ultimi 3 mesi (13 settimane).",
    suffix="%", delta_suffix=" pp", decimals=1,
    bands=_bands_fixed((None, -3.0, "bad", "Drenaggio di liquidità"), (-3.0, 0.0, "warn", "Liquidità in calo"),
                       (0.0, None, "ok", "Liquidità stabile o in aumento")),
    gauge_range=(-15, 15), delta_color="normal", freq="W",
    bands_note="Dal 2003: 25° percentile -1,3%, 5° percentile -4,8%.",
))
_add(Signal(
    "walcl", "Bilancio Fed (totale attivo)", ("WALCL",), lambda d: T.scale(d.get("WALCL"), 1 / 1000),
    "Totale attivo della Federal Reserve in miliardi di dollari: sale con gli acquisti di "
    "titoli (QE), scende con la riduzione del bilancio (QT).",
    suffix=" mld $", delta_suffix=" mld $", decimals=0, delta_color="off",
))
_add(Signal(
    "reserves", "Riserve bancarie", ("WRESBAL",), lambda d: T.scale(d.get("WRESBAL"), 1 / 1000),
    "Depositi delle banche presso la Fed, in miliardi di dollari: la liquidità di base del "
    "sistema bancario.",
    suffix=" mld $", delta_suffix=" mld $", decimals=0, delta_color="off",
))
_add(Signal(
    "tga", "Conto del Tesoro (TGA)", ("WDTGAL",), lambda d: T.scale(d.get("WDTGAL"), 1 / 1000),
    "Liquidità del Tesoro USA depositata presso la Fed, in miliardi di dollari: quando sale "
    "drena liquidità dal sistema, quando scende la restituisce.",
    suffix=" mld $", delta_suffix=" mld $", decimals=0, delta_color="off",
))
_add(Signal(
    "rrp", "Reverse repo overnight", ("RRPONTSYD",), _s("RRPONTSYD"),
    "Liquidità parcheggiata da fondi monetari e altri operatori presso la Fed, in miliardi di "
    "dollari: è liquidità 'ferma' che può tornare nel sistema.",
    suffix=" mld $", delta_suffix=" mld $", decimals=1, delta_color="off",
))
_add(Signal(
    "m2_yoy", "Moneta M2 (a/a)", ("M2SL",), lambda d: T.yoy(d.get("M2SL")),
    "Crescita annua dell'aggregato monetario M2 (contante, depositi, fondi monetari).",
    bands=_bands_fixed((None, 0.0, "bad", "Contrazione"), (0.0, 3.0, "warn", "Crescita debole"),
                       (3.0, 8.0, "ok", "Crescita normale"), (8.0, 12.0, "warn", "Crescita sostenuta"),
                       (12.0, None, "bad", "Espansione eccessiva")),
    gauge_range=(-6, 20), delta_color="off",
    bands_note="Dal 1990: 25° percentile 3,9%, mediana 5,6%, 90° percentile 9,3%.",
))
_add(Signal(
    "dollar_yoy", "Dollaro (indice ampio, a/a)", ("DTWEXBGS",), lambda d: T.yoy(d.get("DTWEXBGS")),
    "Variazione annua del dollaro contro un paniere ampio di valute (indice Fed). Un dollaro "
    "forte rende più restrittive le condizioni finanziarie globali.",
    delta_color="off",
))

# -------------------------------------------------------------------- HOUSING
_HOUSING_BANDS = _bands_fixed((None, 1.0, "bad", "Attività molto debole"), (1.0, 1.3, "warn", "Sotto la media"),
                              (1.3, 1.8, "ok", "Nella norma"), (1.8, None, "warn", "Possibile eccesso"))
_add(Signal(
    "houst", "Nuovi cantieri residenziali", ("HOUST",), lambda d: T.scale(d.get("HOUST"), 1 / 1000),
    "Abitazioni iniziate nel mese, in milioni su base annua (SAAR). Il settore immobiliare "
    "anticipa spesso il ciclo economico.",
    suffix=" mln", delta_suffix=" mln", decimals=2,
    bands=_HOUSING_BANDS, gauge_range=(0.4, 2.4), delta_color="normal",
    bands_note="Mediana dal 1990: 1,35 mln; sotto 1 mln solo in recessione.",
))
_add(Signal(
    "permit", "Permessi di costruzione", ("PERMIT",), lambda d: T.scale(d.get("PERMIT"), 1 / 1000),
    "Permessi di costruzione rilasciati, in milioni su base annua: anticipano i cantieri di "
    "1-2 mesi.",
    suffix=" mln", delta_suffix=" mln", decimals=2,
    bands=_HOUSING_BANDS, gauge_range=(0.4, 2.4), delta_color="normal",
    bands_note="Stesse soglie dei cantieri.",
))
_add(Signal(
    "hpi_yoy", "Prezzi delle case FHFA (a/a)", ("HPIPONM226S",), lambda d: T.yoy(d.get("HPIPONM226S")),
    "Variazione annua dei prezzi delle abitazioni unifamiliari (indice FHFA, sole compravendite, "
    "destagionalizzato). Sostituisce il Case-Shiller, i cui dati richiedono un'autorizzazione "
    "preventiva di S&P per l'uso pubblico.",
    bands=_bands_fixed((None, 0.0, "bad", "Prezzi in calo"), (0.0, 2.0, "warn", "Crescita debole"),
                       (2.0, 7.0, "ok", "Crescita sostenibile"), (7.0, 10.0, "warn", "Crescita sostenuta"),
                       (10.0, None, "bad", "Surriscaldamento")),
    gauge_range=(-10, 20), delta_color="off",
    bands_note="Dal 1992: mediana 5%, 90° percentile 9,9%.",
))
_add(Signal(
    "mortgage30", "Mutuo fisso 30 anni", ("MORTGAGE30US",), _s("MORTGAGE30US"),
    "Tasso medio dei mutui a tasso fisso a 30 anni (sondaggio settimanale Freddie Mac): "
    "determina la rata e quindi l'accessibilità delle case.",
    bands=_bands_fixed((None, 5.0, "ok", "Favorevole"), (5.0, 7.0, "warn", "Accessibilità sotto pressione"),
                       (7.0, None, "bad", "Forte stress sull'accessibilità")),
    gauge_range=(2, 10), delta_color="inverse",
    bands_note="Dal 2000: mediana 5,25%, 90° percentile 6,9%.",
))
_add(Signal(
    "mspus", "Prezzo mediano case nuove vendute", ("MSPUS",), lambda d: T.scale(d.get("MSPUS"), 1 / 1000),
    "Prezzo mediano di vendita delle case nuove, in migliaia di dollari (trimestrale).",
    suffix=" mila $", delta_suffix=" mila $", decimals=0, delta_color="off",
))
_add(Signal(
    "rental_vac", "Sfitto negli affitti", ("RRVRUSQ156N",), _s("RRVRUSQ156N"),
    "Percentuale di abitazioni in affitto vuote. Uno sfitto basso spinge in alto gli affitti "
    "e, con ritardo, la componente abitazione del CPI.",
    bands=_bands_fixed((None, 6.0, "warn", "Mercato teso: affitti sotto pressione"), (6.0, 9.0, "ok", "Equilibrato"),
                       (9.0, None, "warn", "Eccesso di offerta")),
    gauge_range=(4, 12), delta_color="off",
    bands_note="Dal 1990: 25° percentile 7,0%, mediana 7,7%, 75° percentile 9,2%.",
))

# -------------------------------------------------- SENTIMENT, CREDITO, STRESS
_add(Signal(
    "umcsent", "Fiducia consumatori (Michigan)", ("UMCSENT",), _s("UMCSENT"),
    "Indice di fiducia dei consumatori dell'Università del Michigan (1966 = 100). Riflette "
    "inflazione percepita, redditi e aspettative; non sempre si traduce in minori consumi.",
    suffix="", delta_suffix="", decimals=1,
    bands=_bands_fixed((None, 65.0, "bad", "Pessimismo marcato"), (65.0, 85.0, "warn", "Sotto la media storica"),
                       (85.0, None, "ok", "Fiducia nella norma")),
    gauge_range=(40, 120), delta_color="normal",
    bands_note="Dal 1978: 10° percentile 64, mediana 87.",
))
_add(Signal(
    "psavert", "Tasso di risparmio", ("PSAVERT",), _s("PSAVERT"),
    "Quota del reddito disponibile che le famiglie risparmiano. Un risparmio basso lascia "
    "poco margine contro gli shock; uno alto segnala prudenza e consumi frenati.",
    bands=_bands_fixed((None, 3.5, "bad", "Cuscinetto molto sottile"), (3.5, 5.0, "warn", "Risparmio basso"),
                       (5.0, 8.0, "ok", "Nella norma"), (8.0, None, "warn", "Risparmio precauzionale")),
    gauge_range=(0, 15), delta_color="off",
    bands_note="Dal 1990: 10° percentile 3,3%, mediana 5,9%, 90° percentile 8,7%.",
))
_add(Signal(
    "baa10y", "Spread creditizio Baa - Treasury 10A", ("BAA10Y",), _s("BAA10Y"),
    "Differenza tra il rendimento delle obbligazioni societarie con rating Baa (Moody's) e il "
    "Treasury a 10 anni: è il premio chiesto per il rischio di credito. Si allarga quando i "
    "mercati temono insolvenze. Sostituisce lo spread High Yield ICE BofA, i cui dati "
    "richiedono un'autorizzazione preventiva per l'uso pubblico.",
    bands=_bands_fixed((None, 2.5, "ok", "Credito disteso"), (2.5, 3.25, "warn", "Premio al rischio in aumento"),
                       (3.25, None, "bad", "Stress sul credito")),
    gauge_range=(0.5, 6.5), delta_color="inverse", suffix=" pp",
    bands_note="Dal 1986: mediana 2,1, 75° percentile 2,7, media nelle recessioni 3,4.",
))
_add(Signal(
    "stlfsi", "Indice di stress finanziario (St. Louis Fed)", ("STLFSI4",), _s("STLFSI4"),
    "Indice composito di 18 variabili finanziarie (tassi, spread, volatilità). Zero = livello "
    "medio di stress; valori positivi = stress superiore alla media.",
    suffix="", delta_suffix="", decimals=2,
    bands=_bands_fixed((None, 0.0, "ok", "Stress sotto la media"), (0.0, 1.0, "warn", "Stress sopra la media"),
                       (1.0, None, "bad", "Stress elevato")),
    gauge_range=(-2, 5), delta_color="inverse",
    bands_note="Per costruzione zero = media storica; dal 1994 il 95° percentile è 1,36.",
))
_add(Signal(
    "nfci", "Condizioni finanziarie (Chicago Fed NFCI)", ("NFCI",), _s("NFCI"),
    "Indice delle condizioni finanziarie della Chicago Fed (105 variabili). Valori negativi = "
    "condizioni più distese della media; positivi = più restrittive.",
    suffix="", delta_suffix="", decimals=2,
    bands=_bands_fixed((None, 0.0, "ok", "Condizioni distese"), (0.0, 0.5, "warn", "Condizioni in irrigidimento"),
                       (0.5, None, "bad", "Condizioni restrittive")),
    gauge_range=(-1.5, 3), delta_color="inverse",
    bands_note="Per costruzione zero = media storica; dal 1971 il 75° percentile è 0,15.",
))
_add(Signal(
    "drtscilm", "Banche che irrigidiscono il credito", ("DRTSCILM",), _s("DRTSCILM"),
    "Saldo tra banche che rendono più severi e più facili i criteri per i prestiti alle "
    "imprese (sondaggio trimestrale Fed). Valori alti hanno spesso preceduto le recessioni "
    "(con un falso segnale nel 2023).",
    suffix="%", delta_suffix=" pp", decimals=1,
    bands=_bands_fixed((None, 10.0, "ok", "Credito accessibile"), (10.0, 30.0, "warn", "Irrigidimento moderato"),
                       (30.0, None, "bad", "Irrigidimento marcato")),
    gauge_range=(-40, 80), delta_color="inverse",
    bands_note="Dal 1990: mediana 0, 75° percentile 18, media nelle recessioni 51.",
))
_add(Signal(
    "vix", "VIX (volatilità implicita S&P 500)", ("VIXCLS",), _s("VIXCLS"),
    "Volatilità attesa dal mercato delle opzioni sull'S&P 500 nei prossimi 30 giorni. "
    "Sale nelle fasi di paura; livelli molto bassi possono indicare compiacenza.",
    suffix="", delta_suffix="", decimals=1,
    bands=_bands_fixed((None, 20.0, "ok", "Volatilità nella norma"), (20.0, 30.0, "warn", "Tensione"),
                       (30.0, None, "bad", "Paura")),
    gauge_range=(5, 60), delta_color="inverse",
    bands_note="Dal 1990: mediana 17,6, 90° percentile 28,5, 95° percentile 32,9.",
))
_add(Signal(
    "recprob", "Probabilità di recessione (Chauvet-Piger)", ("RECPROUSM156N",), _s("RECPROUSM156N"),
    "Probabilità che l'economia sia in recessione, stimata da un modello statistico su "
    "occupazione, produzione, redditi e vendite. Esce con circa 2 mesi di ritardo: conferma "
    "le recessioni più che anticiparle.",
    decimals=1,
    bands=_bands_fixed((None, 5.0, "ok", "Bassa"), (5.0, 30.0, "warn", "In aumento"), (30.0, None, "bad", "Elevata")),
    gauge_range=(0, 50), delta_color="inverse",
    bands_note="In espansione la media è sotto l'1%; nelle recessioni sopra il 60%.",
))

# =============================================================================
# AREE DEL CRUSCOTTO
# =============================================================================

AREAS: list[tuple[str, str, list[str]]] = [
    ("Inflazione", ":material/local_fire_department:", ["core_pce_yoy", "cpi_yoy", "core_pce_3m", "be5"]),
    ("Lavoro", ":material/work:", ["unrate", "sahm", "payrolls_3m", "claims_rise"]),
    ("Crescita", ":material/factory:", ["gdpnow", "ip_yoy", "retail_real_yoy", "income_real_yoy"]),
    ("Fed e curva", ":material/account_balance:", ["fedfunds", "t10y3m", "t10y2y", "real10y"]),
    ("Credito e stress", ":material/warning:", ["baa10y", "nfci", "stlfsi", "vix", "drtscilm"]),
    ("Liquidità", ":material/water_drop:", ["netliq_13w", "m2_yoy"]),
    ("Famiglie e casa", ":material/home:", ["umcsent", "psavert", "mortgage30", "houst"]),
]

SNAPSHOT_GAUGES = ["core_pce_yoy", "cpi_yoy", "fedfunds", "unrate",
                   "t10y2y", "umcsent", "baa10y", "ip_yoy"]

# =============================================================================
# CALENDARIO (ID release FRED)
# =============================================================================


# Giorno della decisione FOMC (secondo giorno di ogni riunione) dal calendario
# ufficiale: federalreserve.gov/monetarypolicy/fomccalendars.htm.
# Serve perché la release FRED 101 "FOMC Press Release" contiene serie giornaliere
# e FRED la segna come uscita ogni giorno. Da aggiornare una volta l'anno, quando
# la Fed pubblica le date dell'anno successivo (le date future sono provvisorie).
# Escluso il "Monetary Policy Strategy Meeting" del 26-27 ottobre 2027.
FOMC_DECISIONS: tuple[str, ...] = (
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
    "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09",
    "2027-07-28", "2027-09-15", "2027-11-17",
)


@dataclass(frozen=True)
class Release:
    name: str
    importance: int                 # 3 alta, 2 media, 1 bassa
    signals: tuple[str, ...] = field(default_factory=tuple)
    fixed_dates: tuple[str, ...] = ()       # date ufficiali al posto del calendario FRED
    skip_dates_of: int | None = None        # scarta le date in comune con questa release


RELEASES: dict[int, Release] = {
    10: Release("Inflazione al consumo (CPI)", 3, ("cpi_yoy", "core_cpi_yoy")),
    54: Release("Redditi e spese delle famiglie (PCE)", 3, ("core_pce_yoy", "pce_yoy", "psavert")),
    50: Release("Rapporto sull'occupazione (payrolls e disoccupazione)", 3, ("unrate", "payrolls_mom")),
    53: Release("PIL (BEA)", 3, ("gdp_qoq",)),
    101: Release("Decisione FOMC sui tassi", 3, ("fedfunds",), fixed_dates=FOMC_DECISIONS),
    326: Release("Proiezioni economiche FOMC (SEP)", 2, ()),
    46: Release("Prezzi alla produzione (PPI)", 2, ("ppi_yoy",)),
    180: Release("Richieste di sussidio di disoccupazione", 2, ("claims_4w",)),
    192: Release("JOLTS: posti vacanti e dimissioni", 2, ("openings_ratio",)),
    9: Release("Vendite al dettaglio", 2, ("retail_real_yoy",)),
    13: Release("Produzione industriale e utilizzo capacità", 2, ("ip_yoy", "tcu")),
    # FRED aggiorna alcune serie di questa release anche nei giorni delle vendite di
    # case nuove (release 97), ma il rapporto su cantieri e permessi esce una volta al mese.
    27: Release("Cantieri e permessi residenziali", 2, ("houst", "permit"), skip_dates_of=97),
    91: Release("Fiducia consumatori (Univ. of Michigan)", 2, ("umcsent",)),
    386: Release("GDPNow (Atlanta Fed)", 2, ("gdpnow",)),
    97: Release("Vendite di case nuove", 1, ()),
    171: Release("Prezzi delle case FHFA", 1, ("hpi_yoy",)),
    190: Release("Tassi sui mutui (Freddie Mac)", 1, ("mortgage30",)),
    191: Release("Sondaggio Fed sul credito bancario (SLOOS)", 1, ("drtscilm",)),
    20: Release("Bilancio Fed (H.4.1)", 1, ("netliq",)),
    21: Release("Moneta M2 (H.6)", 1, ("m2_yoy",)),
    187: Release("Indice di stress St. Louis Fed", 1, ("stlfsi",)),
    221: Release("Condizioni finanziarie Chicago Fed (NFCI)", 1, ("nfci",)),
    296: Release("Sfitto e proprietà delle abitazioni", 1, ("rental_vac",)),
    261: Release("Probabilità di recessione", 1, ("recprob",)),
}

DAILY_NOTE = ("Rendimenti dei Treasury, spread della curva, breakeven, tasso reale, Fed Funds "
              "effettivo, dollaro, VIX e reverse repo si aggiornano ogni giorno lavorativo.")


# =============================================================================
# FUNZIONI DI SUPPORTO
# =============================================================================

def signal_series_ids(keys) -> list[str]:
    ids: list[str] = []
    for k in keys:
        ids.extend(SIGNALS[k].series)
    return list(dict.fromkeys(ids))


def series_ids_for_areas() -> list[str]:
    keys = [k for _, _, ks in AREAS for k in ks]
    return signal_series_ids(keys)
