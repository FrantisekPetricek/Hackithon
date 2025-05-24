import streamlit as st
import pandas as pd
import geopandas as gpd
import mysql.connector
from shapely import wkt
from streamlit_folium import st_folium
import folium

st.set_page_config(layout="wide")
st.title("Detail vybrané obce")

# Kontrola, zda máme obec_kod
if "obec_kod" not in st.session_state:
    st.switch_page("pages/obce.py")

obec_kod = st.session_state["obec_kod"]
obec_nazev = st.session_state.get("obec_nazev", "Neznámá obec")

# --- Načtení geometrie obce ---
@st.cache_data(ttl=600)
def load_obec_geom(kod):
    conn = mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="geo_data"
    )
    query = """
        SELECT nazev AS NAZEV, ST_AsText(geom) AS geometry_wkt 
        FROM obce 
        WHERE obec_kod = %s
    """
    df = pd.read_sql(query, conn, params=(kod,))
    conn.close()

    if df.empty:
        return None

    gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df["geometry_wkt"]), crs="EPSG:4326")
    return gdf

# --- Načtení údajů o obyvatelstvu ---
@st.cache_data(ttl=600)
def load_obyvatelstvo(kod):
    conn = mysql.connector.connect(
        host="mysql",
        user="root",
        password="root",
        database="geo_data"
    )
    query = """
        SELECT pohlavi_txt, hodnota
        FROM pohlavi
        WHERE uzemi_kod = %s
    """
    df = pd.read_sql(query, conn, params=(kod,))
    conn.close()
    return df

# --- Data ---
gdf_obec = load_obec_geom(obec_kod)
obyvatel_df = load_obyvatelstvo(obec_kod)

if gdf_obec is None:
    st.error("Obec nebyla nalezena.")
    st.stop()

# --- Mapa ---
bounds = gdf_obec.total_bounds
m = folium.Map(
    location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],
    zoom_start=12,
    tiles=None,
    max_bounds=True,
    zoom_control=True,
    scrollWheelZoom=False,
    dragging=False
)
m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

folium.GeoJson(
    gdf_obec,
    style_function=lambda x: {
        "fillColor": "#ff6600",
        "color": "red",
        "weight": 2,
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(fields=["NAZEV"])
).add_to(m)

st_folium(m, width=1400, height=1000)

# --- Textové informace ---
st.subheader(f"Obec: {obec_nazev} (kód: {obec_kod})")

if not obyvatel_df.empty:
    celkem = obyvatel_df[obyvatel_df["pohlavi_txt"] == ""].get("hodnota", pd.Series([0])).values[0]
    muzi = obyvatel_df[obyvatel_df["pohlavi_txt"] == "muž"].get("hodnota", pd.Series([0])).values[0]
    zeny = obyvatel_df[obyvatel_df["pohlavi_txt"] == "žena"].get("hodnota", pd.Series([0])).values[0]

    st.markdown(f"-**Celkem obyvatel:** `{celkem}`")
    st.markdown(f"-**Muži:** `{muzi}`")
    st.markdown(f"-**Ženy:** `{zeny}`")
else:
    st.warning("Počet obyvatel nebyl v databázi nalezen.")

# --- Zpět ---
if st.button("⬅️ Zpět na obce"):
    del st.session_state["obec_kod"]
    del st.session_state["obec_nazev"]
    st.switch_page("pages/obce.py")
