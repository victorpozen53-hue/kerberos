#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# GPLv3 — © Victor Pozen

import sys
import logging
from pathlib import Path

# === CONFIGURATION ===
KERBEROS_ROOT = Path("I:/IA.KERBEROS").resolve()  # À adapter si nécessaire
GUARDS_DIR = KERBEROS_ROOT / "guards"
ENGINE_PATH = KERBEROS_ROOT / "kerberos_engine.py"  # ou ton module principal

# Logs
LOG_DIR = KERBEROS_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "guard_integrity_check.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def discover_guard_files(guards_dir: Path):
    """Liste tous les fichiers guard valides (.py, non __init__)"""
    if not guards_dir.exists():
        logger.error(f"Dossier guards introuvable : {guards_dir}")
        return set()
    files = {
        f.stem for f in guards_dir.glob("*.py")
        if f.name != "__init__.py" and f.is_file()
    }
    logger.info(f"{len(files)} guards trouvés sur disque : {sorted(files)}")
    return files

def extract_registered_guards(engine_path: Path):
    """Extrait les noms de guards explicitement référencés dans le moteur."""
    if not engine_path.exists():
        logger.error(f"Moteur Kerberos introuvable : {engine_path}")
        return set()

    try:
        content = engine_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Impossible de lire {engine_path}: {e}")
        return set()

    # Heuristique simple : cherche les imports ou références explicites
    # Exemple : from guards.guard_xyz import GuardXYZ
    # Ou : "guard_xyz" dans une liste de chargement dynamique
    registered = set()
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("from guards.") and " import " in line:
            mod_name = line.split()[1].split('.')[1]  # after 'from guards.'
            registered.add(mod_name)
        elif '"guard_' in line or "'guard_" in line:
            # Support pour listes comme ["guard_firewall", "guard_backdoor"]
            parts = line.replace('"', "'").split("'")
            for p in parts:
                if p.startswith("guard_"):
                    registered.add(p)

    logger.info(f"{len(registered)} guards enregistrés dans le moteur : {sorted(registered)}")
    return registered

def main():
    logger.info("🔍 Démarrage du vérificateur d’intégrité des guards Kerberos")
    
    disk_guards = discover_guard_files(GUARDS_DIR)
    engine_guards = extract_registered_guards(ENGINE_PATH)

    orphaned = disk_guards - engine_guards
    missing = engine_guards - disk_guards

    print("\n" + "="*60)
    if orphaned:
        print("⚠️  Guards ORPHELINS (présents mais non intégrés) :")
        for g in sorted(orphaned):
            print(f"   • {g}")
        logger.warning(f"Guards orphelins détectés : {orphaned}")
    else:
        print("✅ Tous les guards sur disque sont intégrés.")

    if missing:
        print("\n❌ Guards RÉFÉRENCÉS mais ABSENTS du disque :")
        for g in sorted(missing):
            print(f"   • {g}")
        logger.error(f"Guards manquants : {missing}")
    else:
        print("\n✅ Tous les guards référencés existent sur disque.")

    print("="*60)
    logger.info("Vérification terminée.")

if __name__ == "__main__":
    main()