"""
Dashboard 6: Advanced Analytics
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/advanced')

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("Advanced Analytics"), width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='shap-summary-mortality'), width=6),
        dbc.Col(dcc.Graph(id='shap-summary-hosp'), width=6),
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.H4("Mortality Risk Predictor"),
            dbc.Form([
                dbc.Row([
                    dbc.Col(dcc.Dropdown(id='pred-age', options=[]), width=3),
                    dbc.Col(dcc.Dropdown(id='pred-gender', options=[]), width=3),
                    dbc.Col(dcc.Dropdown(id='pred-race', options=[]), width=3),
                    dbc.Col(dbc.Button("Predict", id='pred-btn'), width=3),
                ]),
            ]),
            html.Div(id='pred-output', className='mt-3')
        ], width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='symptom-clusters'), width=12),
    ], className="mb-4"),
], fluid=True)

@callback(
    [Output('shap-summary-mortality', 'figure'),
     Output('shap-summary-hosp', 'figure'),
     Output('symptom-clusters', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_charts(n):
    # TODO: Query warehouse and update charts
    return {}, {}, {}

@callback(
    Output('pred-output', 'children'),
    Input('pred-btn', 'n_clicks'),
    [Input('pred-age', 'value'),
     Input('pred-gender', 'value'),
     Input('pred-race', 'value')],
    prevent_initial_call=True
)
def predict(n_clicks, age, gender, race):
    # TODO: Load model and make prediction
    return html.Div("Prediction pending")
