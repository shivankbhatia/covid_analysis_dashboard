# Phase 3 — ETL Pipeline Implementation

**Status**: ✅ COMPLETE & READY TO RUN

## Overview

Phase 3 transforms raw data files into cleaned, standardized Parquet format ready for warehouse loading. Six ETL scripts run sequentially, each handling one data source.

## Data Files Status

All required source files are present in `data/raw/`:

| Source | Files | Size | Rows |
|--------|-------|------|------|
| **CDC Cases** | cdc_cases.csv | 872 MB | 8.4M |
| **VAERS 2020-2023** | *VAERSDATA.csv (4 files) | 1.1 GB | 1.3M |
| **VAERS Symptoms** | *VAERSSYMPTOMS.csv (4 files) | 123 MB | 1.6M |
| **VAERS Vaccine** | *VAERSVAX.csv (4 files) | 95 MB | 1.3M |
| **HHS Hospital** | HHS.csv | 187 MB | 292K |
| **NCHS Mortality** | NCHS.csv | 27 MB | 138K |

## ETL Scripts Overview

### 1. CDC Cases (`01_cdc_cases.py`)
**Purpose**: Clean and standardize CDC case surveillance data

**Input**: `data/raw/cdc_cases.csv` (8.4M rows)

**Transformations**:
- Extract year-month from date columns
- Standardize age groups to: 0-17, 18-29, 30-44, 45-59, 60-74, 75+
- Convert Yes/No/Missing to binary (1/0/null)
- Remove uninformative records (both hosp_yn and death_yn null)
- Filter to key fields only

**Output**: `data/processed/cdc_cases.parquet`

**Estimated time**: 2-5 minutes

---

### 2. VAERS Data (`02_vaers_data.py`)
**Purpose**: Concatenate and clean VAERS adverse event reports (2020-2023)

**Input**: 
- `data/raw/2020VAERSDATA.csv`
- `data/raw/2021VAERSDATA.csv`
- `data/raw/2022VAERSDATA.csv`
- `data/raw/2023VAERSDATA.csv`

**Transformations**:
- Concatenate annual files
- Handle encoding issues (UTF-8 → latin-1 fallback)
- Cap age outliers (>120 → null)
- Convert to numeric where applicable
- Select key fields: VAERS_ID, AGE_YRS, SEX, STATE, DIED, HOSPITAL, DISABLE, RECOVD, ER_VISIT, NUMDAYS, RPT_DATE

**Output**: `data/processed/vaers_data.parquet`

**Estimated time**: 3-8 minutes

---

### 3. VAERS Symptoms (`03_vaers_symptoms.py`)
**Purpose**: Transform wide symptom format to long (one row per symptom per report)

**Input**: 
- `data/raw/*VAERSSYMPTOMS.csv` (4 files)

**Transformations**:
- Concatenate annual files
- Unpivot SYMPTOM1-SYMPTOM5 columns
- Remove null symptoms
- Strip whitespace from symptom names

**Output**: `data/processed/vaers_symptoms_long.parquet`

**Expected rows**: ~1.6M (one per symptom occurrence)

**Estimated time**: 2-4 minutes

---

### 4. VAERS Vaccine (`04_vaers_vax.py`)
**Purpose**: Extract and normalize vaccine information, filter to COVID-19 only

**Input**: 
- `data/raw/*VAERSVAX.csv` (4 files)

**Transformations**:
- Concatenate annual files
- Filter to VAX_TYPE == 'COVID19'
- Normalize manufacturer names (Pfizer, Moderna, Janssen, Other/Unknown)
- Select key fields: VAERS_ID, VAX_TYPE, VAX_MANU, VAX_LOT, VAX_DOSE_SERIES, VAX_NAME

**Output**: `data/processed/vaers_vax_covid.parquet`

**Estimated time**: 2-4 minutes

---

### 5. HHS Hospital (`05_hhs_hospital.py`)
**Purpose**: Process hospital capacity data and aggregate to state-week level

**Input**: `data/raw/HHS.csv` (292K rows)

**Transformations**:
- Parse collection_week as date
- Aggregate to state + week level (sum across hospitals)
- Select key fields: collection_week, state, covid_inpatient, covid_icu, covid_admissions

**Output**: `data/processed/hhs_hospital.parquet`

**Estimated time**: 1-2 minutes

---

### 6. NCHS Mortality (`06_nchs_mortality.py`)
**Purpose**: Clean and standardize mortality data

**Input**: `data/raw/NCHS.csv` (138K rows)

**Transformations**:
- Parse date columns
- Normalize column names
- Select key fields: data_as_of, start_date, end_date, state, sex, age_group, covid_deaths, total_deaths

**Output**: `data/processed/nchs_mortality.parquet`

