#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧬 guard_genome.py — Gestionnaire d'ADN, télomères & mutations contrôlées
"""

import hashlib
import struct
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# === DÉTECTION RACINE & BINAIRES ===
def _find_kerberos_root():
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "kerberos.py").exists() or (parent / "LICENCE.txt").exists():
            return parent
    return Path.cwd()

KERBEROS_ROOT = _find_kerberos_root()
LYMPH_DIR = KERBEROS_ROOT / "lymph"
GENOME_STATE = LYMPH_DIR / "genome_v2.json"
LOG_FILE = KERBEROS_ROOT / "logs" / "genome.log"

for d in [LYMPH_DIR, LOG_FILE.parent]:
    d.mkdir(parents=True, exist_ok=True)

def _log(msg: str, level="INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] [{level}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if __name__ == "__main__":
        print(line)

def _get_self_path():
    me = Path(sys.executable if getattr(sys, 'frozen', False) else __file__)
    return me.resolve()

def _read_bytes_safe(path: Path, start: int, length: int) -> bytes:
    try:
        with open(path, "rb") as f:
            f.seek(start)
            return f.read(length)
    except Exception:
        return b""

def compute_dna(include_telomeres=True, include_metadata=True):
    me = _get_self_path()
    full_data = me.read_bytes() if me.exists() else b""

    dna = {
        "core": hashlib.sha256(full_data).hexdigest(),
        "size_bytes": len(full_data),
        "computed_at": datetime.now(timezone.utc).isoformat()
    }

    if include_telomeres and len(full_data) >= 64:
        dna["telomere_start"] = full_data[:32].hex()
        dna["telomere_end"] = full_data[-32:].hex()
        magic = full_data[:2]
        dna["magic"] = magic.hex()
        if magic == b"MZ":
            dna["format"] = "PE (Windows executable)"
        elif b"#!/usr/bin/env python" in full_data[:100]:
            dna["format"] = "Python script"
        else:
            dna["format"] = "inconnu"

    if include_metadata:
        dna["path"] = str(me)
        dna["modified_at"] = me.stat().st_mtime if me.exists() else None

    return dna

def check_telomeres():
    me = _get_self_path()
    if not me.exists():
        return {"valid": False, "reason": "fichier introuvable"}

    data = me.read_bytes()
    if len(data) < 64:
        return {"valid": False, "reason": "trop court (<64 octets)"}

    start = data[:32]
    end = data[-32:]

    start_nulls = start.count(b"\x00")
    end_nulls = end.count(b"\x00")

    issues = []
    if start_nulls > 16:
        issues.append("début trop nul (possible troncature)")
    if end_nulls > 16:
        issues.append("fin trop nulle (possible padding malveillant)")
    if b"VKR1" in end or b"PE\x00\x00" in start:
        issues.append("pattern binaire suspect en télomère")

    return {
        "valid": len(issues) == 0,
        "telomere_start_hex": start.hex()[:16] + "…",
        "telomere_end_hex": end.hex()[:16] + "…",
        "start_null_ratio": f"{start_nulls}/32",
        "end_null_ratio": f"{end_nulls}/32",
        "issues": issues,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def is_self(expected_dna: str = None):
    current = compute_dna(include_telomeres=False)["core"]
    if expected_dna is None:
        if GENOME_STATE.exists():
            try:
                state = json.loads(GENOME_STATE.read_text(encoding="utf-8"))
                expected_dna = state.get("current_dna", {}).get("core")
            except:
                pass

    if expected_dna and current != expected_dna:
        _log(f"🩸 ADN non conforme : attendu {expected_dna[:8]}… / actuel {current[:8]}…", "ALERT")
        return False
    return True

def mutate(seed: int = None, strength=1):
    if seed is None:
        seed = hash(datetime.now().isoformat()) % (2**32)

    import random
    rng = random.Random(seed)

    mutations = []
    if strength >= 1:
        mutations.append({
            "type": "rename",
            "target": "_dna_pulse",
            "new_name": f"_pulse_{rng.randint(100,999)}"
        })
    if strength >= 2:
        mutations.append({
            "type": "xor_strings",
            "target": "TEXTS",
            "key": rng.randint(1, 255)
        })

    _log(f"🧪 Mutation contrôlée générée (seed={seed}, strength={strength})", "MUTATE")
    return {
        "seed": seed,
        "strength": strength,
        "mutations": mutations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "warning": "Aucun fichier modifié — mutation symbolique uniquement.",
        "note": "À appliquer via compilation (ex. : Nuitka + patch)."
    }

def run(dry_run=False):
    _log("="*50, "INFO")
    _log("🧬 GUARD GENOME — analyse génomique en cours", "INFO")

    telo = check_telomeres()
    dna = compute_dna(include_telomeres=True)

    previous = {}
    if GENOME_STATE.exists():
        try:
            previous = json.loads(GENOME_STATE.read_text(encoding="utf-8"))
        except Exception as e:
            _log(f"⚠️ Erreur lecture genome_v2.json : {e}", "WARN")

    was_same = previous.get("current_dna", {}).get("core") == dna["core"]
    status = "stable" if was_same and telo["valid"] else "change_detected"

    new_state = {
        "version": "2.0",
        "current_dna": dna,
        "telomere_check": telo,
        "last_check": datetime.now(timezone.utc).isoformat(),
        "history": previous.get("history", [])[-9:] + [{
            "dna_core": dna["core"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status
        }]
    }

    if not dry_run:
        try:
            GENOME_STATE.write_text(json.dumps(new_state, indent=2, ensure_ascii=False), encoding="utf-8")
            _log(f"💾 État génomique sauvegardé : {GENOME_STATE.name}", "SAVE")
        except Exception as e:
            _log(f"❌ Échec sauvegarde état : {e}", "ERROR")

    return {
        "guard": "genome",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "dna_core": dna["core"][:8] + "…",
        "telomeres_valid": telo["valid"],
        "telomere_issues": telo["issues"],
        "was_stable": was_same,
        "mutation_available": True
    }

# ============================================================================
# === ⚠️ AJOUT CRITIQUE : start_guard() POUR CORTEX ==========================
# ============================================================================

def start_guard():
    """Point d'entrée pour Kerberos — Scan ADN au démarrage"""
    print("🧬 [Genome] Surveillance ADN activée")
    result = run(dry_run=False)
    print(f"   └─ ADN: {result['dna_core']} | Télomères: {'✅' if result['telomeres_valid'] else '❌'}")
    return None  # Scan unique, pas de thread

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧬 GUARD GENOME — ADN, télomères & évolution contrôlée")
    print("White hat • Local only • GPL v3 • (-;")
    print("="*60 + "\n")

    dry = "--dry" in sys.argv
    result = run(dry_run=dry)

    print(f"📊 Rapport génomique :")
    print(f"  • ADN (core)        : {result['dna_core']}")
    print(f"  • Télomères OK      : {'✅' if result['telomeres_valid'] else '❌'}")
    print(f"  • État précédent    : {'stable' if result['was_stable'] else 'modifié'}")
    print(f"  • Statut            : {result['status']}")

    if result["telomere_issues"]:
        print(f"\n⚠️  Problèmes télomères :")
        for issue in result["telomere_issues"]:
            print(f"    • {issue}")

    print(f"\n🩺 Logs : logs/genome.log")
    print("Kerberos ne ment jamais — mais parfois, il grogne… et mute. 🐺🧬\n")