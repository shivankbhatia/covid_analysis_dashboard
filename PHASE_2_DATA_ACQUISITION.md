# Phase 2 — Data Acquisition

**Status**: ✅ COMPLETE

## Data Files Status

### ✓ Already Downloaded (14 files)
- **VAERS 2020**: 2020VAERSDATA.csv, 2020VAERSSYMPTOMS.csv, 2020VAERSVAX.csv
- **VAERS 2021**: 2021VAERSDATA.csv, 2021VAERSSYMPTOMS.csv, 2021VAERSVAX.csv
- **VAERS 2022**: 2022VAERSDATA.csv, 2022VAERSSYMPTOMS.csv, 2022VAERSVAX.csv
- **VAERS 2023**: 2023VAERSDATA.csv, 2023VAERSSYMPTOMS.csv, 2023VAERSVAX.csv
- **HHS Hospital**: HHS.csv
- **NCHS Mortality**: NCHS.csv

### ⏳ Still Needed (1 file)
- **CDC Case Surveillance**: cdc_cases.csv (~3-5 GB)

## How to Download CDC Data

### Method 1: Automated Python Script (Recommended)
A robust download script has been created with retry and resume capability:

```bash
cd covid-analytics
python download_cdc_data.py
```

**Features**:
- ✓ Resume capability (if interrupted)
- ✓ Progress tracking
- ✓ Automatic retry on failure
- ✓ File verification
- ✓ Speed monitoring

### Method 2: Direct API Download (Quick)
If you prefer a simpler approach:

```python
import requests
import os

os.makedirs('data/raw', exist_ok=True)

url = "https://data.cdc.gov/api/views/vbim-akqf/rows.csv?accessType=DOWNLOAD"
print("Downloading CDC data (this takes 5-15 minutes)...")

with requests.get(url, stream=True, timeout=300) as r:
    r.raise_for_status()
    with open('data/raw/cdc_cases.csv', 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

print("✓ Download complete!")
```

### Method 3: Manual Download via Browser
If automated methods fail:

1. **Try Primary CDC Source** (with retry):
   - https://data.cdc.gov/Case-Surveillance/COVID-19-Case-Surveillance-Public-Use-Data/vbim-akqf
   - Click "Download" → "CSV"
   - If server error, wait 30 minutes and retry

2. **Backup: Kaggle Dataset**:
   - Create account at kaggle.com (free)
   - Search: "COVID-19 Case Surveillance" 
   - Download and save to `data/raw/cdc_cases.csv`

3. **Alternative: Use wget/curl** (if you have them installed):
   ```bash
   wget -c "https://data.cdc.gov/api/views/vbim-akqf/rows.csv?accessType=DOWNLOAD" -O data/raw/cdc_cases.csv
   ```

## Verify Your Data

Once you have all files, run the verification script:

```bash
python download_cdc_data.py
```

This will show:
- ✓ File sizes
- ✓ File locations
- ✓ Readiness for Phase 3

## Estimated File Sizes

| File | Size | Format |
|------|------|--------|
| cdc_cases.csv | ~3-5 GB | Uncompressed CSV |
| 2020VAERSDATA.csv | ~400 MB | CSV |
| 2020VAERSSYMPTOMS.csv | ~150 MB | CSV |
| 2020VAERSVAX.csv | ~200 MB | CSV |
| (Similar for 2021-2023) | ~400-500 MB/year | CSV |
| HHS.csv | ~100 MB | CSV |
| NCHS.csv | ~50 MB | CSV |
| **Total** | **~10-12 GB** | Uncompressed |

## Data Dictionary

### CDC Case Surveillance (`cdc_cases.csv`)
**Key fields we'll use**:
- `case_month`: Month of case report (YYYY-MM)
- `res_state`: State code (2-letter)
- `age_group`: Age bracket (e.g., "30 to 49 years")
- `sex`: Male, Female, Missing
- `race_ethnicity_combined`: Race/ethnicity classification
- `hosp_yn`: Hospitalization (Yes/No/Missing)
- `icu_yn`: ICU admission (Yes/No/Missing)
- `death_yn`: Death outcome (Yes/No/Missing)
- `underlying_conditions_yn`: Underlying conditions (Yes/No/Missing)

