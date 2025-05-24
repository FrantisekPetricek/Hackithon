import streamlit as st
import pandas as pd
import geopandas as gpd
import mysql.connector
from shapely import wkt
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="wide")   
st.title("Okresy v kraji")

# Kontrola zda máme předaný NUTS3_KOD
if "nuts3_kod" not in st.session_state:
    st.switch_page("app.py")

nuts_kod = st.session_state["nuts3_kod"]
kraj_nazev = st.session_state.get("kraj_nazev", "Neznámý kraj")

# Načtení dat z DB
@st.cache_data
def load_okresy_from_db(nuts3_kod):
    conn = mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="geo_data"
    )
    query = f"""
        SELECT nazev AS NAZEV, kod AS KOD, nuts3_kod AS NUTS3_KOD, ST_AsText(geom) AS geometry_wkt  
        FROM okres
        WHERE nuts3_kod = '{nuts3_kod}'
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

gdf_filtered = load_okresy_from_db(nuts_kod)

# Spočítej bounding box vybraného kraje
bounds = gdf_filtered.total_bounds  # [minx, miny, maxx, maxy]
bbox_southwest = [bounds[1], bounds[0]]  # [miny, minx]
bbox_northeast = [bounds[3], bounds[2]]  # [maxy, maxx]

# Mapa přiblížená na vybraný kraj
m = folium.Map(
    location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],
    zoom_start=8,
    tiles=None,
    max_bounds=True,
    zoom_control=True,
    scrollWheelZoom=False,
    dragging=False
)
m.fit_bounds([bbox_southwest, bbox_northeast])

# Vybrané okresy (oranžově)
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

st.subheader(f"Okresy v kraji: {kraj_nazev}")
clicked = st_folium(m, width=1400, height=1000)

# Kliknutí na okres – uložení a přechod
if clicked and clicked.get("last_active_drawing"):
    props = clicked["last_active_drawing"]["properties"]
    st.session_state["okres_kod"] = props["KOD"]
    st.session_state["okres_nazev"] = props["NAZEV"]
    st.switch_page("pages/obce.py")

# Tlačítko zpět
if st.button("⬅️ Zpět na kraje"):
    del st.session_state["nuts3_kod"]
    del st.session_state["kraj_nazev"]
    st.switch_page("app.py")
