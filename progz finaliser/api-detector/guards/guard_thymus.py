#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
️ Guard Thymus — Système Immunitaire Adaptatif
Copyright (C) 2026 Victor Pozen — GPLv3
"""
import os, sys, json, hashlib, psutil
from pathlib import Path
from datetime import datetime, timezone

def _find_kerberos_root():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "kerberos.py").exists() or (parent / "kerberos.ultimate.py").exists():
            return parent
    return Path.cwd()

KERBEROS_ROOT = _find_kerberos_root()
LYMPH_DIR = KERBEROS_ROOT / "lymph"
PLASMA_DIR = LYMPH_DIR / "plasma"
GENOME_FILE = LYMPH_DIR / "genome.json"
MEMORY_DIR = LYMPH_DIR / "memory_cells"
LOG_FILE = KERBEROS_ROOT / "logs" / "thymus.log"

for d in [LYMPH_DIR, PLASMA_DIR, MEMORY_DIR, LOG_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

def _log(msg: str, level="INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] [{level}] {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    if __name__ == "__main__":
        print(line.strip())

def _file_dna(path: Path) -> str:
    if not path.exists(): return "MISSING"
    try: return hashlib.sha256(path.read_bytes()).hexdigest()
    except: return "ERROR"

def _load_genome():
    if GENOME_FILE.exists():
        try: return json.loads(GENOME_FILE.read_text(encoding="utf-8"))
        except: pass
    genome = {"version": "1.0", "created": datetime.now(timezone.utc).isoformat(), "vital_files": {}, "memory_cells": []}
    _save_genome(genome)
    return genome

def _save_genome(genome):
    tmp = GENOME_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(genome, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(GENOME_FILE)

VITAL_FILES = [
    Path(r"C:\Windows\System32\drivers\etc\hosts"),
    Path(r"C:\Windows\win.ini"),
    Path(r"C:\Windows\system.ini"),
]

def save_vital_files():
    genome = _load_genome()
    updated = 0
    for path in VITAL_FILES:
        if not path.exists(): continue
        current_dna = _file_dna(path)
        plasma_copy = PLASMA_DIR / path.name
        if not plasma_copy.exists() or plasma_copy.read_bytes() != path.read_bytes():
            try:
                plasma_copy.write_bytes(path.read_bytes())
                genome["vital_files"][str(path)] = {"dna": current_dna, "last_seen": datetime.now(timezone.utc).isoformat()}
                updated += 1
                _log(f"💉 Plasma mis à jour : {path.name}", "HEAL")
            except Exception as e:
                _log(f"❌ Échec sauvegarde plasma {path.name}: {e}", "ERROR")
    if updated: _save_genome(genome)
    return updated

def scan_integrity():
    genome = _load_genome()
    anomalies = []
    for path_str, meta in genome.get("vital_files", {}).items():
        path = Path(path_str)
        current_dna = _file_dna(path)
        expected_dna = meta.get("dna")
        if current_dna == "MISSING":
            anomalies.append({"path": path, "status": "MISSING", "expected": expected_dna})
            _log(f" CRITIQUE — {path.name} supprimé", "ALERT")
        elif current_dna != expected_dna:
            anomalies.append({"path": path, "status": "ALTERED", "expected": expected_dna, "actual": current_dna})
            _log(f"⚠️ ALTÉRATION — {path.name} modifié", "WARN")
    return anomalies

def heal_all(dry_run=False):
    anomalies = scan_integrity()
    healed = []
    for item in anomalies:
        if item["status"] in ["MISSING", "ALTERED"]:
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
    return healed

def run(dry_run=False):
    _log("="*50, "INFO")
    _log("🛡️ GUARD THYMUS — cycle immunitaire démarré", "INFO")
    saved = save_vital_files()
    anomalies = scan_integrity()
    healed = heal_all(dry_run=dry_run)
    status = "success" if len(anomalies) == 0 else "anomalies"
    if healed: status = "healed"
    return {"guard": "thymus", "status": status, "plasma_saved": saved, "anomalies": anomalies, "healed": healed}

def start_guard():
    print("🛡️ [Thymus] Démarrage du système immunitaire...")
    result = run(dry_run=False)
    print(f"✅ [Thymus] Cycle terminé — Statut: {result['status']}")
    return None

if __name__ == "__main__":
    result = run()
    print(f"\n📊 RAPPORT THYMUS : Statut {result['status']}")