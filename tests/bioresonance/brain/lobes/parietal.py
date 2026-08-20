# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Lobe Pariétal – Intégration Sensorielle Karmique                   ║
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

"""
✋ Lobe Pariétal – Fusionne les données sensorielles :
- Lieu de naissance (texte ou coordonnées)
- Date et heure
- Contexte géographique
Transforme les entrées brutes en contexte structuré pour le cortex.
"""

from datetime import datetime

class LobeParietal:
    def __init__(self, cortex):
        self.cortex = cortex

    def integrer_donnees(self, donnees_brutes):
        """
        Transforme les entrées utilisateur en contexte karmique structuré.
        Gère les cas : lieu textuel vs coordonnées directes.
        """
        if not donnees_brutes:
            raise ValueError("Aucune donnée fournie")

        contexte = {
            "date_naissance": None,
            "latitude": None,
            "longitude": None,
            "lieu_textuel": "",
            "schema_karmique": None,
            "geocoder_necessaire": False
        }

        # 1. Date + heure
        date_input = donnees_brutes.get("date_naissance")
        heure_input = donnees_brutes.get("heure_naissance", "12:00")
        if isinstance(date_input, str):
            try:
                dt_str = f"{date_input} {heure_input}"
                contexte["date_naissance"] = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            except ValueError:
                raise ValueError("Format : date=AAAA-MM-JJ, heure=HH:MM")
        elif isinstance(date_input, datetime):
            contexte["date_naissance"] = date_input
        else:
            raise ValueError("Date de naissance manquante")

        # 2. Coordonnées ou lieu textuel
        lat = donnees_brutes.get("latitude")
        lon = donnees_brutes.get("longitude")
        if lat is not None and lon is not None:
            try:
                contexte["latitude"] = float(lat)
                contexte["longitude"] = float(lon)
            except (ValueError, TypeError):
                raise ValueError("Coordonnées invalides")
        else:
            lieu = donnees_brutes.get("lieu", "").strip()
            if lieu:
                contexte["lieu_textuel"] = lieu
                contexte["geocoder_necessaire"] = True
            else:
                raise ValueError("Fournissez soit des coordonnées, soit un lieu.")

        # 3. Schéma karmique (optionnel)
        contexte["schema_karmique"] = donnees_brutes.get("schema")

        return contexte