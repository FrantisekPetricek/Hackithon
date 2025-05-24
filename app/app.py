import streamlit as st
import pandas as pd
import geopandas as gpd
import mysql.connector
from shapely import wkt
from streamlit_folium import st_folium
import folium

# ZÁKLADNÍ NASTAVENÍ STRÁNKY
st.set_page_config(layout="wide", page_title="Kraje ČR", page_icon="🗺️")

# 🔹 MODERNÍ SIDEBAR
with st.sidebar:
    st.markdown("""
        <style>
            .sidebar-header {
                font-size: 22px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 0px;
            }
            .sidebar-subtitle {
                font-size: 14px;
                color: #7f8c8d;
                margin-top: 0px;
                margin-bottom: 20px;
            }
            .sidebar-box {
                padding: 10px;
                background-color: #f4f4f4;
                border-radius: 8px;
                margin-bottom: 20px;
                border: 1px solid #e0e0e0;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='sidebar-header'>🧭 GeoApp Hackathon</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-subtitle'>Kraje České republiky</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-box'>", unsafe_allow_html=True)
    st.markdown("✅ **Klikněte na kraj v mapě** pro zobrazení jeho okresů.")
    st.markdown("🗺️ Mapa je statická – posun a zoom je omezen.")
    st.markdown("</div>", unsafe_allow_html=True)


# 🔹 TITULEK HLAVNÍ STRÁNKY
st.markdown("""
    <h1 style='text-align: center; color: #2c3e50;'>🗺️ Kraje České republiky</h1>
    <p style='text-align: center; color: #7f8c8d; font-size:18px;'>Kliknutím na kraj zobrazíte jeho okresy.</p>
    <hr style='margin-bottom: 2rem;'>
""", unsafe_allow_html=True)

# 🔹 NAČTENÍ DAT Z DATABÁZE
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

# 🔹 MAPA ČR
m = folium.Map(
    location=[49.8, 15.5],
    zoom_start=8,
    tiles="CartoDB positron",  # moderní mapový podklad
    max_bounds=True,
    zoom_control=True,
    scrollWheelZoom=False,
    dragging=False
)

m.fit_bounds([[48.55, 12.09], [51.06, 18.86]])

# 🔹 VYKRESLENÍ KRAJŮ
folium.GeoJson(
    gdf,
    style_function=lambda x: {
        "fillColor": "#3498db",
        "color": "#2980b9",
        "weight": 1,
        "fillOpacity": 0.4,
    },
    highlight_function=lambda x: {
        "fillColor": "#1abc9c",
        "color": "#16a085",
        "weight": 2,
        "fillOpacity": 0.6,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NAZEV"], aliases=["Kraj:"], sticky=True)
).add_to(m)

# 🔹 ZOBRAZENÍ MAPY VE STREAMLITU
st.markdown("<div style='padding: 0 2rem;'>", unsafe_allow_html=True)
clicked = st_folium(m, width=1400, height=800)
st.markdown("</div>", unsafe_allow_html=True)

# 🔹 PŘESMĚROVÁNÍ NA OKRESY
if clicked and clicked.get("last_active_drawing"):
    props = clicked["last_active_drawing"]["properties"]
    st.session_state["nuts3_kod"] = props["NUTS3_KOD"]
    st.session_state["kraj_nazev"] = props["NAZEV"]
    st.switch_page("pages/okresy.py")
