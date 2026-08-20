#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 Guard Cortex — Système Nerveux Central de Kerberos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Manifest épuré : 5 guards vitaux uniquement
- Import dynamique + appel start_guard()
- Flag anti-boucle persistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2026 Victor Pozen — GPLv3
"""
import json
import threading
import importlib.util
import sys
import time
from pathlib import Path
from datetime import datetime

MANIFEST_FILE = Path("guards_manifest.json")
GUARDS_DIR = Path(__file__).parent
LYMPH_DIR = Path(__file__).parent.parent / "lymph"
CORTEX_FLAG_FILE = LYMPH_DIR / ".cortex_loaded.flag"
LYMPH_DIR.mkdir(parents=True, exist_ok=True)

def _is_cortex_already_loaded() -> bool:
    if CORTEX_FLAG_FILE.exists():
        try:
            age = time.time() - CORTEX_FLAG_FILE.stat().st_mtime
            if age < 3600:
                print("[️ Cortex] Déjà actif — skip")
                return True
        except: pass
    return False

def _set_cortex_loaded():
    try:
        CORTEX_FLAG_FILE.write_text(datetime.now().isoformat(), encoding='utf-8')
    except: pass

_active_guards = {}
_cortex_lock = threading.RLock()

def _load_manifest() -> dict:
    if not MANIFEST_FILE.exists():
        default = {
            "version": "5.2",
            "active_guards": [
                "guard_genome.py",
                "guard_thymus.py",
                "guard_cortex.py",
                "guard_yara.py",
                "guard_pip_sentinel.py"
            ],
            "auto_discovery_enabled": False
        }
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _activate_guard(guard_name: str) -> tuple:
    guard_path = GUARDS_DIR / guard_name
    if not guard_path.exists():
        return (guard_name, False, "fichier introuvable")
    if guard_name in ["guard_auto_discovery.py", "guard_auto_activate.py", "guard_cortex.py"]:
        return (guard_name, True, "exclu (anti-boucle)")
    try:
        spec = importlib.util.spec_from_file_location(guard_path.stem, guard_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[guard_path.stem] = module
        spec.loader.exec_module(module)
        if hasattr(module, 'start_guard'):
            result = module.start_guard()
            _active_guards[guard_name] = module
            return (guard_name, True, "activé ✓")
        else:
            return (guard_name, False, "pas de start_guard()")
    except Exception as e:
        return (guard_name, False, f"erreur: {str(e)[:50]}")

def reload_guards() -> list:
    config = _load_manifest()
    results = []
    print("\n" + "="*70)
    print("🧠 [Cortex] Activation des guards...")
    print("="*70)
    with _cortex_lock:
        for guard_name in config.get("active_guards", []):
            result = _activate_guard(guard_name)
            results.append(result)
            status = "✅" if result[1] else "❌"
            print(f"  {status} {guard_name}: {result[2]}")
    print("="*70)
    active_count = len([r for r in results if r[1]])
    print(f"\n✅ [Cortex] {active_count}/{len(results)} guard(s) actif(s)\n")
    return results

def start_guard():
    if _is_cortex_already_loaded():
        return None
    _set_cortex_loaded()
    print("\n🧠 [Cortex] Activation du système nerveux central...")
    results = reload_guards()
    return None

def stop_guard():
    global _active_guards
    print("🛑 [Cortex] Arrêt...")
    _active_guards.clear()

if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🧠 KERBEROS CORTEX — Système Nerveux Central            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    start_guard()