#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# kerberos_brain.py — Le Cœur de Kerberos
# GPLv3 — White hat only | Pas de trace. Pas de nuage. Juste du code qui protège. (-;

import os
import sys
import time
import json
import threading
from pathlib import Path
from datetime import datetime

# === CONFIGURATION — Racine Kerberos ===
ROOT = Path(__file__).parent.parent  # D:\KERBEROS.SDS.WIN.7-10
LOGS_DIR = ROOT / "logs"
APPRENTISSAGE_DIR = ROOT / "apprentissage"
REPORTS_DIR = ROOT / "reports"
GUARDS_DIR = ROOT / "guards"

# Création silencieuse des dossiers critiques
for d in [LOGS_DIR, APPRENTISSAGE_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# === ÉTAT GLOBAL DU SYSTÈME ===
état = {
    "timestamp": 0,
    "menace_active": False,
    "niveau_confiance": 1.0,
    "guards_ok": [],
    "guards_hors_ligne": [],
    "derniere_decision": "",
    "attaques_bloquees": 0,
    "popups_neutralisees": 0,
    "trackers_interceptes": 0,
    "mode": "veille",  # veille | vigilance | alerte | royal_clean
}

# === BUS INTERNE — communication sans réseau ===
_bus_messages = []
_bus_lock = threading.Lock()

def brain_subscribe(guard_name, callback):
    """Un guard s’abonne aux décisions du cerveau."""
    pass  # implémenté via `brain_publish` + écoute active

def brain_publish(from_guard, type_msg, payload):
    """Le cerveau diffuse une décision — tous les guards écoutent."""
    with _bus_lock:
        msg = {
            "from": "kerberos_brain",
            "to": "all",
            "type": type_msg,
            "payload": payload,
            "timestamp": time.time()
        }
        _bus_messages.append(msg)
        # Sauvegarde immédiate dans les frames
        frame_path = LOGS_DIR / "sim.frames" / f"frame_{int(time.time()*1000):012d}.json"
        frame_path.parent.mkdir(parents=True, exist_ok=True)
        frame_path.write_text(json.dumps(msg, indent=2), encoding="utf-8")
        # Log
        print(f"[🧠 BRAIN] {type_msg} → {payload}")

# === MÉMOIRE — apprentissage local ===
def charger_memoire():
    path = APPRENTISSAGE_DIR / "derniere_decision.txt"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def sauver_decision(decision: str):
    état["derniere_decision"] = decision
    # Sauvegarde dans mémoire + logs
    (APPRENTISSAGE_DIR / "derniere_decision.txt").write_text(decision, encoding="utf-8")
    with open(LOGS_DIR / "kerberos.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] DECISION: {decision}\n")

# === DÉCISIONS AUTONOMES — logique explicite, pas d’IA ===
def evaluer_menace(niveau):
    """Retourne ('veille', 'vigilance', 'alerte', 'royal_clean')"""
    if niveau == 0:
        return "veille"
    elif niveau <= 3:
        return "vigilance"
    elif niveau <= 10:
        return "alerte"
    else:
        return "royal_clean"  # mode éthique — pas de honeypot, mais surveillance + rapport immédiat

def traiter_signal(signal):
    """Appelé par les guards via `com/inbox/` ou directement."""
    type_signal = signal.get("type")
    source = signal.get("from", "inconnu")

    if type_signal == "POPUP_DETECTE":
        état["popups_neutralisees"] += 1
    elif type_signal == "TRACKER_INTERCEPTE":
        état["trackers_interceptes"] += 1
    elif type_signal == "REGISTRE_MODIFIE":
        état["menace_active"] = True

    # Calcul du niveau global
    niveau = état["popups_neutralisees"] + 2 * état["trackers_interceptes"] + 5 * int(état["menace_active"])
    nouveau_mode = evaluer_menace(niveau)

    if nouveau_mode != état["mode"]:
        décision = f"Passage en mode {nouveau_mode.upper()} — {état['popups_neutralisees']} popups, {état['trackers_interceptes']} trackers"
        sauver_decision(décision)
        brain_publish("brain", "MODE_CHANGE", {
            "ancien": état["mode"],
            "nouveau": nouveau_mode,
            "raison": décision
        })
        état["mode"] = nouveau_mode

    état["timestamp"] = time.time()

# === INTERFACE PUBLIQUE — pour kerberos.py ===
class KerberosBrain:
    def __init__(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[🧠] Kerberos Brain → Démarré.")

    def _loop(self):
        # Charge la mémoire au démarrage
        decision = charger_memoire()
        if decision:
            print(f"[🧠] Mémoire chargée : {decision}")
            sauver_decision(decision)

        # Écoute passive via dossier `com/inbox/`
        inbox = ROOT / "com" / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        while self.running:
            try:
                for f in inbox.glob("*.json"):
                    try:
                        signal = json.loads(f.read_text(encoding="utf-8"))
                        traiter_signal(signal)
                        f.rename(f.parent.parent / "outbox" / f.name)  # archive
                    except Exception as e:
                        print(f"[🧠] Erreur lecture signal {f}: {e}")
                    time.sleep(0.1)
            except Exception as e:
                print(f"[🧠] Erreur boucle brain : {e}")
            time.sleep(1)

    def get_state(self):
        return état.copy()

    def generate_report(self):
        """Génère un rapport clair, signé, exportable — comme Nassa l’exige."""
        now = datetime.now()
        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Rapport Cérébral — Kerberos</title></head>
<body style="font-family:Consolas;background:#0a0a0a;color:#00ccff;padding:20px">
<h1>🧠 Rapport Cérébral — {now.strftime('%d/%m/%Y %H:%M')}</h1>
<p><b>Mode actuel :</b> <span style="color:#ff6666">{état['mode'].upper()}</span></p>
<p><b>Popups neutralisées :</b> {état['popups_neutralisees']}</p>
<p><b>Trackers interceptés :</b> {état['trackers_interceptes']}</p>
<p><b>Dernière décision :</b><br><code>{état['derniere_decision']}</code></p>
<hr>
<footer style="font-size:0.8em;color:#555">
Kerberos v4.0 — Cerveau autonome — <a href="https://github.com/victorpozen/kerberos">GitHub</a>
<br>Licence : <a href="https://www.gnu.org/licenses/gpl-3.0.txt">GPLv3</a>
<br>Soutien : <a href="https://liberapay.com/EthicalKerberos/">Liberapay</a>
</footer>
</body>
</html>"""
        rapport_path = REPORTS_DIR / f"cerveau_{int(time.time())}.html"
        rapport_path.write_text(html, encoding="utf-8")
        return rapport_path

# === POINT D’ENTRÉE — pour import direct ===
if __name__ == "__main__":
    brain = KerberosBrain()
    print("[🧠] Mode démo — envoi d’un signal de test...")
    traiter_signal({"from": "guard_nassa", "type": "TRACKER_INTERCEPTE", "url": "ads-network.com"})
    print("[🧠] État :", état)
    print("[🧠] Rapport généré :", brain.generate_report())
    input("Appuyez sur Entrée pour quitter…")