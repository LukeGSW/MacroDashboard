# Macro Dashboard USA · Kriterion Quant

Dashboard gratuita sull'economia americana: inflazione, lavoro, crescita, tassi, liquidità della Fed,
housing, sentiment e rischio di recessione, con semafori trasparenti e spiegazioni in italiano.

Realizzata con [Streamlit](https://streamlit.io) e i dati dell'API FRED® della Federal Reserve Bank of St. Louis.

> This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.

## Cosa contiene

| Pagina | Contenuto |
|---|---|
| **Cruscotto** | Semaforo per area, 8 indicatori chiave, ultimi dati usciti e prossime pubblicazioni |
| **Calendario dati** | Date e orari italiani delle prossime uscite (FOMC, CPI, PCE, occupazione, PIL, ...), verificati in automatico su due fonti |
| **Rischio recessione** | Curva dei rendimenti, regola di Sahm, probabilità di recessione, sussidi, credito; storico dei segnali con successi e falsi allarmi |
| **Inflazione** | CPI, PCE, core, momentum a 3 e 6 mesi, componenti persistenti, breakeven, PPI |
| **Lavoro** | Disoccupazione vs tasso naturale (CBO), payrolls, sussidi, salari, JOLTS, occupati 25-54 anni |
| **Crescita** | PIL reale, GDPNow, produzione industriale, utilizzo capacità, consumi e redditi reali |
| **Tassi e curva** | Fed Funds vs neutrale FOMC, curva completa (oggi, 1 mese, 1 anno fa), spread, tassi reali |
| **Liquidità e Fed** | Bilancio Fed, conto del Tesoro, reverse repo, liquidità netta, riserve, M2, dollaro |
| **Housing** | Cantieri e permessi, prezzi FHFA, mutui, sfitto |
| **Sentiment e stress** | Fiducia consumatori, risparmio, spread Baa, NFCI, stress St. Louis Fed, standard bancari, VIX |
| **Note legali e fonti** | Disclaimer, termini d'uso, privacy, licenze di ogni serie, tabella completa delle soglie |

Ogni indicatore ha un tooltip ⓘ con definizione, soglie dei colori, origine delle soglie e fonte.

## Logica dei semafori

- **Verde**: in linea con un'economia in equilibrio o condizioni finanziarie normali
- **Giallo**: da monitorare
- **Rosso**: squilibrio o stress marcato (in entrambe le direzioni, es. inflazione molto alta o deflazione)

Le soglie sono definite in un unico punto (`catalog.py`) e usate da gauge, tabelle, cruscotto e tooltip.
Sono ancorate a riferimenti pubblici (obiettivo del 2% della Fed, tasso neutrale FOMC, tasso naturale di
disoccupazione del CBO, regola di Sahm) o alla distribuzione storica dal 1990. Sono convenzioni descrittive,
non segnali operativi.

## Avvio in locale

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

Crea `.streamlit/secrets.toml` (escluso da git) con la tua chiave FRED gratuita
([richiedila qui](https://fred.stlouisfed.org/docs/api/api_key.html)):

```toml
FRED_API_KEY = "la-tua-chiave"
```

Poi:

```bash
streamlit run app.py
```

## Pubblicazione su Streamlit Community Cloud

1. Collega il repository e indica `app.py` come file principale.
2. In **Settings → Secrets** inserisci `FRED_API_KEY = "..."`.
3. L'URL dell'app non deve contenere "fred" o "federal reserve" (vincolo dei termini d'uso FRED®).

## Struttura

```
app.py              entrypoint: navigazione, controlli globali, header con link, footer legale
config.py           brand, link, parametri, testi legali
catalog.py          serie FRED®, indicatori, soglie, tooltip, aree del cruscotto, uscite del calendario
utils/data.py       download con cache condivisa, limiti di frequenza, calendario release FRED®
utils/official.py   lettura automatica dei calendari ufficiali (Fed, BEA, Census)
utils/cal.py        confronto tra le fonti, controlli sull'arrivo dei dati, liste del calendario
utils/transforms.py trasformazioni (a/a, annualizzati, liquidità netta, recessioni, ...)
utils/signals.py    valutazione indicatori e soglie, testi dei tooltip
utils/charts.py     grafici Plotly con lo stile Kriterion Quant
utils/ui.py         componenti di interfaccia condivisi
views/              una pagina per file
assets/             logo e icona
```

## Calendario delle uscite: come vengono verificate le date

Nessuna data è inserita a mano. Per ogni uscita la dashboard confronta due fonti indipendenti:

- **Fed, BEA, Census**: calendario ufficiale letto in automatico (pagina FOMC e calendario JSON della Fed,
  pagina G.17, calendario ICS della BEA, calendario indicatori Census) confrontato con il calendario FRED®.
  Una data concorde è confermata; le date solo FRED® dove il calendario ufficiale ha già le date vengono
  scartate (aggiornamenti secondari della release FRED®); ogni altro disaccordo è segnato "da confermare".
- **BLS e DOL** (CPI, PPI, occupazione, JOLTS, sussidi): i siti non consentono la lettura automatica, quindi
  la fonte è il calendario FRED®.
- **Dopo ogni uscita** si verifica che la serie su FRED® sia stata aggiornata: se il dato manca da più di
  24 ore l'uscita risulta "non pubblicata" e le date successive della stessa agenzia diventano da confermare
  (es. uno shutdown). Se il dato è arrivato dopo l'ultimo download, le serie collegate vengono riscaricate.
- Se un calendario ufficiale non risponde o cambia struttura, le date collegate risultano da confermare:
  la dashboard non mostra mai come certa una data non verificata.

## Dati e licenze

Le serie provengono dall'API FRED®. Alcune sono protette da copyright dei rispettivi proprietari e sono
mostrate con la citazione e la nota di copyright richieste (tag FRED "copyrighted: citation required").
Le serie che richiedono un'autorizzazione preventiva (S&P Case-Shiller, ICE BofA High Yield) non sono usate.
Elenco completo e citazioni nella pagina **Note legali e fonti**.

## Disclaimer

Contenuti a solo scopo informativo ed educativo: non costituiscono consulenza finanziaria né sollecitazione
all'investimento. Usando l'applicazione accetti i [Termini d'uso dell'API FRED®](https://fred.stlouisfed.org/docs/api/terms_of_use.html).
