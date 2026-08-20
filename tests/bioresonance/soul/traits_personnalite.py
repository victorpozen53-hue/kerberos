# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  BIORESONANCE - TRAITS DE PERSONNALITÉ KARMIQUES                   ║
# ║  Modélise la personnalité comme une empreinte vibratoire issue     ║
# ║  des expériences karmiques, des types d'âme et des lieux sacrés.   ║
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

from typing import List, Dict, Tuple
from dataclasses import dataclass
import math

@dataclass
class TraitPersonnalite:
    nom: str
    intensite: float  # 0.0 → 1.0
    origine: str      # "karma", "type_ame", "lieu_sacre", "pattern"
    description: str

class AnalyseurTraitsPersonnalite:
    """
    Génère un profil de personnalité basé sur :
    - Le type d'âme (guerrier, sage, artisan, etc.)
    - Les expériences karmiques (vies passées)
    - Les lieux sacrés fréquentés
    - Les patterns répétitifs
    """

    def __init__(self):
        # Axes fondamentaux de la personnalité (inspirés de la psychologie + métaphysique)
        self.axes = {
            "introversion_extraversion": ("Introversion", "Extraversion"),
            "intuition_sensibilite": ("Intuition", "Sensibilité"),
            "logique_emotion": ("Logique", "Émotion"),
            "stabilite_adaptation": ("Stabilité", "Adaptation"),
            "autonomie_harmonie": ("Autonomie", "Harmonie sociale")
        }

    def analyser(self,
                 type_ame: str,
                 incarnations: List[Dict],
                 lieux_sacres_proches: List[str] = None,
                 patterns: List[str] = None) -> List[TraitPersonnalite]:
        """
        Retourne un profil de personnalité karmique.
        """
        traits = []

        # 1️⃣ Influence du type d'âme (noyau stable)
        traits += self._traits_par_type_ame(type_ame)

        # 2️⃣ Influence des vies passées
        traits += self._traits_par_incarnations(incarnations)

        # 3️⃣ Influence des lieux sacrés
        if lieux_sacres_proches:
            traits += self._traits_par_lieux_sacres(lieux_sacres_proches)

        # 4️⃣ Influence des patterns répétitifs
        if patterns:
            traits += self._traits_par_patterns(patterns)

        # Normalisation et fusion des traits similaires
        return self._normaliser_traits(traits)

    def _traits_par_type_ame(self, type_ame: str) -> List[TraitPersonnalite]:
        base = []
        mapping = {
            "guerrier": [
                ("Détermination", 0.9, "Courage face à l'adversité"),
                ("Impulsivité", 0.6, "Action avant réflexion"),
                ("Loyauté", 0.85, "Engagement envers ses alliés")
            ],
            "sage": [
                ("Réflexion", 0.95, "Analyse profonde avant décision"),
                ("Détachement", 0.7, "Distance émotionnelle pour clarté"),
                ("Curiosité", 0.8, "Soif de connaissance universelle")
            ],
            "artisan": [
                ("Créativité", 0.9, "Expression par la matière"),
                ("Patience", 0.75, "Travail minutieux et répétitif"),
                ("Pragmatisme", 0.8, "Solutions concrètes aux problèmes")
            ],
            "marchand": [
                ("Adaptabilité", 0.85, "Capacité à naviguer les changements"),
                ("Opportunisme", 0.7, "Repérage des chances rares"),
                ("Charisme", 0.8, "Influence sociale naturelle")
            ],
            "guérisseur": [
                ("Empathie", 0.95, "Connexion aux émotions d'autrui"),
                ("Altruisme", 0.9, "Don de soi sans attente"),
                ("Intuition", 0.85, "Perception des déséquilibres subtils")
            ],
            "victime": [
                ("Hypersensibilité", 0.8, "Réaction intense aux stimuli"),
                ("Méfiance", 0.7, "Peur de la trahison"),
                ("Résilience", 0.6, "Capacité à survivre malgré tout")
            ]
        }

        for nom, intensite, desc in mapping.get(type_ame.lower(), []):
            base.append(TraitPersonnalite(
                nom=nom,
                intensite=intensite,
                origine="type_ame",
                description=desc
            ))
        return base

    def _traits_par_incarnations(self, incarnations: List[Dict]) -> List[TraitPersonnalite]:
        if not incarnations:
            return []

        traits = []
        total = len(incarnations)

        # Comptage des contextes
        guerres = sum(1 for inc in incarnations if "guerre" in inc.get("contexte", "").lower())
        isolements = sum(1 for inc in incarnations if "isolement" in inc.get("contexte", "").lower())
        leadership = sum(1 for inc in incarnations if inc.get("role", "") in ["roi", "chef", "guide"])
        creativite = sum(1 for inc in incarnations if inc.get("metier", "") in ["artiste", "poète", "sculpteur"])

        if guerres / total > 0.4:
            traits.append(TraitPersonnalite(
                nom="Vigilance accrue",
                intensite=min(1.0, 0.5 + guerres/total),
                origine="karma",
                description="Tendance à anticiper les conflits, même en paix."
            ))
        if isolements / total > 0.3:
            traits.append(TraitPersonnalite(
                nom="Autonomie extrême",
                intensite=0.7 + isolements/total,
                origine="karma",
                description="Préférence pour la solitude, difficulté à déléguer."
            ))
        if leadership / total > 0.3:
            traits.append(TraitPersonnalite(
                nom="Autorité naturelle",
                intensite=0.8,
                origine="karma",
                description="Capacité innée à inspirer et diriger."
            ))
        if creativite / total > 0.25:
            traits.append(TraitPersonnalite(
                nom="Imagination active",
                intensite=0.75,
                origine="karma",
                description="Pensée symbolique et associative très développée."
            ))

        return traits

    def _traits_par_lieux_sacres(self, lieux: List[str]) -> List[TraitPersonnalite]:
        traits = []
        if any("pyramide" in l.lower() or "égypte" in l.lower() for l in lieux):
            traits.append(TraitPersonnalite(
                nom="Mémoire akashique",
                intensite=0.7,
                origine="lieu_sacre",
                description="Accès intuitif à des savoirs anciens."
            ))
        if any("temple" in l.lower() and ("asie" in l.lower() or "japon" in l.lower()) for l in lieux):
            traits.append(TraitPersonnalite(
                nom="Discipline intérieure",
                intensite=0.8,
                origine="lieu_sacre",
                description="Capacité à méditer et canaliser l'énergie."
            ))
        if "montagne" in " ".join(lieux).lower():
            traits.append(TraitPersonnalite(
                nom="Persévérance",
                intensite=0.85,
                origine="lieu_sacre",
                description="Résistance aux épreuves, vision à long terme."
            ))
        if "océan" in " ".join(lieux).lower() or "mer" in " ".join(lieux).lower():
            traits.append(TraitPersonnalite(
                nom="Fluidité émotionnelle",
                intensite=0.75,
                origine="lieu_sacre",
                description="Adaptation aux cycles, intuition profonde."
            ))
        return traits

    def _traits_par_patterns(self, patterns: List[str]) -> List[TraitPersonnalite]:
        traits = []
        if "abandon" in patterns:
            traits.append(TraitPersonnalite(
                nom="Peur de l'engagement",
                intensite=0.7,
                origine="pattern",
                description="Hésitation à s'attacher profondément."
            ))
        if "trahison" in patterns:
            traits.append(TraitPersonnalite(
                nom="Méfiance initiale",
                intensite=0.75,
                origine="pattern",
                description="Nécessité de preuves avant confiance."
            ))
        if "sacrifice" in patterns:
            traits.append(TraitPersonnalite(
                nom="Tendance au don excessif",
                intensite=0.8,
                origine="pattern",
                description="Oubli de soi au profit des autres."
            ))
        return traits

    def _normaliser_traits(self, traits: List[TraitPersonnalite]) -> List[TraitPersonnalite]:
        """Fusionne les traits similaires et limite à 8 traits principaux."""
        from collections import defaultdict
        grouped = defaultdict(list)
        for t in traits:
            key = t.nom.lower()
            grouped[key].append(t)

        final = []
        for key, group in grouped.items():
            avg_intensite = min(1.0, sum(t.intensite for t in group) / len(group))
            # Prend la description la plus complète
            desc = group[0].description
            origines = list(set(t.origine for t in group))
            final.append(TraitPersonnalite(
                nom=group[0].nom,
                intensite=avg_intensite,
                origine="+".join(origines),
                description=desc
            ))

        # Trier par intensité et garder les 8 premiers
        return sorted(final, key=lambda x: x.intensite, reverse=True)[:8]

    def generer_profil_textuel(self, traits: List[TraitPersonnalite]) -> str:
        """Retourne une interprétation poétique du profil."""
        if not traits:
            return "🌀 Profil karmique en gestation – les traits se révèleront avec le temps."

        texte = "🌟 **Profil de Personnalité Karmique**\n\n"
        for t in traits:
            emoji = self._emoji_par_trait(t.nom)
            intensite_str = self._intensite_en_mot(t.intensite)
            texte += f"{emoji} **{t.nom}** ({intensite_str})\n"
            texte += f"   → {t.description}\n\n"

        return texte.strip()

    def _emoji_par_trait(self, nom: str) -> str:
        emojis = {
            "détermination": "⚔️",
            "réflexion": "🧠",
            "créativité": "🎨",
            "empathie": "💖",
            "vigilance": "👁️",
            "autonomie": "🏔️",
            "autorité": "👑",
            "imagination": "🌌",
            "mémoire": "📜",
            "discipline": "🧘",
            "persévérance": "⛰️",
            "fluidité": "🌊",
            "peur": "⚠️",
            "méfiance": "🛡️",
            "don": "🕊️"
        }
        nom_min = nom.lower()
        for mot, em in emojis.items():
            if mot in nom_min:
                return em
        return "💫"

    def _intensite_en_mot(self, intensite: float) -> str:
        if intensite >= 0.85:
            return "TRÈS FORT"
        elif intensite >= 0.7:
            return "FORT"
        elif intensite >= 0.5:
            return "MODÉRÉ"
        elif intensite >= 0.3:
            return "PRÉSENT"
        else:
            return "LATENT"