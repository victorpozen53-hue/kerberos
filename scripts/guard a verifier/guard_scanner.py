#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guard_scanner.py — Détecte les guards, même inactifs, dans guards/
→ Permet de finaliser les guards en dev (ex: guard_perc.py)
→ Aucun lancement automatique — juste de la détection + conseil.
"""

import os
import time
import threading
from pathlib import Path

GUARDS_DIR = Path("D:/KERBEROS.SDS.WIN.7-10/guards")

def scan_guards():
    """Retourne une liste de guards avec statut"""
    guards = []
    if not GUARDS_DIR.exists():
        return guards

    for f in GUARDS_DIR.glob("guard_*.py"):
        try:
            code = f.read_text(encoding="utf-8", errors="ignore")
            meta = "GUARD_METADATA" in code
            has_start = "def start(" in code or "def run(" in code
            has_danger = any(kw in code for kw in [
                "subprocess.run(", "os.system(", "import requests",
                "eval(", "exec(", "socket.socket("  # sauf si whitelisted
            ])
            
            if not meta:
                status = "🟠 Incomplet (manque GUARD_METADATA)"
            elif has_danger and not any(w in code for w in ["# whitelist: network"]):
                status = "🔴 Risqué (appel système non commenté)"
            elif has_start:
                # Vérifie si actif (existe dans sys.modules ?)
                status = "✅ Actif" if is_guard_running(f.stem) else "🟡 Inactif"
            else:
                status = "🟠 Incomplet (manque def start())"
                
            guards.append({"name": f.name, "path": f, "status": status, "code": code})
        except Exception as e:
            guards.append({"name": f.name, "status": f"❌ Erreur lecture : {e}"})
    return guards

def is_guard_running(name: str) -> bool:
    """Vérifie si le guard est chargé (via sys.modules) — sans l’importer"""
    try:
        import sys
        return any(name in mod for mod in sys.modules.keys())
    except:
        return False

def suggest_fix(guard):
    """Retourne une suggestion pédagogique"""
    if "GUARD_METADATA" not in guard["code"]:
        return (
            "# 🔧 À ajouter en haut du fichier :\n"
            "GUARD_METADATA = {\n"
            '    "name": "Mon Guard",\n'
            '    "version": "0.1",\n'
            '    "description": "Description courte"\n'
            "}\n"
        )
    if "def start(" not in guard["code"] and "def run(" not in guard["code"]:
        return "# 🔧 Ajoutez une fonction `def start(): ...` pour l’activer."
    return ""

# ———————— INTEGRATION TASKBAR —————————
def report_to_taskbar():
    guards = scan_guards()
    inactive = [g for g in guards if "Inactif" in g["status"] or "Incomplet" in g["status"]]
    if inactive:
        msg = f"🟡 {len(inactive)} guard(s) à finaliser"
        # → Met à jour le bouton taskbar (via callback)
        if hasattr(report_to_taskbar, "update_cb"):
            report_to_taskbar.update_cb(msg, "orange")
    return guards

# ———————— AUTO-SCAN EN ARRIÈRE-PLAN —————————
def start_background_scan():
    def loop():
        while True:
            report_to_taskbar()
            time.sleep(10)
    threading.Thread(target=loop, daemon=True).start()