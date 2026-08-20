#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💀 sim_pickle — Simulation Pickle Exploit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Génère des fichiers .pkl avec les VRAIES signatures d'opcodes
malveillants — mais le payload ne fait que print() / logger.
YARA guard_yara.py doit détecter les opcodes GLOBAL+REDUCE.
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""

import os
import time
import struct
import pickle
import pickletools
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_pickle"
MODULE_LABEL = "Pickle Exploit"
_running     = False

# Dossier de sortie des fichiers fake
_OUT_DIR = Path(__file__).parent.parent / "payloads_fake" / "pickle"


def _ensure_dirs():
    _OUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Payload 1 : pickle GLOBAL os.system → inoffensif ─────────────────────
class _FakeOsSystem:
    """Simule un pickle qui appelle os.system — mais la commande est inoffensive"""
    def __reduce__(self):
        # Signature réelle d'un pickle exploit
        # YARA cherche exactement : opcode GLOBAL + "os\nsystem"
        # Ici la commande est "echo KERBEROS_TEST_PICKLE" — inoffensive
        return (os.system, ("echo KERBEROS_PENTEST_PICKLE_DETECTED",))


# ── Payload 2 : pickle GLOBAL subprocess.run → inoffensif ────────────────
class _FakeSubprocess:
    """Simule un pickle qui appelle subprocess — commande inoffensive"""
    def __reduce__(self):
        import subprocess
        return (subprocess.run, (["echo", "KERBEROS_TEST"],
                                  {"capture_output": True}))


# ── Payload 3 : pickle GLOBAL eval → inoffensif ──────────────────────────
class _FakeEval:
    """Simule un pickle qui appelle eval/exec"""
    def __reduce__(self):
        return (eval, ("1+1",))  # eval d'une expression numérique — inoffensif


# ── Payload 4 : opcodes bruts protocole 4 ────────────────────────────────
def _build_raw_opcodes_pickle() -> bytes:
    """
    Construit manuellement un pickle avec les opcodes suspects
    que YARA recherche (GLOBAL = 0x63, REDUCE = 0x52)
    mais qui ne fait rien de dangereux.
    """
    # Protocol 4 header + opcodes GLOBAL os\ngetenv + REDUCE + STOP
    # os.getenv("PATH") → inoffensif, mais signature identique à os.system
    data = (
        b"\x80\x04"          # PROTO 4
        b"\x95"              # FRAME
        + struct.pack("<Q", 30)
        + b"\x8c\x02os"      # SHORT_BINUNICODE "os"
        + b"\x94"            # BUILD
        + b"\x63"            # GLOBAL opcode (signature YARA)
        + b"os\ngetenv\n"    # module\nname (pattern dangereux mais inoffensif)
        + b"\x52"            # REDUCE opcode (signature YARA)
        + b"\x8c\x04PATH"    # argument
        + b"\x85"            # TUPLE1
        + b"\x52"            # REDUCE
        + b"."               # STOP
    )
    return data


