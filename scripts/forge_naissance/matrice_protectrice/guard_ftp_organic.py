#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD_FTP_ORGANIC – Kerberos Security Guard
--------------------------------------------------
Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)
Auteur : Victor Pozen
Licence : GNU General Public License v3.0 (GPLv3)

Ce guard FTP n'est PAS un serveur FTP classique.
Il est conçu comme un organe de reconnaissance :
- Visible sur le réseau (port 21),
- Mais totalement muet/sourd aux entités non reconnues,
- Seule une IP explicitement autorisée peut initier une session éphémère.

Dons bienvenus : https://liberapay.com/EthicalKerberos/
Code source : https://github.com/victorpozen/kerberos

Copyright (C) 2025 Victor Pozen
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import time
import hmac
import hashlib
import socket
from pathlib import Path

# Chemins intramuros
GUARD_DIR = Path(__file__).parent
BASE_DIR = GUARD_DIR.parent
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"

TRUSTED_IPS_FILE = CONFIG_DIR / "trusted_ips.txt"
BANLIST_FILE = CONFIG_DIR / "banlist.txt"
SHARED_FOLDER_FILE = CONFIG_DIR / "ftp_shared_folder.txt"
DNA_KEY_FILE = BASE_DIR / "kerberos_dna.key"
LOG_FILE = LOGS_DIR / "guard_ftp_organic.log"

CONFIG_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

def log(msg, level="INFO"):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}\n")

def load_set(filepath):
    if not filepath.exists():
        return set()
    return {line.strip() for line in filepath.read_text().splitlines() if line.strip()}

def save_line(filepath, line):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_dna_secret():
    if DNA_KEY_FILE.exists():
        return DNA_KEY_FILE.read_text().strip()
    raw = str(hashlib.sha256(str(socket.gethostname()).encode()).hexdigest()) + "OPTIPOD_KERBEROS"
    secret = hashlib.sha256(raw.encode()).hexdigest()
    DNA_KEY_FILE.write_text(secret)
    log("🔑 ADN machine généré.", "INIT")
    return secret

# Import local de pyftpdlib (intramuros)
sys.path.insert(0, str(BASE_DIR / "lib"))
try:
    from pyftpdlib.authorizers import DummyAuthorizer
    from pyftpdlib.handlers import FTPHandler
    from pyftpdlib.servers import FTPServer
except ImportError:
    log("❌ pyftpdlib manquant dans ./lib/", "FATAL")
    sys.exit(1)

class OrganicFTPHandler(FTPHandler):
    def __init__(self, conn, server):
        self.client_ip = conn.getpeername()[0]
        self.token = None

        trusted_ips = load_set(TRUSTED_IPS_FILE)
        banned_ips = load_set(BANLIST_FILE)

        if self.client_ip in banned_ips:
            log(f"💀 BANNI – refus silencieux : {self.client_ip}", "SECURITY")
            conn.close()
            return

        if self.client_ip not in trusted_ips:
            log(f"🚨 INCONNU – ban automatique : {self.client_ip}", "SECURITY")
            save_line(BANLIST_FILE, self.client_ip)
            conn.close()
            return

        # Génère token éphémère (valide 3 min)
        secret = get_dna_secret()
        window = str(int(time.time() // 180))
        payload = self.client_ip + window + secret
        self.token = "KRB-" + hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:6].upper()
        log(f"✅ AUTORISÉ : {self.client_ip} → token = {self.token}", "SESSION")

        # Injecte le token dans la bannière de bienvenue
        self.banner = f"220 🔑 Token: {self.token} (valide 3 min)"

        super().__init__(conn, server)

    def handle_auth_failed(self, username, password):
        if username == "guest" and password == self.token:
            return
        self.respond("530 Accès refusé.")
        self.close()

def run_guard():
    if not SHARED_FOLDER_FILE.exists():
        log("❌ ftp_shared_folder.txt manquant.", "ERROR")
        return
    shared_dir = SHARED_FOLDER_FILE.read_text().strip()
    if not os.path.isdir(shared_dir):
        log(f"❌ Dossier introuvable : {shared_dir}", "ERROR")
        return

    authorizer = DummyAuthorizer()
    # Lecture seule par défaut
    authorizer.add_user("guest", "dummy", shared_dir, perm="elr")
    authorizer.add_anonymous(shared_dir, perm="")

    handler = OrganicFTPHandler
    handler.authorizer = authorizer

    try:
        server = FTPServer(("0.0.0.0", 21), handler)
        log("🟢 Guard FTP organique démarré (lecture seule).", "STARTUP")
        server.serve_forever()
    except PermissionError:
        log("❌ Port 21 – exécuter en admin ?", "ERROR")
    except Exception as e:
        log(f"💥 Erreur critique : {e}", "FATAL")

if __name__ == "__main__":
    run_guard()