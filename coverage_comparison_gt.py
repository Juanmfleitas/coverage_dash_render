import pandas as pd
import geopandas as gpd
from shapely.wkt import loads
from shapely.wkb import loads as load_wkb

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

    html.H1("Tigo and Claro Mobile Coverage Comparison - Guatemala. Period: December 2024", style={'text-align': 'center'}),

    html.Div([
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
            value='NR',
            style={'width': "40%", 'margin-right': '20px'}
        ),

        dcc.Dropdown(
            id="slct_adm1",
            options=[
                {"label": "Huehuetenango", "value": 'Huehuetenango'},
                {"label": "Petén", "value": 'Petén'},
                {"label": "Alta Verapaz", "value": 'Alta Verapaz'},
                {"label": "Quiché", "value": 'Quiché'},
                {"label": "San Marcos", "value": 'San Marcos'},
                {"label": "Quetzaltenango", "value": 'Quetzaltenango'},
                {"label": "Totonicapán", "value": 'Totonicapán'},
                {"label": "Sololá", "value": 'Sololá'},
                {"label": "Retalhuleu", "value": 'Retalhuleu'},
                {"label": "Suchitepéquez", "value": 'Suchitepéquez'},
                {"label": "Chimaltenango", "value": 'Chimaltenango'},
                {"label": "Guatemala", "value": 'Guatemala'},
                {"label": "Sacatepéquez", "value": 'Sacatepéquez'},
                {"label": "Baja Verapaz", "value": 'Baja Verapaz'},
                {"label": "El Progreso", "value": 'El Progreso'},
                {"label": "Jalapa", "value": 'Jalapa'},
                {"label": "Escuintla", "value": 'Escuintla'},
                {"label": "Santa Rosa", "value": 'Santa Rosa'},
                {"label": "Jutiapa", "value": 'Jutiapa'},
                {"label": "Izabal", "value": 'Izabal'},
                {"label": "Zacapaz", "value": 'Zacapa'},
                {"label": "Chiquimula", "value": 'Chiquimula'}
            ],
            multi=False,
            value='Guatemala',
            style={'width': "40%"}
        )
    ], style={'display': 'flex', 'justify-content': 'center'}),


    html.Div([
        html.Div(id='output_container', children=[], style={'width': "40%", 'margin-right': '20px'}),
        html.Div(id='output_container1', children=[], style={'width': "40%"}),
    
    ], style={'display': 'flex', 'justify-content': 'center'}),
    
    html.Br(),
    dcc.Graph(id='my_tech_map', figure={}),

    html.Br(),
    dcc.Graph(id='comparison_bar_chart', figure={})  # 🆕 Nuevo gráfico

])

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
warnings.filterwarnings("ignore", category=FutureWarning)

@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='output_container1', component_property='children'),
     Output(component_id='my_tech_map', component_property='figure'),
     Output(component_id='comparison_bar_chart', component_property='figure')],  # Nuevo output
    [Input(component_id='slct_tech', component_property='value'),
     Input(component_id='slct_adm1', component_property='value')]
    )

def update_graph(option_slctd, option_adm1):

# ------------------------------------------------------------------------------
# Leer parquet procesado
    columns_needed = ['quadkey', 'geometry', 'technology','comparison','ADM1_ES']
    pivot_table = pd.read_parquet("processed_data.parquet", columns=columns_needed)
    #pivot_table = pd.read_parquet("processed_data.parquet")

    # Convertir geometría WKT a objeto geométrico
    pivot_table['geometry'] = pivot_table['geometry'].apply(load_wkb)

    # Crear GeoDataFrame
    gdf_csv = gpd.GeoDataFrame(pivot_table, geometry="geometry")
    
    if gdf_csv.crs is None:
        gdf_csv.set_crs(epsg=4326, inplace=True)

    print(option_slctd)
    print(option_adm1)

    container = f"The selected technology was: {option_slctd}"
    container1 = f"The selected region was: {option_adm1}"

    # Filtrar GeoDataFrame por tecnología
    dff = gdf_csv[gdf_csv["technology"] == option_slctd]
    dff = dff[dff["ADM1_ES"] == option_adm1]


    if dff.empty:
        print("GeoDataFrame is empty.")
        return container, go.Figure()

    # Convertir GeoDataFrame a GeoJSON
    geojson = json.loads(dff.to_json())

    # Reproyectar temporalmente para calcular centroides correctos
    gdf_projected = dff.to_crs(epsg=3857)
    centroid = gdf_projected.geometry.centroid.to_crs(epsg=4326)

    # Crear figura
    fig_map = px.choropleth_mapbox(
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

    fig_map.update_layout(
        width=1700,
        height=700,
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

   # Gráfico de una sola barra apilada (100%)
    bar_data = dff['comparison'].value_counts(normalize=True).mul(100).round(2)

    bar_fig = go.Figure()
    categories = ['Ambos Tigo + Claro', 'Solo Tigo', 'Solo Claro']
    colors = {
        "Ambos Tigo + Claro": "gray",
        "Solo Tigo": "blue",
        "Solo Claro": "red"
    }

    x0 = 0
    for category in categories:
        value = bar_data.get(category, 0)
        bar_fig.add_trace(go.Bar(
            x=[value],
            y=["Cobertura"],
            name=category,
            orientation='h',
            marker=dict(color=colors[category]),
            text=f"{value}%",
            textposition='inside'
        ))
        x0 += value

    bar_fig.update_layout(
        barmode='stack',
        title='Percentage distribution by type of coverage (total = 100%)',
    #    xaxis=dict(range=[0, 100], title='Porcentaje (%)'),
        yaxis=dict(showticklabels=False),
        height=200,
        margin=dict(t=40, b=20, l=20, r=20),
        showlegend=True
    )

    return container, container1, fig_map, bar_fig

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=10000)
