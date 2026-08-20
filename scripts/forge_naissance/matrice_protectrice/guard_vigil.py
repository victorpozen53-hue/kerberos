# guard_vigil.py — Kerberos v1.0 — GPLv3
# 👁️ Veille systémique ciblée : scan des DLL dans les processus critiques
# White hat only. Pas de trace. Pas de nuage. (-;

import json
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
LOG_FILE = KERBEROS_ROOT / "logs" / "vigil.log"
LOG_X_FILE.mkdir(exist_ok=True)

def _log(msg: str, level="INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:% S UTC")
    line = f"[{ts}] [{level}] {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if __name__ == "__main__":
        print(line)

# Whitelist par processus (minimale, réaliste Win7)
CRITICAL_PROCESSES = {
    "explorer.exe": {"kernel32.dll", "user32.dll", "shell32.dll", "shlwapi.dll"},
    "svchost.exe": {"kernel32.dll", "ntdll.dll", "rpcrt4.dll", "advapi32.dll"},
    "powershell.exe": {"kernel32.dll", "ntdll.dll", "clr.dll", "mscoree.dll"},
    "cmd.exe": {"kernel32.dll", "ntdll.dll", "cmdext.dll"},
    "winlogon.exe": {"kernel32.dll", "ntdll.dll", "user32.dll", "winlogon.exe"},
    "lsass.exe": {"kernel32.dll", "ntdll.dll", "advapi32.dll"},  # lecture limitée
}

def scan_critical_processes():
    """Scan only high-risk processes for unauthorized DLLs."""
    threats = []
    scanned = 0

    for proc in psutil.process_iter(['pid', 'name']):
        name = proc.info['name'].lower()
        if name in CRITICAL_PROCESSES:
            scanned += 1
            try:
                loaded_dlls = set()
                for mmap in proc.memory_maps(grouped=False):
                    if mmap.path and mmap.path.lower().endswith('.dll'):
                        loaded_dlls.add(Path(mmap.path).name.lower())

                allowed = CRITICAL_PROCESSES[name]
                unauthorized = loaded_dlls - allowed
                # Filtrer les artefacts Windows
                unauthorized = {dll for dll in unauthorized if not dll.startswith(("api-ms-", "ext-ms-", "iertutil"))}

                if unauthorized:
                    threats.append({
                        "pid": proc.info['pid'],
                        "process": name,
                        "unauthorized_dlls": list(unauthorized)
                    })
                    _log(f"🚨 {name} (PID {proc.info['pid']}) : DLL non autorisées → {', '.join(unauthorized)}", "ALERT")
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue  # silencieux

    return {
        "scanned_processes": scanned,
        "threats": threats,
        "total_threats": len(threats)
    }

def run(dry_run=False):
    _log("👁️ GUARD VIGIL — veille sur processus critiques…", "INFO")
    report = scan_critical_processes()

    if report["total_threats"] > 0:
        try:
            from kerberos import _show_nag, _set_tray_state
            _set_tray_state("alert")
            _show_nag("👁️ Vigil Alert", f"{report['total_threats']} processus(s) avec DLL suspectes.")
        except:
            pass

    return {
        "guard": "vigil",
        "status": "alert" if report["total_threats"] > 0 else "clean",
        "scanned_processes": report["scanned_processes"],
        "threats": report["threats"]
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("👁️ GUARD VIGIL — Veille systémique ciblée")
    print("White hat • Local only • GPLv3 • (-;")
    print("="*60 + "\n")
    res = run()
    print(f"📊 Processus scannés : {res['scanned_processes']}")
    print(f"🚨 Menaces détectées : {res['total_threats']}")
    if res["threats"]:
        for t in res["threats"]:
            print(f"  - {t['process']} (PID {t['pid']}) → {', '.join(t['unauthorized_dlls'])}")
    print(f"\n🩺 Logs : logs/vigil.log")
    input("\n✅ Appuyez sur Entrée pour quitter.")