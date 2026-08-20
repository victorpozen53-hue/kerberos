# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Photon – Géocodage via photon.komoot.io (OpenStreetMap)            ║
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

def geocode_photon(adresse, timeout=5):
    """
    Géocode une adresse via Photon (komoot.io), basé sur OpenStreetMap.
    Rapide, libre, sans clé API, mais moins détaillé que Nominatim.
    """
    if not adresse or not adresse.strip():
        return None

    query = urllib.parse.quote(adresse.strip())
    # 🔧 Correction : suppression des espaces après le =
    url = f"https://photon.komoot.io/api?q={query}&limit=1"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('features') and len(data['features']) > 0:
                feature = data['features'][0]
                props = feature['properties']
                coords = feature['geometry']['coordinates']
                nom = f"{props.get('name', '')}, {props.get('city', '')}".strip(", ")
                return {
                    "source": "Photon",
                    "lat": float(coords[1]),
                    "lon": float(coords[0]),
                    "nom": nom,
                    "score": 4  # Moyen : rapide mais moins riche que Nominatim
                }
    except Exception:
        pass  # 🔇 Erreur silencieuse → fallback géré par GeoEngine

    return None