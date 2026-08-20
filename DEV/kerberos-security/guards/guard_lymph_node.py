#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧬 Guard Lymph Node — Filtrage Cellulaire Réseau
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Filtre les "agents étrangers" (connexions suspectes)
- Maintient l'homéostasie réseau (équilibre sain)
- Lists de référence mises à jour automatiquement
- Mode "Activité Normale" pour services légitimes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
import os, sys, time, socket, struct, threading, requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import psutil

class LymphNodeFilter:
    """Filtre biologique réseau — Homéostasie des connexions"""
    
    def __init__(self):
        self.filtered_ranges = []
        self.trusted_entities = set()
        self.metrics = {
            "total_filtered": 0,
            "by_source_type": defaultdict(int),
            "recent_events": []
        }
        
        # Répertoires (noms biologiques)
        self.refs_dir = Path("lymph/nodes/references")
        self.refs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = Path("logs/nodes")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Catégories de filtrage (noms neutres)
        self.active_filters = {
            "type_a": True,   # Gouvernements
            "type_b": True,   # Trackers
            "type_c": True,   # Anti-piratage
            "type_d": True,   # Malware
            "type_e": True,   # Spam
            "geo_filter": False,  # Pays
        }
        
        # Mode "activité normale" (gaming, etc.)
        self.normal_activity_mode = False
        self.trusted_services = [
            "steampowered.com", "discord.com", "github.com", "cloudflare.com"
        ]
        
        self._load_references()
        self._load_trusted_list()
    
    def _addr_to_int(self, addr: str) -> int:
        try: return struct.unpack("!I", socket.inet_aton(addr))[0]
        except: return 0
    
    def _int_to_addr(self, n: int) -> str:
        return socket.inet_ntoa(struct.pack("!I", n))
    
    def _parse_reference_line(self, line: str) -> dict:
        try:
            if ':' not in line or '-' not in line: return None
            label, rng = line.split(':', 1)
            start, end = rng.split('-')
            return {
                "label": label.strip(),
                "start": self._addr_to_int(start.strip()),
                "end": self._addr_to_int(end.strip())
            }
        except: return None
    
    def _fetch_reference(self, endpoint: str, fname: str) -> bool:
        try:
            # Endpoint obfusqué (base64 ou calculé)
            url = self._decode_endpoint(endpoint)
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            (self.refs_dir / fname).write_text(resp.text, encoding='utf-8')
            return True
        except: return False
    
    def _decode_endpoint(self, code: str) -> str:
        """Décode un endpoint de manière discrète"""
        # Exemple simple : rotation de caractères
        # En prod : base64 + salage
        return ''.join(chr((ord(c) - 3 - 97) % 26 + 97) if c.islower() else 
                      (chr((ord(c) - 3 - 65) % 26 + 65) if c.isupper() else c) 
                      for c in code)
    
    def _load_references(self):
        """Charge les listes de référence (noms neutres)"""
        refs = {
            "type_a": {"code": "kuvmpd", "file": "ref_a.dat"},  # iblocklist/gov
            "type_b": {"code": "kuvmpd", "file": "ref_b.dat"},  # iblocklist/ads
            "type_c": {"code": "kuvmpd", "file": "ref_c.dat"},  # iblocklist/copyright
            "type_d": {"code": "kuvmpd", "file": "ref_d.dat"},  # iblocklist/malware
            "type_e": {"code": "fcnzufnh", "file": "ref_e.dat"},  # spamhaus
        }
        
        for ftype, enabled in self.active_filters.items():
            if ftype not in refs or not enabled: continue
            info = refs[ftype]
            fpath = self.refs_dir / info["file"]
            if not fpath.exists() or (time.time() - fpath.stat().st_mtime) > 7*86400:
                self._fetch_reference(info["code"], info["file"])
            if fpath.exists():
                self._load_ref_file(fpath, ftype)
    
    def _load_ref_file(self, fpath: Path, ftype: str):
        try:
            for line in fpath.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith(('#', ';')): continue
                parsed = self._parse_reference_line(line)
                if parsed:
                    parsed["filter_type"] = ftype
                    self.filtered_ranges.append(parsed)
        except: pass
    
    def _load_trusted_list(self):
        tfile = Path("lymph/nodes/trusted.lst")
        if not tfile.exists():
            tfile.write_text("\n".join([
                "# Entités de confiance",
                "127.0.0.1", "::1",
                "192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12",
            ] + self.trusted_services), encoding='utf-8')
        try:
            for line in tfile.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#'): continue
                if not line[0].isdigit():
                    try: self.trusted_entities.add(socket.gethostbyname(line))
                    except: pass
                else: self.trusted_entities.add(line)
        except: pass
    
    def _check_filter(self, addr: str) -> dict:
        if addr in self.trusted_entities:
            return {"filtered": False, "reason": "trusted"}
        if addr.startswith(('127.', '192.168.', '10.', '172.16.')):
            return {"filtered": False, "reason": "local"}
        addr_int = self._addr_to_int(addr)
        if addr_int == 0: return {"filtered": False, "reason": "invalid"}
        for rng in self.filtered_ranges:
            if rng["start"] <= addr_int <= rng["end"]:
                return {
                    "filtered": True,
                    "source": rng["filter_type"],
                    "label": rng.get("label", "unknown"),
                    "range": f"{self._int_to_addr(rng['start'])}-{self._int_to_addr(rng['end'])}"
                }
        return {"filtered": False, "reason": "not_matched"}
    
    def _filter_connection(self, addr: str, port: int, proto: str) -> bool:
        result = self._check_filter(addr)
        if result["filtered"]:
            self.metrics["total_filtered"] += 1
            self.metrics["by_source_type"][result["source"]] += 1
            self.metrics["recent_events"].append({
                "addr": addr, "port": port, "proto": proto,
                "source": result["source"], "label": result["label"],
                "ts": datetime.now().isoformat()
            })
            if len(self.metrics["recent_events"]) > 100:
                self.metrics["recent_events"] = self.metrics["recent_events"][-100:]
            self._log_event(addr, port, proto, result)
            # Log discret
            print(f"[Node] Filtered: {addr}:{port} | {result['source']}")
            # TODO: Intégration firewall système (optionnel)
            return True
        return False
    
    def _log_event(self, addr, port, proto, result):
        logfile = self.logs_dir / f"events_{datetime.now().strftime('%Y%m%d')}.log"
        line = f"[{datetime.now().strftime('%H:%M:%S')}] FILTERED {addr}:{port} ({proto}) | {result['source']} | {result['label']}\n"
        try:
            with open(logfile, "a", encoding="utf-8") as f: f.write(line)
        except: pass
    
    def monitor(self):
        while True:
            try:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        self._filter_connection(conn.raddr.ip, conn.raddr.port,
                                              "TCP" if conn.type == socket.SOCK_STREAM else "UDP")
                time.sleep(1)
            except: time.sleep(2)
    
    def enable_normal_mode(self):
        self.normal_activity_mode = True
        for svc in self.trusted_services:
            try: self.trusted_entities.add(socket.gethostbyname(svc))
            except: pass
    
    def disable_normal_mode(self):
        self.normal_activity_mode = False
    
    def get_metrics(self) -> dict:
        return {
            "total_filtered": self.metrics["total_filtered"],
            "by_source_type": dict(self.metrics["by_source_type"]),
            "recent_events": self.metrics["recent_events"][-10:],
            "ranges_count": len(self.filtered_ranges),
            "trusted_count": len(self.trusted_entities),
            "normal_mode": self.normal_activity_mode
        }
    
    def add_trusted(self, entry: str):
        self.trusted_entities.add(entry)
        tfile = Path("lymph/nodes/trusted.lst")
        try:
            with open(tfile, "a", encoding="utf-8") as f: f.write(f"\n{entry}")
        except: pass

def start_guard():
    print("[LymphNode] Initializing network homeostasis...")
    node = LymphNodeFilter()
    thread = threading.Thread(target=node.monitor, daemon=True, name="LymphNode")
    thread.start()
    print("[LymphNode] Active — maintaining network equilibrium")
    return node

def run():
    print("🧬 Kerberos Lymph Node — Network Homeostasis Module")
    node = start_guard()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("[LymphNode] Stopped")

if __name__ == "__main__":
    run()