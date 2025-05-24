import geopandas as gpd
import mysql.connector
from shapely import wkt

# Načtení GeoJSON souboru
gdf = gpd.read_file("/data/simplifiedZSJ_P.geojson")

# Ověř nebo nastav CRS
if gdf.crs is None:
    gdf = gdf.set_crs("EPSG:4326")
else:
    gdf = gdf.to_crs("EPSG:4326")

# Připojení k MySQL databázi
conn = mysql.connector.connect(
    host="mysql",
    user="root",
    password="root",
    database="geo_data"
)
cursor = conn.cursor()

# Vytvoření tabulky s unikátním obec_kod
cursor.execute("""
CREATE TABLE IF NOT EXISTS zsj (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kod VARCHAR(10),
    nazev VARCHAR(255),
    katuze_kod VARCHAR(10),
    obec_kod VARCHAR(10) UNIQUE,
    pou_kod VARCHAR(10),
    orp_kod VARCHAR(10),
    okres_kod VARCHAR(10),
    lau1_kod VARCHAR(10),
    lau2_kod VARCHAR(20),
    char_kod VARCHAR(10),
    geom GEOMETRY NOT NULL SRID 4326
)
""")

# Vkládání dat s aktualizací při duplicitním obec_kod
for _, row in gdf.iterrows():
    wkt_geom = row.geometry.wkt
    cursor.execute("""
        INSERT INTO zsj (
            kod, nazev, katuze_kod, obec_kod, pou_kod,
            orp_kod, okres_kod, lau1_kod, lau2_kod, char_kod, geom
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))
        ON DUPLICATE KEY UPDATE
            kod = VALUES(kod),
            nazev = VALUES(nazev),
            katuze_kod = VALUES(katuze_kod),
            pou_kod = VALUES(pou_kod),
            orp_kod = VALUES(orp_kod),
            okres_kod = VALUES(okres_kod),
            lau1_kod = VALUES(lau1_kod),
            lau2_kod = VALUES(lau2_kod),
            char_kod = VALUES(char_kod),
            geom = VALUES(geom)
    """, (
        row.get("KOD"),
        row.get("NAZEV"),
        row.get("KATUZE_KOD"),
        row.get("OBEC_KOD"),
        row.get("POU_KOD"),
        row.get("ORP_KOD"),
        row.get("OKRES_KOD"),
        row.get("LAU1_KOD"),
        row.get("LAU2_KOD"),
        row.get("CHAR_KOD"),
        wkt_geom
    ))

conn.commit()
conn.close()
print("✅ Import/aktualizace proběhla úspěšně – unikátně podle `obec_kod`.")
