# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Lobe Temporal – Mémoire Karmique & Lieux Sacrés                   ║
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
🕰️ Lobe Temporal – Mémoire karmique, lieux sacrés, schémas vibratoires
Charge TOUTES les données contextuelles depuis resources/lieux_sacres.csv
"""

import csv
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

class LobeTemporal:
    def __init__(self, cortex):
        self.cortex = cortex
        self.lieux_sacres = self._charger_lieux_sacres()
        self.schemas_karmiques = self._charger_schemas()

    def _charger_lieux_sacres(self):
        """Charge TOUS les champs de lieux_sacres.csv"""
        chemin = Path(__file__).parent.parent.parent / "resources" / "lieux_sacres.csv"
        if not chemin.exists():
            print(f"❌ Fichier manquant : {chemin}")
            return []
        lieux = []
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Nettoyer les clés/valeurs
                    row = {k.strip(): v.strip() for k, v in row.items()}
                    lieu = {
                        "nom": row.get("nom_païen", "Lieu sacré"),
                        "latitude": float(row["latitude"]),
                        "longitude": float(row["longitude"]),
                        "type": row.get("type", "sacré"),
                        "frequence_hz": float(row.get("frequence_hz", 7.83)),
                        "epoque": row.get("epoque", "inconnue"),
                        "statut": row.get("statut", "actif")
                    }
                    # Charger annee_approx (supporte valeurs vides ou négatives)
                    annee_str = row.get("annee_approx", "").strip()
                    if annee_str and annee_str.lstrip('-').isdigit():
                        lieu["annee_approx"] = int(annee_str)
                    else:
                        lieu["annee_approx"] = None
                    lieux.append(lieu)
        except KeyError as e:
            print(f"⚠️ Colonne manquante dans lieux_sacres.csv : {e}")
        except ValueError as e:
            print(f"⚠️ Valeur invalide dans lieux_sacres.csv : {e}")
        except Exception as e:
            print(f"⚠️ Erreur chargement {chemin} : {e}")
        return lieux

    def _charger_schemas(self):
        """Charge les schémas karmiques (optionnel)"""
        chemin = Path(__file__).parent.parent.parent / "resources" / "schemas_karmiques.csv"
        if not chemin.exists():
            return {}
        schemas = {}
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row = {k.strip(): v.strip() for k, v in row.items()}
                    nom = row.get("schema")
                    if nom:
                        schemas[nom] = {
                            "description": row.get("description", ""),
                            "frequence_base": float(row.get("frequence_base", 432.0))
                        }
        except Exception as e:
            print(f"⚠️ Erreur chargement {chemin} : {e}")
        return schemas

    def charger_contexte(self, donnees_naissance):
        """
        Enrichit les données avec :
        - Tous les lieux sacrés (statiques + dynamiques si internet OK)
        - Le schéma karmique (si fourni)
        """
        contexte = {
            "date_naissance": donnees_naissance["date_naissance"],
            "latitude": donnees_naissance["latitude"],
            "longitude": donnees_naissance["longitude"],
            "lieux_sacres": self.lieux_sacres.copy(),  # liste complète
            "schéma_karmique": donnees_naissance.get("schema", None)
        }

        # Ajout des lieux dynamiques via OSM (si activé)
        if hasattr(self.cortex, 'internet_ok') and self.cortex.internet_ok:
            from ...geo.scanner_lieux_sacres import ScannerLieuxSacres
            scanner = ScannerLieuxSacres(rayon_km=100)
            lieux_dynamiques = scanner.scanner(
                donnees_naissance["latitude"],
                donnees_naissance["longitude"]
            )
            contexte["lieux_sacres"].extend(lieux_dynamiques)

        return contexte

    def _distance_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # km
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))