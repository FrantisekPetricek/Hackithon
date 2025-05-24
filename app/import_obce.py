import geopandas as gpd
import mysql.connector
from shapely import wkt

# Načtení GeoJSON souboru
gdf = gpd.read_file("/data/OBCE_P.shp.geojson")

# Ověř nebo nastav CRS
if gdf.crs is None:
    gdf = gdf.set_crs("EPSG:4326")
else:
    gdf = gdf.to_crs("EPSG:4326")

# Připojení k MySQL
conn = mysql.connector.connect(
    host="mysql",
    user="root",
    password="root",
    database="geo_data"
)
cursor = conn.cursor()

# Vytvoření tabulky obce
cursor.execute("""
CREATE TABLE IF NOT EXISTS obce (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kod VARCHAR(10),
    nazev VARCHAR(255),
    pou_kod VARCHAR(10),
    orp_kod VARCHAR(10),
    okres_kod VARCHAR(10),
    lau1_kod VARCHAR(10),
    lau2_kod VARCHAR(20),
    nuts3_kod VARCHAR(10),
    vusc_kod VARCHAR(10),
    obec_kod VARCHAR(10) UNIQUE,
    status_kod VARCHAR(10),
    mluv_pad_2 TEXT,
    mluv_pad_3 TEXT,
    mluv_pad_4 TEXT,
    mluv_pad_5 TEXT,
    mluv_pad_6 TEXT,
    mluv_pad_7 TEXT,
    sm_roz_kod VARCHAR(10),
    sm_typ_kod VARCHAR(10),
    vlajka_txt TEXT,
    znak_txt TEXT,
    zkratka VARCHAR(50),
    geom GEOMETRY NOT NULL SRID 4326
)
""")

# Vložení/aktualizace
for _, row in gdf.iterrows():
    wkt_geom = row.geometry.wkt
    cursor.execute("""
        INSERT INTO obce (
            kod, nazev, pou_kod, orp_kod, okres_kod, lau1_kod, lau2_kod,
            nuts3_kod, vusc_kod, obec_kod, status_kod,
            mluv_pad_2, mluv_pad_3, mluv_pad_4, mluv_pad_5,
            mluv_pad_6, mluv_pad_7, sm_roz_kod, sm_typ_kod,
            vlajka_txt, znak_txt, zkratka, geom
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, ST_GeomFromText(%s, 4326))
        ON DUPLICATE KEY UPDATE
            kod=VALUES(kod),
            nazev=VALUES(nazev),
            pou_kod=VALUES(pou_kod),
            orp_kod=VALUES(orp_kod),
            okres_kod=VALUES(okres_kod),
            lau1_kod=VALUES(lau1_kod),
            lau2_kod=VALUES(lau2_kod),
            nuts3_kod=VALUES(nuts3_kod),
            vusc_kod=VALUES(vusc_kod),
            status_kod=VALUES(status_kod),
            mluv_pad_2=VALUES(mluv_pad_2),
            mluv_pad_3=VALUES(mluv_pad_3),
            mluv_pad_4=VALUES(mluv_pad_4),
            mluv_pad_5=VALUES(mluv_pad_5),
            mluv_pad_6=VALUES(mluv_pad_6),
            mluv_pad_7=VALUES(mluv_pad_7),
            sm_roz_kod=VALUES(sm_roz_kod),
            sm_typ_kod=VALUES(sm_typ_kod),
            vlajka_txt=VALUES(vlajka_txt),
            znak_txt=VALUES(znak_txt),
            zkratka=VALUES(zkratka),
            geom=VALUES(geom)
    """, (
        row.get("KOD"),
        row.get("NAZEV"),
        row.get("POU_KOD"),
        row.get("ORP_KOD"),
        row.get("OKRES_KOD"),
        row.get("LAU1_KOD"),
        row.get("LAU2_KOD"),
        row.get("NUTS3_KOD"),
        row.get("VUSC_KOD"),
        row.get("KOD"),  # obec_kod je KOD
        row.get("STATUS_KOD"),
        row.get("MLUV_PAD_2"),
        row.get("MLUV_PAD_3"),
        row.get("MLUV_PAD_4"),
        row.get("MLUV_PAD_5"),
        row.get("MLUV_PAD_6"),
        row.get("MLUV_PAD_7"),
        row.get("SM_ROZ_KOD"),
        row.get("SM_TYP_KOD"),
        row.get("VLAJKA_TXT"),
        row.get("ZNAK_TXT"),
        row.get("ZKRATKA"),
        wkt_geom
    ))

conn.commit()
conn.close()
print("✅ Import obcí dokončen.")
