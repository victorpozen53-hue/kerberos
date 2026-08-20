#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guard_dev_helper.py — Détecte les guards incomplets dans guards/
→ Intégré à Kerberos existant via update_taskbar_status()
→ Pas de dépendance — stdlib only
→ Licence AGPL-3.0+
"""

import os
import sys
import importlib.util
import threading
from pathlib import Path

# 🔹 Chemin fixe — comme dans ton setup
GUARDS_DIR = Path("D:/KERBEROS.SDS.WIN.7-10/guards")

def scan_and_report_dev_guards():
    """Scan les guards incomplets et met à jour la taskbar"""
    dev_guards = []
    
    if not GUARDS_DIR.exists():
        return dev_guards

    for f in GUARDS_DIR.glob("guard_*.py"):
        try:
            code = f.read_text(encoding="utf-8", errors="ignore")
            has_meta = "GUARD_METADATA" in code
            has_entry = any(sig in code for sig in [
                "def start(", "def run(", "if __name__ == \"__main__\":"
            ])

            if not (has_meta and has_entry):
                reasons = []
                if not has_meta: reasons.append("pas de GUARD_METADATA")
                if not has_entry: reasons.append("pas de point d'entrée (start/run)")
                dev_guards.append(f"{f.stem} ({', '.join(reasons)})")
        except Exception as e:
            dev_guards.append(f"{f.stem} (erreur: {type(e).__name__})")

    # 🔹 Mise à jour taskbar — compatible avec ton système existant
    if dev_guards:
        msg = f"🟡 {len(dev_guards)} guard(s) en dev : " + ", ".join(dev_guards[:2])
        if len(dev_guards) > 2:
            msg += f" (+{len(dev_guards)-2})"
        # → Appel compatible avec ton update_taskbar_status(status_text, color)
        try:
            # On suppose que update_taskbar_status est dans le scope global (comme dans ton core)
            update_taskbar_status(msg, "orange")
        except NameError:
            # Fallback : log seulement
            print(f"[dev_helper] {msg}")
    else:
        # Optionnel : efface le statut dev (laisse le vert des guards actifs)
        pass
    
    return dev_guards

def start_dev_scanner():
    """Lance le scan en arrière-plan (toutes les 15s)"""
    def loop():
        while True:
            scan_and_report_dev_guards()
            threading.Event().wait(15)
    threading.Thread(target=loop, daemon=True, name="DevGuardScanner").start()

# 🔹 Activation automatique — à appeler après le chargement des 7 guards
if __name__ == "__main__":
    start_dev_scanner()
    print("[dev_helper] 🟠 Scanner de guards en dev activé")