import streamlit as st
import pandas as pd
import geopandas as gpd
import mysql.connector
from shapely import wkt
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="wide")
st.title("Kraje České republiky")


# Načtení dat z DB
@st.cache_data
def load_kraje_from_db():
    conn = mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="geo_data"
    )
    query = """
        SELECT nazev AS NAZEV, kod AS KOD, nuts AS NUTS3_KOD, ST_AsText(geom) AS geometry_wkt  
        FROM vuscs
    """
    df = pd.read_sql(query, conn)
    conn.close()

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkt(df["geometry_wkt"]),
        crs="EPSG:4326"
    )
    gdf["geometry"] = gdf["geometry"].simplify(0.001, preserve_topology=True)
    return gdf

gdf = load_kraje_from_db()

# Mapa ČR
m = folium.Map(
    location=[49.8, 15.5],
    zoom_start=8,
    tiles=None,  # žádné pozadí
    max_bounds=True,
    zoom_control=True,
    scrollWheelZoom=False,
    dragging=False
)
m.fit_bounds([[48.55, 12.09], [51.06, 18.86]])  # hranice ČR


# Vykreslení všech krajů
folium.GeoJson(
    gdf,
    style_function=lambda x: {
        "fillColor": "#dddddd",
        "color": "#666666",
        "weight": 1,
        "fillOpacity": 0.3,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NAZEV"], aliases=["Kraj:"])
).add_to(m)

# Detekce kliknutí
clicked = st_folium(m, width=1400, height=1000)

# Pokud byl kraj kliknut
if clicked and clicked.get("last_active_drawing"):
    props = clicked["last_active_drawing"]["properties"]
    st.session_state["nuts3_kod"] = props["NUTS3_KOD"]
    st.session_state["kraj_nazev"] = props["NAZEV"]
    st.switch_page("pages/okresy.py")
