"""
Feature engineering pipeline.
"""
import duckdb
import polars as pl

def engineer_features():
    """Compute and save engineered features."""
    con = duckdb.connect('../data/warehouse/covid_analytics.duckdb', read_only=False)
    
    print("Engineering case-level outcome features...")
    # TODO: Compute features from fact_covid_cases
    # severity_score, outcome rates by group, etc.
    
    print("Engineering vaccine adverse event features...")
    # TODO: symptom_count, adverse_event_score, onset_category
    
    print("Computing symptom co-occurrence matrix...")
    # TODO: Build pairwise symptom co-occurrence
    
    print("Computing geographic aggregates...")
    # TODO: State-level rates
    
    con.close()

if __name__ == '__main__':
    engineer_features()
