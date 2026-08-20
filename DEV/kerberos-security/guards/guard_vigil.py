#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👁️ guard_vigil.py — Veille systémique comportementale : détection des DLL injectées
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Scan des processus critiques (explorer, svchost, lsass, winlogon)
- Détection des DLL suspectes chargées en mémoire
- Filtres intelligents (exclut System32, Program Files, WindowsApps)
- Heuristiques sur les noms de DLL (court, alphanumérique, patterns suspects)
- Logs détaillés dans logs/vigil.log
- Intégration Kerberos (get_stats, start_guard)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guard Vigil
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou
#  le modifier selon les termes de la GNU General Public License telle que
#  publiée par la Free Software Foundation, soit la version 3 de la licence,
#  ou (à votre choix) toute version ultérieure.
#
#  Ce programme est distribué dans l'espoir qu'il sera utile, mais SANS
#  AUCUNE GARANTIE ; sans même la garantie implicite de QUALITÉ MARCHANDE
#  ou d'ADÉQUATION À UN USAGE PARTICULIER.
#
#  White hat • Anonymous • Résistant numérique
#  https://liberapay.com/EthicalKerberos/
#  https://github.com/victorpozen
# ============================================================================
#  LICENCE : GPLv3 (GNU General Public License v3.0)
#  AUTEUR  : Victor Pozen
#  VERSION : 4.2 Ultimate
#  DATE    : 2025
# ============================================================================

import json
from pathlib import Path
import psutil
from datetime import datetime, timezone

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================

def _find_kerberos_root():
    """Trouve la racine du projet Kerberos"""
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "kerberos.py").exists() or (parent / "LICENCE.txt").exists():
            return parent
    return Path.cwd()

KERBEROS_ROOT = _find_kerberos_root()
LOG_FILE = KERBEROS_ROOT / "logs" / "vigil.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ============================================================================
# === LOGGING ================================================================
# ============================================================================

