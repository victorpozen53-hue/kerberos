# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Cortex Central – BioResonance / Voyage de l'Âme                   ║
# ║  Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# Copyright (C) 2026  Victor.Pozen
# ... [licence GPLv3 inchangée] ...

"""
🧠 Cortex central du système BioResonance
Orchestre les 4 piliers :
- Corps physique (LobeParietal)
- Corps éthérique (Etherique)
- Âme (Insula + LobeFrontal)
- Esprit (Esprit)
"""

# ============================================================
# PATCH COMPATIBILITÉ DEBUGGER : détection robuste de la racine
# ============================================================
import sys
import os
from pathlib import Path

def trouver_racine_projet():
    """Détecte la racine F:/bioresonance/ même depuis un fichier temporaire"""
    chemins_candidats = [
        Path("F:/bioresonance"),
        Path("F:\\bioresonance"),
        Path.home() / "bioresonance",
        Path.cwd().parent.parent,  # Structure normale: .../bioresonance/brain/cortex.py
    ]
    
    # Recherche ascendante depuis __file__ si disponible
    try:
        current = Path(__file__).resolve().parent
        for _ in range(5):
            if (current / "brain" / "cortex.py").exists() or (current / "kerberos_ame_voyage.v.1.py").exists():
                return current
            current = current.parent
    except:
        pass
    
    # Fallback : chemins connus pour Victor (Belgique/Canaries/France)
    for chemin in chemins_candidats:
        if chemin.exists() and (chemin / "brain").exists():
            return chemin
    
    # Dernier recours : utiliser le chemin courant
    return Path.cwd()

# Appliquer le patch AVANT tout import
project_root = trouver_racine_projet()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"✅ DEBUG: Project root fixé à → {project_root}", file=sys.stderr)

# ============================================================
# IMPORTS (maintenant sécurisés)
# ============================================================
try:
    from brain.lobes import frontal, temporal, occipital, parietal
    from brain.insula import Insula
    from brain.esprit import Esprit
    from brain.etherique import Etherique
except ImportError as e:
    print(f"❌ ERREUR FATALE: Impossible d'importer les modules du cerveau", file=sys.stderr)
    print(f"   Racine du projet: {project_root}", file=sys.stderr)
    print(f"   Contenu du dossier brain: {list(project_root.glob('brain/*')) if (project_root / 'brain').exists() else 'NON TROUVÉ'}", file=sys.stderr)
    raise

# ... [reste du code Cortex inchangé] ...
class Cortex:
    # ... [code existant] ...

if __name__ == "__main__":
    print("🐺 DEBUG: Cortex initialisation test (mode sécurisé)")
    print("=" * 60)
    # ... [bloc de test existant] ...