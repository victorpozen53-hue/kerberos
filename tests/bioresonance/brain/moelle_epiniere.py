# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Moelle Épinière – Interface Cerveau / Monde Extérieur              ║
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
#
# Soutien : https://liberapay.com/EthicalKerberos/
# White hat only. Pas de trace. Pas de nuage. Juste du code libre.

"""
🦴 Moelle Épinière – Le lien entre le cerveau et le monde
Gère les flux d'entrée (utilisateur, fichiers) et de sortie (rapports, sons, erreurs).
Implémente aussi les réflexes karmiques automatiques.
"""

import os
from pathlib import Path
from datetime import datetime

class MoelleEpiniere:
    def __init__(self, cortex):
        self.cortex = cortex
        self.retour_arriere_actif = True  # Pour annulation / debug

    def recevoir_donnees_utilisateur(self, donnees_brutes):
        """
        Point d’entrée principal : reçoit les données de la GUI ou CLI.
        Valide, nettoie, et transmet au cortex.
        """
        try:
            # Validation minimale
            if not donnees_brutes.get("date_naissance"):
                raise ValueError("Date de naissance manquante")

            # Conversion de la date si chaîne
            if isinstance(donnees_brutes["date_naissance"], str):
                donnees_brutes["date_naissance"] = datetime.strptime(
                    donnees_brutes["date_naissance"], "%Y-%m-%d"
                )

            # Transmission au cortex
            return self.cortex.initier_voyage_de_l_ame(donnees_brutes)

        except Exception as e:
            return self._generer_erreur(f"Échec du voyage de l’âme : {e}")

    def declencher_reflexe_karmique(self, evenement):
        """
        Réflexes automatiques (sans passer par le cortex conscient).
        Ex: détection de Göbekli Tepe → active fréquence 8.5 Hz.
        """
        if evenement.get("type") == "lieu_sacre_proche":
            lieu = evenement.get("nom", "").lower()
            if "gobekli" in lieu or "pyramide" in lieu:
                self.emettre_signal_guerison({
                    "frequence": 8.5 if "gobekli" in lieu else 7.83,
                    "urgence": "haute"
                })

    def emettre_signal_guerison(self, signal):
        """Envoie une commande aux modules de guérison (audio, rapport, etc.)"""
        print(f"⚡ Réflexe karmique activé : {signal}")
        # Ici, tu pourras appeler modules/audio/audiogenerator.py plus tard

    def _generer_erreur(self, message):
        """Génère un rapport d’erreur standardisé"""
        erreur = {
            "erreur": True,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "html": None,
            "txt": None
        }
        return erreur

    def sauvegarder_rapport_dans_fichier(self, rapport, dossier="soins_vibratoires"):
        """Utilitaire de sauvegarde (optionnel, redondant avec occipital)"""
        if rapport.get("html"):
            Path(dossier).mkdir(exist_ok=True)
            # Déjà fait par occipital.py → ici, juste un fallback