# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import json

def geocode_mapquest(adresse, mapquest_key, timeout=5):
    if not mapquest_key:
        return None
    query = urllib.parse.quote(adresse.strip())
    url = f"https://www.mapquestapi.com/geocoding/v1/address?key={mapquest_key}&location={query}&maxResults=1"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('results') and data['results'][0].get('locations'):
                loc = data['results'][0]['locations'][0]
                lat = loc['latLng']['lat']
                lon = loc['latLng']['lng']
                nom = f"{loc.get('street', '')}, {loc.get('adminArea5', '')}, {loc.get('adminArea1', '')}".strip(", ")
                return {
                    "source": "MapQuest",
                    "lat": float(lat),
                    "lon": float(lon),
                    "nom": nom,
                    "score": 2
                }
    except Exception as e:
        raise RuntimeError(f"MapQuest error for '{adresse}': {e}")
    return None