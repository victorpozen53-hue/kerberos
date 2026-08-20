# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Lobe Frontal – Détecteur de Résonance Karmique Réelle              ║
# ║  Projet Kerberos – BioResonance                                    ║
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
🧠 Lobe Frontal – Ne simule pas. Perçoit.
Croise :
- Lieu de naissance (lat/lon)
- Date de naissance → influence le poids des époques
- Base de lieux sacrés (lieux_sacres.csv)

Retourne TOUTES les résonances significatives — sans limite, sans jugement.
"""

from datetime import datetime
import math

class LobeFrontal:
    def __init__(self, cortex):
        self.cortex = cortex

    def calculer_incarnations(self, contexte):
        """
        Détecte les incarnations réelles en croisant lieu, date et base de lieux sacrés.
        """
        lat_actuelle = contexte["latitude"]
        lon_actuelle = contexte["longitude"]
        annee_naissance = contexte["date_naissance"].year

        lieux_sacres = self.cortex.lobe_temporal.lieux_sacres
        incarnations = []

        for lieu in lieux_sacres:
            dist_km = self._haversine(lat_actuelle, lon_actuelle, lieu["latitude"], lieu["longitude"])

            # Score de base : distance
            score = 0
            if dist_km < 100:      score += 50
            elif dist_km < 500:    score += 30
            elif dist_km < 2000:   score += 15
            else:                  score += 5

            # Bonus époque
            epoque = lieu.get("epoque", "inconnue")
            if epoque == "néolithique": score += 40
            elif epoque == "antiquité": score += 25
            elif epoque == "gaulois":   score += 20
            elif epoque == "néandertalien": score += 45  # priorité haute

            # Affinité temporelle
            annee_lieu = lieu.get("annee_approx")
            if annee_lieu is not None:
                ecart_annees = abs(annee_naissance - annee_lieu)
                if ecart_annees <= 200:
                    score += 30
                elif ecart_annees <= 1000:
                    score += 15
                elif ecart_annees <= 3000:
                    score += 5

            # Bonus statut
            if lieu.get("statut") == "actif":
                score += 10

            # Seulement les résonances significatives
            if score >= 20:
                annee = annee_lieu if annee_lieu is not None else "époque inconnue"
                incarnations.append({
                    "numero": len(incarnations) + 1,
                    "type_ame": self._type_lieu_vers_type_ame(lieu.get("type", "sacré")),
                    "annee": annee,
                    "epoque": epoque,
                    "latitude": lieu["latitude"],
                    "longitude": lieu["longitude"],
                    "distance_actuelle_km": dist_km,
                    "lecon_karmique": self._determiner_lecon_karmique(lieu),
                    "lieu_sacre": lieu["nom"],
                    "frequence_hz": lieu.get("frequence", 7.83),
                    "score_karmique": score
                })

        # Trier par résonance décroissante
        incarnations.sort(key=lambda x: x["score_karmique"], reverse=True)
        return incarnations

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Rayon terrestre en km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _type_lieu_vers_type_ame(self, type_lieu):
        mapping = {
            "sanctuaire_druidique": "Gardien des forêts sacrées",
            "temple_solaire": "Porteur de lumière",
            "mégalithe": "Ancrage terrestre",
            "grotte": "Mystique des profondeurs",
            "montagne": "Visionnaire céleste",
            "fontaine": "Guérisseur des eaux",
            "lieu_mariaire": "Âme en compassion",
            "sacré": "Âme en éveil"
        }
        return mapping.get(type_lieu, "Âme en quête")

    def _determiner_lecon_karmique(self, lieu):
        type_ame = self._type_lieu_vers_type_ame(lieu.get("type", "sacré"))
        statut = lieu.get("statut", "actif")
        if "Gardien" in type_ame:
            return "Protéger les lieux sacrés sans s'y attacher"
        elif "Porteur" in type_ame:
            return "Rayonner sans brûler autrui"
        elif "Ancrage" in type_ame:
            return "Être enraciné mais libre"
        elif "Mystique" in type_ame:
            return "Explorer l’ombre pour y trouver la lumière"
        elif "Visionnaire" in type_ame:
            return "Voir au-delà du visible"
        elif "Guérisseur" in type_ame:
            return "Soigner par la douceur, non par la force"
        elif "compassion" in type_ame:
            return "Aimer sans condition, même dans la souffrance"
        elif statut == "disparu":
            return "Libérer la mémoire de ce qui a été détruit"
        else:
            return "Réapprendre la connexion sacrée"