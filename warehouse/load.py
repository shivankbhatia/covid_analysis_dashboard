"""
Warehouse loader - creates DuckDB schema and loads data from processed Parquet files.
Phase 4: Warehouse Construction

Updated for Phase 5: Proper dimension key mapping for age, gender, race, location, vaccine.
"""
import duckdb
import os

def create_warehouse():
    """Create DuckDB warehouse and load schema."""
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths
    db_path = os.path.join(script_dir, '../data/warehouse/covid_analytics.duckdb')
    schema_path = os.path.join(script_dir, 'schema.sql')
    
    # Remove existing database to rebuild cleanly
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to DuckDB
    con = duckdb.connect(db_path)
    
    print("Creating schema...")
    
    # Read and execute schema
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Execute schema creation
    con.execute(schema_sql)
    
    print("[OK] Schema created")
    
    # Load dimensions
    print("\nLoading dimension tables...")
    load_dimensions(con, script_dir)
    
    # Load fact tables
    print("\nLoading fact tables...")
    load_facts(con, script_dir)
    
    # Validate
    print("\nValidating warehouse...")
    validate_warehouse(con)
    
    con.close()
    print(f"\n[OK] Warehouse created successfully at {db_path}")

def load_dimensions(con, script_dir):
    """Load dimension tables."""
    # Build base path for data files
    base_path = os.path.join(script_dir, '..')
    processed_path = os.path.join(base_path, 'data', 'processed')
    
    # dim_age
    con.execute("""
        INSERT INTO dim_age VALUES
        (1, '0-17', 0, 17),
        (2, '18-29', 18, 29),
        (3, '30-44', 30, 44),
        (4, '45-59', 45, 59),
        (5, '60-74', 60, 74),
        (6, '75+', 75, 120),
        (7, 'Unknown', NULL, NULL)
    """)
    print("  [OK] dim_age loaded (7 rows)")
    
    # dim_gender
    con.execute("""
        INSERT INTO dim_gender VALUES
        (1, 'Male'),
        (2, 'Female'),
        (3, 'Unknown')
    """)
    print("  [OK] dim_gender loaded (3 rows)")
    
    # dim_race
    con.execute("""
        INSERT INTO dim_race VALUES
        (1, 'White'),
        (2, 'Black/African American'),
        (3, 'Hispanic/Latino'),
        (4, 'Asian'),
        (5, 'American Indian/Alaska Native'),
        (6, 'Native Hawaiian/Other Pacific Islander'),
        (7, 'Multiracial'),
        (8, 'Unknown/Other')
    """)
    print("  [OK] dim_race loaded (8 rows)")
    
    # dim_location - load US states
    states = [
        (1, 'AL', 'Alabama'), (2, 'AK', 'Alaska'), (3, 'AZ', 'Arizona'),
        (4, 'AR', 'Arkansas'), (5, 'CA', 'California'), (6, 'CO', 'Colorado'),
        (7, 'CT', 'Connecticut'), (8, 'DE', 'Delaware'), (9, 'FL', 'Florida'),
        (10, 'GA', 'Georgia'), (11, 'HI', 'Hawaii'), (12, 'ID', 'Idaho'),
        (13, 'IL', 'Illinois'), (14, 'IN', 'Indiana'), (15, 'IA', 'Iowa'),
        (16, 'KS', 'Kansas'), (17, 'KY', 'Kentucky'), (18, 'LA', 'Louisiana'),
        (19, 'ME', 'Maine'), (20, 'MD', 'Maryland'), (21, 'MA', 'Massachusetts'),
        (22, 'MI', 'Michigan'), (23, 'MN', 'Minnesota'), (24, 'MS', 'Mississippi'),
        (25, 'MO', 'Missouri'), (26, 'MT', 'Montana'), (27, 'NE', 'Nebraska'),
        (28, 'NV', 'Nevada'), (29, 'NH', 'New Hampshire'), (30, 'NJ', 'New Jersey'),
        (31, 'NM', 'New Mexico'), (32, 'NY', 'New York'), (33, 'NC', 'North Carolina'),
        (34, 'ND', 'North Dakota'), (35, 'OH', 'Ohio'), (36, 'OK', 'Oklahoma'),
        (37, 'OR', 'Oregon'), (38, 'PA', 'Pennsylvania'), (39, 'RI', 'Rhode Island'),
        (40, 'SC', 'South Carolina'), (41, 'SD', 'South Dakota'), (42, 'TN', 'Tennessee'),
        (43, 'TX', 'Texas'), (44, 'UT', 'Utah'), (45, 'VT', 'Vermont'),
        (46, 'VA', 'Virginia'), (47, 'WA', 'Washington'), (48, 'WV', 'West Virginia'),
        (49, 'WI', 'Wisconsin'), (50, 'WY', 'Wyoming'), (51, 'DC', 'District of Columbia')
    ]
    
    for loc_id, state_code, state_name in states:
        con.execute(
            "INSERT INTO dim_location VALUES (?, ?, ?, NULL)",
            [loc_id, state_code, state_name]
        )
    print(f"  [OK] dim_location loaded ({len(states)} states)")
    
    # dim_vaccine - extract unique vaccines from VAERS data
    vaers_vax_path = os.path.join(processed_path, 'vaers_vax_covid.parquet').replace('\\', '/')
    result = con.execute(f"""
        SELECT DISTINCT VAX_MANU FROM read_parquet(
            '{vaers_vax_path}'
        ) WHERE VAX_MANU IS NOT NULL
        ORDER BY VAX_MANU
    """).fetchall()
    
    vaccine_manufacturers = [(i+1, mfr[0]) for i, mfr in enumerate(result)]
    for vac_id, mfr in vaccine_manufacturers:
        con.execute(
            "INSERT INTO dim_vaccine (vaccine_id, manufacturer) VALUES (?, ?)",
            [vac_id, mfr]
        )
    print(f"  [OK] dim_vaccine loaded ({len(vaccine_manufacturers)} manufacturers)")
    
    # dim_symptom - extract unique symptoms from VAERS symptoms
    vaers_sym_path = os.path.join(processed_path, 'vaers_symptoms_long.parquet').replace('\\', '/')
    result = con.execute(f"""
        SELECT DISTINCT symptom FROM read_parquet(
            '{vaers_sym_path}'
        ) WHERE symptom IS NOT NULL
        ORDER BY symptom
    """).fetchall()
    
    symptoms = [(i+1, sym[0]) for i, sym in enumerate(result)]
    for sym_id, symptom in symptoms:
        con.execute(
            "INSERT INTO dim_symptom VALUES (?, ?)",
            [sym_id, symptom]
        )
    print(f"  [OK] dim_symptom loaded ({len(symptoms)} symptoms)")

