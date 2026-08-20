#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 guard_integrity_check.py — Vérificateur d'intégrité des guards
"""

import sys
from pathlib import Path

def _find_kerberos_root():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "kerberos.py").exists() or (parent / "LICENCE.txt").exists():
            return parent
    return Path.cwd()

KERBEROS_ROOT = _find_kerberos_root()
GUARDS_DIR = KERBEROS_ROOT / "guards"
MANIFEST_FILE = KERBEROS_ROOT / "guards_manifest.json"

def _discover_guards_on_disk():
    if not GUARDS_DIR.exists():
        return set()
    return {
        f.stem for f in GUARDS_DIR.glob("guard_*.py")
        if f.is_file() and f.name != "__init__.py"
    }

def _load_manifest_guards():
    if not MANIFEST_FILE.exists():
        return set()
    try:
        import json
        data = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        return {name.replace(".py", "") for name in data.get("active_guards", [])}
    except Exception:
        return set()

def run(dry_run=False):
    disk_guards = _discover_guards_on_disk()
    manifest_guards = _load_manifest_guards()

    orphaned = disk_guards - manifest_guards
    missing = manifest_guards - disk_guards

    status = "success"
    if missing:
        status = "error"
    elif orphaned:
        status = "partial"

    report = {
        "guard": "integrity_check",
        "status": status,
        "guards_on_disk": sorted(disk_guards),
        "guards_in_manifest": sorted(manifest_guards),
        "orphaned_guards": sorted(orphaned),
        "missing_guards": sorted(missing)
    }

    if __name__ == "__main__":
        print("\n" + "="*60)
        print("🔍 VÉRIFICATEUR D'INTÉGRITÉ DES GUARDS")
        print("="*60)
        print(f"• Guards sur disque : {len(report['guards_on_disk'])}")
        print(f"• Dans le manifeste : {len(report['guards_in_manifest'])}")
        if report["orphaned_guards"]:
            print("\n⚠️  Guards orphelins (non activés) :")
            for g in report["orphaned_guards"]:
                print(f"   • {g}")
        if report["missing_guards"]:
            print("\n❌ Guards manquants (dans manifeste mais absents) :")
            for g in report["missing_guards"]:
                print(f"   • {g}")
        print("\n✅ Vérification terminée.")
    
    return report

# ============================================================================
# === ⚠️ AJOUT CRITIQUE : start_guard() POUR CORTEX ==========================
# ============================================================================

def start_guard():
    """Point d'entrée pour Kerberos — Vérification intégrité"""
    print("🔍 [Integrity Check] Vérification intégrité guards...")
    result = run()
    print(f"   └─ Sur disque: {len(result['guards_on_disk'])} | Dans manifest: {len(result['guards_in_manifest'])}")
    if result['orphaned_guards']:
        print(f"   └─ ⚠️ {len(result['orphaned_guards'])} guard(s) orphelin(s)")
    if result['missing_guards']:
        print(f"   └─ ❌ {len(result['missing_guards'])} guard(s) manquant(s)")
    return None  # Scan unique, pas de thread

if __name__ == "__main__":
    run()