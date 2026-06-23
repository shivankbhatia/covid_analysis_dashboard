"""
Dashboard 1: Demographic Overview
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import duckdb
import pandas as pd

dash.register_page(__name__, path='/demographic', name="Demographics")

# Premium color palette
COLORS = {
    'cyan': '#00f2fe',
    'blue': '#4facfe',
    'magenta': '#ff0844',
    'purple': '#8e2de2',
    'bg_card': '#19191e',
    'text': '#e2e8f0',
    'muted': '#94a3b8'
}

layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H1("Demographic Overview", className="page-title"),
            html.P("Explore the distribution of 106M+ COVID-19 cases by age, gender, and race.", className="text-muted fs-5 mb-4")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label("Filter by State:", className="stat-label"),
                dcc.Dropdown(
                    id='demo-state-dropdown',
                    options=[{'label': 'All States', 'value': 'ALL'}], # Will be populated dynamically
                    value='ALL',
                    clearable=False,
                    className="mb-3"
                )
            ], className="glass-card h-100")
        ], width=12, md=4),
        dbc.Col([
            html.Div([
                html.Label("Total Cases Selected", className="stat-label"),
                html.H2(id='demo-total-cases', className="stat-value")
            ], className="glass-card text-center h-100 d-flex flex-column justify-content-center")
        ], width=12, md=8),
    ], className="mb-4 g-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Cases by Age Group", className="mb-3"),
                dcc.Loading(dcc.Graph(id='age-distribution', config={'displayModeBar': False}), type="circle", color=COLORS['cyan'])
            ], className="glass-card")
        ], width=12, lg=6),
        
        dbc.Col([
            html.Div([
                html.H4("Cases by Gender", className="mb-3"),
                dcc.Loading(dcc.Graph(id='gender-distribution', config={'displayModeBar': False}), type="circle", color=COLORS['magenta'])
            ], className="glass-card")
        ], width=12, lg=6),
    ], className="mb-4 g-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Cases by Race & Ethnicity", className="mb-3"),
                dcc.Loading(dcc.Graph(id='race-distribution', config={'displayModeBar': False}), type="circle", color=COLORS['blue'])
            ], className="glass-card")
        ], width=12),
    ], className="mb-4"),
])


# Shared DuckDB connection for this page
def get_db():
    return duckdb.connect('data/warehouse/covid_analytics.duckdb', read_only=True)

# Initialize dropdown options on load
@callback(
    Output('demo-state-dropdown', 'options'),
    Input('demo-state-dropdown', 'id') # Dummy trigger
)
def populate_dropdown(_):
    con = get_db()
    states = con.execute("SELECT DISTINCT state_code FROM read_parquet('data/processed/geo_covid_rates.parquet') WHERE state_code IS NOT NULL ORDER BY state_code").df()
    con.close()
    options = [{'label': 'All States (National)', 'value': 'ALL'}]
    options.extend([{'label': row['state_code'], 'value': row['state_code']} for _, row in states.iterrows()])
    return options

@callback(
    [Output('demo-total-cases', 'children'),
     Output('age-distribution', 'figure'),
     Output('gender-distribution', 'figure'),
     Output('race-distribution', 'figure')],
    [Input('demo-state-dropdown', 'value')]
)
def update_demographics(state):
    con = get_db()
    
    # Base WHERE clause
    where_clause = ""
    if state and state != 'ALL':
        where_clause = f"WHERE state_code = '{state}'"
        
    # 1. Total Cases
    total = con.execute(f"SELECT COUNT(*) FROM read_parquet('data/processed/features_cases.parquet') {where_clause}").fetchone()[0]
    total_str = f"{total:,}"
    
    # 2. Age Distribution (Bar Chart)
    age_df = con.execute(f"""
        SELECT age_group, COUNT(*) as cases 
        FROM read_parquet('data/processed/features_cases.parquet')
        {where_clause}
        GROUP BY age_group
        ORDER BY cases DESC
    """).df()
    
    fig_age = px.bar(
        age_df, x='age_group', y='cases',
        template='plotly_dark',
        color_discrete_sequence=[COLORS['cyan']]
    )
    fig_age.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="", yaxis_title="Number of Cases",
        font=dict(family="Inter", color=COLORS['text'])
    )
    
    # 3. Gender Distribution (Donut Chart)
    gender_df = con.execute(f"""
        SELECT gender, COUNT(*) as cases 
        FROM read_parquet('data/processed/features_cases.parquet')
        {where_clause}
        GROUP BY gender
    """).df()
    
    fig_gender = px.pie(
        gender_df, names='gender', values='cases', hole=0.6,
        template='plotly_dark',
        color_discrete_sequence=[COLORS['magenta'], COLORS['blue'], COLORS['purple']]
    )
    fig_gender.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="Inter", color=COLORS['text']),
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    # 4. Race Distribution (Horizontal Bar)
    race_df = con.execute(f"""
        SELECT race, COUNT(*) as cases 
        FROM read_parquet('data/processed/features_cases.parquet')
        {where_clause}
        GROUP BY race
        ORDER BY cases ASC
    """).df()
    
    fig_race = px.bar(
        race_df, y='race', x='cases', orientation='h',
        template='plotly_dark',
        color_discrete_sequence=[COLORS['blue']]
    )
    fig_race.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Number of Cases", yaxis_title="",
        font=dict(family="Inter", color=COLORS['text'])
    )
    
    con.close()
    return total_str, fig_age, fig_gender, fig_race
