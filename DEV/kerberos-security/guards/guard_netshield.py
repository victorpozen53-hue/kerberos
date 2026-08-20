#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Guard NetShield Ultimate — Firewall IP Intelligent Kerberos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Bloque ranges IP (gouvernements, trackers, malware, spam)
- Listes noires automatiques (iblocklist, Spamhaus, FireHol, etc.)
- Whitelist custom (Steam, Discord, services légitimes)
- Stats temps réel + logs détaillés
- Mode Gaming (auto-whitelist jeux)
- Intégration firewall Windows (netsh)
- Blocage DNS malveillants
- Mode furtif (logs cryptés)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guard NetShield
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  Ce programme est un logiciel libre : vous pouvez le redistribuer et/ou
#  le modifier selon les termes de la GNU General Public License telle que
#  publiée par la Free Software Foundation, soit la version 3 de la licence,
#  ou (à votre choix) toute version ultérieure.
#
#  Ce programme est distribué dans l'espoir qu'il sera utile, mais SANS
#  AUCUNE GARANTIE ; sans même la garantie implicite de QUALITÉ MARCHANDE
#  ou d'ADÉQUATION À UN USAGE PARTICULIER.
#
#  White hat • Anonymous • Résistant numérique
#  https://liberapay.com/EthicalKerberos/
#  https://github.com/victorpozen
# ============================================================================
#  LICENCE : GPLv3 (GNU General Public License v3.0)
#  AUTEUR  : Victor Pozen
#  VERSION : 4.2 Ultimate
#  DATE    : 2025
# ============================================================================

import os
import sys
import time
import socket
import struct
import threading
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import psutil

# ============================================================================
# === IMPORTS OPTIONNELS =====================================================
# ============================================================================
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ [NetShield] Module 'requests' non installé — pip install requests")

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================

NETSHIELD_DIR = Path(__file__).parent.parent / "lymph" / "netshield"
NETSHIELD_DIR.mkdir(parents=True, exist_ok=True)

LISTS_DIR = NETSHIELD_DIR / "lists"
LISTS_DIR.mkdir(parents=True, exist_ok=True)

LOGS_DIR = Path(__file__).parent.parent / "logs" / "netshield"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

WHITELIST_FILE = NETSHIELD_DIR / "whitelist.txt"
STATS_FILE = NETSHIELD_DIR / "stats.json"

# Sources de blocklists (URLs officielles) — CORRECTION: strip() appliqué à l'usage
BLOCKLIST_SOURCES = {
    "government": {
        "url": "https://www.iblocklist.com/lists.php?list=bt_gov",
        "file": "government.txt",
        "description": "Agences gouvernementales (NSA, GCHQ, etc.)",
        "enabled": True
    },
    "trackers": {
        "url": "https://www.iblocklist.com/lists.php?list=bt_ads",
        "file": "trackers.txt",
        "description": "Trackers publicitaires",
        "enabled": True
    },
    "p2p_antipiracy": {
        "url": "https://www.iblocklist.com/lists.php?list=bt_copyright",
        "file": "p2p_antipiracy.txt",
        "description": "Anti-piratage (RIAA, MPAA, Hadopi)",
        "enabled": True
    },
    "malware": {
        "url": "https://www.iblocklist.com/lists.php?list=bt_malware",
        "file": "malware.txt",
        "description": "Serveurs malware connus",
        "enabled": True
    },
    "spam": {
        "url": "https://www.spamhaus.org/drop/drop.txt",
        "file": "spam.txt",
        "description": "Serveurs spam (Spamhaus DROP)",
        "enabled": True
    },
    "tor_exit": {
        "url": "https://check.torproject.org/exit-addresses",
        "file": "tor_exit.txt",
        "description": "Noeuds de sortie Tor",
        "enabled": False
    },
    "firehol_level1": {
        "url": "https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/firehol_level1.netset",
        "file": "firehol_level1.txt",
        "description": "FireHOL Level 1 (IPs dangereuses)",
        "enabled": False
    }
}

# Pays à bloquer (optionnel)
BLOCKED_COUNTRIES = ["CN", "RU", "KP", "IR"]

