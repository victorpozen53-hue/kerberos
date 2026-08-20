#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ argos_thymus.py — Système immunitaire d'ARGOS (adapté de guard_thymus.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — version ARGOS, civile
- Intégrité des fichiers VITAUX d'Argos (moteur, doctrine, carnet, manifest)
- Plasma : sauvegarde des versions saines -> régénération si corruption
- Mémoire immunitaire (menaces apprises)
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

try:
    import psutil
    HAS_PSUTIL = True
except Exception:
    HAS_PSUTIL = False


def _find_argos_root():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "argos.py").exists() or (parent / "carnet").exists():
            return parent
    return Path.cwd()


ARGOS_ROOT = _find_argos_root()
LYMPH_DIR = ARGOS_ROOT / "lymph_argos"
PLASMA_DIR = LYMPH_DIR / "plasma"
GENOME_FILE = LYMPH_DIR / "genome_argos.json"
MEMORY_DIR = LYMPH_DIR / "memory_cells"
LOG_FILE = ARGOS_ROOT / "logs" / "argos_thymus.log"
for d in (LYMPH_DIR, PLASMA_DIR, MEMORY_DIR, LOG_FILE.parent):
    d.mkdir(parents=True, exist_ok=True)

# === FICHIERS VITAUX D'ARGOS (civils) ===
VITAL_FILES = [ARGOS_ROOT / "argos.py",
               ARGOS_ROOT / "war_doctrine.txt",
               ARGOS_ROOT / "carnet" / "carnet.json",
               ARGOS_ROOT / "argos_manifest.json"]


def _log(msg, level="INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] [{level}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if __name__ == "__main__":
        print(line)


def _file_dna(path):
    if not path.exists():
        return "MISSING"
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return "ERROR"


def _load_genome():
    if GENOME_FILE.exists():
        try:
            return json.loads(GENOME_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    genome = {"version": "1.0-argos", "vital_files": {}, "memory_cells": []}
    _save_genome(genome)
    return genome


def _save_genome(genome):
    tmp = GENOME_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(genome, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(GENOME_FILE)


def save_vital_files():
    genome = _load_genome()
    updated = 0
    for path in VITAL_FILES:
        if not path.exists():
            continue
        cur = _file_dna(path)
        plasma = PLASMA_DIR / path.name
        if not plasma.exists() or plasma.read_bytes() != path.read_bytes():
            try:
                plasma.write_bytes(path.read_bytes())
                genome["vital_files"][str(path)] = {
                    "dna": cur, "plasma_saved": datetime.now(timezone.utc).isoformat()}
                updated += 1
                _log(f"💉 Plasma mis à jour : {path.name}", "HEAL")
            except Exception as e:
                _log(f"❌ Échec plasma {path.name}: {e}", "ERROR")
    if updated:
        _save_genome(genome)
    return updated


def scan_integrity():
    genome = _load_genome()
    anomalies = []
    for path_str, meta in genome.get("vital_files", {}).items():
        path = Path(path_str)
        cur = _file_dna(path)
        exp = meta.get("dna")
        if cur == "MISSING":
            anomalies.append({"path": path, "status": "MISSING", "expected": exp})
            _log(f"🩸 CRITIQUE — {path.name} supprimé", "ALERT")
        elif cur != exp:
            anomalies.append({"path": path, "status": "ALTERED", "expected": exp, "actual": cur})
            _log(f"⚠️ ALTÉRATION — {path.name} modifié", "WARN")
    return anomalies


def heal_all(dry_run=False):
    healed = []
    for item in scan_integrity():
        if item["status"] in ("MISSING", "ALTERED"):
            plasma = PLASMA_DIR / item["path"].name
            if plasma.exists() and not dry_run:
                try:
                    item["path"].parent.mkdir(parents=True, exist_ok=True)
                    item["path"].write_bytes(plasma.read_bytes())
                    healed.append(str(item["path"]))
                    _log(f"✅ RÉGÉNÉRÉ — {item['path'].name}", "HEAL")
                except Exception as e:
                    _log(f"❌ Régénération échouée {item['path'].name}: {e}", "ERROR")
    return healed


def learn_threat(pid):
    if not HAS_PSUTIL:
        return None
    try:
        proc = psutil.Process(pid)
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), "pid": pid,
                  "name": proc.name(), "cmdline": proc.cmdline()}
        (MEMORY_DIR / f"threat_{pid}_{int(datetime.now().timestamp())}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        genome = _load_genome()
        genome["memory_cells"].append(record)
        _save_genome(genome)
        _log(f"🧠 Menace apprise — pid {pid} ({proc.name()})", "LEARN")
        return record
    except Exception as e:
        _log(f"Erreur apprentissage pid {pid}: {e}", "ERROR")
        return None


def run(dry_run=False):
    _log("🛡️ ARGOS THYMUS — cycle immunitaire démarré", "INFO")
    saved = save_vital_files()
    anomalies = scan_integrity()
    healed = heal_all(dry_run=dry_run)
    status = "healed" if healed else ("anomalies" if anomalies else "success")
    _log(f"💉 {saved} plasma • 🔍 {len(anomalies)} anomalie(s) • 🩹 {len(healed)} guéri(s)", "INFO")
    return {"guard": "argos_thymus", "status": status, "plasma_saved": saved,
            "anomalies": len(anomalies), "healed": healed,
            "timestamp": datetime.now(timezone.utc).isoformat()}


def start_guard():
    print("🛡️ [Argos Thymus] Système immunitaire démarré...")
    r = run(dry_run=False)
    print(f"✅ [Argos Thymus] Statut: {r['status']}")
    return None


if __name__ == "__main__":
    r = run()
    print(f"📊 RAPPORT THYMUS ARGOS : plasma={r['plasma_saved']} anomalies={r['anomalies']}"
          f" guéris={len(r['healed'])} statut={r['status']}")