#!/usr/bin/env python3
# immune_core.py
# Projet Kerberos – Système immunitaire ORGANIQUE
# Licence GNU GPL v3
# Reconnaissance par ADN (contenu), pas par chemin

import os
import hashlib
import json
from pathlib import Path

# -------------------------------------------------
# BASE
# -------------------------------------------------
KERBEROS_ROOT = Path(__file__).parent
PLASMA_DIR = KERBEROS_ROOT / "plasma"
PLASMA_DIR.mkdir(exist_ok=True)

CONF_FILE = KERBEROS_ROOT / "kerberos.conf"

# -------------------------------------------------
# FORMAT ADN (TXT / JSON)
# -------------------------------------------------
def _load_format():
    if CONF_FILE.exists():
        for line in CONF_FILE.read_text().splitlines():
            if line.startswith("FORMAT="):
                return line.split("=", 1)[1].strip().lower()
    return "txt"  # défaut safe

FORMAT = _load_format()

GENOME_FILE = PLASMA_DIR / f"kerberos_genome.{FORMAT}"

# -------------------------------------------------
# ADN
# -------------------------------------------------
def compute_adn(filepath):
    """
    ADN stable :
    - premiers 4K
    - taille
    - mtime
    """
    try:
        if not os.path.isfile(filepath):
            return None

        stat = os.stat(filepath)
        with open(filepath, "rb") as f:
            head = f.read(4096)

        raw = f"{head.hex()}:{stat.st_size}:{int(stat.st_mtime)}"
        return hashlib.sha256(raw.encode()).hexdigest()
    except Exception:
        return None

# -------------------------------------------------
# GÉNOME
# -------------------------------------------------
def load_genome():
    if not GENOME_FILE.exists():
        return set()

    try:
        if FORMAT == "json":
            data = json.loads(GENOME_FILE.read_text(encoding="utf-8"))
            return set(data.get("self_signatures", []))
        else:
            return set(
                line.strip()
                for line in GENOME_FILE.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
    except Exception:
        return set()

def save_genome(genome):
    if FORMAT == "json":
        GENOME_FILE.write_text(
            json.dumps({"self_signatures": list(genome)}, indent=2),
            encoding="utf-8"
        )
    else:
        GENOME_FILE.write_text(
            "\n".join(genome),
            encoding="utf-8"
        )

# -------------------------------------------------
# API IMMUNITAIRE
# -------------------------------------------------
def is_self(filepath):
    """
    Retourne True si le fichier est reconnu comme faisant partie de Kerberos.
    """
    if not os.path.exists(filepath):
        return False

    # Heuristique rapide (bootstrapping)
    safe_exts = {".py", ".json", ".txt", ".log", ".bak"}
    try:
        abs_path = Path(filepath).resolve()
        if abs_path.is_relative_to(KERBEROS_ROOT) and abs_path.suffix.lower() in safe_exts:
            return True
    except Exception:
        pass

    adn = compute_adn(filepath)
    if not adn:
        return False

    genome = load_genome()
    return adn in genome

def register_self(filepath):
    """
    Ajoute un fichier au génome.
    À utiliser à l'installation ou lors d'un update.
    """
    adn = compute_adn(filepath)
    if not adn:
        return False

    genome = load_genome()
    genome.add(adn)
    save_genome(genome)
    return True

# -------------------------------------------------
# INITIALISATION AUTO
# -------------------------------------------------
def auto_init_genome():
    """
    Enregistre les fichiers critiques de Kerberos
    au premier lancement.
    """
    if GENOME_FILE.exists():
        return

    print("[🧬] Initialisation du génome Kerberos…")

    core_files = [
        KERBEROS_ROOT / "kerberos.py",
        KERBEROS_ROOT / "immune_core.py",
    ]

    # guards
    guards_dir = KERBEROS_ROOT / "guards"
    if guards_dir.exists():
        for g in guards_dir.glob("guard_*.py"):
            core_files.append(g)

    for f in core_files:
        if f.exists():
            register_self(f)

    print(f"[✅] Génome créé : {GENOME_FILE}")

# -------------------------------------------------
# AUTO-TEST
# -------------------------------------------------
if __name__ == "__main__":
    print("[IMMUNE CORE]")
    print("Format ADN :", FORMAT)
    auto_init_genome()

    if is_self(__file__):
        print("[✅] ADN reconnu : immune_core est bien soi.")
    else:
        print("[❌] Problème d'auto-reconnaissance.")

    input("Entrée pour quitter…")
