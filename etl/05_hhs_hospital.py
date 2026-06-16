"""
HHS Hospital Capacity ETL
Processes hospital capacity data.
"""
import polars as pl
import pandas as pd

def etl_hhs_hospital():
    """Load, transform, and save HHS hospital capacity data."""
    
    print("=" * 80)
    print("HHS HOSPITAL CAPACITY ETL")
    print("=" * 80)
    
    print("\n1. Loading HHS hospital capacity data...")
    
    try:
        df = pl.read_csv('../data/raw/HHS.csv', infer_schema_length=10000)
    except:
        print("   Polars read failed, trying pandas...")
        df_pd = pd.read_csv('../data/raw/HHS.csv', low_memory=False)
        df = pl.from_pandas(df_pd)
    
    print(f"   Loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")
    print(f"   Columns: {df.columns[:10]}...")
    
    # Normalize column names
    df = df.rename({c: c.lower() for c in df.columns})
    
    print("\n2. Selecting relevant columns...")
    
    # Select relevant columns
    keep_cols = ['collection_week', 'state', 'inpatient_beds_used_covid',
                 'staffed_icu_adult_patients_confirmed_covid',
                 'total_adult_patients_hospitalized_confirmed_covid']
    
    available_cols = [c for c in keep_cols if c in df.columns]
    df = df.select(available_cols)
    
    print(f"   Selected: {available_cols}")
    
    print("\n3. Transforming data...")
    
    # Parse collection_week as date
    if 'collection_week' in df.columns:
        try:
            df = df.with_columns([
                pl.col('collection_week').str.to_date('%Y-%m-%d').alias('collection_week')
            ])
        except:
            print("   Could not parse collection_week as date")
    
    # Aggregate to state + week level (sum across facilities)
    print("\n4. Aggregating to state + week level...")
    
    agg_cols = [c for c in available_cols if c not in ['collection_week', 'state']]
    
    df_agg = df.group_by(['collection_week', 'state']).agg([
        pl.col(c).sum() for c in agg_cols
    ])
    
    print(f"   Aggregated to: {df_agg.shape[0]:,} state-week records")
    
    print("\n5. Data quality checks...")
    print(f"   Unique states: {df_agg.select('state').n_unique():,}")
    print(f"   Date range: {df_agg.select('collection_week').min()} to {df_agg.select('collection_week').max()}")
    
    print("\n6. Writing Parquet file...")
    
    import os
    os.makedirs('../data/processed', exist_ok=True)
    
    df_agg.write_parquet('../data/processed/hhs_hospital.parquet')
    
    print(f"   ✓ Saved: data/processed/hhs_hospital.parquet")
    print(f"   Rows: {df_agg.shape[0]:,}")
    
    print("\n" + "=" * 80)
    print("✓ HHS HOSPITAL ETL COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    etl_hhs_hospital()
