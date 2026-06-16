# COVID-19 Demographic Analytics Platform

A comprehensive data analytics platform analyzing COVID-19 case surveillance, vaccine safety data (VAERS), hospital capacity, and mortality trends across demographic groups and geographic regions.

## Project Structure

```
covid-analytics/
├── data/
│   ├── raw/                  # Downloaded source files (gitignored)
│   ├── processed/            # Cleaned Parquet files
│   └── warehouse/            # DuckDB database file
├── etl/                      # ETL pipeline scripts
├── warehouse/                # Schema and data loading
├── features/                 # Feature engineering
├── dashboards/               # Plotly Dash application
├── models/                   # ML models and SHAP analysis
├── reports/                  # Quarto reports
├── notebooks/                # Jupyter notebooks for EDA
├── requirements.txt
└── README.md
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On macOS/Linux
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Additional Requirements

- **Quarto**: Download from https://quarto.org/docs/get-started/ (for Phase 8 reporting)
- **Data Files**: Download from CDC, VAERS, HHS, and NCHS sources (see implementation plan Phase 2)

## Implementation Phases

- **Phase 1** ✅ Environment & Repository Setup
- **Phase 2** Data Acquisition
- **Phase 3** ETL Pipeline
- **Phase 4** Warehouse Construction
- **Phase 5** Feature Engineering
- **Phase 6** Dashboards
- **Phase 7** Machine Learning Models
- **Phase 8** Reporting
- **Phase 9** Testing & Validation
- **Phase 10** Deployment

## Data Sources

- **CDC Case Surveillance**: https://data.cdc.gov/Case-Surveillance/COVID-19-Case-Surveillance-Public-Use-Data/vbim-akqf
- **VAERS**: https://vaers.hhs.gov/data/datasets.html
- **HHS Hospital Capacity**: https://healthdata.gov/Hospital/COVID-19-Reported-Patient-Impact-and-Hospital-Capa/uqq2-txqb
- **NCHS Mortality**: https://data.cdc.gov/NCHS/Provisional-COVID-19-Death-Counts-by-Sex-Age-and-/9bhg-hcku

## Data Disclaimer

VAERS data is a passive surveillance system. Reports are submitted voluntarily and are unverified. An adverse event listed in VAERS does not imply the vaccine caused the event. All vaccine-related analyses must be interpreted alongside denominator data and peer-reviewed safety literature.

## Technology Stack

- **Data Processing**: Python, Pandas, Polars, DuckDB
- **Visualization**: Plotly, Dash
- **ML**: Scikit-Learn, XGBoost, LightGBM, SHAP
- **Reporting**: Quarto
- **Storage**: Parquet, DuckDB

## Next Steps

1. Download raw data files from sources listed above
2. Run ETL pipeline scripts in `etl/` directory
3. Load data into DuckDB warehouse
4. Engineer features and train ML models
5. Run Dash dashboards
6. Generate executive reports