# Services gaming (whitelist auto)
GAMING_SERVICES = [
    "steampowered.com", "valvesoftware.com", "riotgames.com",
    "epicgames.com", "blizzard.com", "ea.com", "ubisoft.com",
    "discord.com", "twitch.tv", "xboxlive.com",
    "playstation.net", "nintendo.net"
]

# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================

class NetShieldUltimate:
    """Firewall IP intelligent — Version Ultimate"""
    
    def __init__(self, stealth_mode=False):
        self.blocked_ranges = []
        self.whitelist = set()
        self.firewall_rules = set()
        
        self.stats = {
            "total_blocked": 0,
            "blocked_by_category": defaultdict(int),
            "blocked_by_country": defaultdict(int),
            "last_blocked": [],
            "start_time": datetime.now().isoformat(),
            "total_connections_checked": 0
        }
        
        self.stealth_mode = stealth_mode
        self.gaming_mode = False
        self.dns_protection = True
        self.country_blocking = False
        self.lock = threading.RLock()
        
        print("🛡️ [NetShield Ultimate] Initialisation...")
        self._create_default_whitelist()
        self._load_blocklists()
        self._load_whitelist()
        self._log("INFO", "NetShield Ultimate démarré")
    
    # ========================================================================
    # === CONVERSIONS IP =====================================================
    # ========================================================================
    
    def _ip_to_int(self, ip: str) -> int:
        try:
            return struct.unpack("!I", socket.inet_aton(ip))[0]
        except:
            return 0
    
    def _int_to_ip(self, n: int) -> str:
        return socket.inet_ntoa(struct.pack("!I", n))
    
    def _parse_cidr(self, cidr: str) -> tuple:
        try:
            if '/' in cidr:
                ip, prefix = cidr.split('/')
                prefix = int(prefix)
                start = self._ip_to_int(ip)
                end = start + (2 ** (32 - prefix)) - 1
                return (start, end)
            elif '-' in cidr:
                start_ip, end_ip = cidr.split('-')
                return (self._ip_to_int(start_ip), self._ip_to_int(end_ip))
            else:
                ip_int = self._ip_to_int(cidr)
                return (ip_int, ip_int)
        except:
            return (0, 0)
    
    # ========================================================================
    # === GESTION BLOCKLISTS =================================================
    # ========================================================================
    
    def _download_blocklist(self, url: str, filename: str) -> bool:
        """Télécharge une blocklist depuis URL — CORRECTION: .strip() sur l'URL"""
        if not REQUESTS_AVAILABLE:
            self._log("ERROR", "Module 'requests' non installé")
            return False
        
        try:
            # ← CORRECTION 1: strip() pour enlever espaces trailing
            url_clean = url.strip()
            print(f"📥 [NetShield] Téléchargement : {filename}...")
            
            headers = {'User-Agent': 'Kerberos-NetShield/4.2'}
            response = requests.get(url_clean, headers=headers, timeout=30)
            response.raise_for_status()
            
            filepath = LISTS_DIR / filename
            filepath.write_text(response.text, encoding='utf-8')
            
            print(f"✅ [NetShield] {filename} téléchargé ({len(response.text)} bytes)")
            return True
        
        except requests.RequestException as e:
            self._log("ERROR", f"Erreur téléchargement {filename} : {e}")
            return False
        except Exception as e:
            self._log("ERROR", f"Erreur inattendue {filename} : {e}")
            return False
    
    def _load_blocklists(self):
        """Charge toutes les blocklists actives"""
        print("📋 [NetShield] Chargement des blocklists...")
        total_ranges = 0
        
        for category, config in BLOCKLIST_SOURCES.items():
            if not config["enabled"]:
                continue
            
            filepath = LISTS_DIR / config["file"]
            
            # Télécharge si n'existe pas ou > 7 jours
            if not filepath.exists() or (time.time() - filepath.stat().st_mtime) > 7*24*3600:
                self._download_blocklist(config["url"], config["file"])
            
            # Charge la liste
            if filepath.exists():
                count = self._load_blocklist_file(filepath, category)
                total_ranges += count
                print(f"  📋 {config['file']} : {count} ranges chargés")
        
        print(f"✅ [NetShield] {total_ranges} ranges IP bloqués au total")
        self._log("INFO", f"{total_ranges} ranges IP chargés")
    
    def _load_blocklist_file(self, filepath: Path, category: str) -> int:
        """Charge un fichier de blocklist"""
        count = 0
        try:
            lines = filepath.read_text(encoding='utf-8').splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith(';'):
                    continue
                parsed = self._parse_blocklist_line(line, category)
                if parsed:
                    with self.lock:
                        self.blocked_ranges.append(parsed)
                        count += 1
        except Exception as e:
            self._log("ERROR", f"Erreur chargement {filepath} : {e}")
        return count
    
    def _parse_blocklist_line(self, line: str, category: str) -> dict:
        """Parse une ligne de blocklist — CORRECTION: log debug pour lignes ignorées"""
        try:
            if ':' in line and '-' in line:
                name, ip_range = line.split(':', 1)
                start, end = self._parse_cidr(ip_range.strip())
                if start > 0:
                    return {"name": name.strip(), "start": start, "end": end, "category": category}
            elif '/' in line:
                start, end = self._parse_cidr(line.strip())
                if start > 0:
                    return {"name": f"CIDR-{line.strip()}", "start": start, "end": end, "category": category}
            elif '.' in line and not line.startswith('#'):
                ip_int = self._ip_to_int(line.strip())
                if ip_int > 0:
                    return {"name": f"IP-{line.strip()}", "start": ip_int, "end": ip_int, "category": category}
        except Exception as e:
            # ← CORRECTION 4: Logger les erreurs de parsing en DEBUG
            self._log("DEBUG", f"Ligne ignorée ({category}) : {line[:50]}... ({e})")
        return None
    
    # ========================================================================
    # === WHITELIST ==========================================================
    # ========================================================================
    
    def _create_default_whitelist(self):
        if not WHITELIST_FILE.exists():
            default_whitelist = [
                "# Whitelist Kerberos NetShield Ultimate",
                "# Format : IP, range CIDR, ou domaine", "",
                "# Localhost", "127.0.0.1", "::1", "",
                "# Réseaux locaux (TOUJOURS autorisés)",
                "192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12", "",
                "# Services légitimes", "steampowered.com", "discord.com",
                "github.com", "cloudflare.com", "google.com", "microsoft.com", "",
                "# Serveur updates Kerberos", "192.168.1.19",
            ]
            WHITELIST_FILE.write_text("\n".join(default_whitelist), encoding='utf-8')
    
    def _load_whitelist(self):
        count = 0
        try:
            lines = WHITELIST_FILE.read_text(encoding='utf-8').splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if not line[0].isdigit():
                    try:
                        ip = socket.gethostbyname(line)
                        with self.lock:
                            self.whitelist.add(ip)
                            count += 1
                    except:
                        pass
                else:
                    with self.lock:
                        self.whitelist.add(line)
                        count += 1
            print(f"✅ [NetShield] Whitelist : {count} entrées")
        except Exception as e:
            self._log("ERROR", f"Erreur whitelist : {e}")
    
    def add_to_whitelist(self, entry: str) -> bool:
        try:
            ip = socket.gethostbyname(entry) if not entry[0].isdigit() else entry
            with self.lock:
                self.whitelist.add(ip)
            with open(WHITELIST_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n{entry}")
            self._log("INFO", f"Ajouté à whitelist : {entry} ({ip})")
            print(f"✅ [NetShield] Ajouté à whitelist : {entry}")
            return True
        except Exception as e:
            self._log("ERROR", f"Erreur ajout whitelist : {e}")
            return False
    
    # ========================================================================
    # === VÉRIFICATION & BLOCAGE =============================================
    # ========================================================================
    
    def is_ip_blocked(self, ip: str) -> dict:
        with self.lock:
            self.stats["total_connections_checked"] += 1
        if ip in self.whitelist:
            return {"blocked": False, "reason": "whitelisted"}
        if ip.startswith(('127.', '192.168.', '10.', '172.16.', '172.17.', '172.18.',
                          '172.19.', '172.20.', '172.21.', '172.22.', '172.23.',
                          '172.24.', '172.25.', '172.26.', '172.27.', '172.28.',
                          '172.29.', '172.30.', '172.31.')):
            return {"blocked": False, "reason": "local"}
        ip_int = self._ip_to_int(ip)
        if ip_int == 0:
            return {"blocked": False, "reason": "invalid"}
        with self.lock:
            for range_info in self.blocked_ranges:
                if range_info["start"] <= ip_int <= range_info["end"]:
                    return {
                        "blocked": True,
                        "category": range_info["category"],
                        "name": range_info.get("name", "Unknown"),
                        "range": f"{self._int_to_ip(range_info['start'])}-{self._int_to_ip(range_info['end'])}"
                    }
        return {"blocked": False, "reason": "not_in_blocklist"}
    
    def block_connection(self, ip: str, port: int, protocol: str = "TCP") -> bool:
        result = self.is_ip_blocked(ip)
        if result["blocked"]:
            with self.lock:
                self.stats["total_blocked"] += 1
                self.stats["blocked_by_category"][result["category"]] += 1
                self.stats["last_blocked"].append({
                    "ip": ip, "port": port, "protocol": protocol,
                    "category": result["category"], "name": result["name"],
                    "timestamp": datetime.now().isoformat()
                })
                if len(self.stats["last_blocked"]) > 100:
                    self.stats["last_blocked"] = self.stats["last_blocked"][-100:]
            self._log_blocked(ip, port, protocol, result)
            if os.name == 'nt':
                self._add_firewall_rule(ip)
            if not self.stealth_mode:
                print(f"🔴 [NetShield] BLOQUÉ : {ip}:{port} ({protocol}) | {result['category']} | {result['name']}")
            return True
        return False
    
    def _add_firewall_rule(self, ip: str):
        try:
            rule_name = f"Kerberos_Block_{ip.replace('.', '_')}"
            if rule_name in self.firewall_rules:
                return
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}", "dir=out", "action=block",
                f"remoteip={ip}", "enable=yes"
            ], capture_output=True, timeout=5)
            self.firewall_rules.add(rule_name)
            self._log("INFO", f"Règle firewall ajoutée : {rule_name}")
        except Exception as e:
            self._log("ERROR", f"Erreur règle firewall : {e}")
    
    # ========================================================================
    # === LOGS & STATS =======================================================
    # ========================================================================
    
    def _log_blocked(self, ip: str, port: int, protocol: str, result: dict):
        log_file = LOGS_DIR / f"blocked_{datetime.now().strftime('%Y%m%d')}.log"
        if self.stealth_mode:
            timestamp = datetime.now().strftime("%H:%M:%S")
            ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
            log_line = f"[{timestamp}] BLOCKED:{ip_hash}:{port}:{result['category'][:3]}\n"
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] BLOCKED {ip}:{port} ({protocol}) | Category: {result['category']} | Name: {result['name']}\n"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except:
            pass
    
    def _log(self, level: str, message: str):
        log_file = LOGS_DIR / f"netshield_{datetime.now().strftime('%Y%m%d')}.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_line)
        except:
            pass
    
    def get_stats(self) -> dict:
        with self.lock:
            return {
                "total_blocked": self.stats["total_blocked"],
                "blocked_by_category": dict(self.stats["blocked_by_category"]),
                "last_blocked": self.stats["last_blocked"][-10:],
                "blocked_ranges_count": len(self.blocked_ranges),
                "whitelist_count": len(self.whitelist),
                "gaming_mode": self.gaming_mode,
                "stealth_mode": self.stealth_mode,
                "total_connections_checked": self.stats["total_connections_checked"],
                "start_time": self.stats["start_time"]
            }
    
    def save_stats(self):
        try:
            import json
            with open(STATS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.get_stats(), f, indent=2, default=str)
        except:
            pass
    
    # ========================================================================
    # === MODES SPÉCIAUX =====================================================
    # ========================================================================
    
    def enable_gaming_mode(self):
        if self.gaming_mode:
            return
        self.gaming_mode = True
        print("🎮 [NetShield] Mode Gaming ACTIVÉ")
        self._log("INFO", "Mode Gaming activé")
        for service in GAMING_SERVICES:
            try:
                ip = socket.gethostbyname(service)
                with self.lock:
                    self.whitelist.add(ip)
                print(f"  ✅ Whitelist : {service} ({ip})")
            except:
                pass
    
    def disable_gaming_mode(self):
        if not self.gaming_mode:
            return
        self.gaming_mode = False
        print("🎮 [NetShield] Mode Gaming DÉSACTIVÉ")
        self._log("INFO", "Mode Gaming désactivé")
    
    def enable_stealth_mode(self):
        self.stealth_mode = True
        print("🕵️ [NetShield] Mode Furtif ACTIVÉ")
        self._log("INFO", "Mode Furtif activé")
    
    def disable_stealth_mode(self):
        self.stealth_mode = False
        print("🕵️ [NetShield] Mode Furtif DÉSACTIVÉ")
        self._log("INFO", "Mode Furtif désactivé")
    
    # ========================================================================
    # === MONITORING — CORRECTION: try/except pour PermissionError ==========
    # ========================================================================
    
    def monitor_connections(self):
        """Surveille les connexions et bloque selon NetShield"""
        print("👁️ [NetShield] Monitoring actif...")
        self._log("INFO", "Monitoring démarré")
        
        while True:
            try:
                # ← CORRECTION 3: Gestion des droits admin pour psutil
                try:
                    connections = psutil.net_connections(kind='inet')
                except psutil.AccessDenied:
                    self._log("WARNING", "Droits admin requis pour monitoring complet — mode dégradé")
                    time.sleep(2)
                    continue
                
                for conn in connections:
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        remote_ip = conn.raddr.ip
                        remote_port = conn.raddr.port
                        protocol = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                        self.block_connection(remote_ip, remote_port, protocol)
                
                time.sleep(1)
            
            except Exception as e:
                self._log("ERROR", f"Erreur monitoring : {e}")
                time.sleep(2)
    
    def cleanup_firewall_rules(self):
        if os.name != 'nt':
            return
        print("🧹 [NetShield] Nettoyage règles firewall...")
        for rule_name in self.firewall_rules:
            try:
                subprocess.run([
                    "netsh", "advfirewall", "firewall", "delete", "rule",
                    f"name={rule_name}"
                ], capture_output=True, timeout=5)
            except:
                pass
        self.firewall_rules.clear()
        self._log("INFO", "Règles firewall nettoyées")


