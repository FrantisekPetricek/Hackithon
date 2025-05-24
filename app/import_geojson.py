import geopandas as gpd
import mysql.connector
from shapely import wkt

gdf = gpd.read_file("/data/VUSC_P.shp.geojson")
gdf = gdf.to_crs(epsg=4326)

conn = mysql.connector.connect(
    host="mysql",
    user="root",
    password="root",
    database="geo_data"
)

cursor = conn.cursor()

# Vytvoř tabulku
cursor.execute("""
CREATE TABLE IF NOT EXISTS vuscs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nazev VARCHAR(255),
    kod VARCHAR(10),
    nuts VARCHAR(10),
    geom GEOMETRY NOT NULL SRID 4326
)
""")

# Vlož data
for _, row in gdf.iterrows():
    wkt_geom = row.geometry.wkt
    cursor.execute("""
        INSERT INTO vuscs (nazev, kod, nuts, geom)
        VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326))
    """, (
        row["NAZEV"],
        row["KOD"],
        row["NUTS3_KOD"],
        wkt_geom
    ))

conn.commit()
conn.close()
