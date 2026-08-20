
#!/usr/bin/env python3
# guard_cortex.py
# Cortex Immunitaire — gestion centralisée des gardes
# Ne jamais modifier ce fichier manuellement.

import json
import threading
import importlib.util
from pathlib import Path
from immune_core import is_self

MANIFEST_FILE = Path("guards_manifest.json")
GUARDS_DIR = Path(__file__).parent

_active_guards = {}
_available_guards = set()

def _load_manifest():
    if not MANIFEST_FILE.exists():
        default = {"active_guards": ["guard_genome.py", "guard_thymus.py"]}
        with open(MANIFEST_FILE, "w") as f:
            json.dump(default, f, indent=2)
        return default
    with open(MANIFEST_FILE) as f:
        return json.load(f)

def _save_manifest(config):
    with open(MANIFEST_FILE, "w") as f:
        json.dump(config, f, indent=2)

def _safe_load_guard(guard_name):
    guard_path = GUARDS_DIR / guard_name
    if not guard_path.exists():
        return None, "fichier manquant"
    if not is_self(guard_path):
        return None, "ADN invalide"
    try:
        spec = importlib.util.spec_from_file_location(guard_path.stem, guard_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(module, 'start_guard'):
            return None, "pas de start_guard()"
        return module.start_guard, "ok"
    except Exception as e:
        return None, str(e)

def _scan_available_guards():
    global _available_guards
    _available_guards = set()
    for f in GUARDS_DIR.glob("guard_*.py"):
        if is_self(f):
            _available_guards.add(f.name)

def _start_guard_by_name(guard_name):
    if guard_name in _active_guards:
        return False, "déjà actif"
    start_fn, msg = _safe_load_guard(guard_name)
    if not start_fn:
        return False, msg
    try:
        thread = start_fn()
        if thread:
            _active_guards[guard_name] = thread
        return True, "activé"
    except Exception as e:
        return False, str(e)

def _stop_guard_by_name(guard_name):
    if guard_name in _active_guards:
        del _active_guards[guard_name]
        return True, "désactivé (soft)"
    return False, "non actif"

def reload_guards():
    config = _load_manifest()
    _scan_available_guards()
    to_remove = [g for g in _active_guards if g not in config["active_guards"]]
    for g in to_remove:
        _stop_guard_by_name(g)
    results = []
    for guard_name in config["active_guards"]:
        if guard_name not in _active_guards:
            ok, msg = _start_guard_by_name(guard_name)
            results.append((guard_name, ok, msg))
        else:
            results.append((guard_name, True, "déjà actif"))
    return results

def cmd_cortex_list(args):
    _scan_available_guards()
    print("\n[🧠 Cortex] Gardes disponibles (ADN valide) :")
    for g in sorted(_available_guards):
        status = " ✅ ACTIF" if g in _active_guards else ""
        print(f"  • {g}{status}")
    print("\n[📝] Gardes activés dans guards_manifest.json :")
    config = _load_manifest()
    for g in config.get("active_guards", []):
        print(f"  → {g}")

def cmd_cortex_enable(args):
    if not args: print("[!] Usage: cortex enable <guard_name.py>"); return
    guard = args[0]
    if not guard.startswith("guard_") or not guard.endswith(".py"):
        print("[!] Nom invalide. Doit être guard_xxx.py")
        return
    config = _load_manifest()
    if guard not in config["active_guards"]:
        config["active_guards"].append(guard)
        _save_manifest(config)
        print(f"[+] {guard} ajouté au manifeste.")
    ok, msg = _start_guard_by_name(guard)
    print(f"[{'✅' if ok else '❌'}] {msg}")

def cmd_cortex_disable(args):
    if not args: print("[!] Usage: cortex disable <guard_name.py>"); return
    guard = args[0]
    config = _load_manifest()
    if guard in config["active_guards"]:
        config["active_guards"].remove(guard)
        _save_manifest(config)
        print(f"[-] {guard} retiré du manifeste.")
    ok, msg = _stop_guard_by_name(guard)
    print(f"[{'✅' if ok else 'ℹ️'}] {msg}")

def cmd_cortex_reload(args):
    print("[🔄] Rechargement des gardes...")
    results = reload_guards()
    for name, ok, msg in results:
        print(f"  {'✅' if ok else '❌'} {name}: {msg}")

def start_guard():
    print("[🧠] Activation du Cortex Immunitaire...")
    reload_guards()
    return None

CORTEX_COMMANDS = {
    "list": cmd_cortex_list,
    "enable": cmd_cortex_enable,
    "disable": cmd_cortex_disable,
    "reload": cmd_cortex_reload,
}
