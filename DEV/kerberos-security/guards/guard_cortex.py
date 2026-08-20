#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Guard Cortex — Système Nerveux Central de Kerberos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ⚠️ VERSION CORRIGÉE — Active VRAIMENT les guards
- Import dynamique + appel start_guard() sur chaque guard
- Flag anti-boucle persistant
- Exclut guard_auto_discovery.py et guard_auto_activate.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""

import json
import threading
import importlib.util
import sys
import time
from pathlib import Path
from datetime import datetime

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================

MANIFEST_FILE = Path("guards_manifest.json")
GUARDS_DIR = Path(__file__).parent
LYMPH_DIR = Path(__file__).parent.parent / "lymph"

# ← FLAG PERSISTANT VIA FICHIER (pas reset à l'import)
CORTEX_FLAG_FILE = LYMPH_DIR / ".cortex_loaded.flag"
LYMPH_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# === 🛡️ FLAG ANTI-BOUCLE (PERSISTANT) ======================================
# ============================================================================

def _is_cortex_already_loaded() -> bool:
    """Vérifie si Cortex est déjà chargé (via fichier persistant)"""
    if CORTEX_FLAG_FILE.exists():
        try:
            age = time.time() - CORTEX_FLAG_FILE.stat().st_mtime
            if age < 3600:  # Valide 1 heure
                print("[ℹ️ Cortex] Déjà actif — skip")
                return True
        except:
            pass
    return False

def _set_cortex_loaded():
    """Marque Cortex comme chargé (fichier persistant)"""
    try:
        CORTEX_FLAG_FILE.write_text(datetime.now().isoformat(), encoding='utf-8')
    except:
        pass

_active_guards = {}
_cortex_lock = threading.RLock()

# ============================================================================
# === GESTION DU MANIFEST ====================================================
# ============================================================================

def _load_manifest() -> dict:
    """Charge le manifest des guards"""
    if not MANIFEST_FILE.exists():
        default = {
            "version": "4.2",
            "active_guards": [
                "guard_genome.py",
                "guard_thymus.py",
                "guard_cortex.py",
                "guard_cybermap.py",
                "guard_antikeylogger.py",
                "guard_browser_shield.py",
                "guard_bubble_shield.py",
                "guard_frog_toxic.py",
                "guard_ftp_organic.py",
                "guard_integrity_check.py",
                "guard_lymph_node.py",
                "guard_lymphatic.py",
                "guard_netshield.py",
                "guard_tardigrade.py",
                "guard_vigil.py",
                "guard_yara.py"
            ],
            "auto_discovery_enabled": False
        }
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================================
# === ACTIVATION VRAIE DES GUARDS ============================================
# ============================================================================

def _activate_guard(guard_name: str) -> tuple:
    """Active VRAIMENT un guard (import + start_guard)"""
    guard_path = GUARDS_DIR / guard_name
    
    if not guard_path.exists():
        return (guard_name, False, "fichier introuvable")
    
    # ← EXCLURE LES GUARDS PROBLÉMATIQUES
    if guard_name in ["guard_auto_discovery.py", "guard_auto_activate.py", "guard_cortex.py"]:
        return (guard_name, True, "exclu (anti-boucle)")
    
    try:
        # Import dynamique
        spec = importlib.util.spec_from_file_location(guard_path.stem, guard_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[guard_path.stem] = module
        spec.loader.exec_module(module)
        
        # Vérifie et appelle start_guard()
        if hasattr(module, 'start_guard'):
            result = module.start_guard()
            _active_guards[guard_name] = module
            return (guard_name, True, "activé ✓")
        else:
            return (guard_name, False, "pas de start_guard()")
    
    except Exception as e:
        return (guard_name, False, f"erreur: {str(e)[:50]}")

def reload_guards() -> list:
    """Recharge TOUS les guards du manifest — ACTIVATION VRAIE"""
    config = _load_manifest()
    results = []
    
    print("\n" + "="*70)
    print("🧠 [Cortex] Activation des guards...")
    print("="*70)
    
    with _cortex_lock:
        for guard_name in config.get("active_guards", []):
            # ← CORRECTION CRITIQUE : Active VRAIMENT le guard
            result = _activate_guard(guard_name)
            results.append(result)
            
            # Affiche le résultat
            status = "✅" if result[1] else "❌"
            print(f"  {status} {guard_name}: {result[2]}")
    
    print("="*70)
    active_count = len([r for r in results if r[1]])
    print(f"\n✅ [Cortex] {active_count}/{len(results)} guard(s) actif(s)\n")
    
    return results

# ============================================================================
# === COMMANDES CORTEX =======================================================
# ============================================================================

def cmd_cortex_list(args):
    """Liste les guards actifs"""
    print("\n[🧠 Cortex] Guards actifs :")
    for name, module in _active_guards.items():
        print(f"  • {name}")
    print(f"  Total: {len(_active_guards)}\n")

def cmd_cortex_reload(args):
    """Recharge les guards"""
    print("[🔄] Rechargement...")
    reload_guards()

def cmd_cortex_status(args):
    """Statut du Cortex"""
    print(f"\n[🧠 Cortex] Statut:")
    print(f"  Guards actifs: {len(_active_guards)}")
    print(f"  Flag: {'chargé' if _is_cortex_already_loaded() else 'non chargé'}\n")

CORTEX_COMMANDS = {
    "list": cmd_cortex_list,
    "reload": cmd_cortex_reload,
    "status": cmd_cortex_status
}

# ============================================================================
# === POINT D'ENTRÉE =========================================================
# ============================================================================

def start_guard():
    """Point d'entrée pour Kerberos — Active TOUS les guards"""
    # ← CHECK CRITIQUE : Déjà chargé ?
    if _is_cortex_already_loaded():
        return None
    
    _set_cortex_loaded()  # ← MARQUE COMME CHARGÉ
    
    print("\n🧠 [Cortex] Activation du système nerveux central...")
    results = reload_guards()
    
    return None

def stop_guard():
    """Arrêt propre du Cortex"""
    global _active_guards
    print("🛑 [Cortex] Arrêt...")
    _active_guards.clear()

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║  🧠 KERBEROS CORTEX — Système Nerveux Central            ║
╚════════════════════════════════════════════════════════════╝
    """)
    start_guard()