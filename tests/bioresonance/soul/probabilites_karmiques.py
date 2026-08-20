# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  BIORESONANCE - MOTEUR DE PROBABILITÉS KARMIQUES                   ║
# ║  Calcule les probabilités liées au voyage de l'âme                  ║
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
# along with this program.  If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.

import math
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from collections import Counter


@dataclass
class ProbabiliteKarmique:
    """Résultat d'un calcul de probabilité karmique"""
    type_calcul: str
    probabilite: float  # Entre 0 et 1
    confiance: float    # Niveau de confiance (0-1)
    details: Dict
    interpretation: str


class MoteurProbabilites:
    """
    Calcule différentes probabilités liées au karma, aux incarnations et aux liens géographiques
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.seed_aleatoire = seed or int(datetime.now(timezone.utc).timestamp())
        random.seed(self.seed_aleatoire)
    
    # ═══════════════════════════════════════════════════════════════════
    # 1️⃣ PROBABILITÉS GÉOGRAPHIQUES
    # ═══════════════════════════════════════════════════════════════════
    
    def probabilite_zone_karmique(self, 
                                   lat_actuelle: float, 
                                   lon_actuelle: float,
                                   incarnations_passees: List[Dict]) -> ProbabiliteKarmique:
        """
        Calcule la probabilité d'avoir un lien karmique fort avec la zone actuelle
        basé sur la proximité des vies antérieures
        """
        if not incarnations_passees:
            return ProbabiliteKarmique(
                type_calcul="zone_karmique",
                probabilite=0.5,
                confiance=0.3,
                details={"raison": "Aucune donnée d'incarnation"},
                interpretation="Probabilité neutre - données insuffisantes"
            )
        
        # Validation des données
        for inc in incarnations_passees:
            if 'latitude' not in inc or 'longitude' not in inc:
                raise ValueError("Chaque incarnation doit contenir 'latitude' et 'longitude'")
        
        # Calcul des distances
        distances = []
        for inc in incarnations_passees:
            dist = self._distance_haversine(
                lat_actuelle, lon_actuelle,
                inc['latitude'], inc['longitude']
            )
            distances.append(dist)
        
        # Analyse statistique
        distance_moyenne = sum(distances) / len(distances)
        distance_min = min(distances)
        nb_vies_proches = sum(1 for d in distances if d < 500)  # < 500 km
        
        # Calcul de probabilité (plus il y a de vies proches, plus c'est fort)
        prob_proximite = nb_vies_proches / len(distances)
        prob_distance_min = max(0, 1 - (distance_min / 10000))  # Diminue avec distance
        prob_moyenne = max(0, 1 - (distance_moyenne / 15000))
        
        probabilite = (prob_proximite * 0.5 + 
                      prob_distance_min * 0.3 + 
                      prob_moyenne * 0.2)
        
        confiance = min(1.0, len(distances) / 10)  # Plus de vies = plus de confiance
        
        interpretation = self._interpreter_probabilite(probabilite, {
            "très_forte": "Zone de concentration karmique INTENSE - Tu es revenu ici maintes fois",
            "forte": "Lien karmique significatif avec cette région",
            "moyenne": "Connexion modérée - quelques passages dans la zone",
            "faible": "Peu de liens directs - zone relativement nouvelle pour ton âme",
            "très_faible": "Territoire karmiquement inexploré"
        })
        
        return ProbabiliteKarmique(
            type_calcul="zone_karmique",
            probabilite=probabilite,
            confiance=confiance,
            details={
                "distance_min_km": round(distance_min, 2),
                "distance_moyenne_km": round(distance_moyenne, 2),
                "vies_proches_500km": nb_vies_proches,
                "total_vies": len(distances)
            },
            interpretation=interpretation
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # 2️⃣ PROBABILITÉS DE RENCONTRE D'ÂMES SŒURS
    # ═══════════════════════════════════════════════════════════════════
    
    def probabilite_ame_soeur(self,
                              date_naissance: str,
                              latitude: float,
                              longitude: float,
                              rayon_km: int = 100) -> ProbabiliteKarmique:
        """
        Calcule la probabilité de rencontrer une âme sœur karmique
        dans un rayon donné autour de la position actuelle
        """
        # Facteurs astrologiques (simplifiés)
        date = datetime.strptime(date_naissance, "%Y-%m-%d")
        facteur_numerologie = self._calcul_numerologie(date)
        
        # Facteur géographique (zones plus peuplées = plus de rencontres)
        facteur_geo = abs(latitude) / 90  # Plus proche équateur = plus peuplé
        
        # Facteur de rayon (plus grand rayon = plus de probabilité)
        facteur_rayon = min(1.0, rayon_km / 1000)
        
        # Calcul composite
        probabilite = (
            facteur_numerologie * 0.4 +
            facteur_geo * 0.3 +
            facteur_rayon * 0.3
        )
        
        # Ajustement saisonnier (mois de naissance)
        mois = date.month
        if mois in [5, 6, 7]:  # Printemps/Été = plus d'ouverture
            probabilite *= 1.15
        
        probabilite = min(1.0, probabilite)
        
        interpretation = self._interpreter_probabilite(probabilite, {
            "très_forte": "🔥 ALERTE COSMIQUE ! Les astres sont alignés pour une rencontre majeure",
            "forte": "💫 Probabilité élevée - reste ouvert aux synchronicités",
            "moyenne": "⭐ Possibilité modérée - cultive ta présence",
            "faible": "🌙 Patience - le timing cosmique se prépare",
            "très_faible": "🌑 Phase d'introspection - travaille sur toi d'abord"
        })
        
        return ProbabiliteKarmique(
            type_calcul="ame_soeur",
            probabilite=probabilite,
            confiance=0.65,
            details={
                "rayon_recherche_km": rayon_km,
                "facteur_numerologie": round(facteur_numerologie, 3),
                "facteur_geo": round(facteur_geo, 3),
                "mois_favorable": mois in [5, 6, 7]
            },
            interpretation=interpretation
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # 3️⃣ PROBABILITÉS DE PATTERNS KARMIQUES
    # ═══════════════════════════════════════════════════════════════════
    
    def probabilite_repetition_pattern(self,
                                       incarnations: List[Dict]) -> ProbabiliteKarmique:
        """
        Détecte et calcule la probabilité qu'un pattern karmique se répète
        """
        if len(incarnations) < 3:
            return ProbabiliteKarmique(
                type_calcul="repetition_pattern",
                probabilite=0.5,
                confiance=0.2,
                details={"raison": "Trop peu de vies pour analyser"},
                interpretation="Analyse impossible - plus de données nécessaires"
            )
        
        for inc in incarnations:
            if 'latitude' not in inc or 'longitude' not in inc:
                raise ValueError("Données d'incarnation incomplètes")
        
        # Analyse des types d'âmes
        types_ames = [inc.get('type_ame', 'inconnu') for inc in incarnations]
        compteur_types = Counter(types_ames)
        
        # Pattern géographique (continent/région)
        continents = self._detecter_continents(incarnations)
        compteur_continents = Counter(continents)
        
        # Pattern temporel (époques similaires)
        epoques = [inc.get('epoque', '') for inc in incarnations]
        
        # Calcul de répétition
        type_max_freq = max(compteur_types.values()) / len(types_ames)
        continent_max_freq = max(compteur_continents.values()) / len(continents)
        
        probabilite = (type_max_freq * 0.6 + continent_max_freq * 0.4)
        
        # Pattern dominant
        type_dominant = compteur_types.most_common(1)[0]
        continent_dominant = compteur_continents.most_common(1)[0]
        
        interpretation = f"""
