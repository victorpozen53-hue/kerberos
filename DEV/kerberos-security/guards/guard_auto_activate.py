#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚡ Guard Auto-Activate — Activation Automatique des Guards
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Active TOUS les guards au démarrage de Kerberos
- Génère la carte Leaflet automatiquement
- Vérifie que chaque guard est fonctionnel
- Redémarre les guards échoués
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""

import json
import threading
import time
import importlib.util
import webbrowser
from pathlib import Path
from datetime import datetime

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================

GUARDS_DIR = Path(__file__).parent
MANIFEST_FILE = GUARDS_DIR / "guards_manifest.json"
MAPS_DIR = GUARDS_DIR.parent / "maps"
KERBEROS_ROOT = GUARDS_DIR.parent

# ============================================================================
# === HTML DE LA CARTE (Généré automatiquement) ==============================
# ============================================================================

LEAFLET_MAP_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Kerberos — Carte Cyber Interactive</title>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0f1a; color: #00ffcc; font-family: 'Consolas', monospace; overflow: hidden; }
#map { height: 100vh; width: 100%; }
.leaflet-tile { filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%); }
.info-panel {
position: absolute; top: 10px; right: 10px;
background: rgba(10,15,26,0.95); border: 2px solid #00ffcc;
border-radius: 10px; padding: 15px; z-index: 1000;
min-width: 280px; box-shadow: 0 0 20px rgba(0,255,204,0.3);
}
.info-panel h3 { color: #00ffcc; margin-bottom: 10px; font-size: 14px; }
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
html: `<div style="background:${colors[threat]};width:14px;height:14px;border-radius:50%;border:2px solid #fff;"></div>`,
iconSize: [14, 14]
});
const marker = L.marker([lat, lng], {icon: icon}).addTo(map);
marker.bindPopup(`<div style="background:#0a0f1a;color:#00ffcc;padding:10px;"><strong>${ip}</strong><br>${region}<br>${threat}</div>`);
markers[markerId++] = marker;
stats[threat] = (stats[threat] || 0) + 1;
updateStats();
}
function updateStats() {
document.getElementById('connCount').textContent = markerId;
document.getElementById('safeCount').textContent = stats.allowed || 0;
document.getElementById('suspectCount').textContent = stats.suspect || 0;
document.getElementById('blockedCount').textContent = stats.blocked || 0;
}
L.marker([48.8566, 2.3522]).addTo(map)
.bindPopup('<div style="background:#0a0f1a;color:#00ffcc;padding:10px;"><strong>🛡️ KERBEROS</strong><br>France</div>')
.openPopup();
window.addConnection = function(lat, lng, ip, threat, region) { addMarker(lat, lng, ip, threat, region); };
</script>
</body>
</html>
"""

# ============================================================================
# === CLASSE AUTO-ACTIVATE ===================================================
# ============================================================================

class AutoActivateManager:
    """Gère l'activation automatique de tous les guards"""
    
    def __init__(self):
        self.active_guards = {}
        self.failed_guards = []
        self.stats = {
            "total_guards": 0,
            "activated": 0,
            "failed": 0,
            "start_time": time.time()
        }
    
    def load_manifest(self):
        """Charge le manifest des guards"""
        if not MANIFEST_FILE.exists():
            print("⚠️ [Auto-Activate] Manifest introuvable — création par défaut")
            default = {
                "active_guards": [
                    "guard_genome.py",
                    "guard_thymus.py",
                    "guard_cortex.py",
                    "guard_cybermap.py",
                    "guard_antikeylogger.py",
                    "guard_browser_shield.py",
                    "guard_bubble_shield.py",
                    "guard_frog_toxic.py",
                    "guard_ftp_organic.py",
                    "guard_integrity_check.py",
                    "guard_lymph_node.py",
                    "guard_lymphatic.py",
                    "guard_lymphatic_heart.py",
                    "guard_netshield.py",
                    "guard_tardigrade.py",
                    "guard_vigil.py",
                    "guard_yara.py"
                ],
                "version": "4.2",
                "auto_activate_enabled": True
            }
            with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2)
            return default
        
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def activate_guard(self, guard_name):
        """Active un guard spécifique"""
        guard_path = GUARDS_DIR / guard_name
        
        if not guard_path.exists():
            print(f"❌ [Auto-Activate] {guard_name} introuvable")
            return False
        
        try:
            # Import dynamique
            spec = importlib.util.spec_from_file_location(guard_path.stem, guard_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Vérifie start_guard()
            if not hasattr(module, 'start_guard'):
                print(f"⚠️ [Auto-Activate] {guard_name} sans start_guard()")
                return False
            
            # Démarre le guard
            thread = module.start_guard()
            self.active_guards[guard_name] = {
                "thread": thread,
                "started_at": time.time(),
                "status": "active"
            }
            
            print(f"✅ [Auto-Activate] {guard_name} activé")
            return True
        
        except Exception as e:
            print(f"❌ [Auto-Activate] {guard_name} erreur : {e}")
            self.failed_guards.append(guard_name)
            return False
    
    def generate_cybermap(self):
        """Génère automatiquement la carte Leaflet"""
        try:
            MAPS_DIR.mkdir(parents=True, exist_ok=True)
            map_file = MAPS_DIR / "cybermap.html"
            map_file.write_text(LEAFLET_MAP_HTML, encoding="utf-8")
            print(f"🗺️ [Auto-Activate] Carte générée : {map_file}")
            return True
        except Exception as e:
            print(f"❌ [Auto-Activate] Erreur génération carte : {e}")
            return False
    
    def activate_all_guards(self):
        """Active TOUS les guards du manifest"""
        print("\n⚡ [Auto-Activate] Démarrage de l'activation automatique...")
        print("=" * 70)
        
        config = self.load_manifest()
        guards_to_activate = config.get("active_guards", [])
        
        self.stats["total_guards"] = len(guards_to_activate)
        
        # Active chaque guard
        for guard_name in guards_to_activate:
            if guard_name == "guard_auto_activate.py":
                continue  # Ne pas s'activer soi-même
            
            success = self.activate_guard(guard_name)
            if success:
                self.stats["activated"] += 1
            else:
                self.stats["failed"] += 1
            
            time.sleep(0.5)  # Petit délai entre chaque activation
        
        # Génère la carte automatiquement
        self.generate_cybermap()
        
        # Résumé
        print("=" * 70)
        print(f"✅ [Auto-Activate] {self.stats['activated']}/{self.stats['total_guards']} guards activés")
        if self.failed_guards:
            print(f"❌ Échecs : {', '.join(self.failed_guards)}")
        print(f"🗺️ Carte Leaflet : générée automatiquement")
        print("=" * 70)
        
        return self.stats
    
    def restart_failed_guards(self):
        """Tente de redémarrer les guards échoués"""
        for guard_name in self.failed_guards:
            print(f"🔄 [Auto-Activate] Nouvelle tentative : {guard_name}")
            time.sleep(2)
            self.activate_guard(guard_name)
    
    def get_status(self):
        """Retourne le statut de l'auto-activation"""
        return {
            **self.stats,
            "uptime": time.time() - self.stats["start_time"],
            "active_guards": list(self.active_guards.keys()),
            "failed_guards": self.failed_guards
        }

# ============================================================================
# === POINTS D'ENTRÉE ========================================================
# ============================================================================

_auto_activate_manager = None

def start_guard():
    """Point d'entrée pour Kerberos — Active TOUS les guards automatiquement"""
    global _auto_activate_manager
    
    print("\n⚡ [Auto-Activate] Initialisation...")
    
    _auto_activate_manager = AutoActivateManager()
    
    # Démarre l'activation en thread (non-bloquant)
    def activation_thread():
        _auto_activate_manager.activate_all_guards()
        
        # Tente de redémarrer les guards échoués après 5s
        time.sleep(5)
        if _auto_activate_manager.failed_guards:
            _auto_activate_manager.restart_failed_guards()
    
    thread = threading.Thread(target=activation_thread, daemon=True, name="AutoActivate")
    thread.start()
    
    print("✅ [Auto-Activate] Guard actif — Activation en cours...")
    return thread

def get_status():
    """Retourne le statut de l'auto-activation"""
    if _auto_activate_manager:
        return _auto_activate_manager.get_status()
    return None

def run():
    """Test standalone"""
    print("""
╔════════════════════════════════════════════════════════════╗
║  ⚡ KERBEROS AUTO-ACTIVATE — Activation Automatique       ║
║                                                            ║
║  • Active TOUS les guards au démarrage                    ║
║  • Génère la carte Leaflet automatiquement                ║
║  • Redémarre les guards échoués                           ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    manager = AutoActivateManager()
    stats = manager.activate_all_guards()
    
    print(f"\n📊 Statistiques :")
    print(f"   Total guards : {stats['total_guards']}")
    print(f"   Activés : {stats['activated']}")
    print(f"   Échoués : {stats['failed']}")
    print(f"   Uptime : {stats['uptime']:.1f}s")

if __name__ == "__main__":
    run()