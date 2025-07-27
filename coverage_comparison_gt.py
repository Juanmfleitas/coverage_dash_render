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
import os

px.set_mapbox_access_token("pk.eyJ1IjoianVhbm1mbGVpdGFzIiwiYSI6ImNrYnZoMTM4ejAzOGcydGxiMjJmeTYycm8ifQ.BcvHwPI_UZZfpfop746GDQ")

# ------------------------------------------------------------------------------
app = Dash(__name__)
server = app.server

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([

    # Incluir Google Fonts en el layout
    html.Link(
        href="https://fonts.googleapis.com/css2?family=Quicksand:wght@500&display=swap",
        rel="stylesheet"
    ),

    html.H1(
        "Digitel and Movistar 4G Mobile Coverage Comparison - Venezuela. Period: Q2 2025",
        style={
            'fontFamily': 'Poppins, sans-serif',
            'fontWeight': 'bold',  # 👈 negritas # 'bold'
            'color': '#0033A0',  # Azul corporativo Tigo
            'marginLeft': '17px'
        }
    ),

    html.Div([
        dcc.Dropdown(
            id="slct_adm1",
            options=[
                {"label": "Amazonas", "value": 'Amazonas'},
                {"label": "Anzoátegui", "value": 'Anzoátegui'},
                {"label": "Apure", "value": 'Apure'},
                {"label": "Aragua", "value": 'Aragua'},
                {"label": "Barinas", "value": 'Barinas'},
                {"label": "Bolívar", "value": 'Bolívar'},
                {"label": "Carabobo", "value": 'Carabobo'},
                {"label": "Cojedes", "value": 'Cojedes'},
                {"label": "Delta Amacuro", "value": 'Delta Amacuro'},
                {"label": "Distrito Capital", "value": 'Distrito Capital'},
                {"label": "Falcón", "value": 'Falcón'},
                {"label": "Guárico", "value": 'Guárico'},
                {"label": "La Guaira", "value": 'La Guaira'},
                {"label": "Lara", "value": 'Lara'},
                {"label": "Mérida", "value": 'Mérida'},
                {"label": "Miranda", "value": 'Miranda'},
                {"label": "Monagas", "value": 'Monagas'},
                {"label": "Nueva Esparta", "value": 'Nueva Esparta'},
                {"label": "Portuguesa", "value": 'Portuguesa'},
                {"label": "Sucre", "value": 'Sucre'},
                {"label": "Táchira", "value": 'Táchira'},
                {"label": "Trujillo", "value": 'Trujillo'},
                {"label": "Yaracuy", "value": 'Yaracuy'},
                {"label": "Zulia", "value": 'Zulia'}
            ],
            multi=False,
            value='Distrito Capital',
            style={'width': "70%"}
        ),
        dcc.Dropdown(
            id="slct_map_style",
            options=[
                {"label": "Satelital", "value": "satellite-streets"},
                {"label": "Light", "value": "carto-positron"},
                {"label": "Nocturno", "value": "carto-darkmatter"},  # Nuevo estilo nocturno
                {"label": "OpenStreetMap", "value": "open-street-map"},
                {"label": "Outdoors", "value": "outdoors"}
            ],
            value="satellite-streets",
            style={'width': "70%"} 
        )
    ], style={'width': "40%", 'fontFamily': 'Quicksand, sans-serif', 'fontSize': '16px', 'display': 'flex', 'gap': '10px', 'marginLeft': '15px'}),

    html.Div([
        html.Div(id='output_container1', children=[], style={'width': "40%"}),
        html.Div(id='output_container2', children=[], style={'width': "40%"}),       
    ], style={'width': "40%", 'fontFamily': 'Quicksand, sans-serif', 'fontSize': '16px', 'display': 'flex', 'gap': '10px', 'marginLeft': '10px'}), 

    html.Div([
        html.Br(),
        dcc.Graph(id='my_tech_map', figure={}, style={'height': '700px'}), #, 'marginLeft': '15px'
        html.Br(),
        dcc.Graph(id='comparison_bar_chart', figure={}, style={'height': '200px'})
    ], style={
        # 'maxWidth': '100%',
        # 'margin': '0 auto',
        'width': '98%',               # Mismo ancho para ambas figuras
        'marginLeft': 'auto',         # Centra automáticamente horizontalmente
        'marginRight': 'auto',
    #    'paddingLeft': '10px',        # Opcional: añade un poco de espacio interno
    #    'paddingRight': '10px'

})

], style={'backgroundColor': '#f1f2f3', 'padding': '5px'})

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
warnings.filterwarnings("ignore", category=FutureWarning)

