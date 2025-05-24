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
def load_okresy_from_db():
    conn = mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="geo_data"
    )
    query = """
        SELECT nazev AS NAZEV, kod AS KOD, nuts3_kod AS NUTS3_KOD, ST_AsText(geom) AS geometry_wkt  
        FROM okres
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

gdf = load_okresy_from_db()
gdf_filtered = gdf[gdf["NUTS3_KOD"] == nuts_kod]

# Mapa okresů
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


# Všechny okresy (šedé pozadí)
folium.GeoJson(
    gdf,
    style_function=lambda x: {
        "fillColor": "#eeeeee",
        "color": "#aaaaaa",
        "weight": 1,
        "fillOpacity": 0.2,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NAZEV"])
).add_to(m)

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

if clicked and clicked.get("last_active_drawing"):
    props = clicked["last_active_drawing"]["properties"]
    st.session_state["nuts3_kod"] = props["NUTS3_KOD"]
    st.session_state["kraj_nazev"] = props["NAZEV"]
    st.switch_page("pages/okresy.py")

# Tlačítko zpět
if st.button("⬅️ Zpět na kraje"):
    del st.session_state["nuts3_kod"]
    del st.session_state["kraj_nazev"]
    st.switch_page("app.py")
