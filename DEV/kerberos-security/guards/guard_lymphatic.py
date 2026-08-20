#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ guard_lymphatic.py — Système immunitaire adaptatif de Kerberos
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import psutil
from datetime import datetime, timezone

def _find_kerberos_root():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "kerberos.py").exists() or (parent / "LICENCE.txt").exists():
            return parent
    return Path.cwd()

KERBEROS_ROOT = _find_kerberos_root()
LYMPH_DIR = KERBEROS_ROOT / "lymph"
PLASMA_DIR = LYMPH_DIR / "plasma"
GENOME_FILE = LYMPH_DIR / "genome.json"
MEMORY_DIR = LYMPH_DIR / "memory_cells"
LOG_FILE = KERBEROS_ROOT / "logs" / "lymphatic.log"

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
    if not path.exists():
        return "MISSING"
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception as e:
        _log(f"Erreur lecture {path}: {e}", "WARN")
        return "ERROR"

def _load_genome():
    if GENOME_FILE.exists():
        try:
            return json.loads(GENOME_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            _log(f"Erreur lecture genome.json: {e} → réinitialisation", "WARN")
    genome = {
        "version": "1.0",
        "created": datetime.now(timezone.utc).isoformat(),
        "vital_files": {},
        "memory_cells": []
    }
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
        if not path.exists():
            continue
        current_dna = _file_dna(path)
        plasma_copy = PLASMA_DIR / path.name
        if not plasma_copy.exists() or plasma_copy.read_bytes() != path.read_bytes():
            try:
                plasma_copy.write_bytes(path.read_bytes())
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
            else:
                _log(f"🩹 Aucun plasma pour {path.name} — sauvegarde manquante", "WARN")
    return healed

def learn_threat(pid: int):
    try:
        proc = psutil.Process(pid)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pid": pid,
            "name": proc.name(),
            "cmdline": proc.cmdline(),
            "username": proc.username(),
            "connections": [
                {"laddr": str(conn.laddr), "raddr": str(conn.raddr), "status": conn.status}
                for conn in proc.connections() if conn.raddr
            ]
        }
        mem_path = MEMORY_DIR / f"threat_{pid}_{int(datetime.now().timestamp())}.json"
        mem_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(f"🧠 Menace apprise — pid {pid} ({proc.name()})", "LEARN")
        genome = _load_genome()
        genome["memory_cells"].append(record)
        _save_genome(genome)
        return record
    except Exception as e:
        _log(f"Erreur apprentissage pid {pid}: {e}", "ERROR")
        return None

def run(dry_run=False):
    _log("="*50, "INFO")
    _log("🛡️  GUARD LYMPHATIC — cycle immunitaire démarré", "INFO")
    _log(f"Racine Kerberos : {KERBEROS_ROOT}", "INFO")
    _log(f"Mode dry_run : {dry_run}", "INFO")
    saved = save_vital_files()
    _log(f"💉 {saved} fichier(s) sauvegardé(s) dans le plasma", "INFO")
    anomalies = scan_integrity()
    _log(f"🔍 {len(anomalies)} anomalie(s) détectée(s)", "INFO")
    healed = heal_all(dry_run=dry_run)
    _log(f"🩹 {len(healed)} fichier(s) régénéré(s)", "INFO")
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

# ============================================================================
# === ⚠️ AJOUT CRITIQUE : start_guard() POUR CORTEX ==========================
# ============================================================================

def start_guard():
    """Point d'entrée pour Kerberos — Système immunitaire"""
    print("🛡️ [Lymphatic] Système immunitaire actif")
    result = run(dry_run=False)
    print(f"   └─ Plasma: {result['plasma_saved']} fichier(s) | Anomalies: {len(result['anomalies'])}")
    return None  # Scan unique, pas de thread

if __name__ == "__main__":
    result = run()
    print(f"\n📊 RAPPORT :")
    print(f"  • Plasma sauvegardé : {result['plasma_saved']}")
    print(f"  • Anomalies         : {len(result['anomalies'])}")
    print(f"  • Fichiers guéris   : {len(result['healed'])}")
    print(f"  • Statut            : {result['status']}")