Pattern karmique détecté :
• Type d'âme récurrent : {type_dominant[0]} ({type_dominant[1]} fois)
• Zone géographique : {continent_dominant[0]} ({continent_dominant[1]} fois)
➜ {'⚠️ PATTERN FORT - Leçon non résolue à transcender' if probabilite > 0.7 else '✓ Variété karmique saine'}
        """.strip()
        
        confiance = min(1.0, len(incarnations) / 8)
        
        return ProbabiliteKarmique(
            type_calcul="repetition_pattern",
            probabilite=probabilite,
            confiance=confiance,
            details={
                "types_ames": dict(compteur_types),
                "continents": dict(compteur_continents),
                "total_vies": len(incarnations)
            },
            interpretation=interpretation
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # 4️⃣ PROBABILITÉ DE GUÉRISON KARMIQUE
    # ═══════════════════════════════════════════════════════════════════
    
    def probabilite_guerison_complete(self,
                                      patterns_detectes: List[str],
                                      distance_moyenne_vies: float,
                                      age_ame: int) -> ProbabiliteKarmique:
        """
        Estime la probabilité qu'une guérison karmique soit complète
        """
        # Facteur 1: Diversité des patterns (moins de répétition = mieux)
        facteur_diversite = max(0, 1 - (len(patterns_detectes) / 10))
        
        # Facteur 2: Mobilité de l'âme (distance parcourue)
        facteur_mobilite = min(1.0, distance_moyenne_vies / 5000)
        
        # Facteur 3: Maturité de l'âme
        facteur_maturite = min(1.0, age_ame / 15)
        
        probabilite = (
            facteur_diversite * 0.35 +
            facteur_mobilite * 0.30 +
            facteur_maturite * 0.35
        )
        
        interpretation = self._interpreter_probabilite(probabilite, {
            "très_forte": "🌟 GUÉRISON AVANCÉE - Ton âme a bien intégré ses leçons",
            "forte": "💚 Guérison en bonne voie - continue le travail",
            "moyenne": "🔄 Processus en cours - patience et persévérance",
            "faible": "⚠️ Blocages présents - travail thérapeutique recommandé",
            "très_faible": "🔴 Patterns lourds - accompagnement professionnel suggéré"
        })
        
        return ProbabiliteKarmique(
            type_calcul="guerison_complete",
            probabilite=probabilite,
            confiance=0.75,
            details={
                "facteur_diversite": round(facteur_diversite, 3),
                "facteur_mobilite": round(facteur_mobilite, 3),
                "facteur_maturite": round(facteur_maturite, 3),
                "patterns_actifs": len(patterns_detectes)
            },
            interpretation=interpretation
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # 5️⃣ PROBABILITÉS MONTE CARLO (SIMULATIONS)
    # ═══════════════════════════════════════════════════════════════════
    
    def simulation_monte_carlo_incarnation_future(self,
                                                  incarnations_passees: List[Dict],
                                                  nb_simulations: int = 10000) -> ProbabiliteKarmique:
        """
        Simule les probabilités géographiques de la prochaine incarnation
        via méthode Monte Carlo
        """
        if not incarnations_passees:
            raise ValueError("Aucune incarnation passée pour simuler")
        
        coords = []
        for inc in incarnations_passees:
            if 'latitude' not in inc or 'longitude' not in inc:
                raise ValueError("Données d'incarnation incomplètes")
            coords.append((inc['latitude'], inc['longitude']))
        
        # Calcul du centroïde et de la variance
        lat_moy = sum(c[0] for c in coords) / len(coords)
        lon_moy = sum(c[1] for c in coords) / len(coords)
        
        variance_lat = sum((c[0] - lat_moy) ** 2 for c in coords) / len(coords)
        variance_lon = sum((c[1] - lon_moy) ** 2 for c in coords) / len(coords)
        
        # Simulation Monte Carlo
        simulations_lat = []
        simulations_lon = []
        
        for _ in range(nb_simulations):
            # Distribution normale autour du centroïde avec variance observée
            lat_sim = random.gauss(lat_moy, math.sqrt(variance_lat))
            lon_sim = random.gauss(lon_moy, math.sqrt(variance_lon))
            
            # Contraintes géographiques
            lat_sim = max(-90, min(90, lat_sim))
            lon_sim = max(-180, min(180, lon_sim))
            
            simulations_lat.append(lat_sim)
            simulations_lon.append(lon_sim)
        
        # Analyse des résultats
        lat_probable = sum(simulations_lat) / nb_simulations
        lon_probable = sum(simulations_lon) / nb_simulations
        
        # Zones de concentration (découpage par quadrants)
        zones = self._analyser_zones_probabilites(simulations_lat, simulations_lon)
        
        # Probabilité la plus forte
        zone_max = max(zones.items(), key=lambda x: x[1])
        probabilite = zone_max[1]
        
        interpretation = f"""
