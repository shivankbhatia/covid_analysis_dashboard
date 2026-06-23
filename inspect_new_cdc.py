"""Inspect cdc_cases_new.csv to understand the data shape and key columns."""
import duckdb

con = duckdb.connect()

print("=== Row count ===")
cnt = con.execute("SELECT COUNT(*) FROM read_csv_auto('data/raw/cdc_cases_new.csv', sample_size=100000)").fetchone()[0]
print(f"Total rows: {cnt:,}")

print("\n=== Distinct age_group ===")
r = con.execute("SELECT DISTINCT age_group FROM read_csv_auto('data/raw/cdc_cases_new.csv', sample_size=100000) ORDER BY age_group").fetchall()
for row in r: print(f"  {row[0]}")

print("\n=== Distinct sex ===")
r = con.execute("SELECT DISTINCT sex FROM read_csv_auto('data/raw/cdc_cases_new.csv', sample_size=100000) ORDER BY sex").fetchall()
for row in r: print(f"  {row[0]}")

print("\n=== Distinct race ===")
r = con.execute("SELECT DISTINCT race FROM read_csv_auto('data/raw/cdc_cases_new.csv', sample_size=100000) ORDER BY race").fetchall()
for row in r: print(f"  {row[0]}")

print("\n=== Distinct ethnicity ===")
r = con.execute("SELECT DISTINCT ethnicity FROM read_csv_auto('data/raw/cdc_cases_new.csv', sample_size=100000) ORDER BY ethnicity").fetchall()
for row in r: print(f"  {row[0]}")

print("\n=== Distinct res_state (sample) ===")
r = con.execute("SELECT DISTINCT res_state FROM read_csv_auto('data/raw/cdc_cases_new.csv', sample_size=100000) ORDER BY res_state LIMIT 20").fetchall()
for row in r: print(f"  {row[0]}")

print("\n=== Distinct res_county (top 10 by count) ===")
r = con.execute("SELECT res_county, COUNT(*) as cnt FROM read_csv_auto('data/raw/cdc_cases_new.csv', sample_size=100000) GROUP BY res_county ORDER BY cnt DESC LIMIT 10").fetchall()
for row in r: print(f"  {row[0]}: {row[1]:,}")

print("\n=== Sample hosp/icu/death values ===")
r = con.execute("SELECT DISTINCT hosp_yn FROM read_csv_auto('data/raw/cdc_cases_new.csv', sample_size=100000) ORDER BY hosp_yn").fetchall()
print("hosp_yn:", [row[0] for row in r])
r = con.execute("SELECT DISTINCT death_yn FROM read_csv_auto('data/raw/cdc_cases_new.csv', sample_size=100000) ORDER BY death_yn").fetchall()
print("death_yn:", [row[0] for row in r])

con.close()
