"""
VAERS Symptoms ETL
Transforms wide symptom data into long format.
Concatenates data from 2020-2023.
"""
import polars as pl
import pandas as pd
from pathlib import Path

def etl_vaers_symptoms():
    """Load, transform, and save VAERS symptoms (long format)."""
    
    print("=" * 80)
    print("VAERS SYMPTOMS ETL")
    print("=" * 80)
    
    print("\n1. Discovering VAERS symptoms files...")
    
    data_dir = Path('../data/raw')
    symptoms_files = sorted(data_dir.glob('*VAERSSYMPTOMS.csv'))
    
    print(f"   Found {len(symptoms_files)} files:")
    for f in symptoms_files:
        print(f"     - {f.name}")
    
    dfs_long = []
    
    for filepath in symptoms_files:
        print(f"\n2. Reading {filepath.name}...")
        
        try:
            df = pd.read_csv(filepath, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            print("   UTF-8 decode failed, trying latin-1...")
            df = pd.read_csv(filepath, encoding='latin-1', low_memory=False)
        
        print(f"   Loaded: {len(df):,} rows")
        
        # Convert to polars
        df_pl = pl.from_pandas(df)
        
        # Select VAERS_ID and SYMPTOM columns
        symptom_cols = [c for c in df_pl.columns if 'SYMPTOM' in c and 'VERSION' not in c]
        
        # Unpivot from wide to long format
        df_long = df_pl.select(['VAERS_ID'] + symptom_cols).unpivot(
            on=symptom_cols,
            index='VAERS_ID',
            value_name='symptom'
        ).filter(pl.col('symptom').is_not_null())
        
        print(f"   Pivoted to long format: {df_long.shape[0]:,} rows")
        
        dfs_long.append(df_long)
    
    print(f"\n3. Concatenating all years...")
    
    df_combined = pl.concat(dfs_long, how='vertical')
    
    # Clean symptom names (strip whitespace, remove nulls)
    df_combined = df_combined.with_columns([
        pl.col('symptom').str.strip_chars().alias('symptom')
    ]).filter(pl.col('symptom') != '')
    
    print(f"   Total rows: {df_combined.shape[0]:,}")
    print(f"   Unique symptoms: {df_combined.select('symptom').n_unique():,}")
    
    print(f"\n4. Writing Parquet file...")
    
    import os
    os.makedirs('../data/processed', exist_ok=True)
    
    df_combined.write_parquet('../data/processed/vaers_symptoms_long.parquet')
    
    print(f"   ✓ Saved: data/processed/vaers_symptoms_long.parquet")
    
    print("\n" + "=" * 80)
    print("✓ VAERS SYMPTOMS ETL COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    etl_vaers_symptoms()
