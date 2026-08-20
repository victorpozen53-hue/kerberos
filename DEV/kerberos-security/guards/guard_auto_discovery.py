#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Guard Auto-Discovery — Détection automatique des guards
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Scanne le dossier guards/ automatiquement
- Détecte les nouveaux guards avec validation ADN
- Met à jour guards_manifest.json automatiquement
- S'exécute en arrière-plan toutes les 30 secondes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
import json
import time
import threading
from pathlib import Path

# === Configuration ===
GUARDS_DIR = Path(__file__).parent
MANIFEST_FILE = Path("guards_manifest.json")
SCAN_INTERVAL = 30  # secondes

# === Validation ADN (sécurité) ===
try:
    from immune_core import is_self
except ImportError:
    def is_self(filepath):
        try:
            return Path(filepath).resolve().parent == GUARDS_DIR.parent and Path(filepath).suffix == ".py"
        except:
            return False

def _load_manifest():
    """Charge le manifest ou crée un par défaut"""
    if not MANIFEST_FILE.exists():
        default = {
            "active_guards": [],
            "auto_discovered": [],
            "version": "4.2",
            "signature_required": False,
            "auto_discovery_enabled": True,
            "auto_discovery_interval": 30
        }
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_manifest(config):
    """Sauvegarde le manifest"""
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def _is_valid_guard(filepath):
    """Vérifie si un fichier est un guard valide"""
    if not is_self(filepath):
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            return "def start_guard(" in content or "def run(" in content
    except:
        return False

def scan_and_update():
    """Scanne les guards et met à jour le manifest automatiquement"""
    if not GUARDS_DIR.exists():
        print("⚠️  [auto-discovery] Dossier guards/ introuvable")
        return {"discovered": 0, "new": 0}
    
    valid_guards = []
    for f in GUARDS_DIR.glob("guard_*.py"):
        if f.name == "guard_auto_discovery.py":
            continue
        if _is_valid_guard(f):
            valid_guards.append(f.name)
    
    config = _load_manifest()
    active_guards = config.get("active_guards", [])
    active_guards = [g if g.endswith('.py') else f"{g}.py" for g in active_guards]
    current_active = set(active_guards)
    already_discovered = set(config.get("auto_discovered", []))
    
    new_guards = [g for g in valid_guards if g not in already_discovered]
    
    if new_guards:
        print(f"\n🔍 [auto-discovery] {len(new_guards)} nouveau(x) guard(s) détecté(s) :")
        for g in new_guards:
            print(f"   ✨ {g}")
            if g not in current_active:
                active_guards.append(g)
            if "auto_discovered" not in config:
                config["auto_discovered"] = []
            config["auto_discovered"].append(g)
        
        config["active_guards"] = active_guards
        config["last_scan"] = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
        config["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
        _save_manifest(config)
        print(f"   ✅ Manifest mis à jour — {len(new_guards)} guard(s) activé(s)\n")
    else:
        config["last_scan"] = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
        _save_manifest(config)
    
    return {
        "discovered": len(valid_guards),
        "new": len(new_guards),
        "active": len(active_guards)
    }

def _auto_discovery_loop():
    """Boucle de surveillance en arrière-plan"""
    print(f"🔍 [auto-discovery] Démarrage — scan toutes les {SCAN_INTERVAL}s")
    while True:
        try:
            scan_and_update()
        except Exception as e:
            print(f"❌ [auto-discovery] Erreur : {e}")
        time.sleep(SCAN_INTERVAL)

def start_guard():
    """Point d'entrée pour Kerberos — démarre le thread de surveillance"""
    thread = threading.Thread(target=_auto_discovery_loop, daemon=True, name="AutoDiscovery")
    thread.start()
    print("✅ [auto-discovery] Guard actif en arrière-plan")
    return thread

def run():
    """Exécution manuelle — scan immédiat"""
    print("🔍 [auto-discovery] Scan manuel des guards...")
    result = scan_and_update()
    report = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 AUTO-DISCOVERY — Rapport de scan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Guards détectés   : {result['discovered']}
Nouveaux guards   : {result['new']}
Guards actifs     : {result['active']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return {
        "guard": "auto_discovery",
        "status": "ok",
        "discovered": result['discovered'],
        "new": result['new'],
        "report": report
    }

if __name__ == "__main__":
    result = run()
    print(result['report'])