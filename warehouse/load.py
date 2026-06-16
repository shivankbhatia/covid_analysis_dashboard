"""
Warehouse loader - creates DuckDB schema and loads data.
"""
import duckdb
import os

def create_warehouse():
    """Create DuckDB warehouse and load schema."""
    db_path = '../data/warehouse/covid_analytics.duckdb'
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to DuckDB
    con = duckdb.connect(db_path)
    
    # Read and execute schema
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Execute schema creation
    con.execute(schema_sql)
    
    # TODO: Load dimension data
    # TODO: Load fact tables from Parquet files
    
    con.close()
    print(f"Warehouse created at {db_path}")

if __name__ == '__main__':
    create_warehouse()
