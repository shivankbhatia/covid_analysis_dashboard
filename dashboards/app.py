"""
Dash application entry point.
"""
import dash
import duckdb
import dash_bootstrap_components as dbc
from dash import html

# Initialize app with CYBORG theme and FontAwesome for icons
app = dash.Dash(__name__, use_pages=True, 
                external_stylesheets=[dbc.themes.CYBORG, dbc.icons.FONT_AWESOME],
                suppress_callback_exceptions=True)

# Build a stylish custom Navbar
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.I(className="fa-solid fa-virus-covid fs-3 text-info")),
                        dbc.Col(dbc.NavbarBrand("COVID-19 Analytics", className="ms-2 fw-bold fs-4 text-white")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="/",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavLink([html.I(className="fa-solid fa-users me-2"), "Demographics"], href="/demographic", active="exact"),
                        dbc.NavLink([html.I(className="fa-solid fa-hospital-user me-2"), "Outcomes"], href="/outcomes", active="exact"),
                        dbc.NavLink([html.I(className="fa-solid fa-syringe me-2"), "Vaccines"], href="/vaccine", active="exact"),
                        dbc.NavLink([html.I(className="fa-solid fa-head-side-cough me-2"), "Symptoms"], href="/symptoms", active="exact"),
                        dbc.NavLink([html.I(className="fa-solid fa-map-location-dot me-2"), "Geographic"], href="/geographic", active="exact"),
                        dbc.NavLink([html.I(className="fa-solid fa-chart-line me-2"), "Advanced"], href="/advanced", active="exact"),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ],
        fluid=True,
    ),
    color="rgba(20, 20, 20, 0.8)",
    dark=True,
    className="mb-4 glass-navbar",
    sticky="top",
)

# Define app layout
app.layout = html.Div([
    navbar,
    dbc.Container(
        dash.page_container,
        fluid=True,
        className="pb-5"
    )
], className="app-container")

if __name__ == '__main__':
    app.run(debug=True)
