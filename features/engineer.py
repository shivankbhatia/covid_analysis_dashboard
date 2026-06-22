"""
Phase 5: Feature Engineering Pipeline
Computes derived features from warehouse data and saves to Parquet files.

Features produced:
  - features_cases.parquet      : Case-level outcomes with severity scores and demographic rates
  - features_vaccine_events.parquet : Vaccine adverse event features with severity and onset categories
  - symptom_cooccurrence.parquet : Symptom pair co-occurrence counts
  - geo_covid_rates.parquet     : State-level COVID-19 case rates (from mortality data)
  - geo_hospital_burden.parquet : State-level hospital burden by week
  - geo_mortality_rates.parquet : State-level mortality rates by gender
"""
import duckdb
import os
import pandas as pd
from pathlib import Path


def engineer_features():
    """Compute and save engineered features from warehouse data."""
    
    # Get the script directory and construct paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(script_dir, '..')
    db_path = os.path.join(base_path, 'data', 'warehouse', 'covid_analytics.duckdb')
    output_path = os.path.join(base_path, 'data', 'processed')
    
    # Create connection
    con = duckdb.connect(db_path, read_only=True)
    
    print("=" * 70)
    print("PHASE 5: FEATURE ENGINEERING")
    print("=" * 70)
    
    # Feature 1: Case-level outcome features
    print("\n1. Engineering case-level outcome features...")
    engineer_case_features(con, output_path)
    
    # Feature 2: Vaccine adverse event features
    print("\n2. Engineering vaccine adverse event features...")
    engineer_vaccine_features(con, output_path)
    
    # Feature 3: Symptom co-occurrence matrix
    print("\n3. Computing symptom co-occurrence matrix...")
    engineer_symptom_cooccurrence(con, output_path)
    
    # Feature 4: Geographic aggregates
    print("\n4. Computing geographic aggregates...")
    engineer_geographic_features(con, output_path)
    
    con.close()
    print("\n" + "=" * 70)
    print("[OK] FEATURE ENGINEERING COMPLETE")
    print("=" * 70)

def engineer_case_features(con, output_path):
    """
    Compute case-level features from COVID-19 case data.
    Features: severity_score, demographic rates, temporal patterns
    """
    
    query = """
    SELECT
        c.case_id,
        c.case_month,
        a.age_group,
        g.gender,
        r.race,
        c.hosp_yn,
        c.icu_yn,
        c.death_yn,
        c.underlying_yn,
        -- Severity score: 0=no severe outcome, 1=hospitalized, 2=ICU, 3=death
        CASE
            WHEN c.death_yn = 1 THEN 3
            WHEN c.icu_yn = 1 THEN 2
            WHEN c.hosp_yn = 1 THEN 1
            ELSE 0
        END AS severity_score,
        -- Outcome flags
        COALESCE(c.hosp_yn, 0) AS hospitalized,
        COALESCE(c.icu_yn, 0) AS icu_admitted,
        COALESCE(c.death_yn, 0) AS deceased,
        -- Group-level rates (for demographics analysis)
        ROUND(100.0 * AVG(COALESCE(c.hosp_yn, 0)) 
            OVER (PARTITION BY a.age_id), 2) AS hosp_rate_by_age_pct,
        ROUND(100.0 * AVG(COALESCE(c.death_yn, 0)) 
            OVER (PARTITION BY a.age_id), 2) AS death_rate_by_age_pct,
        ROUND(100.0 * AVG(COALESCE(c.icu_yn, 0)) 
            OVER (PARTITION BY a.age_id), 2) AS icu_rate_by_age_pct,
        ROUND(100.0 * AVG(COALESCE(c.hosp_yn, 0)) 
            OVER (PARTITION BY g.gender_id), 2) AS hosp_rate_by_gender_pct,
        ROUND(100.0 * AVG(COALESCE(c.death_yn, 0)) 
            OVER (PARTITION BY g.gender_id), 2) AS death_rate_by_gender_pct,
        -- Temporal feature
        EXTRACT(YEAR FROM c.case_month) AS year,
        EXTRACT(MONTH FROM c.case_month) AS month
    FROM fact_covid_cases c
    JOIN dim_age a ON c.age_id = a.age_id
    JOIN dim_gender g ON c.gender_id = g.gender_id
    JOIN dim_race r ON c.race_id = r.race_id
    """
    
    features_df = con.execute(query).df()
    
    output_file = os.path.join(output_path, 'features_cases.parquet')
    features_df.to_parquet(output_file, index=False)
    
    print(f"  [OK] Case features: {len(features_df):,} records")
    print(f"    - Severity scores computed")
    print(f"    - Severity distribution: {dict(features_df['severity_score'].value_counts().sort_index())}")
    print(f"    - Outcome rates by age/gender")
    print(f"    - Saved to: features_cases.parquet")

