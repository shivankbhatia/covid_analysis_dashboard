"""
CDC Case Surveillance ETL (Updated for cdc_cases_new.csv)
Transforms raw CDC case data into processed Parquet format.

Uses pure DuckDB SQL to process the entire file with minimal memory (~1-2 GB).
DuckDB automatically spills to disk, so the 18.6 GB CSV never needs to fit in RAM.

Source: cdc_cases_new.csv (~18.6 GB)
Key columns retained: case_month, res_state, res_county, age_group, sex,
                       race_ethnicity_combined (derived), hosp_yn, icu_yn,
                       death_yn, underlying_conditions_yn
"""
import duckdb
import os

# Number of rows to process. Set to None for full dataset.
ROW_LIMIT = None


def etl_cdc_cases():
    """Load, transform, and save CDC case surveillance data from cdc_cases_new.csv.

    All transformations are pushed into a single DuckDB SQL query so the data
    is streamed from CSV -> transform -> Parquet without ever materialising the
    full dataset in Python memory.
    """

    print("=" * 80)
    print("CDC CASE SURVEILLANCE ETL (cdc_cases_new.csv) — DuckDB Streaming")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.normpath(
        os.path.join(script_dir, '../data/raw/cdc_cases_new.csv')
    ).replace('\\', '/')
    output_path = os.path.normpath(
        os.path.join(script_dir, '../data/processed/cdc_cases.parquet')
    ).replace('\\', '/')

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"\n   Source : {raw_path}")
    print(f"   Output: {output_path}")

    con = duckdb.connect()  # in-memory; DuckDB will spill to disk as needed

    # ------------------------------------------------------------------
    # 1. Count total rows (lightweight — DuckDB streams through the file)
    # ------------------------------------------------------------------
    print("\n1. Counting rows in source CSV...")
    total_rows = con.execute(
        f"SELECT COUNT(*) FROM read_csv_auto('{raw_path}', "
        f"sample_size=100000, all_varchar=true)"
    ).fetchone()[0]
    print(f"   Total rows in file: {total_rows:,}")

    # ------------------------------------------------------------------
    # 2. Build the transform query
    #    Reproduces the original Polars transforms in SQL:
    #      - Select only needed columns
    #      - Combine race + ethnicity → race_ethnicity_combined
    #      - Map age_group to standard buckets (0-17, 18-29, …, 75+, Unknown)
    #      - Normalise Yes/No columns to 1/0/NULL
    #      - UPPER + TRIM res_state and res_county
    #      - Filter rows where BOTH hosp_yn AND death_yn are NULL
    # ------------------------------------------------------------------
    print("\n2. Transforming and writing Parquet (streaming — constant memory)...")

    limit_clause = f"LIMIT {ROW_LIMIT}" if ROW_LIMIT else ""

    transform_sql = f"""
        COPY (
            SELECT
                case_month,
                UPPER(TRIM(res_state))  AS res_state,
                UPPER(TRIM(res_county)) AS res_county,

                -- Age-group mapping (matches utils.standardise_age_group)
                CASE
                    -- Old CDC labels
                    WHEN age_group IN ('0 - 9 Years', '10 - 19 Years')         THEN '0-17'
                    WHEN age_group = '20 - 29 Years'                            THEN '18-29'
                    WHEN age_group IN ('30 - 39 Years', '40 - 49 Years')        THEN '30-44'
                    WHEN age_group IN ('50 - 59 Years')                         THEN '45-59'
                    WHEN age_group IN ('60 - 69 Years', '70 - 79 Years')        THEN '60-74'
                    WHEN age_group = '80+ Years'                                THEN '75+'
                    -- New CDC labels (cdc_cases_new.csv)
                    WHEN age_group = '0 - 17 years'                             THEN '0-17'
                    WHEN age_group = '18 to 49 years'                           THEN '30-44'
                    WHEN age_group = '50 to 64 years'                           THEN '45-59'
                    WHEN age_group = '65+ years'                                THEN '60-74'
                    -- Legacy / alternate
                    WHEN age_group = '18 to 29 years'                           THEN '18-29'
                    WHEN age_group = '30 to 49 years'                           THEN '30-44'
                    ELSE 'Unknown'
                END AS age_group,

                sex,

                -- Combine race + ethnicity → race_ethnicity_combined
                CASE
                    WHEN ethnicity = 'Hispanic/Latino' THEN 'Hispanic/Latino'
                    WHEN race IS NOT NULL              THEN race || ', Non-Hispanic'
                    ELSE 'Unknown'
                END AS race_ethnicity_combined,

                -- Normalise Yes/No outcome columns → 1/0/NULL
                CASE hosp_yn
                    WHEN 'Yes' THEN 1  WHEN 'No' THEN 0  ELSE NULL
                END AS hosp_yn,
                CASE icu_yn
                    WHEN 'Yes' THEN 1  WHEN 'No' THEN 0  ELSE NULL
                END AS icu_yn,
                CASE death_yn
                    WHEN 'Yes' THEN 1  WHEN 'No' THEN 0  ELSE NULL
                END AS death_yn,
                CASE underlying_conditions_yn
                    WHEN 'Yes' THEN 1  WHEN 'No' THEN 0  ELSE NULL
                END AS underlying_conditions_yn

            FROM read_csv_auto(
                '{raw_path}',
                sample_size = 100000,
                all_varchar = true
            )
            WHERE NOT (hosp_yn IS NULL AND death_yn IS NULL)
            {limit_clause}
        ) TO '{output_path}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """

    con.execute(transform_sql)
    print("   [OK] Parquet written successfully.")

    # ------------------------------------------------------------------
    # 3-8. Compute diagnostic statistics from the output Parquet
    #       (lightweight reads — Parquet is small & columnar)
    # ------------------------------------------------------------------
    pq = f"read_parquet('{output_path}')"

    row_count = con.execute(f"SELECT COUNT(*) FROM {pq}").fetchone()[0]
    removed = total_rows - row_count
    print(f"\n3. Row summary")
    print(f"   Source rows   : {total_rows:,}")
    print(f"   Rows removed  : {removed:,}  (both hosp_yn and death_yn null)")
    print(f"   Output rows   : {row_count:,}")

    # Race/ethnicity distribution
    print("\n4. Race/ethnicity distribution (top 8):")
    race_rows = con.execute(
        f"SELECT race_ethnicity_combined, COUNT(*) AS n FROM {pq} "
        f"GROUP BY 1 ORDER BY 2 DESC LIMIT 8"
    ).fetchall()
    for race, n in race_rows:
        print(f"     {race}: {n:,}")

    # Age-group distribution
    print("\n5. Age-group distribution:")
    age_rows = con.execute(
        f"SELECT age_group, COUNT(*) AS n FROM {pq} "
        f"GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall()
    for ag, n in age_rows:
        print(f"     {ag}: {n:,}")

    # Geographic stats
    state_count = con.execute(
        f"SELECT COUNT(DISTINCT res_state) FROM {pq}"
    ).fetchone()[0]
    county_count = con.execute(
        f"SELECT COUNT(DISTINCT res_county) FROM {pq}"
    ).fetchone()[0]
    null_state = con.execute(
        f"SELECT COUNT(*) FROM {pq} WHERE res_state IS NULL"
    ).fetchone()[0]
    print(f"\n6. Geographic stats")
    print(f"   Distinct states  : {state_count}")
    print(f"   Distinct counties: {county_count}")
    print(f"   Null res_state   : {null_state:,} ({null_state/row_count*100:.2f}%)")

    # Outcome rates
    death_count = con.execute(
        f"SELECT COUNT(*) FROM {pq} WHERE death_yn = 1"
    ).fetchone()[0]
    hosp_count = con.execute(
        f"SELECT COUNT(*) FROM {pq} WHERE hosp_yn = 1"
    ).fetchone()[0]
    print(f"\n7. Data quality checks")
    print(f"   Death rate         : {death_count/row_count:.4f} "
          f"({death_count/row_count*100:.2f}%) [{death_count:,} deaths]")
    print(f"   Hospitalization rate: {hosp_count/row_count:.4f} "
          f"({hosp_count/row_count*100:.2f}%) [{hosp_count:,} hospitalizations]")

    # File size
    file_size_mb = os.path.getsize(output_path.replace('/', os.sep)) / (1024 * 1024)
    print(f"\n8. Output file")
    print(f"   Path : {output_path}")
    print(f"   Size : {file_size_mb:.1f} MB")

    con.close()

    print("\n" + "=" * 80)
    print("[OK] CDC ETL COMPLETE (cdc_cases_new.csv) — DuckDB Streaming")
    print("=" * 80)


if __name__ == '__main__':
    etl_cdc_cases()
