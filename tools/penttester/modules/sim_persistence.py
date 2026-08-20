#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔁 sim_persistence — Simulation mécanismes persistence
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Génère signatures persistence courantes :
- Registry Run keys
- Scheduled tasks
- Startup folder shortcuts
- Service creation
- WMI event subscriptions
AUCUNE modification réelle du système.
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import time
import json
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_persistence"
MODULE_LABEL = "Persistence"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "persistence"

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
    
    log("🔁 Démarrage simulation Persistence...")
    
    # ── Test 1 : Registry Run key ────────────────────────────────────
    time.sleep(0.2)
    f1 = _OUT_DIR / "fake_registry_persistence.reg.txt"
    f1.write_text(
        "Windows Registry Editor Version 5.00\n"
        "\n"
        "[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run]\n"
        "\"KerberosTest\"=\"C:\\\\Users\\\\victim\\\\AppData\\\\Roaming\\\\malware.exe\"\n"
        "\n"
        "[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce]\n"
        "\"UpdateCheck\"=\"powershell.exe -enc KERBEROS_PENTEST_TEST\"\n"
        "\n"
        "-- YARA $persist1 : Registry Run key\n"
        "-- YARA $persist2 : Hidden startup entry\n"
        "-- KERBEROS_PENTEST_TEST\n",
        encoding="utf-8"
    )
    results["files"].append(str(f1))
    log(f"✅ Créé : {f1.name}")
    log("   → YARA doit détecter : Registry_Persistence_Pattern")
    
    # ── Test 2 : Scheduled task ──────────────────────────────────────
    time.sleep(0.2)
    f2 = _OUT_DIR / "fake_scheduled_task.xml"
    f2.write_text(
        "<?xml version='1.0'?>\n"
        "<Task version='1.2'>\n"
        "  <RegistrationInfo>\n"
        "    <URI>\\KERBEROS_PENTEST_TEST\\UpdateTask</URI>\n"
        "  </RegistrationInfo>\n"
        "  <Triggers>\n"
        "    <CalendarTrigger>\n"
        "      <StartBoundary>2026-03-02T00:00:00</StartBoundary>\n"
        "      <Enabled>true</Enabled>\n"
        "    </CalendarTrigger>\n"
        "  </Triggers>\n"
        "  <Actions>\n"
        "    <Exec>\n"
        "      <Command>powershell.exe</Command>\n"
        "      <Arguments>-windowstyle hidden -enc KERBEROS_PENTEST_TEST</Arguments>\n"
        "    </Exec>\n"
        "  </Actions>\n"
        "  <!-- YARA $persist3 : Scheduled task with hidden window -->\n"
        "  <!-- KERBEROS_PENTEST_TEST -->\n"
        "</Task>\n",
        encoding="utf-8"
    )
    results["files"].append(str(f2))
    log(f"✅ Créé : {f2.name}")
    log("   → YARA doit détecter : Scheduled_Task_Persistence")
    
    # ── Test 3 : Startup folder shortcut ─────────────────────────────
    time.sleep(0.2)
    f3 = _OUT_DIR / "fake_startup_shortcut.txt"
    f3.write_text(
        "Shortcut Properties (simulated)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Target: C:\\Users\\victim\\AppData\\Roaming\\malware.exe\n"
        "Location: Startup\n"
        "Hidden: Yes\n"
        "Run: Minimized\n"
        "\n"
        "-- YARA $persist4 : Startup folder + hidden\n"
        "-- guard_frog_toxic.py doit détecter : .exe dans Startup\n"
        "-- KERBEROS_PENTEST_TEST\n",
        encoding="utf-8"
    )
    results["files"].append(str(f3))
    log(f"✅ Créé : {f3.name}")
    log("   → guard_frog_toxic.py + YARA : Startup_Persistence")
    
    # ── Test 4 : Service creation ────────────────────────────────────
    time.sleep(0.2)
    f4 = _OUT_DIR / "fake_service_creation.bat.txt"
    f4.write_text(
        "@echo off\n"
        "REM KERBEROS_PENTEST_TEST — simulation uniquement\n"
        "sc create KerberosTest binPath= \"C:\\malware.exe\" start= auto\n"
        "sc start KerberosTest\n"
        "\n"
        "REM YARA $persist5 : sc create + malicious path\n"
        "REM guard_vigil.py doit détecter : service creation suspect\n",
        encoding="utf-8"
    )
    results["files"].append(str(f4))
    log(f"✅ Créé : {f4.name}")
    log("   → YARA + guard_vigil.py : Service_Persistence")
    
    # ── Test 5 : WMI event subscription ──────────────────────────────
    time.sleep(0.2)
    f5 = _OUT_DIR / "fake_wmi_persistence.ps1.txt"
    f5.write_text(
        "# KERBEROS_PENTEST_TEST — simulation uniquement\n"
        "# WMI Event Subscription for persistence\n"
        "\n"
        "$filterName = 'KERBEROS_Test_Filter'\n"
        "$consumerName = 'KERBEROS_Test_Consumer'\n"
        "\n"
        "# YARA $persist6 : WMI __EventFilter + __EventConsumer\n"
        "# YARA $persist7 : CommandLineEventConsumer\n"
        "\n"
        "Write-Host 'KERBEROS_PENTEST_TEST — WMI persistence simulation'\n",
        encoding="utf-8"
    )
    results["files"].append(str(f5))
    log(f"✅ Créé : {f5.name}")
    log("   → YARA : WMI_Persistence_Pattern")
    
    # ── Test 6 : JSON config campagne persistence ────────────────────
    time.sleep(0.2)
    f6 = _OUT_DIR / "fake_persistence_config.json"
    config = {
        "campaign":      "KERBEROS_PENTEST_TEST",
        "methods":       ["registry", "scheduled_task", "startup", "service", "wmi"],
        "target_system": "Windows 10/11",
        "evasion":       ["hidden_window", "encoded_command", "legitimate_name"],
        "note":          "Simulation inoffensive — aucune modification réelle"
    }
    f6.write_text(json.dumps(config, indent=2), encoding="utf-8")
    results["files"].append(str(f6))
    log(f"✅ Créé : {f6.name}")
    log("   → YARA : Persistence_Campaign_Config")
    
    log(f"📊 {len(results['files'])} fichier(s) persistence créés")
    log("⏳ En attente détection par guard_yara.py + guard_vigil.py + guard_frog_toxic.py...")
    
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
        "description": "Génère signatures persistence — aucune modification système",
        "version":     "1.0",
        "targets":     ["guard_yara.py", "guard_vigil.py", "guard_frog_toxic.py"],
    }

if __name__ == "__main__":
    result = run()
    print(f"✅ {len(result['files'])} fichiers créés")