# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Corps Éthérique – Analyse Vibratoire & Soins Karmiques              ║
# ║  Projet Kerberos – BioResonance                                      ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# Copyright (C) 2026  [Ton nom ou pseudonyme]
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
🌿 Corps Éthérique – Champ bioénergétique subtil (NIH "biofield").
Basé sur :
- La fréquence de Schumann (7.83 Hz) → lien Terre/cerveau (NASA, König)
- Les travaux sur le champ biologique (NIH, Rubik, Oschman)
- Les systèmes traditionnels non-dogmatiques :
    • Médecine chinoise : circulation d’énergie (Qi) via les méridiens → modélisé comme flux vibratoire
    • Ayurveda : nadis (canaux subtils) → traduits en "cohérence du champ"
- Aucune mention de chakras, d’entités, ou de hiérarchie spirituelle

Objectif : diagnostiquer l’état du champ éthérique, sans jugement, avec précision.
"""

import math

class CorpsEtherique:
    def __init__(self, cortex):
        self.cortex = cortex

    def analyser_champ(self, contexte, incarnations):
        frequence_base = 7.83  # Fréquence fondamentale de résonance Terre-cerveau (Schumann)
        score_perturbation = 0
        facteurs = []

        # 1. Lieu de naissance : perte de connexion au champ terrestre
        if not self._est_lieu_sacre(contexte["latitude"], contexte["longitude"]):
            score_perturbation += 15
            facteurs.append("naissance en lieu neutre (absence de résonance sacrée)")

        # 2. Départ précoce : rupture du lien éthérique (décès nourrisson)
        if contexte.get("deces_nourrisson"):
            score_perturbation += 25
            facteurs.append("rupture du fil éthérique (décès nourrisson)")

        # 3. Vies passées : charge mémorielle (violence, guerre, pouvoir)
        for inc in incarnations:
            lecon = inc.get("lecon_karmique", "").lower()
            if "guerre" in lecon or "violence" in lecon or "pouvoir absolu" in lecon:
                score_perturbation += 20
                facteurs.append("mémoire collective de violence")
                break
            elif "libérer" in lecon or "détachement" in lecon:
                score_perturbation -= 10
            elif "protéger" in lecon or "rayonner" in lecon:
                score_perturbation -= 5

        # 4. Calcul de la fréquence actuelle (bornes : 4.0–8.5 Hz)
        frequence_actuelle = frequence_base - (score_perturbation * 0.1)
        frequence_actuelle = max(4.0, min(frequence_actuelle, 8.5))

        # 5. État nuancé (basé sur la cohérence du biofield)
        if score_perturbation <= 5:
            etat = "cohérent"
            description = "Ton champ éthérique est en phase avec la fréquence de la Terre."
        elif score_perturbation <= 25:
            etat = "légèrement désynchronisé"
            description = "Des tensions subtiles perturbent ta résonance avec le champ terrestre."
        else:
            etat = "fragmenté"
            description = "Le champ éthérique porte des mémoires profondes nécessitant une harmonisation."

        return {
            "frequence_base_hz": frequence_base,
            "frequence_actuelle_hz": round(frequence_actuelle, 2),
            "score_perturbation": score_perturbation,
            "facteurs": facteurs,
            "etat": etat,
            "description": description,
            "soins_recommandes": self._recommander_soins(etat, frequence_actuelle)
        }

    def _est_lieu_sacre(self, lat, lon):
        lieux = self.cortex.lobe_temporal.lieux_sacres
        for lieu in lieux:
            dist = self._haversine(lat, lon, lieu["latitude"], lieu["longitude"])
            if dist < 50:  # km
                return True
        return False

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _recommander_soins(self, etat, frequence_cible):
        soins = []
        if etat == "cohérent":
            soins.append("Maintenir la connexion terrestre (marche pieds nus, exposition à la nature)")
        elif etat == "légèrement désynchronisé":
            soins.append("Bain sonore à 7.83 Hz (fréquence de Schumann)")
            soins.append("Exposition au lieu sacré le plus proche")
        elif etat == "fragmenté":
            soins.append("Harmonisation par 528 Hz (fréquence de réparation ADN, étudiée en bioacoustique)")
            soins.append("Écoute de battements cardiaques intra-utérins (si disponibles)")

        soins.append(f"Fréquence cible : {frequence_cible:.2f} Hz")
        return soins