#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Test CyberMap Inject — Injecte de fausses attaques dans guard_cybermap.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Usage : python test_cybermap_inject.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import sys
import time
import random
from pathlib import Path

# Ajoute le dossier guards au path
GUARDS_DIR = Path(__file__).parent / "guards"
sys.path.insert(0, str(GUARDS_DIR.parent))

from guards.guard_cybermap import enable_test_mode, inject_test_connection, clear_test_connections

print("""
╔════════════════════════════════════════════════════════════╗
║  🧪 KERBEROS CYBERMAP — TEST INJECTOR                    ║
║                                                            ║
║  • Injecte de fausses connexions dans guard_cybermap.py  ║
║  • Teste l'UI sans vrai trafic réseau                    ║
║  • Commandes : a = attaque, c = clear, q = quit          ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
╚════════════════════════════════════════════════════════════╝
""")

# Active le mode test
enable_test_mode(True)

countries = [
    {"country": "Russie", "city": "Moscou", "lat": 55.7558, "lon": 37.6173},
    {"country": "Chine", "city": "Pékin", "lat": 39.9042, "lon": 116.4074},
    {"country": "États-Unis", "city": "New York", "lat": 40.7128, "lon": -74.0060},
    {"country": "Iran", "city": "Téhéran", "lat": 35.6892, "lon": 51.3890},
    {"country": "Corée du Nord", "city": "Pyongyang", "lat": 39.0392, "lon": 125.7625},
]

print("✅ Mode test ACTIVÉ — Les attaques apparaîtront sur CyberMap")
print("   Ouvrir : ⚙️ Gestion → 🌍 Carte → OUVRIR CYBERMAP DYNAMIQUE")
print()

try:
    while True:
        cmd = input("> ").strip().lower()
        
        if cmd == "a":
            # Injecte une attaque
            source = random.choice(countries)
            inject_test_connection(source)
            print(f"🚨 Attaque injectée depuis {source['country']}")
        
        elif cmd == "aa":
            # Injecte 5 attaques d'un coup
            for i in range(5):
                source = random.choice(countries)
                inject_test_connection(source)
            print(f"🚨 5 attaques injectées !")
        
        elif cmd == "c":
            # Clear
            clear_test_connections()
            print("🧹 Connexions test effacées")
        
        elif cmd == "q":
            # Quit
            enable_test_mode(False)
            clear_test_connections()
            print("✅ Mode test désactivé")
            break
        
        elif cmd == "help":
            print("""
            Commandes :
              a   = Injecter 1 attaque
              aa  = Injecter 5 attaques
              c   = Effacer toutes les attaques test
              q   = Quitter (désactive mode test)
              help = Afficher cette aide
            """)
        
        else:
            print("? Commande inconnue (tapez 'help')")

except KeyboardInterrupt:
    enable_test_mode(False)
    clear_test_connections()
    print("\n✅ Arrêt propre")