def load_facts(con, script_dir):
    """Load fact tables from Parquet files with proper dimension key mapping."""
    
    # Build base path for data files
    base_path = os.path.join(script_dir, '..')
    processed_path = os.path.join(base_path, 'data', 'processed')
    
    # ========================================================================
    # fact_covid_cases — with proper age, gender, race dimension mapping
    # ========================================================================
    cdc_path = os.path.join(processed_path, 'cdc_cases.parquet').replace('\\', '/')
    result = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{cdc_path}')
    """).fetchone()
    cdc_count = result[0]
    
    # Note: CDC Public Use data does not include state, so location_id defaults to NULL
    # Age mapping: parquet age_group already standardised by ETL (0-17, 18-29, etc.)
    con.execute(f"""
        INSERT INTO fact_covid_cases
        SELECT
            row_number() OVER () as case_id,
            CASE 
                WHEN case_month IS NOT NULL THEN CAST(case_month || '/01' AS DATE)
                ELSE NULL
            END as case_month,
            NULL as location_id,
            -- Map age_group text to dim_age.age_id
            CASE age_group
                WHEN '0-17'    THEN 1
                WHEN '18-29'   THEN 2
                WHEN '30-44'   THEN 3
                WHEN '45-59'   THEN 4
                WHEN '60-74'   THEN 5
                WHEN '75+'     THEN 6
                ELSE 7
            END as age_id,
            -- Map sex to dim_gender.gender_id
            CASE 
                WHEN sex = 'Male' THEN 1 
                WHEN sex = 'Female' THEN 2 
                ELSE 3 
            END as gender_id,
            -- Map race_ethnicity_combined to dim_race.race_id
            CASE
                WHEN race_ethnicity_combined LIKE '%White%' THEN 1
                WHEN race_ethnicity_combined LIKE '%Black%' THEN 2
                WHEN race_ethnicity_combined LIKE '%Hispanic%' THEN 3
                WHEN race_ethnicity_combined LIKE '%Asian%' THEN 4
                WHEN race_ethnicity_combined LIKE '%Indian%' OR race_ethnicity_combined LIKE '%Alaska%' THEN 5
                WHEN race_ethnicity_combined LIKE '%Hawaiian%' OR race_ethnicity_combined LIKE '%Pacific%' THEN 6
                WHEN race_ethnicity_combined LIKE '%Multiple%' THEN 7
                ELSE 8
            END as race_id,
            hosp_yn,
            icu_yn,
            death_yn,
            0 as underlying_yn
        FROM read_parquet('{cdc_path}')
        LIMIT 10000
    """)
    print(f"  [OK] fact_covid_cases loaded (sample: 10,000 rows, total available: {cdc_count:,})")
    
    # ========================================================================
    # fact_vaccine_events — with age bucketing, state mapping, vaccine mapping
    # ========================================================================
    vaers_data_path = os.path.join(processed_path, 'vaers_data.parquet').replace('\\', '/')
    vaers_vax_path = os.path.join(processed_path, 'vaers_vax_covid.parquet').replace('\\', '/')
    vaers_count = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{vaers_data_path}')
    """).fetchone()[0]
    
    # Step 1: Create a temp table mapping VAERS_ID -> manufacturer (one row per ID)
    con.execute(f"""
        CREATE TEMPORARY TABLE tmp_vaers_vax AS
        SELECT VAERS_ID, VAX_MANU as manufacturer
        FROM (
            SELECT VAERS_ID, VAX_MANU,
                   ROW_NUMBER() OVER (PARTITION BY VAERS_ID ORDER BY VAX_MANU) as rn
            FROM read_parquet('{vaers_vax_path}')
        ) sub
        WHERE rn = 1
    """)
    
    con.execute(f"""
        INSERT INTO fact_vaccine_events
        SELECT
            row_number() OVER () as event_id,
            d.VAERS_ID as vaers_id,
            CASE WHEN d.RPT_DATE IS NOT NULL 
                THEN CAST(strptime(d.RPT_DATE, '%m/%d/%Y') AS DATE)
                ELSE NULL
            END as rpt_date,
            -- Map AGE_YRS to dim_age buckets
            CASE
                WHEN d.AGE_YRS IS NULL THEN 7
                WHEN d.AGE_YRS < 18 THEN 1
                WHEN d.AGE_YRS < 30 THEN 2
                WHEN d.AGE_YRS < 45 THEN 3
                WHEN d.AGE_YRS < 60 THEN 4
                WHEN d.AGE_YRS < 75 THEN 5
                WHEN d.AGE_YRS <= 120 THEN 6
                ELSE 7
            END as age_id,
            -- Map SEX to dim_gender
            CASE d.SEX 
                WHEN 'M' THEN 1 
                WHEN 'F' THEN 2 
                ELSE 3 
            END as gender_id,
            -- Map STATE to dim_location (UPPER to handle case variations)
            dl.location_id as location_id,
            -- Map manufacturer to dim_vaccine
            dv.vaccine_id as vaccine_id,
            CASE WHEN d.DIED = 'Y' THEN 1 ELSE 0 END as died,
            CASE WHEN d.HOSPITAL = 'Y' THEN 1 ELSE 0 END as hospital,
            CASE WHEN d.DISABLE = 'Y' THEN 1 ELSE 0 END as disable,
            CASE WHEN d.RECOVD = 'Y' THEN 1 ELSE 0 END as recovered,
            CASE WHEN d.ER_VISIT = 'Y' THEN 1 ELSE 0 END as er_visit,
            CAST(d.NUMDAYS AS INTEGER) as onset_days
        FROM read_parquet('{vaers_data_path}') d
        -- INNER JOIN to filter to only COVID-19 vaccine reports
        INNER JOIN tmp_vaers_vax tv ON d.VAERS_ID = tv.VAERS_ID
        LEFT JOIN dim_location dl ON UPPER(d.STATE) = dl.state_code
        INNER JOIN dim_vaccine dv ON tv.manufacturer = dv.manufacturer
        LIMIT 10000
    """)
    
    con.execute("DROP TABLE IF EXISTS tmp_vaers_vax")
    print(f"  [OK] fact_vaccine_events loaded (sample: 10,000 rows, total available: {vaers_count:,})")
    
    # ========================================================================
    # fact_vaccine_symptoms
    # ========================================================================
    vaers_sym_path = os.path.join(processed_path, 'vaers_symptoms_long.parquet').replace('\\', '/')
    symp_count = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{vaers_sym_path}')
    """).fetchone()[0]
    
    con.execute(f"""
        INSERT INTO fact_vaccine_symptoms
        SELECT DISTINCT
            v.VAERS_ID as vaers_id,
            ds.symptom_id
        FROM read_parquet('{vaers_sym_path}') v
        JOIN dim_symptom ds ON v.symptom = ds.symptom
        WHERE v.symptom IS NOT NULL
        LIMIT 100000
    """)
    print(f"  [OK] fact_vaccine_symptoms loaded (sample: 100,000 rows, total available: {symp_count:,})")
    
    # ========================================================================
    # fact_hospital_capacity
    # ========================================================================
    hhs_path = os.path.join(processed_path, 'hhs_hospital.parquet').replace('\\', '/')
    hhs_count = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{hhs_path}')
    """).fetchone()[0]
    
    con.execute(f"""
        INSERT INTO fact_hospital_capacity
        SELECT
            row_number() OVER () as capacity_id,
            CAST(collection_week AS DATE) as collection_week,
            dl.location_id as location_id,
            0 as covid_inpatient,
            0 as covid_icu,
            0 as covid_admissions
        FROM read_parquet('{hhs_path}') h
        -- HHS uses 2-letter state codes
        LEFT JOIN dim_location dl ON UPPER(TRIM(h.state)) = dl.state_code
    """)
    print(f"  [OK] fact_hospital_capacity loaded ({hhs_count:,} rows) [Note: numeric columns not in source]")
    
    # ========================================================================
    # fact_mortality — with state and demographic mapping
    # ========================================================================
    mort_path = os.path.join(processed_path, 'nchs_mortality.parquet').replace('\\', '/')
    mort_count = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{mort_path}')
    """).fetchone()[0]
    
    sql = f"""
        INSERT INTO fact_mortality
        SELECT
            row_number() OVER () as mortality_id,
            CASE WHEN m."start date" IS NOT NULL 
                THEN CAST(strptime(m."start date", '%m/%d/%Y') AS DATE)
                ELSE NULL
            END as period_start,
            CASE WHEN m."end date" IS NOT NULL 
                THEN CAST(strptime(m."end date", '%m/%d/%Y') AS DATE)
                ELSE NULL
            END as period_end,
            dl.location_id as location_id,
            -- Map NCHS age groups to dim_age
            CASE
                WHEN m."age group" IN ('Under 1 year', '0-17 years', '1-4 years', '5-14 years', '15-24 years') THEN 1
                WHEN m."age group" IN ('18-29 years', '25-34 years') THEN 2
                WHEN m."age group" IN ('30-44 years', '35-44 years') THEN 3
                WHEN m."age group" IN ('45-54 years', '45-59 years', '55-64 years') THEN 4
                WHEN m."age group" IN ('60-74 years', '65-74 years') THEN 5
                WHEN m."age group" IN ('75-84 years', '85 years and over', '75+') THEN 6
                ELSE 7
            END as age_id,
            CASE m.sex 
                WHEN 'Male' THEN 1 
                WHEN 'Female' THEN 2 
                ELSE 3 
            END as gender_id,
            CAST(REPLACE(m."covid-19 deaths", ',', '') AS INTEGER) as covid_deaths,
            CAST(REPLACE(m."total deaths", ',', '') AS INTEGER) as total_deaths
        FROM read_parquet('{mort_path}') m
        -- NCHS uses full state names ('Alabama'), so join on state_name
        LEFT JOIN dim_location dl ON m.state = dl.state_name
    """
    con.execute(sql)
    print(f"  [OK] fact_mortality loaded ({mort_count:,} rows)")

def validate_warehouse(con):
    """Validate warehouse integrity."""
    
    # Check row counts
    tables = [
        ('dim_age', 'dimensions'),
        ('dim_gender', 'dimensions'),
        ('dim_race', 'dimensions'),
        ('dim_location', 'dimensions'),
        ('dim_vaccine', 'dimensions'),
        ('dim_symptom', 'dimensions'),
        ('fact_covid_cases', 'facts'),
        ('fact_vaccine_events', 'facts'),
        ('fact_vaccine_symptoms', 'facts'),
        ('fact_hospital_capacity', 'facts'),
        ('fact_mortality', 'facts'),
    ]
    
    print("\n  Row counts by table:")
    total_rows = 0
    for table_name, table_type in tables:
        try:
            result = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            count = result[0]
            total_rows += count
            status = "[OK]" if count > 0 else "[!!]"
            print(f"    {status} {table_name}: {count:,} rows")
        except Exception as e:
            print(f"    [ERR] {table_name}: ERROR - {e}")
    
    print(f"\n  Total rows loaded: {total_rows:,}")
    
    # Validate dimension key distribution in fact tables
    print("\n  Dimension key distribution checks:")
    
    # CDC cases - age distribution
    r = con.execute("""
        SELECT a.age_group, COUNT(*) as cnt 
        FROM fact_covid_cases c 
        JOIN dim_age a ON c.age_id = a.age_id 
        GROUP BY a.age_group ORDER BY cnt DESC
    """).fetchall()
    print("    Age groups in CDC cases:", [(row[0], row[1]) for row in r])
    
    # CDC cases - race distribution  
    r = con.execute("""
        SELECT r.race, COUNT(*) as cnt 
        FROM fact_covid_cases c 
        JOIN dim_race r ON c.race_id = r.race_id 
        GROUP BY r.race ORDER BY cnt DESC
    """).fetchall()
    print("    Races in CDC cases:", [(row[0], row[1]) for row in r])
    
    # VAERS - vaccine distribution
    r = con.execute("""
        SELECT v.manufacturer, COUNT(*) as cnt 
        FROM fact_vaccine_events e 
        JOIN dim_vaccine v ON e.vaccine_id = v.vaccine_id 
        GROUP BY v.manufacturer ORDER BY cnt DESC
    """).fetchall()
    print("    Vaccines in VAERS events:", [(row[0], row[1]) for row in r])
    
    # VAERS - state distribution (top 5)
    r = con.execute("""
        SELECT l.state_code, COUNT(*) as cnt 
        FROM fact_vaccine_events e 
        JOIN dim_location l ON e.location_id = l.location_id 
        GROUP BY l.state_code ORDER BY cnt DESC LIMIT 5
    """).fetchall()
    print("    Top 5 states in VAERS:", [(row[0], row[1]) for row in r])
    
    # Mortality - state distribution (top 5)
    r = con.execute("""
        SELECT l.state_code, COUNT(*) as cnt 
        FROM fact_mortality m 
        JOIN dim_location l ON m.location_id = l.location_id 
        GROUP BY l.state_code ORDER BY cnt DESC LIMIT 5
    """).fetchall()
    print("    Top 5 states in mortality:", [(row[0], row[1]) for row in r])
    
    print("\n  STATUS: Warehouse loaded with proper dimension mapping (fact tables use samples)")

if __name__ == '__main__':
    create_warehouse()
