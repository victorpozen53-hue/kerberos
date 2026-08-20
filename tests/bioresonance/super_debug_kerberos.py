# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  SUPER DEBUG KERBEROS – BioResonance / Voyage de l’Âme              ║
# ║  GPLv3 – https://www.gnu.org/licenses/gpl-3.0.html                 ║
# ║  Soutien : https://liberapay.com/EthicalKerberos/                  ║
# ╚══════════════════════════════════════════════════════════════════════╝

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

def log(msg, ok=True):
    prefix = "✅" if ok else "❌"
    print(f"{prefix} {msg}")

def main():
    print("🧠 SUPER DEBUG KERBEROS – Cerveau Neuronal")
    print("=" * 50)

    # Vérifier les dossiers critiques
    for dossier in ["brain", "resources", "soins_vibratoires"]:
        if (ROOT / dossier).exists():
            log(f"Dossier '{dossier}' OK")
        else:
            log(f"Dossier '{dossier}' manquant", ok=False)
            return

    # Vérifier les fichiers essentiels
    fichiers = [
        "brain/cortex.py",
        "brain/lobes/temporal.py",
        "resources/lieux_sacres.csv"
    ]
    for f in fichiers:
        if (ROOT / f).exists():
            log(f"Fichier '{f}' OK")
        else:
            log(f"Fichier '{f}' manquant", ok=False)
            return

    # Tester le chargement des lieux sacrés
    try:
        with open(ROOT / "resources" / "lieux_sacres.csv", "r", encoding="utf-8") as file:
            lines = file.readlines()
            if len(lines) < 2:
                log("Fichier lieux_sacres.csv vide ou incomplet", ok=False)
                return
            if "nom" not in lines[0]:
                log("Entête 'nom' manquante dans lieux_sacres.csv", ok=False)
                return
        log("Lieux sacrés : format OK")
    except Exception as e:
        log(f"Erreur lecture lieux_sacres.csv : {e}", ok=False)
        return

    # Tester l’import du cerveau
    try:
        from brain.cortex import Cortex
        cortex = Cortex()
        log("Cortex neuronal initialisé")
    except Exception as e:
        log(f"Échec initialisation cerveau : {e}", ok=False)
        return

    # Test minimal du voyage
    try:
        donnees = {"date_naissance": "1990-01-01", "latitude": 48.8566, "longitude": 2.3522}
        rapport = cortex.initier_voyage_de_l_ame(donnees)
        if "incarnations" in rapport and len(rapport["incarnations"]) == 7:
            log("Voyage de l’âme : succès (7 incarnations)")
        else:
            log("Voyage de l’âme : résultat incomplet", ok=False)
            return
    except Exception as e:
        log(f"Échec simulation voyage : {e}", ok=False)
        return

    print("\n🎉 TOUT EST OPÉRATIONNEL.")
    print("➡️ Tu peux lancer Kerberos en toute sécurité.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 Erreur critique : {e}")
    input("\nAppuyez sur Entrée pour quitter...")