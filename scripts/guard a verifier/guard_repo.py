#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guard_repo.py — Mini-serveur d'applis locales pour Kerberos
→ Héberge tes .ros, .apk, scripts, docs — partage en LAN
→ Aucun cloud. Aucun compte. Aucun consentement.
→ Démarrage automatique (pas de reboot requis)
→ Statut : vert (actif), orange (initialisation), rouge (arrêté/erreur)
"""

import os
import sys
import time
import socket
import threading
import http.server
import socketserver
from pathlib import Path
import json

# ———————— CONFIG —————————
REPO_DIR = Path.home() / "kerberos" / "repo"
REPO_DIR.mkdir(parents=True, exist_ok=True)  # Seulement si utilisé
PORT = 8080
HOST = "0.0.0.0"  # Écoute sur tout le LAN

# ———————— FINGERPRINT (pour auth .vkr optionnelle) —————————
def fingerprint_hdd():
    try:
        import subprocess
        vol = subprocess.check_output("wmic diskdrive get SerialNumber", shell=True).decode()
        serial = vol.strip().split('\n')[-1].strip()
        return hashlib.sha256(serial.encode()).hexdigest()[:16]
    except:
        import uuid
        return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:16]

# ———————— GÉNÉRATION index.ros —————————
def generate_index():
    apps = []
    for f in REPO_DIR.iterdir():
        if f.is_file() and f.suffix in (".ros", ".apk", ".py", ".vkr", ".pdf"):
            apps.append({
                "name": f.name,
                "size": f.stat().st_size,
                "mtime": f.stat().st_mtime,
                "desc": _read_description(f)
            })
    index_path = REPO_DIR / "index.ros"
    index_path.write_text(json.dumps({"repo": "Kerberos Local", "apps": apps}, indent=2), encoding="utf-8")

def _read_description(path: Path) -> str:
    # Lit la 1re ligne du fichier (si .py/.ros) ou nomme par convention
    if path.suffix in (".py", ".ros"):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                first_line = f.readline().strip()
                if first_line.startswith("#") or first_line.startswith("//"):
                    return first_line.lstrip("#/ ").strip() or f"Appli {path.stem}"
        except:
            pass
    return f"Appli locale : {path.name}"

# ———————— SERVEUR HTTP MINIMAL —————————
class KerberosHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/kerberos.repo":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "name": socket.gethostname(),
                "ip": self.client_address[0],
                "port": PORT,
                "apps": [a["name"] for a in json.loads((REPO_DIR / "index.ros").read_text())["apps"]]
            }).encode())
            return
        return super().do_GET()

# ———————— THREAD SERVEUR —————————
server_thread = None
server_active = False

def start_server():
    global server_active, server_thread
    if server_active:
        return
    try:
        with socketserver.TCPServer((HOST, PORT), KerberosHTTPRequestHandler) as httpd:
            server_active = True
            print(f"[guard_repo] 🟢 Serveur actif → http://{socket.gethostbyname(socket.gethostname())}:{PORT}")
            generate_index()
            httpd.serve_forever()
    except Exception as e:
        print(f"[guard_repo] 🔴 Erreur serveur : {e}")
        server_active = False

def ensure_running():
    global server_thread
    if not server_thread or not server_thread.is_alive():
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        time.sleep(0.5)

# ———————— API POUR KERBEROS —————————
def get_local_repos():
    """Retourne la liste des repo LAN détectés (via scan rapide UDP ou mDNS léger)"""
    # Version simple : scan des IPs 192.168.1.1–254 sur port 8080 + requête /kerberos.repo
    # → à étendre avec SSDP/mDNS si besoin
    return [{"name": "Local", "url": f"http://127.0.0.1:{PORT}"}]

def download_app(repo_url: str, app_name: str, target: Path):
    """Télécharge une appli depuis un repo (ex: http://192.168.1.10:8080/qr_intramuros.ros)"""
    import urllib.request
    try:
        urllib.request.urlretrieve(f"{repo_url.rstrip('/')}/{app_name}", target)
        print(f"[guard_repo] ✅ {app_name} → {target}")
        return True
    except Exception as e:
        print(f"[guard_repo] ❌ Échec téléchargement : {e}")
        return False

# ———————— LANCEMENT AUTO —————————
if __name__ == "__main__":
    print("🛡️ guard_repo.py — Serveur d’applis locales (Kerberos)")
    print(f"📁 Dossier : {REPO_DIR}")
    print(f"🌐 Accès : http://{socket.gethostbyname(socket.gethostname())}:{PORT}")
    print("→ Dépose des .ros, .apk, .py… → Kerberos les découvre automatiquement.")
    ensure_running()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[guard_repo] Arrêt demandé.")