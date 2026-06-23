"""
Shared utility functions for ETL pipeline.
"""
import polars as pl

AGE_BINS = ['0-17', '18-29', '30-44', '45-59', '60-74', '75+']

def standardise_age_group(series: pl.Series) -> pl.Series:
    """Map varied age strings to standard DIM_AGE buckets.
    
    Handles actual CDC Case Surveillance age labels:
      '0 - 9 Years', '10 - 19 Years', '20 - 29 Years', '30 - 39 Years',
      '40 - 49 Years', '50 - 59 Years', '60 - 69 Years', '70 - 79 Years',
      '80+ Years', 'NA', 'Unknown'
    """
    mapping = {
        # CDC Case Surveillance actual labels (old dataset: cdc_cases.csv)
        '0 - 9 Years': '0-17',
        '10 - 19 Years': '0-17',
        '20 - 29 Years': '18-29',
        '30 - 39 Years': '30-44',
        '40 - 49 Years': '30-44',
        '50 - 59 Years': '45-59',
        '60 - 69 Years': '60-74',
        '70 - 79 Years': '60-74',
        '80+ Years': '75+',
        # New CDC dataset labels (cdc_cases_new.csv) — wider buckets
        '0 - 17 years': '0-17',
        '18 to 49 years': '30-44',   # Wide bucket: maps to middle range
        '50 to 64 years': '45-59',
        '65+ years': '60-74',
        # Legacy/alternate labels (from implementation plan)
        '18 to 29 years': '18-29',
        '30 to 49 years': '30-44',
        # Handle NA/Unknown
        'NA': 'Unknown',
        'Missing': 'Unknown',
    }
    return series.replace(mapping).fill_null('Unknown')

def normalise_yn(series: pl.Series) -> pl.Series:
    """Convert 'Yes'/'No'/'Unknown'/'Missing' to 1/0/null."""
    return (
        series
        .replace({'Yes': '1', 'No': '0'})
        .cast(pl.Int8, strict=False)
    )

def normalise_manufacturer(series: pl.Series) -> pl.Series:
    """Standardise vaccine manufacturer names."""
    mfr_map = {
        'PFIZER\\BIONTECH': 'Pfizer',
        'PFIZER-BIONTECH': 'Pfizer',
        'MODERNA': 'Moderna',
        'JANSSEN': 'Janssen',
    }
    return series.str.to_uppercase().replace(mfr_map).fill_null('Other/Unknown')
