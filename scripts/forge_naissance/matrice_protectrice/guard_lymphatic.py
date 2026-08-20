#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2025–2026 Victor Pozen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# KERBEROS — Système de défense numérique éthique (mode local pur)
# White hat • Anonymous • Résistant numérique • (-;

"""
🛡️ guard_lymphatic.py — Système immunitaire adaptatif de Kerberos

Fonctionne comme un organe vivant :
  → scanne l’intégrité des fichiers vitaux (ADN),
  → sauvegarde les versions saines dans le plasma,
  → régénère les fichiers corrompus,
  → apprend des menaces (mémoire immunitaire).

Conçu pour vieux PCs (Win7/10, HDD, faible RAM).
Aucun réseau. Aucun cloud. Aucune trace.

GPLv3 — Victor.Pozen @2026
(-;
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import psutil
from datetime import datetime, timezone

# === DÉTECTION AUTOMATIQUE DE LA RACINE KERBEROS ===
def _find_kerberos_root():
    # On part du chemin de ce guard
    here = Path(__file__).resolve()
    # On remonte jusqu’à trouver 'kerberos.py' ou 'LICENSE'
    for parent in [here.parent] + list(here.parents):
        if (parent / "kerberos.py").exists() or (parent / "LICENCE.txt").exists():
            return parent
    # Sinon, on prend le dossier courant (fallback)
    return Path.cwd()

KERBEROS_ROOT = _find_kerberos_root()
LYMPH_DIR = KERBEROS_ROOT / "lymph"
PLASMA_DIR = LYMPH_DIR / "plasma"
GENOME_FILE = LYMPH_DIR / "genome.json"
MEMORY_DIR = LYMPH_DIR / "memory_cells"
LOG_FILE = KERBEROS_ROOT / "logs" / "lymphatic.log"

# Création silencieuse des dossiers nécessaires
for d in [LYMPH_DIR, PLASMA_DIR, MEMORY_DIR, LOG_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

# === UTILITAIRES BIOLOGIQUES ===

def _log(msg: str, level="INFO"):
    """Écrit dans lymphatic.log + stdout si exécuté seul."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] [{level}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if __name__ == "__main__":
        print(line)

def _file_dna(path: Path) -> str:
    """Renvoie le SHA-256 d’un fichier — ou 'MISSING' s’il n’existe pas."""
    if not path.exists():
        return "MISSING"
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception as e:
        _log(f"Erreur lecture {path}: {e}", "WARN")
        return "ERROR"

