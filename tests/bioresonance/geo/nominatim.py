# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Nominatim – Géocodage via OpenStreetMap (OSM)                      ║
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

def geocode_nominatim(adresse, timeout=5):
    """
    Géocode une adresse via Nominatim (OpenStreetMap).
    Respecte la politique de fair use (User-Agent explicite, pas de spam).
    """
    if not adresse or not adresse.strip():
        return None

    query = urllib.parse.quote(adresse.strip())
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1&addressdetails=1&polygon=0"

    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Kerberos-v2.0 (ethical, GPLv3, no tracking)',
            'Accept': 'application/json'
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data and len(data) > 0:
                result = data[0]
                importance = float(result.get('importance', 0.5))
                score = 5 + int(importance * 10)  # Score entre 5 et 15
                return {
                    "source": "Nominatim",
                    "lat": float(result['lat']),
                    "lon": float(result['lon']),
                    "nom": result['display_name'],
                    "score": score
                }
    except Exception:
        pass  # Erreur silencieuse → laissée au moteur principal

    return None