📍 Coordonnées probables prochaine incarnation :
   {lat_probable:.2f}°, {lon_probable:.2f}°

🗺️  Zones de forte probabilité :
{self._formatter_zones(zones)}

🎲 {nb_simulations:,} simulations effectuées
        """.strip()
        
        return ProbabiliteKarmique(
            type_calcul="monte_carlo_incarnation",
            probabilite=probabilite,
            confiance=0.80,
            details={
                "lat_probable": round(lat_probable, 4),
                "lon_probable": round(lon_probable, 4),
                "nb_simulations": nb_simulations,
                "zones": zones
            },
            interpretation=interpretation
        )
    
    # ═══════════════════════════════════════════════════════════════════
    # 🔧 MÉTHODES UTILITAIRES
    # ═══════════════════════════════════════════════════════════════════
    
    def _distance_haversine(self, lat1, lon1, lat2, lon2):
        """Calcule la distance entre 2 points (formule de Haversine)"""
        R = 6371  # Rayon Terre en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calcul_numerologie(self, date):
        """Calcul numérologique simplifié"""
        jour = date.day
        mois = date.month
        annee = date.year
        
        somme = jour + mois + sum(int(d) for d in str(annee))
        
        # Réduction à un chiffre
        while somme > 9:
            somme = sum(int(d) for d in str(somme))
        
        return somme / 9  # Normalisation 0-1
    
    def _detecter_continents(self, incarnations):
        """Détecte le continent approximatif de chaque incarnation"""
        continents = []
        for inc in incarnations:
            lat = inc['latitude']
            lon = inc['longitude']
            
            # Détection simplifiée par coordonnées
            if -10 < lat < 40 and -20 < lon < 60:
                continents.append("Afrique")
            elif 35 < lat < 75 and -10 < lon < 50:
                continents.append("Europe")
            elif 5 < lat < 75 and 25 < lon < 180:
                continents.append("Asie")
            elif -55 < lat < 15 and 110 < lon < 180:
                continents.append("Océanie")
            elif -60 < lat < 85 and -170 < lon < -30:
                continents.append("Amériques")
            else:
                continents.append("Inconnu")
        
        return continents
    
    def _interpreter_probabilite(self, prob, messages):
        """Interprète une probabilité selon des seuils"""
        if prob >= 0.8:
            return messages["très_forte"]
        elif prob >= 0.6:
            return messages["forte"]
        elif prob >= 0.4:
            return messages["moyenne"]
        elif prob >= 0.2:
            return messages["faible"]
        else:
            return messages["très_faible"]
    
    def _analyser_zones_probabilites(self, lats, lons):
        """Découpe le monde en zones et compte les occurrences"""
        zones = {
            "Europe": 0,
            "Asie": 0,
            "Afrique": 0,
            "Amériques": 0,
            "Océanie": 0,
            "Pôles": 0
        }
        
        for lat, lon in zip(lats, lons):
            if abs(lat) > 66:
                zones["Pôles"] += 1
            elif -10 < lat < 40 and -20 < lon < 60:
                zones["Afrique"] += 1
            elif 35 < lat < 75 and -10 < lon < 50:
                zones["Europe"] += 1
            elif 5 < lat < 75 and 25 < lon < 180:
                zones["Asie"] += 1
            elif -60 < lat < 85 and -170 < lon < -30:
                zones["Amériques"] += 1
            else:
                zones["Océanie"] += 1
        
        # Normalisation
        total = len(lats)
        return {k: v / total for k, v in zones.items()}
    
    def _formatter_zones(self, zones):
        """Formate joliment les zones de probabilités"""
        lignes = []
        for zone, prob in sorted(zones.items(), key=lambda x: x[1], reverse=True):
            if prob > 0.05:  # Affiche seulement si > 5%
                barre = "█" * int(prob * 20)
                lignes.append(f"   {zone:12} : {barre} {prob*100:.1f}%")
        return "\n".join(lignes)