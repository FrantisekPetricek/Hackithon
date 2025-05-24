import streamlit as st
import pandas as pd
import geopandas as gpd
import mysql.connector
from shapely import wkt
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="wide")
st.title("Interaktivní mapa obcí")

# --- Cacheovaná funkce pro načtení krajů z MySQL ---
@st.cache_data(ttl=600)  # data se uloží do cache na 10 minut
def load_kraje_from_db():
    conn = mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="geo_data"
    )
    query = """
        SELECT nazev AS NAZEV, obec_kod AS KOD, lau1_kod AS NUTS3_KOD, 
               ST_AsText(geom) AS geometry_wkt  
        FROM zsj
    """
    df = pd.read_sql(query, conn)
    conn.close()

    # Převedeme WKT na geometrii
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkt(df["geometry_wkt"]),
        crs="EPSG:4326"
    )
    gdf["geometry"] = gdf["geometry"].simplify(0.001, preserve_topology=True)
    return gdf

# --- Načtení dat ---
gdf = load_kraje_from_db()

# --- Výběr kraje ---
kraje = sorted(gdf["NAZEV"].unique())
vybrany_kraj = st.selectbox("Vyber okres", kraje)
gdf_filtered = gdf[gdf["NAZEV"] == vybrany_kraj]

# --- Vytvoření mapy ---
center = [49.8, 15.5]
m = folium.Map(
    location=center,
    zoom_start=8,
    tiles=None,
    zoom_control=False,
    scrollWheelZoom=False,
    dragging=False,
    doubleClickZoom=False,
    touchZoom=False
)

# Základní vrstvy
folium.GeoJson(
    gdf,
    style_function=lambda x: {
        "fillColor": "#FFFFFF",
        "color": "#000000",
        "weight": 1,
        "fillOpacity": 0.3,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NAZEV"], aliases=["okres:"])
).add_to(m)

# Zvýrazněný kraj
folium.GeoJson(
    gdf_filtered,
    style_function=lambda x: {
        "fillColor": "#ff6600",
        "color": "red",
        "weight": 2,
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NAZEV"], aliases=["Vybraný okres:"])
).add_to(m)

# Zobraz mapa
st_folium(m, width=1400, height=1000)

# --- Dodatečné info ---
if not gdf_filtered.empty:
    nuts_kod = gdf_filtered["NUTS3_KOD"].iloc[0]
    st.markdown(f"**NUTS3 kód vybraného okres:** `{nuts_kod}`")
