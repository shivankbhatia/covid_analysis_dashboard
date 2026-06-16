"""
VAERS Data ETL
Transforms raw VAERS data into processed Parquet format.
Concatenates data from 2020-2023.
"""
import polars as pl
import pandas as pd
from pathlib import Path

def etl_vaers_data():
    """Load, transform, and save VAERS data (2020-2023)."""
    
    print("=" * 80)
    print("VAERS DATA ETL")
    print("=" * 80)
    
    print("\n1. Discovering VAERS data files...")
    
    data_dir = Path('../data/raw')
    vaers_files = sorted(data_dir.glob('*VAERSDATA.csv'))
    
    print(f"   Found {len(vaers_files)} files:")
    for f in vaers_files:
        print(f"     - {f.name}")
    
    dfs = []
    
    for filepath in vaers_files:
        print(f"\n2. Reading {filepath.name}...")
        
        try:
            # Try UTF-8 first
            df = pd.read_csv(filepath, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            # Fall back to latin-1
            print("   UTF-8 decode failed, trying latin-1...")
            df = pd.read_csv(filepath, encoding='latin-1', low_memory=False)
        
        print(f"   Loaded: {len(df):,} rows, {len(df.columns)} columns")
        
        # Select relevant columns
        keep_cols = ['VAERS_ID', 'AGE_YRS', 'SEX', 'STATE', 'DIED', 'HOSPITAL', 
                     'DISABLE', 'RECOVD', 'ER_VISIT', 'NUMDAYS', 'RPT_DATE']
        
        available_cols = [c for c in keep_cols if c in df.columns]
        df = df[available_cols]
        
        print(f"   Selected columns: {available_cols}")
        
        # Clean age
        df['AGE_YRS'] = pd.to_numeric(df['AGE_YRS'], errors='coerce')
        df.loc[df['AGE_YRS'] > 120, 'AGE_YRS'] = None
        
        # Convert to polars
        df_pl = pl.from_pandas(df)
        dfs.append(df_pl)
    
    print(f"\n3. Concatenating all years...")
    
    df_combined = pl.concat(dfs, how='vertical')
    
    print(f"   Total rows: {df_combined.shape[0]:,}")
    print(f"   Columns: {df_combined.shape[1]}")
    
    print(f"\n4. Data quality checks...")
    print(f"   Unique VAERS_IDs: {df_combined.select('VAERS_ID').n_unique():,}")
    
    print(f"\n5. Writing Parquet file...")
    
    import os
    os.makedirs('../data/processed', exist_ok=True)
    
    df_combined.write_parquet('../data/processed/vaers_data.parquet')
    
    print(f"   ✓ Saved: data/processed/vaers_data.parquet")
    
    print("\n" + "=" * 80)
    print("✓ VAERS DATA ETL COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    etl_vaers_data()