def engineer_vaccine_features(con, output_path):
    """
    Compute vaccine adverse event features.
    Features: symptom count, severity scores, onset categories
    """
    
    query = """
    SELECT
        v.event_id,
        v.vaers_id,
        v.rpt_date,
        a.age_group,
        g.gender,
        COALESCE(m.manufacturer, 'Unknown') as manufacturer,
        l.state_code,
        v.died,
        v.hospital,
        v.disable,
        v.recovered,
        v.er_visit,
        v.onset_days,
        -- Adverse event severity score
        CASE
            WHEN v.died = 1 THEN 4
            WHEN v.disable = 1 THEN 3
            WHEN v.hospital = 1 THEN 2
            WHEN v.er_visit = 1 THEN 1
            WHEN v.recovered = 1 THEN 0
            ELSE -1
        END AS adverse_event_score,
        -- Onset time category
        CASE
            WHEN v.onset_days IS NULL THEN 'Unknown'
            WHEN v.onset_days < 1 THEN '<1 day'
            WHEN v.onset_days <= 3 THEN '1-3 days'
            WHEN v.onset_days <= 7 THEN '4-7 days'
            WHEN v.onset_days <= 30 THEN '8-30 days'
            ELSE '30+ days'
        END AS onset_category,
        -- Count symptoms per event (via subquery)
        (SELECT COUNT(DISTINCT symptom_id) 
         FROM fact_vaccine_symptoms 
         WHERE vaers_id = v.vaers_id) AS symptom_count,
        -- Extract year/month for temporal analysis
        EXTRACT(YEAR FROM v.rpt_date) AS year,
        EXTRACT(MONTH FROM v.rpt_date) AS month
    FROM fact_vaccine_events v
    JOIN dim_age a ON v.age_id = a.age_id
    JOIN dim_gender g ON v.gender_id = g.gender_id
    LEFT JOIN dim_vaccine m ON v.vaccine_id = m.vaccine_id
    LEFT JOIN dim_location l ON v.location_id = l.location_id
    """
    
    features_df = con.execute(query).df()
    
    output_file = os.path.join(output_path, 'features_vaccine_events.parquet')
    features_df.to_parquet(output_file, index=False)
    
    print(f"  [OK] Vaccine event features: {len(features_df):,} records")
    print(f"    - Adverse event severity scores")
    print(f"    - Severity distribution: {dict(features_df['adverse_event_score'].value_counts().sort_index())}")
    print(f"    - Onset time categories")
    print(f"    - Symptom counts per event")
    print(f"    - Saved to: features_vaccine_events.parquet")