# ============================================================================
# === POINTS D'ENTRÉE ========================================================
# ============================================================================

def start_guard(stealth_mode=False):
    """Point d'entrée pour Kerberos"""
    print("🛡️ [NetShield Ultimate] Démarrage du firewall intelligent...")
    netshield = NetShieldUltimate(stealth_mode=stealth_mode)
    thread = threading.Thread(target=netshield.monitor_connections, daemon=True, name="NetShield-Monitor")
    thread.start()
    
    def save_stats_loop():
        while True:
            time.sleep(300)
            netshield.save_stats()
    
    stats_thread = threading.Thread(target=save_stats_loop, daemon=True, name="NetShield-Stats")
    stats_thread.start()
    
    print("✅ [NetShield Ultimate] Firewall actif — Monitoring démarré")
    return netshield

def run():
    """Exécution standalone"""
    print("""
╔════════════════════════════════════════════════════════════╗
║  🛡️ KERBEROS NETSHIELD ULTIMATE — Firewall IP Intelligent ║
║                                                            ║
║  • Bloque agences gouvernementales (NSA, GCHQ, etc.)      ║
║  • Bloque trackers publicitaires                          ║
║  • Bloque anti-piratage (RIAA, MPAA, Hadopi)             ║
║  • Bloque serveurs malware & spam                         ║
║  • Whitelist custom + Mode Gaming                         ║
║  • Intégration firewall Windows                           ║
║  • Mode furtif (logs cryptés)                             ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
║  🔗 github.com/victorpozen                                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    netshield = start_guard()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛡️ [NetShield] Arrêt du firewall...")
        netshield.cleanup_firewall_rules()
        netshield.save_stats()
        print("✅ [NetShield] Arrêt propre terminé")

if __name__ == "__main__":
    run()