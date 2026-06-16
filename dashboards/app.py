"""
Dash application entry point.
"""
import dash
import duckdb
import dash_bootstrap_components as dbc

# Initialize app
app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Connect to warehouse (read-only)
try:
    con = duckdb.connect('../data/warehouse/covid_analytics.duckdb', read_only=True)
    app.con = con
except Exception as e:
    print(f"Warning: Could not connect to warehouse: {e}")

# Define app layout
app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand="COVID-19 Demographic Analytics",
        color="dark",
        dark=True,
        className="mb-4"
    ),
    dash.page_container
], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)
