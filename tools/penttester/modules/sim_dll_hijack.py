#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 sim_dll_hijack — Simulation DLL Hijacking / Injection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Génère les signatures exactes que guard_dll_shield.py cherchera :
  - Fausse DLL avec exports suspects dans un dossier PATH
  - Script avec API Windows d'injection (VirtualAllocEx etc.)
  - Fichier OCX non signé dans %APPDATA%
  - Rapport des DLL vulnérables au hijacking sur le système
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import os
import sys
import time
import struct
import platform
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_dll_hijack"
MODULE_LABEL = "DLL Hijack"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "dll"


def _build_fake_pe_dll(name: str) -> bytes:
    """
    Construit un faux PE (MZ header) avec les strings suspectes
    que YARA recherche dans Bubble_Shield_Memory_Injection.
    Pas un vrai PE exécutable — juste les signatures.
    """
    mz = b"MZ"  # Magic bytes PE
    # Padding minimal
    header = mz + b"\x00" * 58 + struct.pack("<I", 64)
    pe_sig  = b"PE\x00\x00"

    # Strings que YARA cherche dans Bubble_Shield_Memory_Injection
    suspicious_strings = (
        b"VirtualAllocEx\x00"
        b"WriteProcessMemory\x00"
        b"CreateRemoteThread\x00"
        b"KERBEROS_PENTEST_TEST_DLL\x00"
        b"This DLL is a test payload - inoffensif\x00"
    )

    # DLL Export table fake (nom de la DLL suspect)
    exports = f"{name}\x00FakeExport1\x00FakeExport2\x00".encode()

    return header + pe_sig + b"\x00" * 200 + suspicious_strings + exports


def _create_injection_script():
    """Crée un script avec les API Windows d'injection (YARA Bubble_Shield)"""
    content = '''#!/usr/bin/env python3
# KERBEROS PENTEST TEST — Signatures injection DLL (inoffensif)
# Contient les appels API Windows que guard_dll_shield.py surveille

import ctypes  # import réel mais fonctions jamais appelées

# YARA $inject1 : "VirtualAllocEx"
# YARA $inject2 : "WriteProcessMemory"
# YARA $inject3 : "CreateRemoteThread"
# Ces fonctions sont référencées mais JAMAIS appelées

FAKE_INJECTION_CODE = """
# Simulation d'injection DLL classique :
# 1. VirtualAllocEx(hProcess, NULL, size, MEM_COMMIT, PAGE_EXECUTE_READWRITE)
# 2. WriteProcessMemory(hProcess, remote_addr, dll_path, len, None)
# 3. CreateRemoteThread(hProcess, None, 0, LoadLibraryA, remote_addr, 0, None)
# → guard_dll_shield.py MODULE 5 doit détecter la région RWX
"""

# YARA $target_proc1 : "lsass.exe"
FAKE_TARGET = "lsass.exe"  # string présente mais processus jamais ouvert

# Phantom DLL — référence à une DLL absente
PHANTOM_DLL = "WindowsCodecs_KERBEROS_TEST.dll"

def fake_hijack_info():
    return {
        "technique":   "DLL Hijacking",
        "target_dll":  PHANTOM_DLL,
        "target_proc": FAKE_TARGET,
        "status":      "SIMULATION ONLY — KERBEROS PENTEST TEST"
    }

if __name__ == "__NEVER__":
    print(fake_hijack_info())
'''
    f = _OUT_DIR / "fake_dll_injection.py"
    f.write_text(content, encoding="utf-8")
    return f


