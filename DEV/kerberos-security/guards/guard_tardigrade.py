#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐻 Guard Tardigrade — Mode cryptobiose : survie extrême
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guard Tardigrade
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE : GPLv3
#  AUTEUR  : Victor Pozen
#  VERSION : 4.2 Ultimate
#  DATE    : 2025
#  🔗 https://github.com/victorpozen
#  💰 https://liberapay.com/EthicalKerberos/
# ============================================================================

import os
import sys
import json
import zipfile
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timezone

# ============================================================================
# === DÉTECTION RACINE KERBEROS =============================================
# ============================================================================

def _find_kerberos_root():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "kerberos.py").exists() or (parent / "LICENCE.txt").exists():
            return parent
    return Path.cwd()

KERBEROS_ROOT = _find_kerberos_root()
LYMPH_DIR = KERBEROS_ROOT / "lymph"
TARDI_STATE = LYMPH_DIR / "last_safe_state.zip"
TARDI_FLAG = LYMPH_DIR / ".cryptobiosis.flag"
LOG_FILE = KERBEROS_ROOT / "logs" / "tardigrade.log"

for d in [LYMPH_DIR, LOG_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

def _log(msg: str, level="INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] [{level}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if __name__ == "__main__":
        print(line)

# ============================================================================
# === ÉTAT VITAL À SAUVEGARDER ==============================================
# ============================================================================

VITAL_STATE = [
    LYMPH_DIR / "genome.json",
    LYMPH_DIR / "plasma" / "hosts",
    LYMPH_DIR / "plasma" / "win.ini",
    KERBEROS_ROOT / "guards" / "last_reg_export.reg",
]

# ============================================================================
# === FONCTIONS CRYPTOBIOSIS ================================================
# ============================================================================

def _disconnect_network():
    """🔌 Coupe les interfaces réseau actives (mode silencieux)."""
    try:
        result = subprocess.run(
            ["netsh", "interface", "show", "interface"],
            capture_output=True, text=True, shell=True, timeout=8
        )
        interfaces = []
        for line in result.stdout.splitlines():
            if "Enabled" in line and "Connected" in line:
                parts = line.split()
                if len(parts) >= 4:
                    name = " ".join(parts[3:])
                    interfaces.append(name)
        
        disabled = []
        for iface in interfaces:
            try:
                subprocess.run(
                    ["netsh", "interface", "set", "interface", f'"{iface}"', "admin=disable"],
                    shell=True, timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                disabled.append(iface)
                _log(f"🔌 Interface désactivée : {iface}", "ACTION")
            except Exception as e:
                _log(f"⚠️ Échec désactivation {iface}: {e}", "WARN")
        return disabled
    except Exception as e:
        _log(f"❌ Erreur déconnexion réseau : {e}", "ERROR")
        return []

def _create_safe_snapshot():
    """💾 Sauvegarde l'état vital dans last_safe_state.zip."""
    try:
        with zipfile.ZipFile(TARDI_STATE, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in VITAL_STATE:
                if path.exists():
                    zf.write(path, arcname=path.name)
                    _log(f"💾 Snapshot ajouté : {path.name}", "SAVE")
        return True
    except Exception as e:
        _log(f"❌ Échec création snapshot : {e}", "ERROR")
        return False

def _suspend_non_essential_guards():
    """⏸️ Signale aux guards de se mettre en veille (pas de kill)."""
    return 0

def enter_cryptobiosis(reason="menace critique"):
    """🐻 Active la cryptobiose — seulement si appelé par un autre guard."""
    _log("=" * 50, "ALERT")
    _log(f"🐻 CRYPTOBIOSIS DÉCLENCHE — Raison : {reason}", "ALERT")
    
    if not _create_safe_snapshot():
        _log("❌ Snapshot échoué — cryptobiose annulée", "ABORT")
        return {"status": "failed", "reason": "snapshot_failed"}
    
    disconnected = _disconnect_network()
    
    TARDI_FLAG.write_text(json.dumps({
        "entered_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "disconnected_interfaces": disconnected
    }, indent=2), encoding="utf-8")
    
    _log("✅ Cryptobiose activée — Kerberos en veille profonde.", "ALERT")
    return {
        "status": "cryptobiosis_active",
        "entered_at": datetime.now(timezone.utc).isoformat(),
        "disconnected_interfaces": disconnected,
        "snapshot_saved": TARDI_STATE.exists()
    }

def is_in_cryptobiosis():
    """🔍 Vérifie si on vient de se réveiller."""
    return TARDI_FLAG.exists()

def revive():
    """🌱 Réveil après redémarrage — restauration depuis le snapshot."""
    if not TARDI_FLAG.exists() or not TARDI_STATE.exists():
        return {"status": "nothing_to_revive"}
    try:
        meta = json.loads(TARDI_FLAG.read_text(encoding="utf-8"))
        _log(f"🌱 Réveil depuis cryptobiose ({meta['entered_at']})", "REVIVE")
        
        with zipfile.ZipFile(TARDI_STATE, "r") as zf:
            for name in zf.namelist():
                target = LYMPH_DIR / "plasma" / name if name in ("hosts", "win.ini") else LYMPH_DIR / name
                target.parent.mkdir(parents=True, exist_ok=True)
                zf.extract(name, target.parent)
                extracted = target.parent / name
                if extracted != target:
                    extracted.replace(target)
                _log(f"✅ Restauré : {name}", "REVIVE")
        
        TARDI_FLAG.unlink(missing_ok=True)
        _log("✅ Réveil complet — état sain restauré.", "REVIVE")
        return {"status": "revived", "original_entry": meta}
    except Exception as e:
        _log(f"❌ Échec réveil : {e}", "ERROR")
        return {"status": "revive_failed", "error": str(e)}

# ============================================================================
# === INTERFACE GUARD — compatible avec KerberosApp =========================
# ============================================================================

def start_guard():
    """
    ⚠️ Ne fait RIEN ici.
    Le tardigrade ne s'active PAS automatiquement.
    Il doit être invoqué par un autre guard (ex: thymus en cas de compromission).
    """
    _log("🐻 Tardigrade en veille — prêt à répondre à un appel de détresse.", "IDLE")
    return None

def run(dry_run=False, reason=None):
    """
    🧪 Mode test uniquement.
    En production, utiliser `enter_cryptobiosis()` via un autre guard.
    """
    if dry_run:
        snapshot_size = TARDI_STATE.stat().st_size if TARDI_STATE.exists() else 0
        return {
            "guard": "tardigrade",
            "status": "dry_run",
            "snapshot_exists": TARDI_STATE.exists(),
            "snapshot_size_bytes": snapshot_size
        }
    else:
        return {
            "guard": "tardigrade",
            "status": "manual_activation_blocked",
            "message": "La cryptobiose ne peut être déclenchée que par un autre guard."
        }

# ============================================================================
# === MODE STANDALONE (pour tests) ==========================================
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🐻 GUARD TARDIGRADE — Survie extrême pour Kerberos")
    print("White hat • Local only • GPL v3 • (-;")
    print("=" * 60 + "\n")
    
    if "--revive" in sys.argv:
        result = revive()
        print(f"  → Statut : {result['status']}")
    else:
        print("🧪 Mode test : utilisez --dry ou --revive")
        result = run(dry_run=True)
        print(f"  → Snapshot existe : {result['snapshot_exists']}")
    
    print(f"\n🩺 Logs : logs/tardigrade.log")
    print("Kerberos ne ment jamais — mais parfois, il grogne… puis il revient. 🐺✨\n")