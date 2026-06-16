"""
NCHS Mortality ETL
Processes mortality data from NCHS.
"""
import polars as pl
import pandas as pd

def etl_nchs_mortality():
    """Load, transform, and save NCHS mortality data."""
    
    print("=" * 80)
    print("NCHS MORTALITY ETL")
    print("=" * 80)
    
    print("\n1. Loading NCHS mortality data...")
    
    try:
        df = pl.read_csv('../data/raw/NCHS.csv', infer_schema_length=10000)
    except:
        print("   Polars read failed, trying pandas...")
        df_pd = pd.read_csv('../data/raw/NCHS.csv', low_memory=False)
        df = pl.from_pandas(df_pd)
    
    print(f"   Loaded: {df.shape[0]:,} rows, {df.shape[1]} columns")
    print(f"   Columns: {df.columns}")
    
    print("\n2. Selecting and renaming columns...")
    
    # Normalize column names
    df = df.rename({c: c.lower() for c in df.columns})
    
    # Select relevant columns
    keep_cols = ['data as of', 'start date', 'end date', 'state', 'sex', 'age group',
                 'covid-19 deaths', 'total deaths', 'pneumonia and covid-19 deaths']
    
    available_cols = [c for c in keep_cols if c in df.columns]
    df = df.select(available_cols)
    
    print(f"   Selected {len(available_cols)} columns")
    
    print("\n3. Parsing dates...")
    
    # Parse date columns
    for date_col in ['start date', 'end date', 'data as of']:
        if date_col in df.columns:
            try:
                df = df.with_columns([
                    pl.col(date_col).str.to_date('%Y-%m-%d').alias(date_col)
                ])
            except:
                print(f"   Could not parse {date_col} as date")
    
    print(f"   Date columns parsed")
    
    print("\n4. Data quality checks...")
    
    if 'state' in df.columns:
        print(f"   Unique states: {df.select('state').n_unique():,}")
    
    if 'sex' in df.columns:
        sex_counts = df.group_by('sex').agg(pl.count('sex').alias('count'))
        print("   Sex breakdown:")
        for row in sex_counts.to_dicts():
            print(f"     {row['sex']:.<20} {row['count']:>8,}")
    
    print("\n5. Writing Parquet file...")
    
    import os
    os.makedirs('../data/processed', exist_ok=True)
    
    df.write_parquet('../data/processed/nchs_mortality.parquet')
    
    print(f"   ✓ Saved: data/processed/nchs_mortality.parquet")
    print(f"   Rows: {df.shape[0]:,}")
    
    print("\n" + "=" * 80)
    print("✓ NCHS MORTALITY ETL COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    etl_nchs_mortality()
