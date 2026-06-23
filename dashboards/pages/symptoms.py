"""
Dashboard 4: Symptom Analytics
"""
import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import duckdb
import networkx as nx

dash.register_page(__name__, path='/symptoms', name="Symptoms")

COLORS = {
    'cyan': '#00f2fe',
    'blue': '#4facfe',
    'magenta': '#ff0844',
    'purple': '#8e2de2',
    'bg_card': '#19191e',
    'text': '#e2e8f0',
    'edge': 'rgba(255, 255, 255, 0.1)'
}

layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.H1("Symptom Co-occurrence Network", className="page-title"),
            html.P("Interactive graph showing which vaccine adverse event symptoms most frequently occur together.", className="text-muted fs-5 mb-4")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Label("Number of top symptom pairs to display:", className="stat-label mb-2"),
                dcc.Slider(
                    id='symptom-slider',
                    min=10, max=200, step=10, value=50,
                    marks={i: str(i) for i in range(10, 201, 30)},
                    className="mb-4"
                ),
            ], className="glass-card mb-4")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div([
                dcc.Loading(dcc.Graph(id='symptom-network', style={'height': '70vh'}, config={'displayModeBar': False}), type="circle", color=COLORS['cyan'])
            ], className="glass-card h-100")
        ], width=12)
    ], className="mb-4"),
])

def get_db():
    return duckdb.connect('data/warehouse/covid_analytics.duckdb', read_only=True)

@callback(
    Output('symptom-network', 'figure'),
    [Input('symptom-slider', 'value')]
)
def update_network(top_n):
    con = get_db()
    
    # Get top pairs
    df = con.execute(f"""
        SELECT symptom_1, symptom_2, num_reports
        FROM read_parquet('data/processed/symptom_cooccurrence.parquet')
        ORDER BY num_reports DESC
        LIMIT {top_n}
    """).df()
    con.close()
    
    if df.empty:
        return go.Figure()
        
    # Build NetworkX graph
    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_edge(row['symptom_1'], row['symptom_2'], weight=row['num_reports'])
        
    # Calculate positions
    pos = nx.spring_layout(G, seed=42, k=0.5)
    
    # Calculate node sizes based on degree
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1
    
    # Edges trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color=COLORS['edge']),
        hoverinfo='none',
        mode='lines'
    )
    
    # Nodes trace
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node} (Connections: {degrees[node]})")
        
        # Scale size between 10 and 40
        size = 10 + (degrees[node] / max_degree) * 30
        node_size.append(size)
        
        # Color based on degree
        node_color.append(degrees[node])
        
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[node for node in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        hoverinfo="text",
        marker=dict(
            showscale=False,
            colorscale='Bluered',
            reversescale=False,
            color=node_color,
            size=node_size,
            line_width=2,
            line_color='rgba(255,255,255,0.8)'
        ),
        textfont=dict(
            family="Inter",
            color=COLORS['text'],
            size=10
        )
    )
    
    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=0, l=0, r=0, t=0),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
             ))
             
    return fig