def run(target: str = "127.0.0.1", callback=None) -> dict:
    global _running
    _running = True
    _ensure_dirs()

    results = {
        "module":    MODULE_NAME,
        "target":    target,
        "started":   datetime.now().isoformat(),
        "events":    [],
        "files":     [],
        "status":    "running",
    }

    def log(msg):
        results["events"].append(msg)
        if callback:
            callback(msg)

    log("💀 Démarrage simulation Pickle Exploit...")
    log("   Génération fichiers .pkl avec opcodes GLOBAL+REDUCE réels")
    log("   Payload : inoffensif (echo/getenv) — signature identique au vrai malware")

    # ── Test 1 : os.system fake ───────────────────────────────────────────
    if not _running:
        return results
    time.sleep(0.3)
    f1 = _OUT_DIR / "fake_model_os_system.pkl"
    try:
        with open(f1, "wb") as fh:
            pickle.dump(_FakeOsSystem(), fh, protocol=4)
        results["files"].append(str(f1))
        log(f"✅ Créé : {f1.name} (opcode GLOBAL os.system)")
        log(f"   → YARA doit détecter : Pickle_Exploit_Payload + os\\nsystem")
    except Exception as e:
        log(f"❌ Erreur création {f1.name} : {e}")

    # ── Test 2 : subprocess fake ──────────────────────────────────────────
    if not _running:
        return results
    time.sleep(0.3)
    f2 = _OUT_DIR / "fake_model_subprocess.pkl"
    try:
        with open(f2, "wb") as fh:
            pickle.dump(_FakeSubprocess(), fh, protocol=4)
        results["files"].append(str(f2))
        log(f"✅ Créé : {f2.name} (opcode GLOBAL subprocess)")
        log(f"   → YARA doit détecter : Pickle_Exploit_Payload + subprocess\\nrun")
    except Exception as e:
        log(f"❌ Erreur création {f2.name} : {e}")

    # ── Test 3 : eval fake ────────────────────────────────────────────────
    if not _running:
        return results
    time.sleep(0.3)
    f3 = _OUT_DIR / "fake_model_eval.pkl"
    try:
        with open(f3, "wb") as fh:
            pickle.dump(_FakeEval(), fh, protocol=4)
        results["files"].append(str(f3))
        log(f"✅ Créé : {f3.name} (opcode GLOBAL eval)")
        log(f"   → YARA doit détecter : Pickle_Exploit_Payload + builtins\\neval")
    except Exception as e:
        log(f"❌ Erreur création {f3.name} : {e}")

    # ── Test 4 : opcodes bruts ────────────────────────────────────────────
    if not _running:
        return results
    time.sleep(0.3)
    f4 = _OUT_DIR / "fake_model_raw_opcodes.pkl"
    try:
        f4.write_bytes(_build_raw_opcodes_pickle())
        results["files"].append(str(f4))
        log(f"✅ Créé : {f4.name} (opcodes bruts protocole 4)")
        log(f"   → YARA doit détecter : opcodes 0x63 + 0x80 0x04")
    except Exception as e:
        log(f"❌ Erreur création {f4.name} : {e}")

    # ── Test 5 : faux modèle PyTorch .pt ─────────────────────────────────
    if not _running:
        return results
    time.sleep(0.3)
    f5 = _OUT_DIR / "fake_pytorch_model.pt"
    try:
        # Un vrai .pt est un ZIP contenant archive/data.pkl
        # On simule la structure avec les strings suspectes
        import zipfile, io
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            # Le pickle interne avec signature suspecte
            inner_pkl = pickle.dumps(_FakeOsSystem(), protocol=4)
            zf.writestr("archive/data.pkl", inner_pkl)
            zf.writestr("archive/version",  "1\n")
        f5.write_bytes(buf.getvalue())
        results["files"].append(str(f5))
        log(f"✅ Créé : {f5.name} (faux modèle PyTorch avec pickle interne)")
        log(f"   → YARA doit détecter : PyTorch_Malicious_Model")
    except Exception as e:
        log(f"❌ Erreur création {f5.name} : {e}")

    time.sleep(0.5)
    log(f"📊 {len(results['files'])} fichier(s) pickle suspect(s) créés dans payloads_fake/pickle/")
    log("⏳ En attente détection par guard_yara.py (AI Shield)...")
    log("💡 Si Kerberos n'alerte pas → guard_yara.py manque les opcodes pickle")

    results["status"]   = "completed"
    results["finished"] = datetime.now().isoformat()
    _running = False
    return results


def stop():
    global _running
    _running = False


def get_info() -> dict:
    return {
        "name":        MODULE_NAME,
        "label":       MODULE_LABEL,
        "description": "Génère fichiers .pkl avec opcodes GLOBAL+REDUCE réels — payload inoffensif",
        "version":     "1.0",
        "targets":     ["guard_yara.py", "guard_ai_shield.py"],
    }