@app.callback(
    [Output(component_id='output_container1', component_property='children'),
     Output(component_id='output_container2', component_property='children'),
     Output(component_id='my_tech_map', component_property='figure'),
     Output(component_id='comparison_bar_chart', component_property='figure')],  # Nuevo output
    [Input(component_id='slct_adm1', component_property='value'),
     Input(component_id='slct_map_style', component_property='value')]

    )

def update_graph(option_adm1, map_style):

# ------------------------------------------------------------------------------
# Leer parquet procesado
    columns_needed = ['quadkey', 'geometry', 'technology','comparison','ADM1_ES']
    pivot_table = pd.read_parquet("processed_data_VE.parquet", columns=columns_needed)
    pivot_table = pivot_table[pivot_table["ADM1_ES"] == option_adm1]  # 👈 primero filtras 

# Convertir geometría load_WKT a objeto geométrico
    pivot_table['geometry'] = pivot_table['geometry'].apply(load_wkb)

# Crear GeoDataFrame
    gdf_csv = gpd.GeoDataFrame(pivot_table, geometry="geometry")
    
    if gdf_csv.crs is None:
        gdf_csv.set_crs(epsg=4326, inplace=True)

    print(option_adm1)
    print(map_style)

#    container = f"The selected adm1 was: {option_adm1}"
    container1 = html.Div(
    f"Selected region: {option_adm1}",
    style={
        'fontFamily': 'Quicksand, sans-serif',
        'color': '#0033A0',  # Azul corporativo Tigo
 #       'fontWeight': 'bold',
        'width': "100%",
        'fontSize': '18px',
        'marginLeft': '7px',  # 👈 Alineación izquierda ajustada
        'marginRight': '10px',  # 👈 espacio hacia container2
    }
    )

#    container = f"The selected background was: {map_style}"
    container2 = html.Div(
    f"Selected background: {map_style}",
    style={
        'fontFamily': 'Quicksand, sans-serif',
        'color': '#0033A0',  # Azul corporativo Tigo
 #       'fontWeight': 'bold',
        'fontSize': '18px',
        'width': "150%",
        'marginLeft': '70px'  # 👈 Alineación izquierda ajustada
    }
    )

# Filtrar GeoDataFrame por tecnología
    dff = gdf_csv[gdf_csv["ADM1_ES"] == option_adm1]

    if dff.empty:
        print("GeoDataFrame is empty.")
        return container1, go.Figure()  #cambiar---------------------

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
        mapbox_style=map_style,
        center={
            "lat": centroid.y.mean(),
            "lon": centroid.x.mean()
        },
        zoom=11,
        opacity=0.6,
        hover_name="quadkey",
        color_discrete_map={
            "Ambos Digitel + Movistar": "gray",
            "Solo Movistar": "green",
            "Solo Digitel": "purple"
        }
    )

    fig_map.update_layout(
#    width=1700,
    height=700,
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    legend=dict(
        x=0.01,          # horizontal position (0 = left, 1 = right)
        y=0.02,         # vertical position (0 = bottom, 1 = top)
        bgcolor='white',  # Fondo blanco sólido
#        bgcolor='rgba(255,255,255,0.6)',  # semi-transparent background
        bordercolor='black',
        borderwidth=1,
        font=dict(size=12)
    )
    )

# Gráfico de una sola barra apilada (100%)
    bar_data = dff['comparison'].value_counts(normalize=True).mul(100).round(2)

    bar_fig = go.Figure()
    categories = ['Ambos Digitel + Movistar', 'Solo Movistar', 'Solo Digitel']
    colors = {
        "Ambos Digitel + Movistar": "gray",
        "Solo Movistar": "green",
        "Solo Digitel": "purple"
    }

    for category in categories:
        value = bar_data.get(category, 0)
        bar_fig.add_trace(go.Bar(
            x=[value],
            y=["Cobertura"],
            name=category,
            orientation='h',
            marker=dict(color=colors[category]),
            text=f"{value}%",
            textposition='inside',
            textfont=dict(size=19, color='white')  # <-- Tamaño y color del texto
        ))

    bar_fig.update_layout(
        barmode='stack',
        #title='Distribución porcentual por operador móvil disponible',
        title=dict(
        text='Percentage distribution by available mobile operator',
        x=0,  # 👈 más cerca del borde izquierdo
        font=dict(
            family='Quicksand, sans-serif',
            size=20,
            color='#0033A0'  # Azul corporativo Tigo
        )
        ),
        yaxis=dict(showticklabels=False),
        height=160,
#        margin=dict(t=40, b=20, l=20, r=20),
        margin=dict(t=30, b=0, l=0, r=0),
        showlegend=False,
        paper_bgcolor='#f1f2f3',  # Fondo del canvas (todo el gráfico)
        plot_bgcolor='#f1f2f3'    # Fondo del área del gráfico en sí
    )

    return container1, container2, fig_map, bar_fig

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8054))
    app.run_server(debug=False, host="0.0.0.0", port=port)