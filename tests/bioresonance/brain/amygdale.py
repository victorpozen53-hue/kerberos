# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  BIORESONANCE - AMYGDALE KARMIQUE                                  ║
# ║  Module inspiré de l'amygdale humaine : détecte la peur,          ║
# ║  le stress et les mémoires émotionnelles liées aux incarnations.   ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# Copyright (C) 2026  [Ton nom]
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

from typing import List, Dict, Optional
from dataclasses import dataclass
import math

@dataclass
class ChargeEmotionnelle:
    """Représente une charge émotionnelle karmique non résolue"""
    emotion: str              # "peur", "colère", "honte", "abandon", etc.
    intensite: float          # 0.0 (apaisé) → 1.0 (traumatique)
    source: Dict              # incarnation d'origine
    resolue: bool             # True si intégrée/guérie
    impact_actuel: float      # influence sur la vie présente (0–1)

class AmygdaleKarmique:
    """
    Simule les fonctions de l'amygdale humaine dans le contexte karmique :
    - Détection des menaces émotionnelles (passées/présentes)
    - Activation de réponses de survie
    - Mémorisation des expériences traumatisantes
    - Modulation de la perception du danger
    """

    def __init__(self):
        self.seuil_peur = 0.65  # seuil d'activation de la réponse de peur
        self.memoire_emotionnelle = []

    def scanner_incarnations(self, incarnations: List[Dict]) -> List[ChargeEmotionnelle]:
        """
        Analyse les incarnations passées pour détecter les charges émotionnelles.
        Inspiré de la fonction biologique : l'amygdale encode les souvenirs chargés en émotion.
        """
        charges = []
        for inc in incarnations:
            # Détection basée sur des indicateurs karmiques
            cause_mort = inc.get("cause_mort", "").lower()
            contexte = inc.get("contexte", "").lower()
            epoque = inc.get("epoque", "")
            type_ame = inc.get("type_ame", "")

            intensite = 0.0
            emotion = "neutre"

            # 🔥 Détection de traumatismes (comme l'amygdale détecte les menaces)
            if any(mot in cause_mort for mot in ["violence", "guerre", "meurtre", "bataille"]):
                intensite = max(intensite, 0.9)
                emotion = "peur"
            elif "famine" in cause_mort or "maladie" in cause_mort:
                intensite = max(intensite, 0.7)
                emotion = "détresse"
            elif "trahison" in contexte or "isolement" in contexte:
                intensite = max(intensite, 0.8)
                emotion = "abandon"
            elif type_ame == "victime" or type_ame == "martyr":
                intensite = max(intensite, 0.75)
                emotion = "honte"

            # Réduction si guérison partielle (ex. : fin paisible, sagesse)
            if "sage" in type_ame or "guérisseur" in type_ame:
                intensite *= 0.6

            if intensite > 0.3:
                charge = ChargeEmotionnelle(
                    emotion=emotion,
                    intensite=intensite,
                    source=inc,
                    resolue=(intensite < 0.4),
                    impact_actuel=self._calculer_impact_actuel(intensite, inc)
                )
                charges.append(charge)

        self.memoire_emotionnelle = charges
        return charges

    def evaluer_niveau_peur_actuel(self, position_actuelle: Dict) -> float:
        """
        Évalue si la situation actuelle active des schémas de peur karmique.
        Comme l'amygdale compare les stimuli présents aux menaces passées.
        """
        if not self.memoire_emotionnelle:
            return 0.1  # calme par défaut

        # Exemple : si tu es dans une zone de guerre aujourd'hui → activation
        contexte_actuel = position_actuelle.get("contexte", "").lower()
        facteur_contexte = 0.0
        if "conflit" in contexte_actuel or "stress" in contexte_actuel:
            facteur_contexte = 0.5

        # Charge émotionnelle moyenne non résolue
        charges_non_resolues = [c for c in self.memoire_emotionnelle if not c.resolue]
        if not charges_non_resolues:
            return 0.2 + facteur_contexte

        intensite_moyenne = sum(c.intensite for c in charges_non_resolues) / len(charges_non_resolues)
        return min(1.0, intensite_moyenne * 0.7 + facteur_contexte)

    def generer_reponse_survie(self, niveau_peur: float) -> Dict[str, any]:
        """
        Simule la réponse biologique : combat, fuite, figement, soumission.
        Transposée en conseils karmiques.
        """
        if niveau_peur >= self.seuil_peur:
            if niveau_peur > 0.85:
                reponse = "figement_karmique"  # blocage, procrastination
                conseil = "⚠️ L'âme est en état de sidération. Recommandé : méditation racinaire, ancrage géobiologique."
            elif niveau_peur > 0.7:
                reponse = "fuite_spirituelle"   # évitement, déni
                conseil = "🌀 Tendance à fuir les leçons. Recommandé : travail avec un lieu sacré stabilisant (ex. : montagnes)."
            else:
                reponse = "hypervigilance"      # contrôle excessif
                conseil = "👁️ L'âme scrute chaque signe. Recommandé : binaurales alpha, Schumann 7.83 Hz."
        else:
            reponse = "calme_integration"
            conseil = "🌿 L'amygdale karmique est apaisée. Moment propice à l'intégration des leçons."

        return {
            "mode": reponse,
            "niveau_peur": niveau_peur,
            "conseil_guerison": conseil,
            "activation": niveau_peur >= self.seuil_peur
        }

    def _calculer_impact_actuel(self, intensite: float, incarnation: Dict) -> float:
        """Plus la vie est récente, plus l'impact est fort (comme la mémoire émotionnelle)"""
        annee_actuelle = 2026
        annee_vie = incarnation.get("annee", annee_actuelle - 500)
        decalage = max(1, annee_actuelle - annee_vie)
        decay = math.exp(-decalage / 300)  # demi-vie karmique ~300 ans
        return min(1.0, intensite * decay)

    def rapport_html(self) -> str:
        """Génère un extrait de rapport pour LobeOccipital"""
        if not self.memoire_emotionnelle:
            return "<p>🧠 Amygdale karmique : calme. Aucune charge émotionnelle majeure détectée.</p>"

        non_resolues = [c for c in self.memoire_emotionnelle if not c.resolue]
        html = "<div class='amygdale-section'>\n<h3>👁️ Amygdale Karmique</h3>\n<ul>\n"
        for c in sorted(non_resolues, key=lambda x: x.intensite, reverse=True)[:3]:
            html += f"<li><strong>{c.emotion.title()}</strong> ({c.intensite:.0%}) : "
            html += f"Vie à {c.source.get('lieu', '?')} ({c.source.get('epoque', '?')})</li>\n"
        html += "</ul>\n</div>"
        return html