def _scan_hijackable_dlls() -> list:
    """
    Scanne le PATH actuel pour trouver des opportunités réelles de DLL hijacking.
    Retourne la liste des DLL manquantes dans les dossiers PATH.
    Inoffensif — lecture seule.
    """
    # DLL Windows couramment hijackées (phantom DLL bien connues)
    phantom_dlls = [
        "WindowsCodecs.dll",
        "wlidprov.dll",
        "WINMM.dll",
        "WINHTTP.dll",
        "cryptsp.dll",
        "dpapi.dll",
    ]

    vulnerable = []
    if platform.system() != "Windows":
        return []

    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for dll_name in phantom_dlls:
        for dir_str in path_dirs[:10]:  # Limiter aux 10 premiers dossiers
            dir_path = Path(dir_str)
            if dir_path.exists() and not (dir_path / dll_name).exists():
                # Cette DLL est absente dans ce dossier PATH
                vulnerable.append({
                    "dll":    dll_name,
                    "path":   str(dir_path),
                    "risk":   "Un attaquant pourrait placer une fausse DLL ici",
                })
                break

    return vulnerable


def run(target: str = "127.0.0.1", callback=None) -> dict:
    global _running
    _running = True
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {"module": MODULE_NAME, "target": target,
               "started": datetime.now().isoformat(),
               "events": [], "files": [], "status": "running"}

    def log(msg):
        results["events"].append(msg)
        if callback: callback(msg)

    log("🔧 Démarrage simulation DLL Hijacking...")

    # ── Test 1 : Fausse DLL avec signatures YARA ─────────────────────────
    time.sleep(0.2)
    for dll_name in ["fake_WindowsCodecs.dll", "fake_WINMM.dll", "fake_wlidprov.dll"]:
        if not _running:
            break
        f = _OUT_DIR / dll_name
        f.write_bytes(_build_fake_pe_dll(dll_name))
        results["files"].append(str(f))
        log(f"✅ Créé : {f.name} (MZ header + VirtualAllocEx + CreateRemoteThread)")
        time.sleep(0.1)
    log("   → YARA doit détecter : Bubble_Shield_Memory_Injection")

    # ── Test 2 : Script injection ─────────────────────────────────────────
    time.sleep(0.2)
    f2 = _create_injection_script()
    results["files"].append(str(f2))
    log(f"✅ Créé : {f2.name}")
    log("   → YARA $inject1/$inject2/$inject3 + $target_proc1 lsass.exe")

    # ── Test 3 : Faux OCX non signé ───────────────────────────────────────
    time.sleep(0.2)
    f3 = _OUT_DIR / "fake_unsigned.ocx"
    f3.write_bytes(b"MZ" + b"\x00" * 100 +
                   b"KERBEROS_PENTEST_OCX_TEST\x00" +
                   b"ActiveX_Fake_Component\x00")
    results["files"].append(str(f3))
    log(f"✅ Créé : {f3.name} (faux OCX non signé)")
    log("   → guard_dll_shield.py MODULE 3 doit détecter : OCX non signé")

    # ── Test 4 : Scan phantom DLL (Windows uniquement) ───────────────────
    time.sleep(0.2)
    if platform.system() == "Windows":
        log("🔍 Scan des phantom DLL dans le PATH...")
        vulns = _scan_hijackable_dlls()
        if vulns:
            for v in vulns[:5]:
                log(f"  ⚠️ Phantom DLL : {v['dll']} absent dans {v['path']}")
            log(f"   → {len(vulns)} opportunité(s) de hijacking détectées")
            results["phantom_dlls"] = vulns
        else:
            log("   ✅ Aucune phantom DLL évidente trouvée")
    else:
        log("ℹ️  Scan phantom DLL — Windows uniquement (ignoré sur Linux/Mac)")

    log(f"📊 {len(results['files'])} fichier(s) DLL suspects créés")
    log("⏳ En attente détection par guard_dll_shield.py + guard_yara.py...")

    results["status"] = "completed"
    results["finished"] = datetime.now().isoformat()
    _running = False
    return results


def stop():
    global _running
    _running = False


def get_info() -> dict:
    return {"name": MODULE_NAME, "label": MODULE_LABEL,
            "description": "Fausses DLL + signatures injection — inoffensif",
            "version": "1.0", "targets": ["guard_dll_shield.py", "guard_yara.py"]}
