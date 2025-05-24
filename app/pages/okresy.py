import streamlit as st
import pandas as pd
import geopandas as gpd
import mysql.connector
from shapely import wkt
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="wide", page_title="Okresy v kraji", page_icon="🗺️")

# ---- TITULEK ----
st.markdown(f"""
    <h1 style='text-align: center; color: #2c3e50;'>🗺️ Okresy v kraji</h1>
    <h3 style='text-align: center; color: #e67e22;'>{st.session_state.get("kraj_nazev", "Neznámý kraj")}</h3>
    <p style='text-align: center; color: #7f8c8d;'>Kliknutím na okres zobrazíte seznam obcí</p>
    <hr style='margin-top: 0; margin-bottom: 2rem;'>
""", unsafe_allow_html=True)

# ---- KONTROLA PŘECHODU ----
if "nuts3_kod" not in st.session_state:
    st.switch_page("app.py")

nuts_kod = st.session_state["nuts3_kod"]

# ---- NAČTENÍ DAT ----
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

# ---- MAPA ----
bounds = gdf_filtered.total_bounds
bbox_southwest = [bounds[1], bounds[0]]
bbox_northeast = [bounds[3], bounds[2]]

m = folium.Map(
    location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],
    zoom_start=8,
    tiles="CartoDB positron",
    max_bounds=True,
    zoom_control=True,
    scrollWheelZoom=False,
    dragging=False
)
m.fit_bounds([bbox_southwest, bbox_northeast])

folium.GeoJson(
    gdf_filtered,
    style_function=lambda x: {
        "fillColor": "#e67e22",
        "color": "#d35400",
        "weight": 2,
        "fillOpacity": 0.6,
    },
    highlight_function=lambda x: {
        "fillColor": "#f39c12",
        "color": "#e67e22",
        "weight": 3,
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NAZEV"], aliases=["Okres:"], sticky=True)
).add_to(m)

# ---- ZOBRAZENÍ MAPY ----
st.markdown("<div style='padding: 0 2rem;'>", unsafe_allow_html=True)
clicked = st_folium(m, width=1400, height=850)
st.markdown("</div>", unsafe_allow_html=True)

# ---- ZPRACOVÁNÍ KLIKU ----
if clicked and clicked.get("last_active_drawing"):
    props = clicked["last_active_drawing"]["properties"]
    st.session_state["okres_kod"] = props["KOD"]
    st.session_state["okres_nazev"] = props["NAZEV"]
    st.switch_page("pages/obce.py")

# ---- TLAČÍTKO ZPĚT ----
st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 9])
with col1:
    if st.button("⬅️ Zpět  na  kraje "):
        del st.session_state["nuts3_kod"]
        del st.session_state["kraj_nazev"]
        st.switch_page("app.py")
