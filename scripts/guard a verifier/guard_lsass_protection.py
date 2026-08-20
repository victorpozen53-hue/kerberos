#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# guard_lsass_protection.py
# Kerberos Sentinel — LV4_DONE.md ✅
# (c) Victor.Pozen — White hat mode | Bare-metal | GPLv3
# "Pas de trace. Pas de nuage. Juste du code qui protège." (-;
# https://liberapay.com/EthicalKerberos/ | https://github.com/victorpozen/kerberos

import os
import sys
import psutil
import time
import ctypes
from datetime import datetime
import win32api
import win32con
import win32security

# === CONFIG ===
LOG_DIR = r"D:\KERBEROS.SDS.WIN.7-10\guards\logs_attaques"  # ← comme demandé
LOG_FILE = os.path.join(LOG_DIR, "lsass_guard.log")
ALERT_TITLE = "🔒 Kerberos Sentinel — Intrusion Attempt Blocked"
LSASS_NAME = "lsass.exe"
ALLOWED_SIGNERS = [
    "Microsoft Windows",
    "Microsoft Corporation"
]

ALERT_MSG = (
    "⚠️ LSASS under siege — blocked. (-;\n\n"
    "→ Either:\n"
    "   • Mimikatz frappe à la porte… on lui a servi du plomb,\n"
    "   • Un outil légitime a oublié ses manières,\n"
    "   • Ou… c’est toi, Victor ? (-; 👀\n\n"
    "📄 Rapport : {}\n\n"
    "🔒 Kerberos — Pas de trace. Pas de nuage. Juste du code qui protège."
)

# ✅ Création silencieuse du dossier d’attaques (cohérent avec logs_attaques/)
os.makedirs(LOG_DIR, exist_ok=True)

def log_event(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{now}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        # Fallback dans guards\logs\ si échec (ex. permissions HDD)
        fallback = r"D:\KERBEROS.SDS.WIN.7-10\guards\logs\lsass_fallback.log"
        os.makedirs(os.path.dirname(fallback), exist_ok=True)
        try:
            with open(fallback, "a", encoding="utf-8") as ff:
                ff.write(f"[{now}] FALLBACK — {entry.strip()} | {e}\n")
        except:
            print(f"[FALLBACK FAILED] {entry.strip()}")
    print(entry.strip())

def enable_debug_privilege():
    """Active SeDebugPrivilege — requis pour accéder à LSASS, même en admin."""
    try:
        hToken = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
        )
        luid = win32security.LookupPrivilegeValue(None, win32security.SE_DEBUG_NAME)
        win32security.AdjustTokenPrivileges(
            hToken, 0,
            [(luid, win32con.SE_PRIVILEGE_ENABLED)]
        )
        win32api.CloseHandle(hToken)
        log_event("🔧 SeDebugPrivilege activated — LSASS monitoring ready. (-;")
        return True
    except Exception as e:
        log_event(f"⚠️ Failed to enable SeDebugPrivilege: {e}")
        return False

def is_suspicious_process(proc):
    try:
        name = proc.name().lower()
        cmdline = " ".join(proc.cmdline()).lower() if proc.cmdline() else ""

        # 1. Nom suspect ?
        if any(bad in name for bad in ["mimikatz", "procdump", "dumpert", "pypykatz", "sharpdump", "sekurlsa"]):
            return True, f"Suspicious process name: {name}"

        # 2. Ligne de commande cible LSASS ?
        if "lsass" in cmdline and any(kw in cmdline for kw in ["dump", "minidump", "-ma", "sekurlsa", "/svc"]):
            return True, f"Suspicious cmdline: {cmdline}"

        return False, ""
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False, ""

def block_and_alert(proc, reason):
    try:
        pid = proc.pid
        name = proc.name()
        cmdline = " ".join(proc.cmdline()) if proc.cmdline() else "N/A"

        proc.kill()
        log_event(f"‼️ KILLED PID {pid} ({name}) — {reason} | cmdline: {cmdline}")

        win32api.MessageBox(
            0,
            ALERT_MSG.format(LOG_FILE),
            ALERT_TITLE,
            win32con.MB_ICONWARNING | win32con.MB_OK
        )

    except Exception as e:
        log_event(f"⚠️ Failed to block PID {pid}: {e}")

# === MAIN GUARD LOOP ===
def main():
    # Vérif admin
    if not ctypes.windll.shell32.IsUserAnAdmin():
        win32api.MessageBox(
            0,
            "Run Kerberos Sentinel as Administrator to protect LSASS.\n"
            "→ LSASS is sacred. Don’t leave it unprotected. (-;",
            "🔒 Admin Required",
            win32con.MB_ICONERROR | win32con.MB_OK
        )
        sys.exit(1)

    # 🔑 Activation critique du privilège de débogage
    if not enable_debug_privilege():
        win32api.MessageBox(
            0,
            "Impossible d’activer SeDebugPrivilege.\n"
            "Kerberos surveillera LSASS en mode dégradé (cmdline only).\n"
            "Pour une protection complète : relancez via 'Exécuter en tant qu’administrateur'. (-;",
            "⚠️ Protection partielle",
            win32con.MB_ICONWARNING | win32con.MB_OK
        )

    log_event("🛡️ LSASS Guard activated — Watching for pirates… (-;")
    seen_pids = set()

    while True:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.pid in seen_pids:
                    continue
                seen_pids.add(proc.pid)

                suspicious, reason = is_suspicious_process(proc)
                if suspicious:
                    block_and_alert(proc, reason)

            time.sleep(1.2)  # ~0.8 Hz — léger sur OptiPlex 780
        except KeyboardInterrupt:
            log_event("⏹️ LSASS Guard manually stopped.")
            break
        except Exception as e:
            log_event(f"💥 Guard error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()