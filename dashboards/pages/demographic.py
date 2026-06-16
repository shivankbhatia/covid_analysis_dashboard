"""
Dashboard 1: Demographic Overview
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/demographic')

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Demographic Overview"), width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='age-distribution'), width=6),
        dbc.Col(dcc.Graph(id='gender-distribution'), width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='race-distribution'), width=12),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Date Range:"),
            dcc.DatePickerRange(
                id='date-range',
                start_date_placeholder_text='Select start date',
                end_date_placeholder_text='Select end date'
            )
        ], width=6),
        dbc.Col([
            html.Label("State:"),
            dcc.Dropdown(id='state-dropdown', multi=False)
        ], width=6),
    ], className="mb-4"),
], fluid=True)

@callback(
    [Output('age-distribution', 'figure'),
     Output('gender-distribution', 'figure'),
     Output('race-distribution', 'figure')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('state-dropdown', 'value')]
)
def update_charts(start_date, end_date, state):
    # TODO: Query warehouse and update charts
    return {}, {}, {}