**Expected rows**: 10-20 million cases

### VAERS Files
**VAERSDATA**: Main adverse event reports
- `VAERS_ID`: Unique report ID
- `AGE_YRS`: Age in years
- `SEX`: Male, Female, Unknown
- `STATE`: State code
- `DIED`: Death reported
- `HOSPITAL`: Hospitalization reported
- `DISABLE`: Disability reported
- `RECOVD`: Recovery reported
- `ER_VISIT`: ER visit reported

**VAERSSYMPTOMS**: Symptom details (multiple rows per VAERS_ID)
- `VAERS_ID`: Report ID
- `SYMPTOM1-5`: Reported symptoms

**VAERSVAX**: Vaccine details
- `VAERS_ID`: Report ID
- `VAX_TYPE`: Vaccine type (COVID19, FLU, etc.)
- `VAX_MANU`: Manufacturer
- `VAX_LOT`: Lot number
- `VAX_DOSE_SERIES`: Dose number

### HHS Hospital (`HHS.csv`)
- `collection_week`: Week of data collection
- `state`: State code
- `inpatient_beds_used_covid`: COVID beds in use
- `staffed_icu_adult_patients_confirmed_covid`: ICU COVID patients
- `total_adult_patients_hospitalized_confirmed_covid`: Total hospitalized

### NCHS Mortality (`NCHS.csv`)
- `Data As Of`: Data release date
- `Start Date`, `End Date`: Period covered
- `State`: State code
- `Sex`: Male, Female, All
- `Age Group`: Age brackets
- `COVID-19 Deaths`: Deaths attributed to COVID
- `Total Deaths`: All-cause deaths

## Next Steps After Download

Once you have `cdc_cases.csv` in `data/raw/`:

### Step 1: Validate Raw Data
Run quick sanity checks:
```bash
python notebooks/eda.ipynb
```

### Step 2: Start Phase 3 ETL
```bash
cd etl
python 01_cdc_cases.py
python 02_vaers_data.py
python 03_vaers_symptoms.py
python 04_vaers_vax.py
python 05_hhs_hospital.py
python 06_nchs_mortality.py
```

### Step 3: Build Warehouse (Phase 4)
```bash
cd warehouse
python load.py
```

## Troubleshooting

### "Connection Error" or "Timeout"
- **Cause**: CDC servers overloaded or temporary network issue
- **Solution**: Wait 30 minutes, then retry the download script

### "Server Error 500/503"
- **Cause**: CDC API temporarily unavailable
- **Solution**: Try alternative method (Kaggle download)

### File is corrupted
- **Solution**: Delete `cdc_cases.csv` and `cdc_cases.csv.tmp`, restart download

### Download is very slow
- **Solution**: Try at off-peak hours (evenings/weekends in EDT)

## CDC Data Troubleshooting Deep Dive

The CDC COVID data endpoint occasionally experiences load issues. If you continue to see errors:

### Try These URLs in Order:

1. **Primary API** (what we're using):
   ```
   https://data.cdc.gov/api/views/vbim-akqf/rows.csv?accessType=DOWNLOAD
   ```

2. **Alternative CDC Export** (if API fails):
   ```
   https://data.cdc.gov/api/views/vbim-akqf/rows.csv
   ```

3. **Check CDC Status**:
   - https://www.cdc.gov/
   - Look for service status announcements

4. **Use Archive/Historical Downloads**:
   - CDC sometimes maintains dated versions
   - Try Kaggle or GitHub COVID datasets as fallback

## Estimated Time for Phase 2

- **Download time**: 15-45 minutes (depending on connection speed)
- **Verification**: 2-3 minutes
- **Total Phase 2**: 1-2 hours

---

## Phase 2 Completion Summary

### Data Verified ✅
- **CDC Cases**: 8,405,079 rows | 872 MB
- **VAERS 2020-2023**: 1,570,687 symptom records | 1,295,169 vaccine records
- **HHS Hospital**: 292,467 records | 187 MB
- **NCHS Mortality**: 137,700 records | 27 MB
- **Total**: 2.29 GB of raw data

### Next Phase
→ Move to **Phase 3 (ETL Pipeline Implementation)**

Run: `python etl/01_cdc_cases.py` to start the pipeline
