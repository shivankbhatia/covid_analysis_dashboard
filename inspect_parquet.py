import duckdb
import os

con = duckdb.connect()
processed_path = "data/processed"

files = [
    'vaers_vax_covid.parquet',
    'vaers_symptoms_long.parquet',
    'cdc_cases.parquet',
    'vaers_data.parquet',
    'hhs_hospital.parquet',
    'nchs_mortality.parquet'
]

for fname in files:
    fpath = os.path.join(processed_path, fname)
    if os.path.exists(fpath):
        print(f"\n{'='*60}")
        print(f"{fname}")
        print('='*60)
        try:
            df = con.execute(f"SELECT * FROM read_parquet('{fpath}') LIMIT 1").df()
            cols = df.columns.tolist()
            print(f"Columns ({len(cols)}): {cols}")
            count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{fpath}')").fetchone()[0]
            print(f"Total rows: {count:,}")
            print("\nSample row:")
            print(df.to_string())
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"\n{'='*60}")
        print(f"{fname} === NOT FOUND")
        print('='*60)
