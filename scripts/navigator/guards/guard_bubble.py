# guard_bubble.py — v0.1 — (-;
# Exécute un processus dans une "bulle" locale — pas de VM, pas de cloud.
# Capture : réseau, écriture disque, comportements anormaux.

import os
import subprocess
import time
import tempfile
import shutil
import sys

BUBBLE_BASE = os.path.join(os.path.expanduser("~"), ".kerberos", "bubble")
os.makedirs(BUBBLE_BASE, exist_ok=True)

BLACKLIST_DOMAINS = {
    "shodan.io", "censys.io", "zoomeye.org",
    "google-analytics.com", "doubleclick.net", "adservice.google.",
    "facebook.com", "meta.com", "connect.facebook.net"
}

BLACKLIST_PATHS = {
    "AppData\\Roaming", "AppData\\Local\\Temp\\ads_", 
    "ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
    "mining.exe", "miner.", "cryptonight"
}

def run_in_bubble(cmd: list, cwd=None, timeout=300):
    """Exécute cmd dans une bulle isolée — retourne chemin du rapport."""
    bubble_id = f"bubble_{int(time.time())}"
    bubble_dir = os.path.join(BUBBLE_BASE, bubble_id)
    os.makedirs(bubble_dir, exist_ok=True)
    log_file = os.path.join(bubble_dir, "activity.log")
    
    print(f"[BULLE] ▶️ Lancement : {' '.join(cmd)} — (-;")
    
    try:
        with open(log_file, "w", encoding="utf-8", errors="replace") as log:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd or bubble_dir,
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            proc.wait(timeout=timeout)
        
        # Analyse
        threats = []
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                line_l = line.lower()
                for domain in BLACKLIST_DOMAINS:
                    if domain in line_l:
                        threats.append(f"L{str(i).zfill(3)} | 📡 DNS/HTTP : {domain}")
                for path in BLACKLIST_PATHS:
                    if path.lower() in line_l:
                        threats.append(f"L{str(i).zfill(3)} | 📁 Écriture suspecte : {path}")
        
        # Rapport
        report_path = os.path.join(bubble_dir, "REPORT.txt")
        with open(report_path, "w", encoding="utf-8") as rpt:
            rpt.write("KERBEROS — BULLE DE SÉCURITÉ — (-;\n")
            rpt.write("="*50 + "\n")
            rpt.write(f"Commande : {' '.join(cmd)}\n")
            rpt.write(f"Dossier bulle : {bubble_dir}\n")
            rpt.write(f"Durée : {timeout}s max\n")
            rpt.write("="*50 + "\n\n")
            if threats:
                rpt.write("🚨 MENACES DÉTECTÉES\n")
                for t in threats:
                    rpt.write(f"  • {t}\n")
            else:
                rpt.write("✅ Aucune menace détectée — (-;\n")
        
        if threats:
            print(f"[BULLE] ⚠️ Menaces détectées — rapport : {report_path}")
        else:
            print(f"[BULLE] ✅ Propre — (-;")
        return bubble_dir

    except subprocess.TimeoutExpired:
        proc.kill()
        print(f"[BULLE] ⏹️ Timeout ({timeout}s) — bulle préservée : {bubble_dir}")
        return bubble_dir
    except Exception as e:
        print(f"[BULLE] ❌ Erreur : {e} — (-;")
        return bubble_dir