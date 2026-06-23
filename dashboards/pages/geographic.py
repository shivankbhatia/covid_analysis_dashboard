"""
Dashboard 5: Geographic Analytics
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import duckdb

dash.register_page(__name__, path='/geographic', name="Geographic")

COLORS = {
    'cyan': '#00f2fe',
    'blue': '#4facfe',
    'magenta': '#ff0844',
    'purple': '#8e2de2',
    'bg_card': '#19191e',
    'text': '#e2e8f0'
}

layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H1("Geographic Distribution", className="page-title"),
            html.P("State-level choropleth maps of COVID-19 cases, mortality, and VAERS events.", className="text-muted fs-5 mb-4")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Total COVID-19 Cases by State", className="mb-3"),
                dcc.Loading(dcc.Graph(id='cases-map', style={'height': '50vh'}, config={'displayModeBar': False}), type="circle", color=COLORS['cyan'])
            ], className="glass-card mb-4")
        ], width=12, lg=6),
        
        dbc.Col([
            html.Div([
                html.H4("COVID-19 Death Rate by State (%)", className="mb-3"),
                dcc.Loading(dcc.Graph(id='death-rate-map', style={'height': '50vh'}, config={'displayModeBar': False}), type="circle", color=COLORS['magenta'])
            ], className="glass-card mb-4")
        ], width=12, lg=6),
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("VAERS Reports by State", className="mb-3"),
                dcc.Loading(dcc.Graph(id='vaers-map', style={'height': '50vh'}, config={'displayModeBar': False}), type="circle", color=COLORS['purple'])
            ], className="glass-card mb-4")
        ], width=12, lg=12),
    ]),
    
    # Dummy input
    html.Div(id='geo-init', style={'display': 'none'})
])

def get_db():
    return duckdb.connect('data/warehouse/covid_analytics.duckdb', read_only=True)

@callback(
    [Output('cases-map', 'figure'),
     Output('death-rate-map', 'figure'),
     Output('vaers-map', 'figure')],
    [Input('geo-init', 'id')]
)
def update_maps(_):
    con = get_db()
    
    # 1. COVID Rates
    covid_df = con.execute("""
        SELECT state_code, total_cases, death_rate_pct
        FROM read_parquet('data/processed/geo_covid_rates.parquet')
        WHERE state_code IS NOT NULL AND state_code != 'UNKNOWN'
    """).df()
    
    def style_map(fig):
        fig.update_layout(
            geo=dict(
                scope='usa',
                projection=go.layout.geo.Projection(type='albers usa'),
                bgcolor='rgba(0,0,0,0)',
                lakecolor='rgba(0,0,0,0)',
                showland=True,
                landcolor='rgba(40,40,45,1)',
                showlakes=False
            ),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            font=dict(family="Inter", color=COLORS['text'])
        )
        return fig
        
    import plotly.graph_objects as go
    
    fig_cases = px.choropleth(
        covid_df, locations='state_code', locationmode="USA-states",
        color='total_cases', color_continuous_scale="Blues",
        labels={'total_cases': 'Cases'}
    )
    fig_cases = style_map(fig_cases)
    
    fig_deaths = px.choropleth(
        covid_df, locations='state_code', locationmode="USA-states",
        color='death_rate_pct', color_continuous_scale="Reds",
        labels={'death_rate_pct': 'Death Rate (%)'}
    )
    fig_deaths = style_map(fig_deaths)
    
    # 2. VAERS Rates
    vaers_df = con.execute("""
        SELECT state_code, total_events
        FROM read_parquet('data/processed/geo_vaers_rates.parquet')
        WHERE state_code IS NOT NULL AND state_code != 'UNKNOWN'
    """).df()
    
    fig_vaers = px.choropleth(
        vaers_df, locations='state_code', locationmode="USA-states",
        color='total_events', color_continuous_scale="Purples",
        labels={'total_events': 'VAERS Events'}
    )
    fig_vaers = style_map(fig_vaers)
    
    con.close()
    return fig_cases, fig_deaths, fig_vaers