**Estimated time**: 1-2 minutes

---

## How to Run

### Option 1: Run All Scripts at Once (Recommended)
```bash
cd covid-analytics
python run_etl_pipeline.py
```

This runs all 6 scripts sequentially with progress tracking.

**Total time**: 10-25 minutes (depending on system speed)

### Option 2: Run Individual Scripts
```bash
cd covid-analytics/etl

# Run one at a time
python 01_cdc_cases.py
python 02_vaers_data.py
python 03_vaers_symptoms.py
python 04_vaers_vax.py
python 05_hhs_hospital.py
python 06_nchs_mortality.py
```

### Option 3: Run from Jupyter Notebook
```python
import subprocess
import sys

scripts = [
    'etl/01_cdc_cases.py',
    'etl/02_vaers_data.py',
    # ... etc
]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run([sys.executable, script], cwd='covid-analytics')
```

## Expected Output

After successful ETL completion, you'll have in `data/processed/`:

```
data/processed/
├── cdc_cases.parquet          (compressed CDC data)
├── vaers_data.parquet         (VAERS adverse events)
├── vaers_symptoms_long.parquet (symptoms in long format)
├── vaers_vax_covid.parquet     (COVID-19 vaccine records)
├── hhs_hospital.parquet        (hospital capacity aggregated)
└── nchs_mortality.parquet      (mortality data)
```

## Monitoring Progress

The ETL pipeline provides detailed progress output:

```
================================================================================
CDC CASE SURVEILLANCE ETL
================================================================================

1. Loading CDC case surveillance data...
   Loaded: 8,405,079 rows, X columns

2. Examining column names...
   Columns: ['cdc_report_dt', 'pos_spec_dt', 'onset_dt', ...]

3. Transforming data...
   After transformations: 8,400,000 rows

4. Data quality checks...
   Death rate: 0.0152 (1.52%)
   Hospitalization rate: 0.0743 (7.43%)

5. Writing Parquet file...
   ✓ Saved: data/processed/cdc_cases.parquet
   Rows: 8,400,000
   Columns: 9

================================================================================
✓ CDC ETL COMPLETE
================================================================================
```

## Troubleshooting

### Encoding Errors
**Issue**: `UnicodeDecodeError: 'utf-8' codec can't decode byte...`

**Solution**: Scripts automatically fall back to latin-1 encoding. This is handled automatically.

### Memory Issues
**Issue**: Process runs out of memory

**Solution**: 
- Close other applications
- VAERS files are read in chunks (encoding parsing only reads necessary rows)
- CDC file is large but Polars is memory-efficient

### File Not Found
**Issue**: `FileNotFoundError: data/raw/cdc_cases.csv`

**Solution**: 
- Verify file exists in `data/raw/`
- Check file paths are correct
- Ensure you're running from the `covid-analytics` directory

### Script Hangs
**Issue**: Script seems to be frozen

**Solution**:
- Large file parsing can take 2-5 minutes per script
- Check CPU/disk usage (should be high)
- Wait at least 10 minutes before killing the process
- HHS and NCHS scripts finish faster (small files)

## Performance Expectations

| Script | Input Size | Processing Time | Output Size |
|--------|-----------|-----------------|-------------|
| CDC Cases | 872 MB | 2-5 min | 300-400 MB |
| VAERS Data | 1.1 GB | 3-8 min | 400-500 MB |
| VAERS Symptoms | 123 MB | 2-4 min | 80-100 MB |
| VAERS Vaccine | 95 MB | 2-4 min | 60-80 MB |
| HHS Hospital | 187 MB | 1-2 min | 50-80 MB |
| NCHS Mortality | 27 MB | 1-2 min | 20-30 MB |
| **TOTAL** | **~2.3 GB** | **~15 min** | **~1.0 GB** |

Output files use Parquet format (highly compressed).

## Quality Checks

Each script includes built-in quality checks:

✓ Row count validation
✓ Null rate reporting
✓ Date range verification
✓ Unique value counts
✓ Categorical value distributions

## Next Steps (Phase 4)

Once all ETL scripts complete successfully:

1. **Verify output files exist**:
   ```bash
   ls -lh data/processed/
   ```

2. **Build warehouse**:
   ```bash
   python warehouse/load.py
   ```

3. **Engineer features**:
   ```bash
   python features/engineer.py
   ```

## Retry Strategy

If a script fails:

1. Check the error message
2. Fix the issue if applicable
3. Re-run the failed script individually
4. Continue with remaining scripts

ETL scripts are idempotent (safe to run multiple times).

---

**Estimated Phase 3 Duration**: 15-30 minutes

**Status**: Ready to execute. Run `python run_etl_pipeline.py` to begin!
