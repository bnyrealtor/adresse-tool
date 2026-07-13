import streamlit as st
import geopandas as gpd
from owslib.wfs import WebFeatureService
from geopy.geocoders import Nominatim
from pyproj import Transformer

st.set_page_config(page_title="ImmoDaten-Tool NI", layout="wide")
st.title("Immobilien-Abfrage LGLN")

# 1. Adresse zu Koordinaten (Geocoding)
def get_coords(address):
    geolocator = Nominatim(user_agent="radtke_immo_tool")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None

# 2. WFS Abfrage (vereinfacht)
def fetch_wfs_data(lat, lon):
    # LGLN WFS Service
    wfs = WebFeatureService(url="https://opendata.lgln.niedersachsen.de/wfs/gds_alkis", version="2.0.0")
    
    # Transformation von WGS84 (GPS) in ETRS89/UTM32N für LGLN
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    e, n = transformer.transform(lon, lat)
    
    # Bounding Box um die Koordinate (50m Radius)
    bbox = (e-50, n-50, e+50, n+50)
    
    # Abfrage - WICHTIG: Prüfe im WFS-Layer, wie das Objekt genau heißt (hier Beispiel)
    response = wfs.getfeature(typename='alkis:flurstueck', bbox=bbox, outputFormat='json')
    return gpd.read_file(response)

# UI
address = st.text_input("Adresse eingeben (Straße, PLZ, Ort)")
if st.button("Abfrage starten"):
    with st.spinner("Suche Flurstück..."):
        coords = get_coords(address)
        if coords:
            gdf = fetch_wfs_data(coords[0], coords[1])
            if not gdf.empty:
                st.success("Daten gefunden!")
                st.dataframe(gdf)
            else:
                st.warning("Kein Flurstück gefunden.")
        else:
            st.error("Adresse nicht gefunden.")
