"""
Dashboard 4: Symptom Analytics
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/symptoms')

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Symptom Analytics"), width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='top-symptoms'), width=12),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='symptom-heatmap'), width=6),
        dbc.Col(dcc.Graph(id='symptom-network'), width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='symptom-treemap'), width=12),
    ], className="mb-4"),
], fluid=True)

@callback(
    [Output('top-symptoms', 'figure'),
     Output('symptom-heatmap', 'figure'),
     Output('symptom-network', 'figure'),
     Output('symptom-treemap', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_charts(n):
    # TODO: Query warehouse and update charts
    return {}, {}, {}, {}
