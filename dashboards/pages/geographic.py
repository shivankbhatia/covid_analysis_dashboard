"""
Dashboard 5: Geographic Analytics
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/geographic')

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Geographic Analytics"), width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='cases-choropleth'), width=12),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='deaths-choropleth'), width=6),
        dbc.Col(dcc.Graph(id='hospital-map'), width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='state-comparison'), width=12),
    ], className="mb-4"),
], fluid=True)

@callback(
    [Output('cases-choropleth', 'figure'),
     Output('deaths-choropleth', 'figure'),
     Output('hospital-map', 'figure'),
     Output('state-comparison', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_charts(n):
    # TODO: Query warehouse and update charts
    return {}, {}, {}, {}