def _load_genome():
    """Charge ou initialise genome.json."""
    if GENOME_FILE.exists():
        try:
            return json.loads(GENOME_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            _log(f"Erreur lecture genome.json: {e} → réinitialisation", "WARN")
    # Génome vide par défaut
    genome = {
        "version": "1.0",
        "created": datetime.now(timezone.utc).isoformat(),
        "vital_files": {},   # chemin → { "dna": "...", "last_seen": "..." }
        "memory_cells": []   # comportements appris
    }
    _save_genome(genome)
    return genome

def _save_genome(genome):
    """Sauvegarde le génome — atomique (écriture temp puis rename)."""
    tmp = GENOME_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(genome, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(GENOME_FILE)

# === FICHIERS VITAUX — à adapter selon machine cible (Win7/10) ===
# Inspiré des cibles classiques de backdoors / persistence
VITAL_FILES = [
    Path(r"C:\Windows\System32\drivers\etc\hosts"),
    Path(r"C:\Windows\System32\drivers\etc\lmhosts"),
    Path(r"C:\Windows\win.ini"),
    Path(r"C:\Windows\system.ini"),
    # Ajout discret : DNS client config (souvent modifié)
    Path(r"C:\Windows\System32\Drivers\etc\networks"),
]

# === FONCTIONS PRINCIPALES ===

def save_vital_files():
    """💉 Sauvegarde les fichiers vitaux dans le plasma (si absents ou plus récents)."""
    genome = _load_genome()
    updated = 0

    for path in VITAL_FILES:
        if not path.exists():
            continue
        current_dna = _file_dna(path)
        plasma_copy = PLASMA_DIR / path.name

        # Sauvegarde si : pas dans plasma OU ADN différent
        if not plasma_copy.exists() or plasma_copy.read_bytes() != path.read_bytes():
            try:
                plasma_copy.write_bytes(path.read_bytes())
                # Mise à jour du génome
                genome["vital_files"][str(path)] = {
                    "dna": current_dna,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                    "plasma_saved": datetime.now(timezone.utc).isoformat()
                }
                updated += 1
                _log(f"💉 Plasma mis à jour : {path.name}", "HEAL")
            except Exception as e:
                _log(f"❌ Échec sauvegarde plasma {path.name}: {e}", "ERROR")

    if updated:
        _save_genome(genome)
    return updated

def scan_integrity():
    """🔍 Vérifie l’intégrité des fichiers vitaux contre le génome."""
    genome = _load_genome()
    anomalies = []

    for path_str, meta in genome.get("vital_files", {}).items():
        path = Path(path_str)
        current_dna = _file_dna(path)
        expected_dna = meta.get("dna")

        if current_dna == "MISSING":
            anomalies.append({"path": path, "status": "MISSING", "expected": expected_dna})
            _log(f"🩸 CRITIQUE — {path.name} supprimé", "ALERT")
        elif current_dna != expected_dna:
            anomalies.append({"path": path, "status": "ALTERED", "expected": expected_dna, "actual": current_dna})
            _log(f"⚠️ ALTÉRATION — {path.name} modifié", "WARN")
        else:
            _log(f"✅ Stable — {path.name}", "INFO")

    return anomalies

def heal_all(dry_run=False):
    """🩹 Tente de régénérer tous les fichiers altérés depuis le plasma."""
    anomalies = scan_integrity()
    healed = []

    for item in anomalies:
        if item["status"] == "MISSING" or item["status"] == "ALTERED":
            path = item["path"]
            plasma_copy = PLASMA_DIR / path.name

            if plasma_copy.exists():
                if not dry_run:
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(plasma_copy.read_bytes())
                        healed.append(str(path))
                        _log(f"✅ RÉGÉNÉRÉ — {path.name}", "HEAL")
                    except Exception as e:
                        _log(f"❌ Échec régénération {path.name}: {e}", "ERROR")
                else:
                    _log(f"[DRY] Régénération possible : {path.name}", "DRY")
            else:
                _log(f"🩹 Aucun plasma pour {path.name} — sauvegarde manquante", "WARN")

    return healed

def learn_threat(pid: int):
    """🧠 Enregistre un comportement malveillant dans memory_cells (apprentissage immunitaire)."""
    try:
        proc = psutil.Process(pid)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pid": pid,
            "name": proc.name(),
            "cmdline": proc.cmdline(),
            "username": proc.username(),
            "connections": [
                {"laddr": conn.laddr, "raddr": conn.raddr, "status": conn.status}
                for conn in proc.connections() if conn.raddr
            ]
        }

        mem_path = MEMORY_DIR / f"threat_{pid}_{int(datetime.now().timestamp())}.json"
        mem_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(f"🧠 Menace apprise — pid {pid} ({proc.name()})", "LEARN")

        # Ajout au génome (pour scan futur)
        genome = _load_genome()
        genome["memory_cells"].append(record)
        _save_genome(genome)

        return record
    except Exception as e:
        _log(f"Erreur apprentissage pid {pid}: {e}", "ERROR")
        return None

# === INTERFACE GUARD (exécuté par KerberosApp) ===

def run(dry_run=False):
    """
    Exécute un cycle complet du système lymphatique :
      1. Sauvegarde les fichiers vitaux (si besoin)
      2. Scan d’intégrité
      3. Régénération auto (si dry_run=False)
      4. Rapport synthétique

    Retourne un dict conforme aux guards Kerberos.
    """
    _log("="*50, "INFO")
    _log("🛡️  GUARD LYMPHATIC — cycle immunitaire démarré", "INFO")
    _log(f"Racine Kerberos : {KERBEROS_ROOT}", "INFO")
    _log(f"Mode dry_run : {dry_run}", "INFO")

    # 1. Sauvegarde initiale (plasma)
    saved = save_vital_files()
    _log(f"💉 {saved} fichier(s) sauvegardé(s) dans le plasma", "INFO")

    # 2. Scan
    anomalies = scan_integrity()
    _log(f"🔍 {len(anomalies)} anomalie(s) détectée(s)", "INFO")

    # 3. Guérison
    healed = heal_all(dry_run=dry_run)
    _log(f"🩹 {len(healed)} fichier(s) régénéré(s)", "INFO")

    # 4. Bilan
    status = "success" if len(anomalies) == 0 else "anomalies"
    if not dry_run and healed:
        status = "healed"

    report = {
        "guard": "lymphatic",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "plasma_saved": saved,
        "anomalies": [
            {
                "path": str(a["path"]),
                "status": a["status"],
                "expected_dna": a.get("expected", "")[:8] + "…"
            }
            for a in anomalies
        ],
        "healed": healed
    }

    _log("✅ Cycle lymphatique terminé.", "INFO")
    return report

# === MODE STANDALONE (pour tests/debug) ===
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🛡️  GUARD LYMPHATIC — système immunitaire de Kerberos")
    print("White hat • Local only • GPLv3 • (-;")
    print("="*60 + "\n")

    dry = "--dry" in sys.argv
    result = run(dry_run=dry)
    
    print(f"\n📊 RAPPORT :")
    print(f"  • Plasma sauvegardé : {result['plasma_saved']}")
    print(f"  • Anomalies         : {len(result['anomalies'])}")
    print(f"  • Fichiers guéris   : {len(result['healed'])}")
    print(f"  • Statut            : {result['status']}")
    
    if result["anomalies"]:
        print("\n⚠️  Détails :")
        for a in result["anomalies"]:
            print(f"    - {a['path']} → {a['status']} (ADN: {a['expected_dna']})")
    
    print("\n🩺 Logs disponibles dans : logs/lymphatic.log")
    print("Kerberos ne ment jamais — mais parfois, il grogne. 🐺\n")