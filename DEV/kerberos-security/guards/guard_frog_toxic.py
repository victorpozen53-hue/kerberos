# guard_frog_toxic.py — Kerberos v1.0 — GPLv3
# 🐸 Défense active locale : détection de fichiers suspects sur le Bureau
# White hat only. Pas de trace. Pas de nuage. (-;
#
# Copyright (C) 2025–2026 Victor Pozen
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

import os
import time
import hashlib
import threading
from pathlib import Path

# === CONFIGURATION ===
DESKTOP_PATH = Path.home() / "Desktop"
LOG_PATH = Path("logs/kerberos_bulle_alert.log")
QUARANTINE_DIR = Path("soins_vibratoires/quarantine_frog")
SUSPICIOUS_EXTS = {".exe", ".dll", ".bat", ".scr", ".js", ".vbs", ".ps1"}

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

def _log(msg: str):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[FROG] {time.ctime()} | {msg}\n")

def _is_suspicious_file(file_path: Path) -> bool:
    """Détection comportementale (pas de whitelist)."""
    name = file_path.name.lower()
    # Fichiers temporaires, aléatoires, ou scripts exécutables
    if any(kw in name for kw in ("tmp", "cache", "update", "install", "setup")):
        return True
    if len(file_path.stem) <= 6 and file_path.stem.isalnum():
        return True
    return False

def _quarantine_file(file_path: Path) -> bool:
    """Déplace le fichier suspect en quarantaine (pas de suppression)."""
    try:
        target = QUARANTINE_DIR / f"{file_path.name}.quarantine"
        # Ajouter timestamp si conflit
        counter = 1
        while target.exists():
            target = QUARANTINE_DIR / f"{file_path.stem}_{counter}{file_path.suffix}.quarantine"
            counter += 1
        file_path.rename(target)
        return True
    except Exception as e:
        _log(f"Échec quarantaine {file_path}: {e}")
        return False

def _watch_desktop():
    known_files = set()
    while True:
        try:
            current_files = {
                f for f in DESKTOP_PATH.iterdir()
                if f.is_file() and f.suffix.lower() in SUSPICIOUS_EXTS
            }
            new_files = current_files - known_files
            for f in new_files:
                if _is_suspicious_file(f):
                    if _quarantine_file(f):
                        _log(f"SUSPECT mis en quarantaine : {f}")
                    else:
                        _log(f"Échec quarantaine : {f}")
            known_files = current_files
            time.sleep(5)
        except Exception as e:
            _log(f"Erreur veille : {e}")
            time.sleep(10)

# === POINT D’ENTRÉE KERBEROS ===
def start_guard():
    """Lancé automatiquement par le Cortex."""
    _log("Garde FROG TOXIC activé (mode=auto-quarantaine)")
    thread = threading.Thread(target=_watch_desktop, daemon=True, name="kerberos_guard_frog_toxic")
    thread.start()
    return thread

def run():
    """Appelé via le bouton 'Exécuter' dans l’UI."""
    _log("Activation manuelle de Frog Toxic (rapport uniquement)")
    # Scan unique du Bureau
    threats = []
    for f in DESKTOP_PATH.iterdir():
        if f.is_file() and f.suffix.lower() in SUSPICIOUS_EXTS and _is_suspicious_file(f):
            threats.append(str(f))
    return {
        "guard": "frog_toxic",
        "status": "scan_complete",
        "suspicious_files": threats,
        "quarantine_dir": str(QUARANTINE_DIR)
    }

if __name__ == "__main__":
    print("[🐸] Mode standalone : scan unique du Bureau")
    result = run()
    print(f"Menaces trouvées : {len(result['suspicious_files'])}")
    for f in result["suspicious_files"]:
        print(f"  - {f}")