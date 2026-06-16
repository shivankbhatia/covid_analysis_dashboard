"""
Shared utility functions for ETL pipeline.
"""
import polars as pl

AGE_BINS = ['0-17', '18-29', '30-44', '45-59', '60-74', '75+']

def standardise_age_group(series: pl.Series) -> pl.Series:
    """Map varied age strings to standard DIM_AGE buckets."""
    mapping = {
        '0 - 17 years': '0-17',
        '18 to 29 years': '18-29',
        '30 to 49 years': '30-44',   # CDC uses wider bucket; split not possible
        '50 to 64 years': '45-59',
        '65+ years': '60-74',        # Will be refined with NCHS data
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
