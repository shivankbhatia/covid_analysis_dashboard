"""
Dashboard 3: Vaccine Analytics
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import duckdb

dash.register_page(__name__, path='/vaccine', name="Vaccines")

COLORS = {
    'cyan': '#00f2fe',
    'blue': '#4facfe',
    'magenta': '#ff0844',
    'purple': '#8e2de2',
    'bg_card': '#19191e',
    'text': '#e2e8f0',
    'warning': '#ffb347'
}

layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H1("Vaccine Adverse Events", className="page-title"),
            html.P("Analysis of the VAERS (Vaccine Adverse Event Reporting System) data for COVID-19 vaccines.", className="text-muted fs-5 mb-2")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fa-solid fa-triangle-exclamation text-warning me-2 fs-4"),
                html.Span(
                    "VAERS reports are unverified and do not imply vaccine causation. "
                    "Report counts reflect reporting volume, not true adverse event rates.",
                    style={'color': COLORS['warning'], 'fontWeight': '500'}
                )
            ], className="glass-card mb-4 border border-warning border-opacity-25")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label("Filter by State:", className="stat-label"),
                dcc.Dropdown(
                    id='vaccine-state-dropdown',
                    options=[{'label': 'All States', 'value': 'ALL'}],
                    value='ALL',
                    clearable=False,
                    className="mb-3"
                )
            ], className="glass-card h-100")
        ], width=12, md=4),
        dbc.Col([
            html.Div([
                html.Label("Total Events Selected", className="stat-label"),
                html.H2(id='vaccine-total-events', className="stat-value")
            ], className="glass-card text-center h-100 d-flex flex-column justify-content-center")
        ], width=12, md=8),
    ], className="mb-4 g-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Total Events by Manufacturer", className="mb-3"),
                dcc.Loading(dcc.Graph(id='events-by-mfr', config={'displayModeBar': False}), type="circle", color=COLORS['cyan'])
            ], className="glass-card h-100")
        ], width=12, lg=4),
        
        dbc.Col([
            html.Div([
                html.H4("Events by Age Group", className="mb-3"),
                dcc.Loading(dcc.Graph(id='events-by-age', config={'displayModeBar': False}), type="circle", color=COLORS['blue'])
            ], className="glass-card h-100")
        ], width=12, lg=4),
        
        dbc.Col([
            html.Div([
                html.H4("Events by Gender", className="mb-3"),
                dcc.Loading(dcc.Graph(id='events-by-gender', config={'displayModeBar': False}), type="circle", color=COLORS['magenta'])
            ], className="glass-card h-100")
        ], width=12, lg=4),
    ], className="mb-4 g-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Severity Distribution by Manufacturer", className="mb-3"),
                dcc.Loading(dcc.Graph(id='severity-by-mfr', config={'displayModeBar': False}), type="circle", color=COLORS['blue'])
            ], className="glass-card h-100")
        ], width=12, lg=6),
        
        dbc.Col([
            html.Div([
                html.H4("Onset Timing", className="mb-3"),
                dcc.Loading(dcc.Graph(id='onset-by-mfr', config={'displayModeBar': False}), type="circle", color=COLORS['purple'])
            ], className="glass-card h-100")
        ], width=12, lg=6),
    ], className="mb-4 g-4"),
])

def get_db():
    return duckdb.connect('data/warehouse/covid_analytics.duckdb', read_only=True)

# Initialize dropdown options on load
@callback(
    Output('vaccine-state-dropdown', 'options'),
    Input('vaccine-state-dropdown', 'id')
)
def populate_dropdown(_):
    con = get_db()
    states = con.execute("SELECT DISTINCT state_code FROM read_parquet('data/processed/geo_covid_rates.parquet') WHERE state_code IS NOT NULL ORDER BY state_code").df()
    con.close()
    options = [{'label': 'All States (National)', 'value': 'ALL'}]
    options.extend([{'label': row['state_code'], 'value': row['state_code']} for _, row in states.iterrows()])
    return options

@callback(
    [Output('vaccine-total-events', 'children'),
     Output('events-by-mfr', 'figure'),
     Output('events-by-age', 'figure'),
     Output('events-by-gender', 'figure'),
     Output('severity-by-mfr', 'figure'),
     Output('onset-by-mfr', 'figure')],
    [Input('vaccine-state-dropdown', 'value')]
)
def update_charts(state):
    con = get_db()
    
    # Base WHERE clause
    where_clause = ""
    if state and state != 'ALL':
        where_clause = f"WHERE state_code = '{state}'"
        
    # 0. Total Events
    total = con.execute(f"SELECT COUNT(*) FROM read_parquet('data/processed/features_vaccine_events.parquet') {where_clause}").fetchone()[0]
    total_str = f"{total:,}"
    
    # 1. Events by Manufacturer
    mfr_df = con.execute(f"""
        SELECT manufacturer, COUNT(*) as events 
        FROM read_parquet('data/processed/features_vaccine_events.parquet')
        {where_clause}
        GROUP BY manufacturer
        ORDER BY events DESC
    """).df()
    
    fig_mfr = px.pie(
        mfr_df, names='manufacturer', values='events', hole=0.5,
        template='plotly_dark',
        color_discrete_sequence=[COLORS['blue'], COLORS['purple'], COLORS['magenta'], COLORS['cyan'], COLORS['warning']]
    )
    fig_mfr.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="Inter", color=COLORS['text'])
    )
    
    # 2. Events by Age
    age_df = con.execute(f"""
        SELECT age_group, COUNT(*) as events 
        FROM read_parquet('data/processed/features_vaccine_events.parquet')
        {where_clause}
        GROUP BY age_group
        ORDER BY events DESC
    """).df()
    
    fig_age = px.bar(
        age_df, x='age_group', y='events',
        template='plotly_dark',
        color_discrete_sequence=[COLORS['cyan']]
    )
    fig_age.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="", yaxis_title="Events",
        font=dict(family="Inter", color=COLORS['text'])
    )
    
    # 3. Events by Gender
    gender_df = con.execute(f"""
        SELECT gender, COUNT(*) as events 
        FROM read_parquet('data/processed/features_vaccine_events.parquet')
        {where_clause}
        GROUP BY gender
    """).df()
    
    fig_gender = px.pie(
        gender_df, names='gender', values='events', hole=0.6,
        template='plotly_dark',
        color_discrete_sequence=[COLORS['magenta'], COLORS['blue'], COLORS['purple']]
    )
    fig_gender.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(family="Inter", color=COLORS['text']),
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    # 4. Severity Distribution
    severity_where = where_clause + " AND adverse_event_score > 0" if where_clause else "WHERE adverse_event_score > 0"
    severity_df = con.execute(f"""
        SELECT manufacturer, 
               CASE adverse_event_score 
                 WHEN 4 THEN 'Death'
                 WHEN 3 THEN 'Disabled'
                 WHEN 2 THEN 'Hospitalized'
                 WHEN 1 THEN 'ER Visit'
                 WHEN 0 THEN 'Recovered'
                 ELSE 'Unknown' END as severity,
               COUNT(*) as count
        FROM read_parquet('data/processed/features_vaccine_events.parquet')
        {severity_where}
        GROUP BY manufacturer, adverse_event_score
        ORDER BY adverse_event_score DESC
    """).df()
    
    fig_severity = px.bar(
        severity_df, x='manufacturer', y='count', color='severity',
        template='plotly_dark', barmode='group',
        color_discrete_map={'Death': COLORS['magenta'], 'Disabled': COLORS['warning'], 'Hospitalized': COLORS['purple'], 'ER Visit': COLORS['cyan']}
    )
    fig_severity.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="", yaxis_title="Number of Events",
        font=dict(family="Inter", color=COLORS['text']),
        legend_title_text=""
    )
    
    # 5. Onset Category
    onset_df = con.execute(f"""
        SELECT onset_category, COUNT(*) as events
        FROM read_parquet('data/processed/features_vaccine_events.parquet')
        {where_clause}
        GROUP BY onset_category
        ORDER BY events DESC
    """).df()
    
    fig_onset = px.bar(
        onset_df, x='onset_category', y='events',
        template='plotly_dark',
        color_discrete_sequence=[COLORS['purple']]
    )
    fig_onset.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="", yaxis_title="Number of Events",
        font=dict(family="Inter", color=COLORS['text'])
    )
    
    con.close()
    return total_str, fig_mfr, fig_age, fig_gender, fig_severity, fig_onset
