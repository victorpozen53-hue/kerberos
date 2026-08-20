#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODULE CYBERMAP — Carte Leaflet Interactive
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Module indépendant pour Kerberos Ultimate v4.2
Peut être lancé seul ou depuis l'application principale
GPLv3 — Victor Pozen 2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import psutil
import socket
import webbrowser
import tempfile
from pathlib import Path

# === CARTE LEAFLET HTML (Style KERBEROS v4.0) ===
LEAFLET_MAP_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🗺️ KERBEROS — Carte Cyber Interactive</title>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0f1a; color: #00ffcc; font-family: 'Consolas', monospace; overflow: hidden; }
#map { height: 100vh; width: 100%; }
.leaflet-tile { filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%); }
.leaflet-container { background: #0a0f1a !important; }
.info-panel {
    position: absolute; top: 10px; right: 10px;
    background: rgba(10,15,26,0.95); border: 2px solid #00ffcc;
    border-radius: 10px; padding: 15px; z-index: 1000;
    min-width: 280px; box-shadow: 0 0 20px rgba(0,255,204,0.3);
}
.info-panel h3 { color: #00ffcc; margin-bottom: 10px; font-size: 14px; text-shadow: 0 0 10px #00ffcc; }
.info-panel .stat { display: flex; justify-content: space-between; margin: 5px 0; font-size: 12px; }
.info-panel .stat-value { color: #00ffcc; font-weight: bold; }
</style>
</head>
<body>
<div id="map"></div>
<div class="info-panel">
    <h3>🗺️ CYBERMAP KERBEROS v4.2</h3>
    <div class="stat"><span>Connexions:</span><span class="stat-value" id="connCount">0</span></div>
    <div class="stat"><span>🟢 Sûres:</span><span class="stat-value" style="color:#4CAF50" id="safeCount">0</span></div>
    <div class="stat"><span>🟡 Suspectes:</span><span class="stat-value" style="color:#ff9800" id="suspectCount">0</span></div>
    <div class="stat"><span>🔴 Bloquées:</span><span class="stat-value" style="color:#ff5252" id="blockedCount">0</span></div>
    <div style="margin-top: 15px; font-size: 11px; color: #6a8a9a;">
        🖱️ Scroll pour zoomer<br>🖱️ Drag pour déplacer<br>🖱️ Clique sur les marqueurs
    </div>
</div>
<script>
const map = L.map('map').setView([20, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap', maxZoom: 18, minZoom: 2
}).addTo(map);

const markers = {};
let markerId = 0;
let stats = {allowed: 0, suspect: 0, blocked: 0};

function addMarker(lat, lng, ip, threat, region) {
    const colors = {allowed: '#4CAF50', suspect: '#ff9800', blocked: '#ff5252'};
    const icon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="background:${colors[threat] || '#ff9800'};width:14px;height:14px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 15px ${colors[threat] || '#ff9800'};animation:pulse 2s infinite;"></div>`,
        iconSize: [14, 14]
    });
    const marker = L.marker([lat, lng], {icon: icon}).addTo(map);
    marker.bindPopup(`<div style="background:#0a0f1a;color:#00ffcc;padding:10px;border-radius:5px;min-width:200px;"><strong>${ip}</strong><br>Région: ${region}<br>Statut: ${threat}</div>`);
    markers[markerId++] = marker;
    stats[threat] = (stats[threat] || 0) + 1;
    updateStats();
    if (Object.keys(markers).length > 50) {
        const oldKey = Object.keys(markers)[0];
        map.removeLayer(markers[oldKey]);
        delete markers[oldKey];
    }
}

function updateStats() {
    document.getElementById('connCount').textContent = markerId;
    document.getElementById('safeCount').textContent = stats.allowed || 0;
    document.getElementById('suspectCount').textContent = stats.suspect || 0;
    document.getElementById('blockedCount').textContent = stats.blocked || 0;
}

// Marqueur central (VOUS)
L.marker([48.8566, 2.3522]).addTo(map)
    .bindPopup('<div style="background:#0a0f1a;color:#00ffcc;padding:10px;border-radius:5px;"><strong>🛡️ KERBEROS</strong><br>Centre de Contrôle<br>France</div>')
    .openPopup();

// Animation pulse
const style = document.createElement('style');
style.textContent = `@keyframes pulse {
    0% { box-shadow: 0 0 10px currentColor; }
    50% { box-shadow: 0 0 20px currentColor; }
    100% { box-shadow: 0 0 10px currentColor; }
}`;
document.head.appendChild(style);

// Fonctions pour Python
window.addConnection = function(lat, lng, ip, threat, region) { addMarker(lat, lng, ip, threat, region); };
window.clearMarkers = function() {
    for (const key in markers) { map.removeLayer(markers[key]); }
    markerId = 0; stats = {allowed: 0, suspect: 0, blocked: 0}; updateStats();
};
</script>
</body>
</html>
"""

class CyberMapModule:
    """Module Carte Cyber — Indépendant et Léger"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🗺️ KERBEROS — Carte Cyber Interactive")
        self.root.geometry("1000x650")
        self.root.configure(bg='#1e1e2e')
        
        self.map_file_path = None
        self.connections = []
        self.stats = {'allowed': 0, 'suspect': 0, 'blocked': 0}
        
        self._setup_ui()
        self._create_map_file()
        self._start_monitoring()
        
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self.root.mainloop()
    
    def _setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#16213e', height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🗺️ CARTE CYBER LEAFLET",
                bg='#16213e', fg='#00ffcc', font=("Consolas", 16, "bold")).pack(pady=10)
        
        # Main
        main = tk.Frame(self.root, bg='#1e1e2e')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left - Stats & Controls
        left = tk.Frame(main, bg='#1e1e2e', width=280)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left.pack_propagate(False)
        
        # Stats
        stats_frame = tk.LabelFrame(left, text=" 📊 Statistiques ",
                                   bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 10, "bold"))
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stat_labels = {}
        for key, label, color in [
            ('total', 'Total', '#00ffcc'),
            ('allowed', '🟢 Sûres', '#4CAF50'),
            ('suspect', '🟡 Suspectes', '#ff9800'),
            ('blocked', '🔴 Bloquées', '#ff5252')
        ]:
            frame = tk.Frame(stats_frame, bg='#161a2e')
            frame.pack(fill=tk.X, pady=3)
            tk.Label(frame, text=label, bg='#161a2e', fg=color, font=("Consolas", 9)).pack(side=tk.LEFT, padx=10)
            count = tk.Label(frame, text="0", bg='#161a2e', fg='white', font=("Consolas", 11, "bold"))
            count.pack(side=tk.RIGHT, padx=10)
            self.stat_labels[key] = count
        
        # Controls
        ctrl_frame = tk.LabelFrame(left, text=" ⚙️ Contrôles ",
                                  bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 10, "bold"))
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Button(ctrl_frame, text="🌐 Ouvrir Carte", bg='#2d5a7b', fg='white',
                 font=("Consolas", 9), command=self._open_in_browser).pack(fill=tk.X, pady=3)
        tk.Button(ctrl_frame, text="🔄 Rafraîchir", bg='#5a3a7b', fg='white',
                 font=("Consolas", 9), command=self._refresh).pack(fill=tk.X, pady=3)
        tk.Button(ctrl_frame, text="🗑️ Effacer", bg='#7b3a3a', fg='white',
                 font=("Consolas", 9), command=self._clear).pack(fill=tk.X, pady=3)
        
        # Log
        log_frame = tk.LabelFrame(left, text=" 📝 Log ",
                                 bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 10, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log = scrolledtext.ScrolledText(log_frame, height=15, font=("Consolas", 8),
                                            bg='#0a0a0a', fg='#00ff00', relief=tk.FLAT)
        self.log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log.insert(tk.END, "🌐 En attente...\n")
        self.log.configure(state='disabled')
        
        # Right - Info
        right = tk.Frame(main, bg='#1e1e2e')
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        info = tk.LabelFrame(right, text=" 🗺️ Carte Interactive ",
                            bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 10, "bold"))
        info.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(info, text="La carte Leaflet s'ouvre dans votre navigateur.\n\nStyle Google Earth • Zoom • Drag • Marqueurs interactifs",
                bg='#1e1e2e', fg='#a0a0c0', font=("Consolas", 10), justify=tk.CENTER).pack(pady=80)
        
        tk.Button(info, text="🚀 OUVRIR LA CARTE", bg='#00ffcc', fg='#0a0f1a',
                 font=("Consolas", 12, "bold"), padx=30, pady=15,
                 command=self._open_in_browser).pack(pady=20)
        
        # Status
        self.status = ttk.Label(self.root, text='✅ Module Carte Prêt', relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_map_file(self):
        try:
            maps_dir = Path(__file__).parent.parent / "maps"
            maps_dir.mkdir(exist_ok=True)
            self.map_file_path = maps_dir / "cybermap.html"
            self.map_file_path.write_text(LEAFLET_MAP_HTML, encoding='utf-8')
            print(f"[✓] Carte créée: {self.map_file_path}")
        except Exception as e:
            print(f"[✗] Erreur: {e}")
    
    def _open_in_browser(self):
        try:
            if self.map_file_path and self.map_file_path.exists():
                webbrowser.open(self.map_file_path.as_uri())
                self._log("✅ Carte ouverte")
                self.status.config(text='🌐 Carte ouverte')
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
    
    def _refresh(self):
        self._open_in_browser()
        self._log("🔄 Rafraîchi")
    
    def _clear(self):
        self.connections = []
        self.stats = {'allowed': 0, 'suspect': 0, 'blocked': 0}
        for key in self.stat_labels:
            self.stat_labels[key].config(text="0")
        self._log("🗑️ Effacé")
    
    def _start_monitoring(self):
        threading.Thread(target=self._monitor, daemon=True).start()
    
    def _monitor(self):
        last = set()
        while True:
            try:
                conns = psutil.net_connections(kind='inet')
                current = set()
                for c in conns:
                    if c.status == 'ESTABLISHED' and c.raddr:
                        current.add((c.raddr.ip, c.raddr.port))
                        if (c.raddr.ip, c.raddr.port) not in last:
                            threat = self._classify(c.raddr.ip, c.raddr.port)
                            region = self._get_region(c.raddr.ip)
                            coords = self._get_coords(region)
                            self.root.after(0, lambda ip=c.raddr.ip, p=c.raddr.port,
                                          t=threat, r=region, c=coords: self._add(ip, p, t, r, c))
                last = current
                time.sleep(2)
            except: time.sleep(3)
    
    def _classify(self, ip, port):
        suspicious = [23, 135, 139, 445, 1433, 3306, 3389, 5900]
        if ip.startswith(('192.168.', '10.', '172.16.', '127.')): return 'allowed'
        if port in suspicious: return 'blocked'
        if port in [80, 443, 8080]: return 'allowed'
        return 'suspect'
    
    def _get_region(self, ip):
        if ip.startswith(('192.168.', '10.', '172.16.', '127.')): return 'Europe'
        first = int(ip.split('.')[0]) if ip.count('.') == 3 else 0
        if first in range(2, 64): return 'Europe'
        if first in range(64, 128): return 'Amériques'
        if first in range(128, 192): return 'Asie'
        return 'Autres'
    
    def _get_coords(self, region):
        return {'Europe': (48.8566, 2.3522), 'Amériques': (40.7128, -74.0060),
                'Asie': (35.6762, 139.6503), 'Autres': (-33.8688, 151.2093)}.get(region, (48.8566, 2.3522))
    
    def _add(self, ip, port, threat, region, coords):
        self.connections.append({'ip': ip, 'threat': threat})
        self.stats[threat] = self.stats.get(threat, 0) + 1
        self.stat_labels['total'].config(text=str(len(self.connections)))
        for key in ['allowed', 'suspect', 'blocked']:
            self.stat_labels[key].config(text=str(self.stats.get(key, 0)))
        icons = {'allowed': '🟢', 'suspect': '🟡', 'blocked': '🔴'}
        self._log(f"{icons.get(threat, '⚪')} {region} → {ip}:{port}")
    
    def _log(self, msg):
        try:
            self.log.configure(state='normal')
            self.log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log.see(tk.END)
            self.log.configure(state='disabled')
        except: pass
    
    def _on_close(self):
        self.root.destroy()

if __name__ == '__main__':
    print("🗺️ KERBEROS — Module Carte Cyber")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    CyberMapModule()