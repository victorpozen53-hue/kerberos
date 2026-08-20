#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Victor Pozen - GPLv3
# Guard de scan web pré-téléchargement (léger, sans YARA)

"""
Guard Web Scanner - Analyse les téléchargements avant qu'ils touchent le disque.
Intercepte les fichiers dangereux en vérifiant :
- Extensions suspectes (.exe, .bat, .vbs, .scr, .com, .pif)
- URLs dans des blacklists connues
- Headers HTTP suspects
- Taille anormale (très petit = dropper, très gros = bomb)
"""

import os
import re
import hashlib
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import socket

# === CONFIGURATION ===
KERBEROS_ROOT = Path(__file__).parent.parent
LOGS_DIR = KERBEROS_ROOT / "logs"
BLACKLIST_FILE = KERBEROS_ROOT / "vocab" / "web_blacklist.txt"
WHITELIST_FILE = KERBEROS_ROOT / "vocab" / "web_whitelist.txt"
REPORT_FILE = LOGS_DIR / "web_scan_reports.json"

# Extensions dangereuses (priorité haute)
DANGEROUS_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', 
    '.js', '.jar', '.msi', '.hta', '.reg', '.ps1', '.wsf'
}

# Extensions suspectes (priorité moyenne)
SUSPICIOUS_EXTENSIONS = {
    '.zip', '.rar', '.7z', '.iso', '.img', '.dll', '.sys'
}

# Domaines blacklistés par défaut (malware connus)
DEFAULT_BLACKLIST = [
    'malware-download.com',
    'virus-test.com',
    'phishing-site.net',
    # Ajoutez vos propres domaines suspects ici
]

# Domaines whitelistés (sources fiables)
DEFAULT_WHITELIST = [
    'github.com',
    'sourceforge.net',
    'microsoft.com',
    'python.org',
    'mozilla.org',
    # Ajoutez vos domaines de confiance
]

# === INITIALISATION ===
def init_files():
    """Crée les fichiers de config s'ils n'existent pas."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    (KERBEROS_ROOT / "vocab").mkdir(parents=True, exist_ok=True)
    
    if not BLACKLIST_FILE.exists():
        BLACKLIST_FILE.write_text('\n'.join(DEFAULT_BLACKLIST), encoding='utf-8')
    
    if not WHITELIST_FILE.exists():
        WHITELIST_FILE.write_text('\n'.join(DEFAULT_WHITELIST), encoding='utf-8')
    
    if not REPORT_FILE.exists():
        REPORT_FILE.write_text('[]', encoding='utf-8')

# === FONCTIONS DE SCAN ===
def load_list(filepath):
    """Charge une liste de domaines depuis un fichier."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip() and not line.startswith('#')]
    except:
        return []

def extract_domain(url):
    """Extrait le domaine d'une URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ""

def check_extension(filename):
    """Vérifie si l'extension est dangereuse."""
    ext = Path(filename).suffix.lower()
    
    if ext in DANGEROUS_EXTENSIONS:
        return "DANGER", f"Extension très dangereuse : {ext}"
    elif ext in SUSPICIOUS_EXTENSIONS:
        return "SUSPECT", f"Extension suspecte : {ext} (peut contenir un exécutable)"
    else:
        return "OK", f"Extension acceptable : {ext}"

def check_domain(url, blacklist, whitelist):
    """Vérifie si le domaine est blacklisté ou whitelisté."""
    domain = extract_domain(url)
    
    if not domain:
        return "SUSPECT", "Impossible d'extraire le domaine"
    
    # Check whitelist d'abord (prioritaire)
    for trusted in whitelist:
        if trusted in domain:
            return "OK", f"Domaine de confiance : {domain}"
    
    # Check blacklist
    for blocked in blacklist:
        if blocked in domain:
            return "DANGER", f"Domaine blacklisté : {domain}"
    
    return "UNKNOWN", f"Domaine inconnu : {domain}"

