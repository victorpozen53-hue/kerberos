# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Scanner de Lieux Sacrés – Overpass API (OpenStreetMap)             ║
# ║  Projet Kerberos – BioResonance                                     ║
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

"""
🌍 Scanner dynamique de lieux sacrés via Overpass API.
Trouve automatiquement :
- Églises, chapelles, cathédrales
- Dolmens, menhirs, sites mégalithiques
- Grottes sacrées, sources miraculeuses
- Sanctuaires druidiques, lieux mariaux
- Autres lieux de culte ou de mémoire collective

Fonctionne sans clé API. Respecte les limites d’usage d’Overpass.
"""

import urllib.request
import urllib.parse
import json
import math


class ScannerLieuxSacres:
    def __init__(self, rayon_km=100):
        self.rayon_km = rayon_km
        # 🔧 Correction : suppression de l'espace final dans l'URL
        self.overpass_url = "https://overpass-api.de/api/interpreter"

    def _degres_vers_metres(self, lat, lon, rayon_km):
        """Convertit un rayon en km en degrés de latitude/longitude."""
        lat_delta = rayon_km / 111.0
        lon_delta = rayon_km / (111.0 * math.cos(math.radians(lat)))
        return lat_delta, lon_delta

    def scanner(self, lat_naissance, lon_naissance):
        """
        Retourne une liste de lieux sacrés autour du lieu de naissance,
        formatée comme dans lieux_sacres.csv.
        """
        lat_delta, lon_delta = self._degres_vers_metres(lat_naissance, lon_naissance, self.rayon_km)
        
        bbox = [
            lat_naissance - lat_delta,
            lon_naissance - lon_delta,
            lat_naissance + lat_delta,
            lon_naissance + lon_delta
        ]
        
        # Requête Overpass Turbo – lieux sacrés
        overpass_query = f"""
        [out:json];
        (
          node["amenity"="place_of_worship"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["historic"="archaeological_site"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["natural"="cave_entrance"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["historic"="stone"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          way["amenity"="place_of_worship"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
          node["religion"="christian"]["name"~"Notre-Dame|Marie|Bernadette",i]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        );
        out center;
        """
        
        try:
            encoded_query = urllib.parse.quote(overpass_query)
            url = f"{self.overpass_url}?data={encoded_query}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            lieux = []
            for elem in data.get("elements", []):
                if "lat" not in elem or "lon" not in elem:
                    continue

                tags = elem.get("tags", {})
                nom = tags.get("name", "Lieu sacré")
                religion = tags.get("religion", "")
                historic = tags.get("historic", "")
                amenity = tags.get("amenity", "")

                # Déterminer le type Kerberos
                if "dolmen" in nom.lower() or "menhir" in nom.lower() or historic == "stone":
                    type_ame = "mégalithe"
                    epoque = "néolithique"
                    freq = 8.5
                    annee = -4000
                elif religion == "christian":
                    if any(kw in nom.lower() for kw in ["marie", "notre-dame", "bernadette"]):
                        type_ame = "lieu_mariaire"
                        epoque = "mariage"
                        freq = 7.2
                        annee = 1866
                    else:
                        type_ame = "lieu_sacre"
                        epoque = "médiéval"
                        freq = 7.5
                        annee = 1200
                elif "cave" in historic or "grotte" in nom.lower():
                    type_ame = "grotte"
                    epoque = "paléolithique"
                    freq = 6.8
                    annee = -15000
                elif amenity == "place_of_worship":
                    type_ame = "sacré"
                    epoque = "inconnue"
                    freq = 7.83
                    annee = None
                else:
                    continue  # ignorer les lieux non pertinents
                
                lieux.append({
                    "nom_païen": nom,
                    "latitude": elem["lat"],
                    "longitude": elem["lon"],
                    "type": type_ame,
                    "epoque": epoque,
                    "frequence_hz": freq,
                    "statut": "actif",
                    "annee_approx": annee,
                    "source": "osm"
                })
            return lieux
        
        except Exception as e:
            print(f"⚠️ Erreur OSM : {e}")
            return []