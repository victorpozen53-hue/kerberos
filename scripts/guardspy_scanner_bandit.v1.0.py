# -*- coding: utf-8 -*-
# guardspy_scanner_bandit.py
# Scanner comportemental – Version définitive (carte blanche)
# GPLv3 – https://liberapay.com/EthicalKerberos/

import os
import sys
import time
import shutil
import threading

# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUARANTINE_DIR = os.path.join(BASE_DIR, "quarantine", "bandit")
IGNORED_FILE = os.path.join(BASE_DIR, "ignored_files.txt")
os.makedirs(QUARANTINE_DIR, exist_ok=True)

# === LISTE BLANCHE DES RACCOURCIS SYSTÈME ===
SYSTEM_SHORTCUTS = [
    "ce pc", "this pc", "ordinateur", "computer",
    "corbeille", "recycle bin", "papierkorb",
    "network", "réseau", "onedrive", "skydrive",
    "documents", "images", "musique", "vidéos"
]

# === MÉMOIRE DES ÉCHECS (évite les boucles) ===
FAILED_FILES = set()

# === UTILITAIRES ===
def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(os.path.join(BASE_DIR, "bandit_debug.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def load_ignored_files():
    if not os.path.exists(IGNORED_FILE):
        return set()
    with open(IGNORED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def is_system_shortcut(filepath):
    """Exclut les raccourcis système connus."""
    if not filepath.lower().endswith(".lnk"):
        return False
    name = os.path.basename(filepath).lower()
    return any(kw in name for kw in SYSTEM_SHORTCUTS)

def is_ignored(filepath):
    """Vérifie si le fichier doit être ignoré."""
    return (
        filepath in FAILED_FILES or
        filepath in load_ignored_files() or
        is_system_shortcut(filepath)
    )

def safe_read_bytes(filepath, max_bytes=1024):
    """Lit les premiers octets en binaire – sans crash."""
    try:
        with open(filepath, "rb") as f:
            return f.read(max_bytes)
    except:
        return b""

def is_suspicious_file(filepath):
    """Détection comportementale – pas de magie."""
    basename = os.path.basename(filepath).lower()
    
    # Règle 1 : noms suspects (aléatoires, chiffres + majuscules)
    if basename.endswith(('.exe', '.bat', '.scr', '.dll', '.ps1')):
        clean = basename.replace(".", "").replace("_", "").replace("-", "")
        if len(clean) < 8 and clean.isalnum():
            if any(c.isdigit() for c in clean) and any(c.isupper() for c in clean):
                return True
    
    # Règle 2 : signature binaire MZ (fichier PE Windows)
    content = safe_read_bytes(filepath)
    if content.startswith(b"MZ"):
        return True

    return False

def quarantine_file(filepath):
    """Tente de déplacer en quarantaine – sans boucle."""
    if filepath in FAILED_FILES:
        return False

    try:
        dest_name = os.path.basename(filepath)
        safe_name = "".join(c if c.isalnum() else "_" for c in dest_name)
        dest_path = os.path.join(QUARANTINE_DIR, f"{safe_name}_{hash(filepath) % 1000000:06d}{os.path.splitext(filepath)[1]}")
        shutil.move(filepath, dest_path)
        log(f"✅ Quarantaine : {dest_path}")
        return True
    except PermissionError:
        log(f"🔒 Fichier système protégé : {filepath}")
        FAILED_FILES.add(filepath)  # Ne plus jamais réessayer
        return False
    except Exception as e:
        log(f"❌ Erreur quarantaine : {e}")
        return False

def scan_directory(directory):
    """Analyse un dossier – sans crash, sans boucle."""
    if not os.path.exists(directory):
        return

    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if is_ignored(filepath):
                continue
            if is_suspicious_file(filepath):
                log(f"🚨 SUSPICIOUS : {filepath}")
                quarantine_file(filepath)

def start_monitoring(paths, interval=600):
    """Surveillance périodique – threadé, silencieux."""
    def loop():
        while True:
            for path in paths:
                scan_directory(path)
            time.sleep(interval)
    threading.Thread(target=loop, daemon=True).start()
    log("=== GUARDSPY SCANNER BANDIT – ACTIF ===")

# === LANCEMENT ===
if __name__ == "__main__":
    # Dossiers à surveiller (à adapter)
    TARGET_PATHS = [
        os.path.expanduser("~/Desktop"),
        os.path.join(os.path.expanduser("~"), "Downloads")
    ]
    start_monitoring(TARGET_PATHS, interval=600)  # toutes les 10 min

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("Arrêt manuel.")