def engineer_symptom_cooccurrence(con, output_path):
    """
    Compute symptom co-occurrence matrix.
    Identifies symptoms that frequently appear together in adverse event reports.
    """
    
    # First check how many symptoms are in the data
    total_symptoms = con.execute("SELECT COUNT(*) FROM fact_vaccine_symptoms").fetchone()[0]
    print(f"    Total symptom records: {total_symptoms:,}")
    
    # Use a lower threshold if data is small (sample mode)
    threshold = 5 if total_symptoms < 200000 else 50
    
    query = f"""
    SELECT
        a.symptom_id AS symptom_id_1,
        b.symptom_id AS symptom_id_2,
        s1.symptom AS symptom_1,
        s2.symptom AS symptom_2,
        COUNT(*) AS cooccurrence_count,
        COUNT(DISTINCT a.vaers_id) AS num_reports
    FROM fact_vaccine_symptoms a
    JOIN fact_vaccine_symptoms b 
        ON a.vaers_id = b.vaers_id 
        AND a.symptom_id < b.symptom_id
    JOIN dim_symptom s1 ON a.symptom_id = s1.symptom_id
    JOIN dim_symptom s2 ON b.symptom_id = s2.symptom_id
    GROUP BY 1, 2, 3, 4
    HAVING COUNT(*) >= {threshold}
    ORDER BY COUNT(*) DESC
    LIMIT 5000
    """
    
    cooccurrence_df = con.execute(query).df()
    
    output_file = os.path.join(output_path, 'symptom_cooccurrence.parquet')
    cooccurrence_df.to_parquet(output_file, index=False)
    
    print(f"  [OK] Symptom co-occurrence: {len(cooccurrence_df):,} pairs")
    print(f"    - Minimum {threshold} co-occurrences")
    print(f"    - Top pairs by frequency")
    
    # Show top 10 pairs
    if len(cooccurrence_df) > 0:
        print("\n    Top 10 symptom pairs:")
        for idx, row in cooccurrence_df.head(10).iterrows():
            print(f"      {idx+1}. {row['symptom_1']} + {row['symptom_2']}: {row['cooccurrence_count']} co-occurrences")
    else:
        print("    [WARNING] No co-occurrence pairs found above threshold")
    
    print(f"    - Saved to: symptom_cooccurrence.parquet")

