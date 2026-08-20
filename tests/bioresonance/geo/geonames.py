# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import json

def geocode_geonames(adresse, timeout=5):
    query = urllib.parse.quote(adresse.split(',')[0].strip())
    url = f"http://api.geonames.org/searchJSON?q={query}&maxRows=1&username=kerberos_v2"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('geonames'):
                item = data['geonames'][0]
                return {
                    "source": "GeoNames",
                    "lat": float(item['lat']),
                    "lon": float(item['lng']),
                    "nom": f"{item['name']}, {item.get('countryName', '')}".strip(", "),
                    "score": 3
                }
    except Exception as e:
        raise RuntimeError(f"GeoNames error for '{adresse}': {e}")
    return None