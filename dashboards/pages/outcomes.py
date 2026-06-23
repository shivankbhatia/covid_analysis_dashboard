"""
Dashboard 2: Outcomes Analysis
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import duckdb

dash.register_page(__name__, path='/outcomes', name="Outcomes")

COLORS = {
    'cyan': '#00f2fe',
    'blue': '#4facfe',
    'magenta': '#ff0844',
    'purple': '#8e2de2',
    'yellow': '#f6d365',
    'bg_card': '#19191e',
    'text': '#e2e8f0'
}

layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H1("Severe Outcomes Analysis", className="page-title"),
            html.P("Analyzing Hospitalization, ICU admission, and Mortality rates across demographics.", className="text-muted fs-5 mb-4")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label("Filter by State:", className="stat-label"),
                dcc.Dropdown(
                    id='outcomes-state-dropdown',
                    options=[{'label': 'All States', 'value': 'ALL'}],
                    value='ALL',
                    clearable=False,
                    className="mb-3"
                )
            ], className="glass-card h-100")
        ], width=12, md=4),
        dbc.Col([
            html.Div([
                html.Label("Total Cases Analyzed", className="stat-label"),
                html.H2(id='outcomes-total-cases', className="stat-value")
            ], className="glass-card text-center h-100 d-flex flex-column justify-content-center")
        ], width=12, md=8),
    ], className="mb-4 g-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Hospitalization Rate by Age (%)", className="mb-3"),
                dcc.Loading(dcc.Graph(id='hosp-by-age', config={'displayModeBar': False}), type="circle", color=COLORS['blue'])
            ], className="glass-card h-100")
        ], width=12, lg=4),
        
        dbc.Col([
            html.Div([
                html.H4("ICU Rate by Age (%)", className="mb-3"),
                dcc.Loading(dcc.Graph(id='icu-by-age', config={'displayModeBar': False}), type="circle", color=COLORS['purple'])
            ], className="glass-card h-100")
        ], width=12, lg=4),
        
        dbc.Col([
            html.Div([
                html.H4("Mortality Rate by Age (%)", className="mb-3"),
                dcc.Loading(dcc.Graph(id='mortality-by-age', config={'displayModeBar': False}), type="circle", color=COLORS['magenta'])
            ], className="glass-card h-100")
        ], width=12, lg=4),
    ], className="mb-4 g-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Mortality by Gender", className="mb-3"),
                dcc.Loading(dcc.Graph(id='mortality-by-gender', config={'displayModeBar': False}), type="circle", color=COLORS['cyan'])
            ], className="glass-card")
        ], width=12, lg=4),
        
        dbc.Col([
            html.Div([
                html.H4("Severe Outcomes Over Time", className="mb-3"),
                dcc.Loading(dcc.Graph(id='outcome-trends', config={'displayModeBar': False}), type="circle", color=COLORS['cyan'])
            ], className="glass-card")
        ], width=12, lg=8),
    ], className="mb-4 g-4"),
])

def get_db():
    return duckdb.connect('data/warehouse/covid_analytics.duckdb', read_only=True)

# Initialize dropdown options on load
@callback(
    Output('outcomes-state-dropdown', 'options'),
    Input('outcomes-state-dropdown', 'id')
)
def populate_dropdown(_):
    con = get_db()
    states = con.execute("SELECT DISTINCT state_code FROM read_parquet('data/processed/geo_covid_rates.parquet') WHERE state_code IS NOT NULL ORDER BY state_code").df()
    con.close()
    options = [{'label': 'All States (National)', 'value': 'ALL'}]
    options.extend([{'label': row['state_code'], 'value': row['state_code']} for _, row in states.iterrows()])
    return options

@callback(
    [Output('outcomes-total-cases', 'children'),
     Output('hosp-by-age', 'figure'),
     Output('icu-by-age', 'figure'),
     Output('mortality-by-age', 'figure'),
     Output('mortality-by-gender', 'figure'),
     Output('outcome-trends', 'figure')],
    [Input('outcomes-state-dropdown', 'value')]
)
def update_charts(state):
    con = get_db()
    
    # Base WHERE clause
    where_clause = ""
    if state and state != 'ALL':
        where_clause = f"WHERE state_code = '{state}'"
        
    # 0. Total Cases
    total = con.execute(f"SELECT COUNT(*) FROM read_parquet('data/processed/features_cases.parquet') {where_clause}").fetchone()[0]
    total_str = f"{total:,}"
    
    # 1. Age Rates (Dynamically calculated so state filters work accurately)
    age_df = con.execute(f"""
        SELECT age_group, 
               ROUND(100.0 * AVG(hospitalized), 2) as hosp_rate,
               ROUND(100.0 * AVG(icu_admitted), 2) as icu_rate,
               ROUND(100.0 * AVG(deceased), 2) as death_rate
        FROM read_parquet('data/processed/features_cases.parquet')
        {where_clause}
        GROUP BY age_group
        ORDER BY age_group
    """).df()
    
    def style_bar(fig, color):
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="", yaxis_title="Rate (%)",
            font=dict(family="Inter", color=COLORS['text'])
        )
        fig.update_traces(marker_color=color)
        return fig
        
    fig_hosp = style_bar(px.bar(age_df, x='age_group', y='hosp_rate', template='plotly_dark'), COLORS['blue'])
    fig_icu = style_bar(px.bar(age_df, x='age_group', y='icu_rate', template='plotly_dark'), COLORS['purple'])
    fig_mort = style_bar(px.bar(age_df, x='age_group', y='death_rate', template='plotly_dark'), COLORS['magenta'])
    
    # 2. Gender Mortality
    gender_df = con.execute(f"""
        SELECT gender, 
               ROUND(100.0 * AVG(deceased), 2) as death_rate
        FROM read_parquet('data/processed/features_cases.parquet')
        {where_clause}
        GROUP BY gender
    """).df()
    
    fig_gender = px.bar(
        gender_df, x='gender', y='death_rate',
        template='plotly_dark', color_discrete_sequence=[COLORS['cyan']]
    )
    fig_gender.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="", yaxis_title="Death Rate (%)",
        font=dict(family="Inter", color=COLORS['text'])
    )
    
    # 3. Time Trends
    time_where = where_clause + " AND year IS NOT NULL AND month IS NOT NULL" if where_clause else "WHERE year IS NOT NULL AND month IS NOT NULL"
    trend_df = con.execute(f"""
        SELECT 
            make_date(CAST(year AS INTEGER), CAST(month AS INTEGER), 1) as ds,
            SUM(hospitalized) as hosp_count,
            SUM(icu_admitted) as icu_count,
            SUM(deceased) as death_count
        FROM read_parquet('data/processed/features_cases.parquet')
        {time_where}
        GROUP BY year, month
        ORDER BY year, month
    """).df()
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=trend_df['ds'], y=trend_df['hosp_count'], mode='lines', name='Hospitalized', line=dict(color=COLORS['blue'], width=3)))
    fig_trend.add_trace(go.Scatter(x=trend_df['ds'], y=trend_df['icu_count'], mode='lines', name='ICU', line=dict(color=COLORS['purple'], width=3)))
    fig_trend.add_trace(go.Scatter(x=trend_df['ds'], y=trend_df['death_count'], mode='lines', name='Deceased', line=dict(color=COLORS['magenta'], width=3)))
    
    fig_trend.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="", yaxis_title="Total Cases",
        font=dict(family="Inter", color=COLORS['text']),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    con.close()
    return total_str, fig_hosp, fig_icu, fig_mort, fig_gender, fig_trend
