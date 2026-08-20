# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  GeoNames – Géocodage via geonames.org                             ║
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

def geocode_geonames(adresse, timeout=5):
    """
    Géocode une adresse via GeoNames (geonames.org).
    Nécessite un compte gratuit (username=kerberos_v2).
    """
    if not adresse or not adresse.strip():
        return None

    # Utiliser seulement la première partie de l'adresse (ville/pays)
    query = urllib.parse.quote(adresse.split(',')[0].strip())
    url = f"http://api.geonames.org/searchJSON?q={query}&maxRows=1&username=kerberos_v2"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('geonames') and len(data['geonames']) > 0:
                item = data['geonames'][0]
                nom = f"{item['name']}, {item.get('countryName', '')}".strip(", ")
                return {
                    "source": "GeoNames",
                    "lat": float(item['lat']),
                    "lon": float(item['lng']),
                    "nom": nom,
                    "score": 3  # Score bas : précision limitée (ville/pays seulement)
                }
    except Exception:
        pass  # Erreur silencieuse → laissée au moteur principal

    return None