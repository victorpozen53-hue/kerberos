# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Géocodeur Triangulé – BioResonance / Kerberos                      ║
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

import json
from pathlib import Path
from .engines.nominatim import geocode_nominatim
from .engines.photon import geocode_photon
from .engines.geonames import geocode_geonames
from .engines.mapquest import geocode_mapquest

class GeoEngine:
    def __init__(self, cache_dir="resources/geo_cache", mapquest_key=None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "geocache.json"
        self.cache = self._load_cache()
        self.mapquest_key = mapquest_key

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text(encoding="utf-8"))
            except:
                pass
        return {}

    def _save_cache(self):
        self.cache_file.write_text(
            json.dumps(self.cache, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def _cache_key(self, adresse):
        import hashlib
        return hashlib.md5(adresse.lower().encode()).hexdigest()

    def geocode(self, adresse, log_callback=None):
        key = self._cache_key(adresse)
        if key in self.cache:
            if log_callback:
                log_callback(f"📦 Cache hit : {adresse}")
            return self.cache[key]

        resultats = []
        engines = [
            ("Nominatim", lambda: geocode_nominatim(adresse)),
            ("Photon", lambda: geocode_photon(adresse)),
            ("GeoNames", lambda: geocode_geonames(adresse)),
        ]
        if self.mapquest_key:
            engines.append(("MapQuest", lambda: geocode_mapquest(adresse, self.mapquest_key)))

        for name, engine in engines:
            try:
                r = engine()
                if r:
                    resultats.append(r)
                    if log_callback:
                        log_callback(f"✅ {name}: {r['lat']:.5f}, {r['lon']:.5f}")
            except Exception as e:
                if log_callback:
                    log_callback(f"⚠️ {name} : {str(e)[:50]}")

        if not resultats:
            raise Exception("Aucune API n'a pu géocoder cette adresse")

        if len(resultats) >= 2:
            resultat = self._triangulate(resultats, log_callback)
        else:
            resultat = resultats[0]

        self.cache[key] = resultat
        self._save_cache()
        return resultat

    def _triangulate(self, resultats, log_callback):
        total_score = sum(r['score'] for r in resultats)
        lat = sum(r['lat'] * r['score'] for r in resultats) / total_score
        lon = sum(r['lon'] * r['score'] for r in resultats) / total_score
        sources = " + ".join(r['source'] for r in resultats)
        if log_callback:
            log_callback(f"🎯 TRIANGULATION ({sources})")
            for r in resultats:
                log_callback(f"   • {r['source']}: {r['lat']:.5f}, {r['lon']:.5f} (score: {r['score']})")
            log_callback(f"   ➜ Résultat final: {lat:.5f}, {lon:.5f}")
        return {
            "source": f"Triangulation ({sources})",
            "lat": lat,
            "lon": lon,
            "nom": f"Triangulé depuis {len(resultats)} sources",
            "score": sum(r['score'] for r in resultats)
        }