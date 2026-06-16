"""
Dashboard 3: Vaccine Analytics
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/vaccine')

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Vaccine Analytics"), width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.P(
                    "⚠️ VAERS reports are unverified and do not imply vaccine causation. "
                    "Report counts reflect reporting volume, not adverse event rates.",
                    style={
                        'backgroundColor': '#fff3cd',
                        'padding': '10px',
                        'borderRadius': '5px',
                        'fontSize': '0.9em'
                    }
                )
            ], className="alert alert-warning")
        ], width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='events-by-mfr'), width=6),
        dbc.Col(dcc.Graph(id='deaths-by-mfr'), width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='hosp-by-mfr'), width=6),
        dbc.Col(dcc.Graph(id='severity-by-mfr'), width=6),
    ], className="mb-4"),
], fluid=True)

@callback(
    [Output('events-by-mfr', 'figure'),
     Output('deaths-by-mfr', 'figure'),
     Output('hosp-by-mfr', 'figure'),
     Output('severity-by-mfr', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_charts(n):
    # TODO: Query warehouse and update charts
    return {}, {}, {}, {}
