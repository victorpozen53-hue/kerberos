# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  MapQuest – Géocodage (optionnel, nécessite clé)                    ║
# ║  Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# Copyright (C) 2026  Victor.Pozen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import urllib.request
import urllib.parse
import json

def geocode_mapquest(adresse, mapquest_key, timeout=5):
    """
    Géocode via MapQuest (nécessite une clé API).
    ⚠️ Optionnel : utilisé seulement si une clé est fournie.
    Score bas (2) car service centralisé, non libre, potentiellement traçant.
    """
    if not mapquest_key or not adresse or not adresse.strip():
        return None

    query = urllib.parse.quote(adresse.strip())
    # 🔧 Correction : suppression des espaces après le =
    url = f"https://www.mapquestapi.com/geocoding/v1/address?key={mapquest_key}&location={query}&maxResults=1"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('results') and len(data['results']) > 0:
                locations = data['results'][0].get('locations', [])
                if locations:
                    loc = locations[0]
                    lat_lng = loc.get('latLng', {})
                    lat = lat_lng.get('lat')
                    lon = lat_lng.get('lng')
                    if lat is not None and lon is not None:
                        nom = f"{loc.get('street', '')}, {loc.get('adminArea5', '')}, {loc.get('adminArea1', '')}".strip(", ")
                        return {
                            "source": "MapQuest",
                            "lat": float(lat),
                            "lon": float(lon),
                            "nom": nom,
                            "score": 2  # Bas : service propriétaire, non conforme à l'éthique libre
                        }
    except Exception:
        pass  # 🔇 Erreur silencieuse → fallback sur d'autres moteurs

    return None