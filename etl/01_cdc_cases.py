"""
CDC Case Surveillance ETL
Transforms raw CDC case data into processed Parquet format.
"""
import polars as pl
import pandas as pd
from utils import standardise_age_group, normalise_yn

def etl_cdc_cases():
    """Load, transform, and save CDC case surveillance data."""
    
    print("=" * 80)
    print("CDC CASE SURVEILLANCE ETL")
    print("=" * 80)
    
    print("\n1. Loading CDC case surveillance data...")
    
    # Try reading with polars first, fall back to pandas if encoding issues
    try:
        df = pl.read_csv('../data/raw/cdc_cases.csv', infer_schema_length=10000)
    except Exception as e:
        print(f"   Polars read failed ({type(e).__name__}), trying pandas...")
        df_pd = pd.read_csv('../data/raw/cdc_cases.csv', encoding='latin-1', 
                             infer_datetime_format=True, low_memory=False)
        df = pl.from_pandas(df_pd)
    
    print(f"   Loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")
    
    print("\n2. Examining column names...")
    actual_cols = df.columns
    print(f"   Columns: {actual_cols[:10]}...")
    
    # Normalize column names to lowercase
    df = df.rename({c: c.lower() for c in df.columns})
    
    # Map actual CDC column names to our standard names
    # Common CDC column names: cdc_report_dt, pos_spec_dt, onset_dt, current_status, sex, age_group, etc.
    col_mapping = {}
    
    # Identify which columns we have (prefer one mapping per target column)
    for col in df.columns:
        col_lower = col.lower()
        if 'race' in col_lower and 'ethnicity' in col_lower:
            col_mapping[col] = 'race_ethnicity_combined'
        elif col_lower == 'cdc_report_dt' and 'case_month' not in col_mapping.values():
            col_mapping[col] = 'case_month'
        elif col_lower == 'res_state':
            col_mapping[col] = 'res_state'
        elif col_lower == 'sex':
            col_mapping[col] = 'sex'
        elif col_lower == 'age_group':
            col_mapping[col] = 'age_group'
        elif col_lower == 'hosp_yn':
            col_mapping[col] = 'hosp_yn'
        elif col_lower == 'icu_yn':
            col_mapping[col] = 'icu_yn'
        elif col_lower == 'death_yn':
            col_mapping[col] = 'death_yn'
    
    # Select and rename available columns
    available_cols = list(col_mapping.keys())
    df = df.select(available_cols).rename(col_mapping)
    
    print(f"   Selected columns: {list(col_mapping.values())}")
    
    print("\n3. Transforming data...")
    
    # Extract year-month from date columns
    if 'case_month' in df.columns:
        # Try to parse as date and extract year-month
        try:
            df = df.with_columns([
                pl.col('case_month').cast(pl.Utf8).str.slice(0, 7).alias('case_month_ym')
            ])
            df = df.drop('case_month').rename({'case_month_ym': 'case_month'})
        except:
            pass
    
    # Standardize dimensions
    df = df.with_columns([
        standardise_age_group(pl.col('age_group')).alias('age_group') if 'age_group' in df.columns else pl.lit('Unknown').alias('age_group'),
        normalise_yn(pl.col('hosp_yn')).alias('hosp_yn') if 'hosp_yn' in df.columns else pl.lit(None).alias('hosp_yn'),
        normalise_yn(pl.col('icu_yn')).alias('icu_yn') if 'icu_yn' in df.columns else pl.lit(None).alias('icu_yn'),
        normalise_yn(pl.col('death_yn')).alias('death_yn') if 'death_yn' in df.columns else pl.lit(None).alias('death_yn'),
    ])
    
    # Remove uninformative records (both hosp and death null)
    if 'hosp_yn' in df.columns and 'death_yn' in df.columns:
        df = df.filter(~(pl.col('hosp_yn').is_null() & pl.col('death_yn').is_null()))
    
    print(f"   After transformations: {df.shape[0]:,} rows")
    
    print("\n4. Data quality checks...")
    
    if 'death_yn' in df.columns:
        death_rate = df.filter(pl.col('death_yn') == 1).shape[0] / df.shape[0]
        print(f"   Death rate: {death_rate:.4f} ({death_rate*100:.2f}%)")
    
    if 'hosp_yn' in df.columns:
        hosp_rate = df.filter(pl.col('hosp_yn') == 1).shape[0] / df.shape[0]
        print(f"   Hospitalization rate: {hosp_rate:.4f} ({hosp_rate*100:.2f}%)")
    
    print("\n5. Writing Parquet file...")
    
    # Ensure output directory exists
    import os
    os.makedirs('../data/processed', exist_ok=True)
    
    df.write_parquet('../data/processed/cdc_cases.parquet')
    
    print(f"   ✓ Saved: data/processed/cdc_cases.parquet")
    print(f"   Rows: {df.shape[0]:,}")
    print(f"   Columns: {df.shape[1]}")
    
    print("\n" + "=" * 80)
    print("✓ CDC ETL COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    etl_cdc_cases()
