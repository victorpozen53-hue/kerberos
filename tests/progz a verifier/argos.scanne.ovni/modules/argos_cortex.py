#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 argos_cortex.py — Système nerveux central d'ARGOS (adapté de guard_cortex.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — version ARGOS
- Manifest argos_guards_manifest.json (liste des organes actifs)
- Activation VRAIE : import + start_guard() sur chaque organe
- Flag anti-boucle persistant (lymph_argos/.argos_cortex_loaded.flag)
- Commandes : list / reload / status
"""
import json
import threading
import importlib.util
import sys
import time
from pathlib import Path
from datetime import datetime

GUARDS_DIR = Path(__file__).parent
ARGOS_ROOT = GUARDS_DIR.parent
LYMPH_DIR = ARGOS_ROOT / "lymph_argos"
MANIFEST_FILE = GUARDS_DIR / "argos_guards_manifest.json"
FLAG_FILE = LYMPH_DIR / ".argos_cortex_loaded.flag"
LYMPH_DIR.mkdir(parents=True, exist_ok=True)

_active_guards = {}
_lock = threading.RLock()


def _is_already_loaded():
    if FLAG_FILE.exists():
        try:
            if time.time() - FLAG_FILE.stat().st_mtime < 3600:
                print("[ℹ️ Argos Cortex] Déjà actif — skip")
                return True
        except Exception:
            pass
    return False


def _set_loaded():
    try:
        FLAG_FILE.write_text(datetime.now().isoformat(), encoding="utf-8")
    except Exception:
        pass


def _load_manifest():
    if not MANIFEST_FILE.exists():
        default = {"version": "3.0",
                   "active_guards": ["argos_genome.py", "argos_thymus.py"],
                   "auto_discovery_enabled": False}
        MANIFEST_FILE.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))


def _activate_guard(name):
    path = GUARDS_DIR / name
    if not path.exists():
        return (name, False, "fichier introuvable")
    if name in ("argos_cortex.py",):
        return (name, True, "exclu (anti-boucle)")
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = mod
        spec.loader.exec_module(mod)
        if hasattr(mod, "start_guard"):
            mod.start_guard()
            _active_guards[name] = mod
            return (name, True, "activé ✓")
        return (name, False, "pas de start_guard()")
    except Exception as e:
        return (name, False, f"erreur: {str(e)[:50]}")


def reload_guards():
    config = _load_manifest()
    results = []
    print("\n🧠 [Argos Cortex] Activation des organes...")
    with _lock:
        for name in config.get("active_guards", []):
            r = _activate_guard(name)
            results.append(r)
            print(f"  {'✅' if r[1] else '❌'} {name}: {r[2]}")
    n = len([r for r in results if r[1]])
    print(f"✅ [Argos Cortex] {n}/{len(results)} organe(s) actif(s)\n")
    return results


def cmd_list(args):
    print("[🧠 Argos Cortex] Organes actifs :")
    for name in _active_guards:
        print(f"  • {name}")


def cmd_reload(args):
    reload_guards()


def cmd_status(args):
    print(f"[🧠 Argos Cortex] actifs={len(_active_guards)} "
          f"flag={'chargé' if _is_already_loaded() else 'non chargé'}")


CORTEX_COMMANDS = {"list": cmd_list, "reload": cmd_reload, "status": cmd_status}


def start_guard():
    if _is_already_loaded():
        return None
    _set_loaded()
    print("🧠 [Argos Cortex] Système nerveux central...")
    reload_guards()
    return None


def stop_guard():
    print("🛑 [Argos Cortex] Arrêt...")
    _active_guards.clear()


if __name__ == "__main__":
    print("╔═══ 🧠 ARGOS CORTEX — système nerveux central ═══╗")
    start_guard()