def engineer_geographic_features(con, output_path):
    """
    Compute geographic aggregates (state-level rates).
    Useful for choropleth maps and regional analysis.
    
    Note: CDC case data does not include state-level data (privacy).
    Geographic features use VAERS state data, HHS hospital data, and NCHS mortality data.
    """
    
    # ====================================================================
    # COVID-19 case rates — aggregated from mortality data (has state)
    # Since CDC cases don't have state, we derive geographic case info
    # from mortality data as the best available proxy.
    # ====================================================================
    covid_query = """
    SELECT
        l.state_code,
        l.state_name,
        SUM(COALESCE(m.covid_deaths, 0)) AS total_covid_deaths,
        SUM(COALESCE(m.total_deaths, 0)) AS total_deaths,
        ROUND(100.0 * SUM(COALESCE(m.covid_deaths, 0)) / 
              NULLIF(SUM(COALESCE(m.total_deaths, 0)), 0), 2) AS covid_death_rate_pct,
        COUNT(DISTINCT m.age_id) AS age_groups_reported,
        COUNT(*) AS num_records
    FROM fact_mortality m
    JOIN dim_location l ON m.location_id = l.location_id
    WHERE l.state_code IS NOT NULL
    GROUP BY 1, 2
    ORDER BY total_covid_deaths DESC
    """
    
    covid_state_df = con.execute(covid_query).df()
    
    covid_output = os.path.join(output_path, 'geo_covid_rates.parquet')
    covid_state_df.to_parquet(covid_output, index=False)
    
    if len(covid_state_df) > 0:
        print(f"  [OK] COVID-19 geographic rates: {len(covid_state_df):,} states")
        print(f"    - Total COVID deaths: {covid_state_df['total_covid_deaths'].sum():,}")
        total_d = covid_state_df['total_deaths'].sum()
        covid_d = covid_state_df['total_covid_deaths'].sum()
        if total_d > 0:
            print(f"    - Overall COVID death rate: {(covid_d / total_d * 100):.2f}%")
    else:
        print("  [WARNING] No geographic COVID data found")
    print(f"    - Saved to: geo_covid_rates.parquet")
    
    # ====================================================================
    # Hospital burden by state and week
    # ====================================================================
    hospital_query = """
    SELECT
        h.collection_week,
        l.state_code,
        l.state_name,
        COUNT(*) AS num_records,
        AVG(h.covid_inpatient) AS avg_covid_inpatient,
        AVG(h.covid_icu) AS avg_covid_icu,
        AVG(h.covid_admissions) AS avg_covid_admissions,
        EXTRACT(YEAR FROM h.collection_week) AS year,
        EXTRACT(WEEK FROM h.collection_week) AS week_of_year
    FROM fact_hospital_capacity h
    JOIN dim_location l ON h.location_id = l.location_id
    WHERE l.state_code IS NOT NULL
    GROUP BY 1, 2, 3, 8, 9
    ORDER BY year DESC, week_of_year DESC
    """
    
    hospital_df = con.execute(hospital_query).df()
    
    hospital_output = os.path.join(output_path, 'geo_hospital_burden.parquet')
    hospital_df.to_parquet(hospital_output, index=False)
    
    if len(hospital_df) > 0:
        print(f"\n  [OK] Hospital burden by state/week: {len(hospital_df):,} records")
        print(f"    - Time period: {hospital_df['collection_week'].min()} to {hospital_df['collection_week'].max()}")
        print(f"    - States covered: {hospital_df['state_code'].nunique()}")
    else:
        print("\n  [WARNING] No hospital burden data found")
    print(f"    - Saved to: geo_hospital_burden.parquet")
    
    # ====================================================================
    # Mortality rates by state and gender
    # ====================================================================
    mortality_query = """
    SELECT
        l.state_code,
        l.state_name,
        g.gender,
        COUNT(*) AS num_records,
        SUM(COALESCE(m.covid_deaths, 0)) AS total_covid_deaths,
        SUM(COALESCE(m.total_deaths, 0)) AS total_deaths,
        ROUND(100.0 * SUM(COALESCE(m.covid_deaths, 0)) / 
              NULLIF(SUM(COALESCE(m.total_deaths, 0)), 0), 2) AS covid_death_rate_pct
    FROM fact_mortality m
    JOIN dim_location l ON m.location_id = l.location_id
    JOIN dim_gender g ON m.gender_id = g.gender_id
    WHERE l.state_code IS NOT NULL
    GROUP BY 1, 2, 3
    ORDER BY total_covid_deaths DESC
    """
    
    mortality_df = con.execute(mortality_query).df()
    
    mortality_output = os.path.join(output_path, 'geo_mortality_rates.parquet')
    mortality_df.to_parquet(mortality_output, index=False)
    
    if len(mortality_df) > 0:
        print(f"\n  [OK] Mortality rates by state/gender: {len(mortality_df):,} records")
        print(f"    - Total COVID deaths: {mortality_df['total_covid_deaths'].sum():,}")
        total_d = mortality_df['total_deaths'].sum()
        covid_d = mortality_df['total_covid_deaths'].sum()
        if total_d > 0:
            print(f"    - COVID death rate: {(covid_d / total_d * 100):.2f}%")
        print(f"    - States covered: {mortality_df['state_code'].nunique()}")
    else:
        print("\n  [WARNING] No mortality data found")
    print(f"    - Saved to: geo_mortality_rates.parquet")
    
    # ====================================================================
    # VAERS adverse event rates by state (additional geographic feature)
    # ====================================================================
    vaers_geo_query = """
    SELECT
        l.state_code,
        l.state_name,
        COUNT(*) AS total_events,
        SUM(v.died) AS death_reports,
        SUM(v.hospital) AS hospital_reports,
        SUM(v.disable) AS disability_reports,
        SUM(v.er_visit) AS er_visit_reports,
        ROUND(100.0 * SUM(v.died) / NULLIF(COUNT(*), 0), 2) AS death_report_pct,
        ROUND(100.0 * SUM(v.hospital) / NULLIF(COUNT(*), 0), 2) AS hospital_report_pct
    FROM fact_vaccine_events v
    JOIN dim_location l ON v.location_id = l.location_id
    WHERE l.state_code IS NOT NULL
    GROUP BY 1, 2
    ORDER BY total_events DESC
    """
    
    vaers_geo_df = con.execute(vaers_geo_query).df()
    
    vaers_geo_output = os.path.join(output_path, 'geo_vaers_rates.parquet')
    vaers_geo_df.to_parquet(vaers_geo_output, index=False)
    
    if len(vaers_geo_df) > 0:
        print(f"\n  [OK] VAERS geographic rates: {len(vaers_geo_df):,} states")
        print(f"    - Total events: {vaers_geo_df['total_events'].sum():,}")
        print(f"    - States covered: {vaers_geo_df['state_code'].nunique()}")
    else:
        print("\n  [WARNING] No VAERS geographic data found")
    print(f"    - Saved to: geo_vaers_rates.parquet")


if __name__ == '__main__':
    engineer_features()