def _log(msg: str, level="INFO"):
    """Log un message dans le fichier vigil.log"""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] [{level}] {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass
    if __name__ == "__main__":
        print(line)

# ============================================================================
# === DÉTECTION DLL SUSPECTES ================================================
# ============================================================================

def _is_suspicious_dll(dll_path: str) -> bool:
    """
    Détermine si une DLL est suspecte selon des heuristiques.
    Retourne True si la DLL semble suspecte, False sinon.
    """
    try:
        path = Path(dll_path).resolve()
    except Exception:
        return False

    path_str = str(path).lower()

    # ← Exclure les chemins système légitimes
    system_roots = (
        "windows\\system32",
        "windows\\syswow64",
        "windows\\winsxs",
        "windows\\servicing"
    )
    if any(root in path_str for root in system_roots):
        return False

    # ← Exclure Program Files
    if "program files" in path_str:
        return False

    # ← Exclure Windows Store apps
    if "\\windowsapps\\" in path_str or "\\systemapps\\" in path_str:
        return False

    # ← Inclure les chemins à risque (AppData, Temp, Desktop, etc.)
    risky_dirs = (
        "\\appdata\\", "\\temp\\", "\\desktop\\",
        "\\downloads\\", "\\documents\\"
    )
    if any(risk_dir in path_str for risk_dir in risky_dirs):
        return True

    # ← Heuristiques sur le nom de fichier
    name = path.name.lower()
    if name.endswith(".dll"):
        stem = name[:-4]
        # Nom court + alphanumérique + pas de préfixe connu = suspect
        if len(stem) <= 8 and stem.isalnum() and not stem.startswith((
            "api-", "ext-", "msvcp", "vcruntime", "ucrt"
        )):
            return True
        # Patterns suspects dans le nom
        if any(c in stem for c in (
            "_", "-", "tmp", "cache", "update", "install",
            "setup", "patch", "svchost", "lsass"
        )):
            return True

    return False

# ============================================================================
# === SCAN PROCESSUS CRITIQUES ===============================================
# ============================================================================

def scan_critical_processes():
    """
    Scan les processus critiques pour détecter des DLL suspectes.
    Retourne un dict avec les résultats du scan.
    """
    threats = []
    scanned = 0

    TARGET_PROCESSES = {"explorer.exe", "svchost.exe", "lsass.exe", "winlogon.exe"}

    for proc in psutil.process_iter(['pid', 'name']):
        name = proc.info['name'].lower()
        if name in TARGET_PROCESSES:
            scanned += 1
            try:
                suspicious_dlls = []
                for mmap in proc.memory_maps(grouped=False):
                    if mmap.path and mmap.path.lower().endswith('.dll'):
                        if _is_suspicious_dll(mmap.path):
                            suspicious_dlls.append(Path(mmap.path).name)

                if suspicious_dlls:
                    threats.append({
                        "pid": proc.info['pid'],
                        "process": name,
                        "suspicious_dlls": suspicious_dlls
                    })
                    _log(
                        f"🚨 {name} (PID {proc.info['pid']}) : "
                        f"DLL suspectes → {', '.join(suspicious_dlls)}",
                        "ALERT"
                    )
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

    return {
        "scanned_processes": scanned,
        "threats": threats,
        "total_threats": len(threats)  # ← Clé importante pour Kerberos
    }

# ============================================================================
# === POINTS D'ENTRÉE ========================================================
# ============================================================================

def run(dry_run=False):
    """
    Exécution complète du guard Vigil.
    Retourne un dict avec le statut et les résultats.
    """
    _log("👁️ GUARD VIGIL v2.1 — détection comportementale activée", "INFO")
    report = scan_critical_processes()

    # ← Intégration Kerberos (optionnelle, silencieuse si échec)
    if report["total_threats"] > 0:
        try:
            from kerberos import _show_nag, _set_tray_state
            _set_tray_state("alert")
            _show_nag(
                "👁️ Vigil Alert",
                f"{report['total_threats']} processus(s) avec DLL suspectes."
            )
        except:
            pass

    # ← CORRECTION CRITIQUE : Ajouter "total_threats" dans le return
    return {
        "guard": "vigil",
        "status": "alert" if report["total_threats"] > 0 else "clean",
        "scanned_processes": report["scanned_processes"],
        "total_threats": report["total_threats"],  # ← AJOUTÉ (fix KeyError)
        "threats": report["threats"]
    }

def start_guard():
    """
    Point d'entrée pour Kerberos — Veille DLL suspectes.
    Appelé par le Cortex au démarrage.
    """
    print("👁️ [Vigil] Veille comportementale active")
    result = run()
    # ← CORRECTION: Utiliser .get() pour sécurité supplémentaire
    if result.get('total_threats', 0) > 0:
        print(f"   └─ 🚨 {result['total_threats']} processus avec DLL suspectes")
    else:
        print("   └─ ✅ Aucun processus suspect détecté")
    return None  # Scan unique, pas de thread persistant

def get_stats() -> dict:
    """
    Retourne les statistiques pour le registry Kerberos.
    Compatible avec l'onglet Guards.
    """
    return {
        "guard_name": "Vigil",
        "status": "active",
        "last_scan": datetime.now(timezone.utc).isoformat(),
        "description": "Veille comportementale — Détection DLL injectées"
    }

# ============================================================================
# === EXÉCUTION STANDALONE ===================================================
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("👁️ GUARD VIGIL v2.1 — Détection comportementale finale")
    print("White hat • Local only • GPLv3 • (-;")
    print("="*60 + "\n")
    
    res = run()
    
    print(f"📊 Processus scannés : {res['scanned_processes']}")
    print(f"🚨 Menaces détectées : {res['total_threats']}")
    
    if res["threats"]:
        print("\n⚠️  DÉTAILS DES MENACES :")
        for t in res["threats"]:
            print(f"  - {t['process']} (PID {t['pid']}) → {', '.join(t['suspicious_dlls'])}")
    
    print(f"\n🩺 Logs : logs/vigil.log")
    input("\n✅ Appuyez sur Entrée pour quitter.")