#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔒 sim_ransomware — Simulation comportement ransomware fake
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Simule les PATTERNS d'un ransomware IA-généré :
  - Création massive de fichiers (burst FS → watchdog)
  - Renommage avec extension .encrypted (YARA pattern)
  - Script avec signature YARA AI_Generated_Ransomware_Pattern
  - Note de rançon fake
AUCUN fichier réel n'est chiffré.
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import os
import time
import json
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_ransomware"
MODULE_LABEL = "Ransomware Fake"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "ransomware"


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

    log("🔒 Démarrage simulation Ransomware IA-généré...")

    # ── Test 1 : Script ransomware signé (YARA) ───────────────────────────
    time.sleep(0.2)
    f1 = _OUT_DIR / "fake_ransomware.py"
    f1.write_text('''#!/usr/bin/env python3
# KERBEROS PENTEST TEST — Signature ransomware IA (inoffensif)
# Contient les patterns YARA sans chiffrer quoi que ce soit

# YARA $enc2 : "Fernet.encrypt"
# from cryptography.fernet import Fernet  # commenté
FAKE_KEY = b"KERBEROS_TEST_KEY_NOT_REAL_FERNET_KEY_PADDING="

# YARA $walk2 : "rglob("
def fake_encrypt_files(root):
    for f in Path(root).rglob("*"):  # rglob pattern YARA
        print(f"[FAKE] simulé chiffrement : {f.name}")
        # Fernet.encrypt(data)  # jamais exécuté

# YARA $pay2 : "monero"
RANSOM_WALLET = "FAKE_MONERO_WALLET_ADDRESS_FOR_TEST_ONLY"

# YARA $ext2 : ".locked"
ENCRYPTED_EXTENSION = ".locked"

# YARA $pay4 : "ransom"
RANSOM_NOTE = "ransom_note_KERBEROS_TEST.txt"

if __name__ == "__NEVER__":
    fake_encrypt_files("/tmp")
''', encoding="utf-8")
    results["files"].append(str(f1))
    log(f"✅ Créé : {f1.name}")
    log("   → YARA doit détecter : AI_Generated_Ransomware_Pattern")

    # ── Test 2 : Burst création fichiers (watchdog FS) ────────────────────
    time.sleep(0.2)
    log("📁 Création burst de fichiers (simule chiffrement massif)...")
    log("   → AI Shield watchdog FS doit détecter l'activité anormale")

    burst_dir = _OUT_DIR / "fake_encrypted_files"
    burst_dir.mkdir(exist_ok=True)

    created = 0
    # Créer 60 fichiers rapidement → dépasse FILE_CREATE_THRESHOLD (50/min)
    for i in range(60):
        if not _running:
            break
        f = burst_dir / f"document_{i:03d}.locked"
        f.write_text(
            f"KERBEROS_PENTEST_TEST\n"
            f"Fichier fake chiffré #{i}\n"
            f"Contenu inoffensif — test watchdog FS\n"
            f"Extension .locked pour signature YARA\n",
            encoding="utf-8")
        created += 1
        if i % 10 == 0:
            log(f"  📁 {created}/60 fichiers .locked créés...")
        time.sleep(0.02)

    log(f"✅ {created} fichiers .locked créés en burst")
    log("   → Watchdog FS : burst d'écriture disque détectable")

    # ── Test 3 : Note de rançon fake ─────────────────────────────────────
    time.sleep(0.2)
    f3 = _OUT_DIR / "RANSOM_NOTE_FAKE.txt"
    f3.write_text(
        "=== KERBEROS PENTEST TEST ===\n"
        "Ceci est une FAUSSE note de rançon.\n"
        "Aucun fichier n'a été chiffré.\n"
        "Ce fichier teste la détection des patterns ransomware.\n\n"
        "Fake bitcoin address: bc1KERBEROS_TEST_ONLY\n"
        "Fake monero address: 4KERBEROS_PENTEST_FAKE\n",
        encoding="utf-8")
    results["files"].append(str(f3))
    log(f"✅ Créé : {f3.name} (fausse note de rançon)")
    log("   → YARA pattern : $pay1 bitcoin + $pay2 monero")

    log(f"📊 Simulation terminée — {created} fichiers burst + {len(results['files'])} signatures")
    log("⏳ En attente détection Kerberos...")

    results["status"] = "completed"
    results["finished"] = datetime.now().isoformat()
    _running = False
    return results


def stop():
    global _running
    _running = False


def get_info() -> dict:
    return {"name": MODULE_NAME, "label": MODULE_LABEL,
            "description": "Burst fichiers + signatures ransomware — rien chiffré",
            "version": "1.0", "targets": ["guard_yara.py", "guard_ai_shield.py"]}
