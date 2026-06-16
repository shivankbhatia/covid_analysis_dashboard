"""
VAERS Vaccine ETL
Filters and processes vaccine information from VAERS.
Concatenates data from 2020-2023, filters to COVID-19 only.
"""
import polars as pl
import pandas as pd
from pathlib import Path
from utils import normalise_manufacturer

def etl_vaers_vax():
    """Load, transform, and save VAERS vaccine data (COVID-19 only)."""
    
    print("=" * 80)
    print("VAERS VACCINE ETL")
    print("=" * 80)
    
    print("\n1. Discovering VAERS vaccine files...")
    
    data_dir = Path('../data/raw')
    vax_files = sorted(data_dir.glob('*VAERSVAX.csv'))
    
    print(f"   Found {len(vax_files)} files:")
    for f in vax_files:
        print(f"     - {f.name}")
    
    dfs = []
    
    for filepath in vax_files:
        print(f"\n2. Reading {filepath.name}...")
        
        try:
            df = pd.read_csv(filepath, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            print("   UTF-8 decode failed, trying latin-1...")
            df = pd.read_csv(filepath, encoding='latin-1', low_memory=False)
        
        print(f"   Loaded: {len(df):,} rows")
        
        # Convert to polars
        df_pl = pl.from_pandas(df)
        
        # Filter to COVID-19 only
        if 'VAX_TYPE' in df_pl.columns:
            df_pl = df_pl.filter(pl.col('VAX_TYPE') == 'COVID19')
            print(f"   After COVID-19 filter: {df_pl.shape[0]:,} rows")
        
        dfs.append(df_pl)
    
    print(f"\n3. Concatenating all years...")
    
    df_combined = pl.concat(dfs, how='vertical')
    
    print(f"   Total rows: {df_combined.shape[0]:,}")
    
    # Normalize manufacturer names
    if 'VAX_MANU' in df_combined.columns:
        print(f"\n4. Normalizing manufacturer names...")
        
        df_combined = df_combined.with_columns([
            normalise_manufacturer(pl.col('VAX_MANU')).alias('VAX_MANU')
        ])
        
        mfr_counts = df_combined.group_by('VAX_MANU').agg(pl.count('VAX_MANU').alias('count')).sort('count', descending=True)
        print("   Manufacturer breakdown:")
        for row in mfr_counts.to_dicts():
            print(f"     {row['VAX_MANU']:.<30} {row['count']:>8,}")
    
    # Select relevant columns
    keep_cols = ['VAERS_ID', 'VAX_TYPE', 'VAX_MANU', 'VAX_LOT', 'VAX_DOSE_SERIES', 'VAX_NAME']
    available_cols = [c for c in keep_cols if c in df_combined.columns]
    df_combined = df_combined.select(available_cols)
    
    print(f"\n5. Writing Parquet file...")
    
    import os
    os.makedirs('../data/processed', exist_ok=True)
    
    df_combined.write_parquet('../data/processed/vaers_vax_covid.parquet')
    
    print(f"   ✓ Saved: data/processed/vaers_vax_covid.parquet")
    print(f"   Rows: {df_combined.shape[0]:,}")
    
    print("\n" + "=" * 80)
    print("✓ VAERS VACCINE ETL COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    etl_vaers_vax()