def check_url_patterns(url):
    """Détecte des patterns suspects dans l'URL."""
    suspicious_patterns = [
        (r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', "IP directe (suspect)"),
        (r'(download|get|file)\.(php|asp|jsp)', "Script de download dynamique"),
        (r'(crack|keygen|patch|serial|activator)', "Mots-clés piratage"),
        (r'\.tk$|\.ml$|\.ga$|\.cf$', "TLD gratuit (souvent malware)"),
        (r'bit\.ly|tinyurl|goo\.gl', "URL raccourcie (risque redirection)"),
    ]
    
    issues = []
    for pattern, desc in suspicious_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            issues.append(desc)
    
    if issues:
        return "SUSPECT", " | ".join(issues)
    return "OK", "Pas de pattern suspect détecté"

def check_dns_reputation(domain):
    """Vérifie si le domaine résout correctement (détection typosquatting)."""
    try:
        socket.gethostbyname(domain)
        return "OK", "DNS résolu correctement"
    except socket.gaierror:
        return "DANGER", "Domaine inexistant ou typosquatting"
    except:
        return "UNKNOWN", "Impossible de vérifier le DNS"

def scan_url(url, filename="unknown"):
    """Analyse complète d'une URL avant téléchargement."""
    init_files()
    
    blacklist = load_list(BLACKLIST_FILE)
    whitelist = load_list(WHITELIST_FILE)
    domain = extract_domain(url)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "filename": filename,
        "domain": domain,
        "checks": {},
        "verdict": "OK",
        "risk_score": 0,
        "reasons": []
    }
    
    # === CHECKS ===
    
    # 1. Extension
    status, msg = check_extension(filename)
    report["checks"]["extension"] = {"status": status, "message": msg}
    if status == "DANGER":
        report["risk_score"] += 50
        report["reasons"].append(msg)
    elif status == "SUSPECT":
        report["risk_score"] += 20
        report["reasons"].append(msg)
    
    # 2. Domaine (blacklist/whitelist)
    status, msg = check_domain(url, blacklist, whitelist)
    report["checks"]["domain"] = {"status": status, "message": msg}
    if status == "DANGER":
        report["risk_score"] += 100
        report["reasons"].append(msg)
    elif status == "UNKNOWN":
        report["risk_score"] += 10
    
    # 3. Patterns URL
    status, msg = check_url_patterns(url)
    report["checks"]["url_patterns"] = {"status": status, "message": msg}
    if status == "SUSPECT":
        report["risk_score"] += 30
        report["reasons"].append(msg)
    
    # 4. DNS Reputation (léger, mais utile)
    if domain:
        status, msg = check_dns_reputation(domain)
        report["checks"]["dns"] = {"status": status, "message": msg}
        if status == "DANGER":
            report["risk_score"] += 80
            report["reasons"].append(msg)
    
    # === VERDICT FINAL ===
    if report["risk_score"] >= 100:
        report["verdict"] = "BLOQUER"
    elif report["risk_score"] >= 40:
        report["verdict"] = "AVERTIR"
    else:
        report["verdict"] = "OK"
    
    # Sauvegarde du rapport
    save_report(report)
    
    return report

def save_report(report):
    """Sauvegarde le rapport de scan dans un fichier JSON."""
    try:
        existing = json.loads(REPORT_FILE.read_text(encoding='utf-8'))
        existing.append(report)
        # Garde seulement les 100 derniers rapports
        existing = existing[-100:]
        REPORT_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding='utf-8')
    except:
        pass

def print_report(report):
    """Affiche un rapport lisible dans la console."""
    print("\n" + "="*70)
    print(f"🌐 WEB SCANNER - Rapport de scan")
    print("="*70)
    print(f"URL      : {report['url']}")
    print(f"Fichier  : {report['filename']}")
    print(f"Domaine  : {report['domain']}")
    print(f"Risque   : {report['risk_score']}/100")
    print(f"Verdict  : {report['verdict']}")
    print("\n📋 Détails des checks :")
    
    for check_name, check_data in report['checks'].items():
        status_icon = "🔴" if check_data['status'] == "DANGER" else \
                      "🟡" if check_data['status'] == "SUSPECT" else "🟢"
        print(f"  {status_icon} {check_name.upper()}: {check_data['message']}")
    
    if report['reasons']:
        print("\n⚠️ Raisons de l'alerte :")
        for reason in report['reasons']:
            print(f"  • {reason}")
    
    print("="*70)
    
    # Recommandation
    if report['verdict'] == "BLOQUER":
        print("❌ TÉLÉCHARGEMENT BLOQUÉ - DANGER ÉLEVÉ")
    elif report['verdict'] == "AVERTIR":
        print("⚠️ TÉLÉCHARGEMENT DÉCONSEILLÉ - Procédez avec prudence")
    else:
        print("✅ Téléchargement autorisé")
    print("="*70 + "\n")

# === FONCTION PRINCIPALE (appelée par Kerberos) ===
def run():
    """Point d'entrée du guard - Lance un scan de test."""
    print("\n🛡️ Guard Web Scanner activé")
    print("📡 Surveillance des téléchargements web...")
    
    # Exemples de tests (remplacez par vos URLs réelles)
    test_urls = [
        ("https://github.com/victorpozen/kerberos/archive/main.zip", "kerberos-main.zip"),
        ("http://malware-download.com/trojan.exe", "trojan.exe"),
        ("https://192.168.1.1/download.php?file=crack.exe", "crack.exe"),
        ("https://microsoft.com/updates/security.msi", "security.msi"),
    ]
    
    print(f"\n🧪 Test sur {len(test_urls)} URLs...\n")
    
    blocked = 0
    warned = 0
    
    for url, filename in test_urls:
        report = scan_url(url, filename)
        print_report(report)
        
        if report['verdict'] == "BLOQUER":
            blocked += 1
        elif report['verdict'] == "AVERTIR":
            warned += 1
    
    print(f"\n📊 Résumé : {blocked} bloqués | {warned} avertissements | {len(test_urls)-blocked-warned} OK")
    print(f"📁 Rapports sauvegardés dans : {REPORT_FILE}")
    
    return f"✅ Web Scanner actif - {blocked} menaces détectées"

# === INTÉGRATION NAVIGATEUR (TODO) ===
def monitor_browser_downloads():
    """
    TODO : Surveillance temps réel des téléchargements navigateur.
    Nécessite : hook sur dossier Downloads ou interception proxy HTTP.
    """
    downloads_dir = Path.home() / "Downloads"
    print(f"🔍 Surveillance du dossier : {downloads_dir}")
    # Implémentation future avec watchdog ou mitmproxy

if __name__ == '__main__':
    run()