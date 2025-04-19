import pandas as pd
import geopandas as gpd
from shapely.wkt import loads

import numpy as np
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output  # pip install dash (version 2.0.0 or higher)
import mercantile
import json
import warnings

# ------------------------------------------------------------------------------

app = Dash(__name__)

server = app.server

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([

    html.H1("Comparación Cobertura Móvil Tigo y Claro - Guatemala. Periodo: Octubre 2024 a Marzo 2025", style={'text-align': 'center'}),

    dcc.Dropdown(
        id="slct_tech",
        options=[
            {"label": "5G", "value": 'NR'},
            {"label": "4G", "value": 'LTE'},
            {"label": "WCDMA", "value": 'WCDMA'},
            {"label": "CDMA", "value": 'CDMA'},
            {"label": "GSM", "value": 'GSM'}
        ],
        multi=False,
        value='LTE',
        style={'width': "40%"}
    ),

    html.Div(id='output_container', children=[]),
    html.Br(),

    dcc.Graph(id='my_tech_map', figure={})

])

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
warnings.filterwarnings("ignore", category=FutureWarning)

@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='my_tech_map', component_property='figure')],
#     Output(component_id='bar_plot', component_property='figure')],
    [Input(component_id='slct_tech', component_property='value')]

    )

def update_graph(option_slctd):

# ------------------------------------------------------------------------------
# Leer parquet procesado
    columns_needed = ['quadkey', 'geometry', 'technology','comparison']
    pivot_table = pd.read_parquet("processed_data.parquet", columns=columns_needed)
    #pivot_table = pd.read_parquet("processed_data.parquet")

    # Convertir geometría WKT a objeto geométrico
    pivot_table['geometry'] = pivot_table['geometry'].apply(loads)

    # Crear GeoDataFrame
    gdf_csv = gpd.GeoDataFrame(pivot_table, geometry="geometry")

    if gdf_csv.crs is None:
        gdf_csv.set_crs(epsg=4326, inplace=True)

    print(option_slctd)

    container = f"The selected technology was: {option_slctd}"

    # Filtrar GeoDataFrame por tecnología
    dff = gdf_csv[gdf_csv["technology"] == option_slctd]

    if dff.empty:
        print("GeoDataFrame is empty.")
        return container, go.Figure()

    # Convertir GeoDataFrame a GeoJSON
    geojson = json.loads(dff.to_json())

    # Reproyectar temporalmente para calcular centroides correctos
    gdf_projected = dff.to_crs(epsg=3857)
    centroid = gdf_projected.geometry.centroid.to_crs(epsg=4326)

    # Crear figura
    fig = px.choropleth_mapbox(
        dff,
        geojson=geojson,
        locations=dff.index,
        color="comparison",
        mapbox_style="carto-positron",
        center={
            "lat": centroid.y.mean(),
            "lon": centroid.x.mean()
        },
        zoom=11,
        opacity=0.6,
        hover_name="quadkey",
        color_discrete_map={
            "Ambos Tigo + Claro": "gray",
            "Solo Tigo": "blue",
            "Solo Claro": "red"
        }
    )

    fig.update_layout(
        width=1700,
        height=900,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    return container, fig

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=10000)
