import streamlit as st
import pandas as pd
import geopandas as gpd
import mysql.connector
from shapely import wkt
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="wide")
st.title("Obce v okrese")

# Kontrola, že máme předaný okres_kod
if "okres_kod" not in st.session_state:
    st.switch_page("pages/okresy.py")

okres_kod = st.session_state["okres_kod"]
okres_nazev = st.session_state.get("okres_nazev", "Neznámý okres")

# --- Načtení obcí z DB ---
@st.cache_data(ttl=600)
def load_obce_z_okresu(okres_kod):
    conn = mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="geo_data"
    )
    query = f"""
        SELECT nazev AS NAZEV, obec_kod AS KOD, okres_kod AS OKRES_KOD, 
               ST_AsText(geom) AS geometry_wkt  
        FROM obce
        WHERE okres_kod = '{okres_kod}'
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

gdf_filtered = load_obce_z_okresu(okres_kod)

# --- Bounding box ---
bounds = gdf_filtered.total_bounds
bbox_southwest = [bounds[1], bounds[0]]
bbox_northeast = [bounds[3], bounds[2]]

# --- Vytvoření mapy ---
m = folium.Map(
    location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],
    zoom_start=10,
    tiles=None,
    zoom_control=True,
    scrollWheelZoom=False,
    dragging=False
)
m.fit_bounds([bbox_southwest, bbox_northeast])

# --- Vybrané obce (oranžově) ---
folium.GeoJson(
    gdf_filtered,
    style_function=lambda x: {
        "fillColor": "#ff6600",
        "color": "red",
        "weight": 2,
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NAZEV"])
).add_to(m)

st.subheader(f"Obce v okrese: {okres_nazev}")
clicked = st_folium(m, width=1400, height=1000)

# --- Přejít na detail obce po kliknutí ---
if clicked and clicked.get("last_active_drawing"):
    props = clicked["last_active_drawing"]["properties"]
    st.session_state["obec_kod"] = props["KOD"]
    st.session_state["obec_nazev"] = props["NAZEV"]
    st.switch_page("pages/obec_detail.py")

# --- Tlačítko zpět ---
if st.button("⬅️ Zpět na okresy"):
    del st.session_state["okres_kod"]
    del st.session_state["okres_nazev"]
    st.switch_page("pages/okresy.py")
