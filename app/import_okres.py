import geopandas as gpd
import mysql.connector
from shapely import wkt

# Načtení GeoJSON souboru
gdf = gpd.read_file("/data/OKRESY_P.shp.geojson")
gdf = gdf.to_crs(epsg=4326)

# Připojení k MySQL databázi
conn = mysql.connector.connect(
    host="mysql",       # pokud používáš docker-compose službu
    user="root",
    password="root",
    database="geo_data"
)
cursor = conn.cursor()

# Vytvoření tabulky (rozšířeno o LAU1_KOD a VUSC_KOD)
cursor.execute("""
CREATE TABLE IF NOT EXISTS okres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kod VARCHAR(10),
    nazev VARCHAR(255),
    lau1_kod VARCHAR(10),
    vusc_kod VARCHAR(10),
    nuts3_kod VARCHAR(10),
    geom GEOMETRY NOT NULL SRID 4326
)
""")

# Vkládání dat
for _, row in gdf.iterrows():
    wkt_geom = row.geometry.wkt
    cursor.execute("""
        INSERT INTO okres (kod, nazev, lau1_kod, vusc_kod, nuts3_kod, geom)
        VALUES (%s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))
    """, (
        row["KOD"],
        row["NAZEV"],
        row["LAU1_KOD"],
        row["VUSC_KOD"],
        row["NUTS3_KOD"],
        wkt_geom
    ))

conn.commit()
conn.close()
