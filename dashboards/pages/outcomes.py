"""
Dashboard 2: Outcomes Analysis
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/outcomes')

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Outcomes Analysis"), width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='hosp-by-age'), width=6),
        dbc.Col(dcc.Graph(id='icu-by-age'), width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='mortality-by-age'), width=6),
        dbc.Col(dcc.Graph(id='mortality-by-gender'), width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='outcome-trends'), width=12),
    ], className="mb-4"),
], fluid=True)

@callback(
    [Output('hosp-by-age', 'figure'),
     Output('icu-by-age', 'figure'),
     Output('mortality-by-age', 'figure'),
     Output('mortality-by-gender', 'figure'),
     Output('outcome-trends', 'figure')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_charts(start_date, end_date):
    # TODO: Query warehouse and update charts
    return {}, {}, {}, {}, {}
