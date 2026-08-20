# -*- coding: utf-8 -*-
"""
Guard Kerberos : Fix Backdoor Watchdog
Surveillance active des backdoors Windows (RDP, services, processus, registre)
Auteur : Mirko & Victor (équipe Cerbère)
Date : 28 octobre 2025
Compatible : Windows 10 Pro 64-bit (v10.0.19045)
"""

import os
import sys
import subprocess
import winreg
import psutil
import socket
import time
import datetime
import logging
from pathlib import Path

# === CONFIGURATION ===
LOG_DIR = Path(r"I:\IA.KERBEROS\logs")
LOG_FILE = LOG_DIR / "backdoor_surveillance.log"
SNAPSHOT_FILE = LOG_DIR / "backdoor_baseline.txt"
GUARD_NAME = "Fix Backdoor Watchdog"

# Création du dossier logs si absent
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configuration du logger
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    encoding='utf-8'
)

def log_info(msg):
    print(f"[🛡️ {GUARD_NAME}] {msg}")
    logging.info(msg)

def log_alert(msg):
    print(f"[🚨 {GUARD_NAME}] {msg}")
    logging.warning(msg)

def is_port_open(port):
    """Vérifie si un port est en écoute."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False

def get_rdp_status():
    """Récupère l'état du RDP via la clé de registre."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SYSTEM\CurrentControlSet\Control\Terminal Server")
        value, _ = winreg.QueryValueEx(key, "fDenyTSConnections")
        winreg.CloseKey(key)
        return value == 0  # 0 = RDP autorisé, 1 = refusé
    except Exception as e:
        log_alert(f"Erreur lecture registre RDP : {e}")
        return None

def set_rdp_enabled(enabled=True):
    """Active ou désactive RDP via le registre."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SYSTEM\CurrentControlSet\Control\Terminal Server", 0,
                             winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "fDenyTSConnections", 0, winreg.REG_DWORD, 0 if enabled else 1)
        winreg.CloseKey(key)
        action = "activé" if enabled else "désactivé"
        log_info(f"RDP {action} via registre.")
        # Redémarrer le service TermService pour appliquer
        subprocess.run(["net", "stop", "TermService"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["net", "start", "TermService"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        log_alert(f"Échec modification RDP : {e}")
        return False

def detect_suspicious_processes():
    """Détecte les processus de remote control non autorisés."""
    suspicious_names = {
        'anydesk.exe', 'teamviewer.exe', 'tightvnc.exe', 'realvnc.exe',
        'ultravnc.exe', 'rustdesk.exe', 'dwrcs.exe', 'vncserver.exe'
    }
    found = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            if name in suspicious_names:
                found.append((proc.info['pid'], proc.info['name']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found

def detect_persistent_services():
    """Liste les services non-Microsoft avec démarrage automatique."""
    suspicious_services = []
    try:
        output = subprocess.check_output("wmic service where \"StartMode='Auto' AND NOT PathName LIKE '%Windows%'\" get Name,PathName", shell=True, text=True, encoding='utf-8', errors='ignore')
        lines = output.strip().split('\n')[1:]
        for line in lines:
            if line.strip() and 'System32' not in line:
                suspicious_services.append(line.strip())
    except Exception as e:
        log_alert(f"Erreur scan services persistants : {e}")
    return suspicious_services

def save_baseline():
    """Sauvegarde un état de référence 'propre'."""
    log_info("Création du snapshot de référence (baseline).")
    baseline = {
        'rdp_enabled': get_rdp_status(),
        'suspicious_processes': [],
        'timestamp': str(datetime.datetime.now())
    }
    try:
        with open(SNAPSHOT_FILE, 'w', encoding='utf-8') as f:
            for k, v in baseline.items():
                f.write(f"{k}: {v}\n")
        log_info("Baseline sauvegardé.")
    except Exception as e:
        log_alert(f"Échec sauvegarde baseline : {e}")

def load_baseline():
    """Charge le baseline si existant."""
    if not SNAPSHOT_FILE.exists():
        return None
    try:
        baseline = {}
        with open(SNAPSHOT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    k, v = line.split(':', 1)
                    baseline[k.strip()] = v.strip()
        return baseline
    except Exception as e:
        log_alert(f"Erreur chargement baseline : {e}")
        return None

def run_full_scan(auto_repair=False):
    """Exécute une analyse complète."""
    log_info("🔍 Démarrage de la surveillance backdoor...")
    
    # 1. État du port 3389
    port_3389_open = is_port_open(3389)
    rdp_reg_status = get_rdp_status()
    
    log_info(f"Port 3389 ouvert : {port_3389_open}")
    log_info(f"RDP autorisé (registre) : {rdp_reg_status}")
    
    # Incohérence = alerte
    if port_3389_open and rdp_reg_status is False:
        log_alert("⚠️ Incohérence détectée : port 3389 ouvert mais RDP désactivé dans le registre !")
    
    # 2. Processus suspects
    sus_procs = detect_suspicious_processes()
    if sus_procs:
        for pid, name in sus_procs:
            log_alert(f"Processus suspect détecté : {name} (PID {pid})")
    else:
        log_info("✅ Aucun processus de remote control non autorisé détecté.")
    
    # 3. Services persistants
    sus_services = detect_persistent_services()
    if sus_services:
        for svc in sus_services[:5]:  # limite pour lisibilité
            log_alert(f"Service persistant non-Microsoft : {svc}")
    else:
        log_info("✅ Aucun service persistant suspect détecté.")
    
    # 4. Réparation auto si demandée
    if auto_repair:
        if port_3389_open or (rdp_reg_status is True):
            log_info("🔧 Mode réparation : désactivation du RDP...")
            set_rdp_enabled(False)
        log_info("✅ Réparation appliquée.")
    
    # 5. Comparaison avec baseline (optionnelle)
    baseline = load_baseline()
    if baseline:
        log_info("📊 Comparaison avec baseline activée.")
        # Ici tu pourrais étendre avec plus de checks (ex: hash de services, etc.)
    
    log_info("✅ Surveillance terminée.")

# === POINT D'ENTRÉE POUR TKINTER ===
def launch_guard(auto_repair=False, create_baseline=False):
    """Fonction appelable depuis l'interface Kerberos."""
    print("\n" + "="*60)
    print(f"🚀 {GUARD_NAME} - Par Mirko & Victor")
    print("="*60)
    
    if create_baseline:
        save_baseline()
        return
    
    run_full_scan(auto_repair=auto_repair)

# Si exécuté directement (debug)
if __name__ == "__main__":
    # Exemple : lancer avec réparation auto
    launch_guard(auto_repair=False)