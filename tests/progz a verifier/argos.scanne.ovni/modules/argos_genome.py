#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧬 argos_genome.py — ADN & télomères d'ARGOS (adapté de guard_genome.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — version ARGOS, civile
- Calcule l'ADN du MOTEUR (argos.py) + télomères (début/fin)
- Détecte les mutations non conformes (intégrité)
- Mutations contrôlées symboliques (jamais de fichier modifié)
"""
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def _find_argos_root():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "argos.py").exists() or (parent / "carnet").exists():
            return parent
    return Path.cwd()


ARGOS_ROOT = _find_argos_root()
LYMPH_DIR = ARGOS_ROOT / "lymph_argos"
GENOME_STATE = LYMPH_DIR / "genome_v2_argos.json"
LOG_FILE = ARGOS_ROOT / "logs" / "argos_genome.log"
for d in (LYMPH_DIR, LOG_FILE.parent):
    d.mkdir(parents=True, exist_ok=True)


def _log(msg, level="INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] [{level}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if __name__ == "__main__":
        print(line)


def _target():
    """L'ADN surveillé = le moteur argos.py (ou moi-même si absent)."""
    t = ARGOS_ROOT / "argos.py"
    return t if t.exists() else Path(__file__).resolve()


def compute_dna(include_telomeres=True):
    me = _target()
    full = me.read_bytes() if me.exists() else b""
    dna = {"core": hashlib.sha256(full).hexdigest(), "size_bytes": len(full),
           "computed_at": datetime.now(timezone.utc).isoformat()}
    if include_telomeres and len(full) >= 64:
        dna["telomere_start"] = full[:32].hex()
        dna["telomere_end"] = full[-32:].hex()
        magic = full[:2]
        dna["magic"] = magic.hex()
        dna["format"] = "PE (exe)" if magic == b"MZ" else (
            "Python script" if b"#!/usr/bin/env python" in full[:100] else "inconnu")
    return dna


def check_telomeres():
    me = _target()
    if not me.exists():
        return {"valid": False, "reason": "fichier introuvable"}
    data = me.read_bytes()
    if len(data) < 64:
        return {"valid": False, "reason": "trop court (<64 octets)"}
    start, end = data[:32], data[-32:]
    issues = []
    if start.count(b"\x00") > 16:
        issues.append("début trop nul (troncature possible)")
    if end.count(b"\x00") > 16:
        issues.append("fin trop nulle (padding suspect)")
    return {"valid": not issues, "telomere_start_hex": start.hex()[:16] + "…",
            "telomere_end_hex": end.hex()[:16] + "…", "issues": issues,
            "timestamp": datetime.now(timezone.utc).isoformat()}


def is_self(expected_dna=None):
    current = compute_dna(include_telomeres=False)["core"]
    if expected_dna is None and GENOME_STATE.exists():
        try:
            expected_dna = json.loads(GENOME_STATE.read_text(encoding="utf-8")).get(
                "current_dna", {}).get("core")
        except Exception:
            pass
    if expected_dna and current != expected_dna:
        _log(f"🩸 ADN non conforme : attendu {expected_dna[:8]}… / actuel {current[:8]}…", "ALERT")
        return False
    return True


def run(dry_run=False):
    _log("🧬 ARGOS GENOME — analyse génomique du moteur", "INFO")
    telo = check_telomeres()
    dna = compute_dna()
    previous = {}
    if GENOME_STATE.exists():
        try:
            previous = json.loads(GENOME_STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    was_same = previous.get("current_dna", {}).get("core") == dna["core"]
    status = "stable" if was_same and telo["valid"] else "change_detected"
    new_state = {"version": "2.0-argos", "current_dna": dna, "telomere_check": telo,
                 "last_check": datetime.now(timezone.utc).isoformat(),
                 "history": previous.get("history", [])[-9:] + [
                     {"dna_core": dna["core"], "status": status,
                      "timestamp": datetime.now(timezone.utc).isoformat()}]}
    if not dry_run:
        try:
            GENOME_STATE.write_text(json.dumps(new_state, indent=2, ensure_ascii=False),
                                    encoding="utf-8")
        except Exception as e:
            _log(f"❌ Échec sauvegarde : {e}", "ERROR")
    return {"guard": "argos_genome", "status": status, "dna_core": dna["core"][:8] + "…",
            "telomeres_valid": telo["valid"], "was_stable": was_same,
            "timestamp": datetime.now(timezone.utc).isoformat()}


def start_guard():
    print("🧬 [Argos Genome] Surveillance ADN du moteur activée")
    r = run(dry_run=False)
    print(f"   └─ ADN: {r['dna_core']} | Télomères: {'✅' if r['telomeres_valid'] else '❌'}")
    return None


if __name__ == "__main__":
    print("🧬 ARGOS GENOME — White hat • Local only • GPLv3")
    r = run(dry_run="--dry" in sys.argv)
    print(f"  • ADN: {r['dna_core']} • Télomères: {'✅' if r['telomeres_valid'] else '❌'}"
          f" • Statut: {r['status']}")