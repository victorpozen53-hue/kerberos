#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕵️ sim_anti_forensics — Simulation techniques anti-forensics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Génère signatures anti-forensics :
- Timestomp (modification timestamps)
- Secure wiping (overwriting)
- Log clearing (EventLog, bash_history)
- File carving evasion
- Artifact deletion (prefetch, shimcache)
AUCUNE modification réelle du système — signatures uniquement.
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import time
import json
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_anti_forensics"
MODULE_LABEL = "Anti-Forensics"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "anti_forensics"

def run(target: str = "127.0.0.1", callback=None) -> dict:
    global _running
    _running = True
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    
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
    
    log("🕵️ Démarrage simulation Anti-Forensics...")
    
    # ── Test 1 : Script timestomp ────────────────────────────────────
    time.sleep(0.2)
    f1 = _OUT_DIR / "fake_timestomp.py"
    f1.write_text(
        "#!/usr/bin/env python3\n"
        "# KERBEROS_PENTEST_TEST — timestomp inoffensif\n"
        "# YARA $timestomp1 : os.utime\n"
        "# YARA $timestomp2 : SetFileTime (via ctypes)\n"
        "\n"
        "import os\n"
        "from datetime import datetime\n"
        "\n"
        "def fake_timestomp(filepath: str):\n"
        "    # Modifier les timestamps d'un fichier\n"
        "    # fake_time = datetime(2020, 1, 1, 0, 0, 0).timestamp()  ' commenté\n"
        "    # os.utime(filepath, (fake_time, fake_time))  ' commenté\n"
        "    print(f'[FAKE] Timestomp simulé : {filepath}')\n"
        "\n"
        "# YARA $timestomp3 : $STANDARD_INFORMATION\n"
        "# YARA $timestomp4 : $FILE_NAME timestamp mismatch\n"
        "\n"
        "if __name__ == '__NEVER__':\n"
        "    fake_timestomp('C:\\\\test\\\\file.txt')\n"
        "    print('KERBEROS_PENTEST_TEST — simulation only')\n",
        encoding="utf-8"
    )
    results["files"].append(str(f1))
    log(f"✅ Créé : {f1.name}")
    log("   → YARA doit détecter : Timestomp_Script")
    
    # ── Test 2 : Script secure wipe ──────────────────────────────────
    time.sleep(0.2)
    f2 = _OUT_DIR / "fake_secure_wipe.py"
    f2.write_text(
        "#!/usr/bin/env python3\n"
        "# KERBEROS_PENTEST_TEST — secure wipe inoffensif\n"
        "# YARA $wipe1 : overwrite + random\n"
        "# YARA $wipe2 : multiple passes\n"
        "\n"
        "import os\n"
        "import secrets\n"
        "\n"
        "def fake_secure_wipe(filepath: str, passes: int = 3):\n"
        "    # Effacement sécurisé (multi-pass)\n"
        "    # file_size = os.path.getsize(filepath)  ' commenté\n"
        "    # for _ in range(passes):  ' commenté\n"
        "    #     with open(filepath, 'wb') as f:  ' commenté\n"
        "    #         f.write(secrets.token_bytes(file_size))  ' commenté\n"
        "    # os.remove(filepath)  ' commenté\n"
        "    print(f'[FAKE] Secure wipe simulé : {filepath} ({passes} passes)')\n"
        "\n"
        "# YARA $wipe3 : sdelete /cipher (Windows tools)\n"
        "# YARA $wipe4 : shred (Linux tool)\n"
        "\n"
        "if __name__ == '__NEVER__':\n"
        "    fake_secure_wipe('C:\\\\test\\\\sensitive.txt')\n"
        "    print('KERBEROS_PENTEST_TEST — simulation only')\n",
        encoding="utf-8"
    )
    results["files"].append(str(f2))
    log(f"✅ Créé : {f2.name}")
    log("   → YARA doit détecter : Secure_Wipe_Script")
    
    # ── Test 3 : Script log clearing ─────────────────────────────────
    time.sleep(0.2)
    f3 = _OUT_DIR / "fake_log_clear.py"
    f3.write_text(
        "#!/usr/bin/env python3\n"
        "# KERBEROS_PENTEST_TEST — log clearing inoffensif\n"
        "# YARA $logclear1 : wevtutil cl\n"
        "# YARA $logclear2 : Clear-EventLog\n"
        "# YARA $logclear3 : bash_history\n"
        "\n"
        "import subprocess\n"
        "import os\n"
        "\n"
        "def fake_clear_event_logs():\n"
        "    # Windows EventLog clearing\n"
        "    # logs = ['Security', 'System', 'Application']  ' commenté\n"
        "    # for log in logs:  ' commenté\n"
        "    #     subprocess.run(['wevtutil', 'cl', log])  ' commenté\n"
        "    # subprocess.run(['powershell', '-c', 'Clear-EventLog -LogName *'])  ' commenté\n"
        "    print('[FAKE] EventLog clearing simulé')\n"
        "\n"
        "def fake_clear_bash_history():\n"
        "    # Linux bash_history clearing\n"
        "    # os.remove(os.path.expanduser('~/.bash_history'))  ' commenté\n"
        "    # subprocess.run(['history', '-c'])  ' commenté\n"
        "    print('[FAKE] bash_history clearing simulé')\n"
        "\n"
        "# YARA $logclear4 : .bash_history + unlink\n"
        "# YARA $logclear5 : EventLog + Clear\n"
        "\n"
        "if __name__ == '__NEVER__':\n"
        "    fake_clear_event_logs()\n"
        "    fake_clear_bash_history()\n"
        "    print('KERBEROS_PENTEST_TEST — simulation only')\n",
        encoding="utf-8"
    )
    results["files"].append(str(f3))
    log(f"✅ Créé : {f3.name}")
    log("   → YARA doit détecter : Log_Clearing_Script")
    
    # ── Test 4 : Artifact deletion ───────────────────────────────────
    time.sleep(0.2)
    f4 = _OUT_DIR / "fake_artifact_deletion.py"
    f4.write_text(
        "#!/usr/bin/env python3\n"
        "# KERBEROS_PENTEST_TEST — artifact deletion inoffensif\n"
        "# YARA $artifact1 : prefetch + delete\n"
        "# YARA $artifact2 : shimcache + delete\n"
        "# YARA $artifact3 : amcache + delete\n"
        "\n"
        "import os\n"
        "import glob\n"
        "\n"
        "def fake_delete_prefetch():\n"
        "    # Delete Windows Prefetch files\n"
        "    # prefetch_path = 'C:\\\\Windows\\\\Prefetch\\\\*.pf'  ' commenté\n"
        "    # for f in glob.glob(prefetch_path):  ' commenté\n"
        "    #     os.remove(f)  ' commenté\n"
        "    print('[FAKE] Prefetch deletion simulé')\n"
        "\n"
        "def fake_delete_shimcache():\n"
        "    # Delete ShimCache artifact\n"
        "    # registry_path = 'HKLM\\\\SYSTEM\\\\CurrentControlSet\\\\Control\\\\Session Manager\\\\AppCompatCache'  ' commenté\n"
        "    print('[FAKE] ShimCache deletion simulé')\n"
        "\n"
        "# YARA $artifact4 : usnjrnl + delete\n"
        "# YARA $artifact5 : SRUM + delete\n"
        "\n"
        "if __name__ == '__NEVER__':\n"
        "    fake_delete_prefetch()\n"
        "    fake_delete_shimcache()\n"
        "    print('KERBEROS_PENTEST_TEST — simulation only')\n",
        encoding="utf-8"
    )
    results["files"].append(str(f4))
    log(f"✅ Créé : {f4.name}")
    log("   → YARA doit détecter : Artifact_Deletion_Script")
    
    # ── Test 5 : Config JSON campagne anti-forensics ─────────────────
    time.sleep(0.2)
    f5 = _OUT_DIR / "fake_anti_forensics_config.json"
    config = {
        "campaign":    "KERBEROS_PENTEST_TEST",
        "techniques":  ["timestomp", "secure_wipe", "log_clearing", "artifact_deletion"],
        "targets":     ["EventLog", "Prefetch", "ShimCache", "AmCache", "SRUM", "USNJRNL"],
        "tools":       ["wevtutil", "sdelete", "cipher", "shred", "bleachbit"],
        "evasion":     ["timestamp_manipulation", "file_carving_evasion", "metadata_stripping"],
        "note":        "Simulation inoffensive — aucune modification réelle du système"
    }
    f5.write_text(json.dumps(config, indent=2), encoding="utf-8")
    results["files"].append(str(f5))
    log(f"✅ Créé : {f5.name}")
    log("   → YARA : Anti_Forensics_Config_Pattern")
    
    log(f"📊 {len(results['files'])} fichier(s) anti-forensics créés")
    log("⏳ En attente détection par guard_yara.py + guard_integrity_check.py...")
    
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
        "description": "Génère signatures anti-forensics — aucune modification système",
        "version":     "1.0",
        "targets":     ["guard_yara.py", "guard_integrity_check.py"],
    }

if __name__ == "__main__":
    result = run()
    print(f"✅ {len(result['files'])} fichiers créés")