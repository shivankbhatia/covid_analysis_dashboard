# COVID-19 Demographic Analytics Platform

A data analytics pipeline analyzing COVID-19 case surveillance, vaccine safety (VAERS), hospital capacity, and mortality trends across demographic groups and U.S. states.

## Tech Stack

| Layer | Tool |
|--------|------|
| Large-file ETL | DuckDB (streaming SQL) |
| Fast in-memory processing | Polars, Pandas |
| Intermediate storage | Apache Parquet (ZSTD) |
| Analytical warehouse | DuckDB (star schema) |
| Dashboard | Plotly Dash + Bootstrap CYBORG |
| ML (planned) | Scikit-learn, XGBoost, SHAP |
| Reporting (planned) | Quarto |

## Project Structure

```text
covid_analysis_dashboard/
├── etl/                  # ETL scripts (01–06) + utils.py
├── warehouse/            # schema.sql + load.py
├── features/             # engineer.py
├── dashboards/
│   ├── app.py            # Dash entry point
│   └── pages/            # demographic, outcomes, vaccine,
│                         # symptoms, geographic, advanced
├── models/               # ML models (planned)
├── reports/              # Quarto reports (planned)
└── requirements.txt
```

## Data Sources

- **CDC Case Surveillance** — 18.6 GB individual case records
- **VAERS (2020–2023)** — vaccine adverse event reports
- **HHS** — weekly hospital capacity by state
- **NCHS** — provisional COVID mortality by age/sex/state

## Pipeline Flow

```text
Raw CSVs
    ↓
ETL (etl/)
    ↓
Parquet files
    ↓
DuckDB warehouse
    ↓
Feature Parquets
    ↓
Dash App
```

## ETL Scripts

| Script | Input | Output |
|--------|-------|--------|
| `01_cdc_cases.py` | `cdc_cases_new.csv` (18.6 GB) | `cdc_cases.parquet` |
| `02_vaers_data.py` | `*VAERSDATA.csv` (2020–2023) | `vaers_data.parquet` |
| `03_vaers_symptoms.py` | `*VAERSSYMPTOMS.csv` | `vaers_symptoms_long.parquet` |
| `04_vaers_vax.py` | `*VAERSVAX.csv` | `vaers_vax_covid.parquet` |
| `05_hhs_hospital.py` | `HHS.csv` | `hhs_hospital.parquet` |
| `06_nchs_mortality.py` | `NCHS CSV` | `nchs_mortality.parquet` |

### Key preprocessing steps

- Age groups normalised to standard buckets: `0-17`, `18-29`, `30-44`, `45-59`, `60-74`, `75+`
- Yes/No outcome columns converted to `1` / `0` / `null`
- CDC file streamed via DuckDB SQL — never loaded fully into RAM
- VAERS symptoms reshaped from wide (5 columns) to long (1 row per symptom)
- HHS data aggregated from facility-level to state + week level

## Warehouse Schema (Star Schema)

**Dimensions**

- `dim_age`
- `dim_gender`
- `dim_race`
- `dim_location`
- `dim_vaccine`
- `dim_symptom`

**Facts**

- `fact_covid_cases` — CDC individual case records
- `fact_vaccine_events` — VAERS adverse event reports
- `fact_vaccine_symptoms` — event ↔ symptom bridge table
- `fact_hospital_capacity` — weekly state hospital metrics
- `fact_mortality` — NCHS death counts by state/age/gender

## Feature Engineering

Derived Parquet files written by `features/engineer.py`:

- `features_cases.parquet` — severity score (0–3), outcome rates by age/gender
- `features_vaccine_events.parquet` — adverse event score (0–4), onset category, symptom count
- `symptom_cooccurrence.parquet` — symptom pairs that co-occur in VAERS reports
- `geo_covid_rates.parquet` — state-level case/hosp/death rates
- `geo_hospital_burden.parquet` — state + week hospital load
- `geo_mortality_rates.parquet` — state + gender mortality rates

## Dashboard Pages

| Route | Description |
|--------|-------------|
| `/demographic` | Cases by age, sex, race |
| `/outcomes` | Hospitalization, ICU, death rates |
| `/vaccine` | VAERS events by manufacturer, severity, onset |
| `/symptoms` | Top symptoms, co-occurrence analysis |
| `/geographic` | Choropleth maps by state |
| `/advanced` | Cross-dataset and ML analysis |

## Setup

```bash
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Download raw data files into data/raw/ (see README for sources)

python etl/01_cdc_cases.py
python etl/02_vaers_data.py
python etl/03_vaers_symptoms.py
python etl/04_vaers_vax.py
python etl/05_hhs_hospital.py
python etl/06_nchs_mortality.py

python warehouse/load.py
python features/engineer.py

python dashboards/app.py
# → http://localhost:8050
```

## Data Disclaimer

````
VAERS is a passive surveillance system. Reports are submitted voluntarily and unverified.

An adverse event reported to VAERS does **not** imply that the vaccine caused the event.
````
