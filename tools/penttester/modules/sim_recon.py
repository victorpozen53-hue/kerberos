#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 sim_recon — Simulation Reconnaissance / Port Scan local
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import time
import socket
import platform
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_recon"
MODULE_LABEL = "Recon / Scan"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "recon"

# Ports courants à scanner sur localhost
_PORTS = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143,
          443, 445, 993, 995, 1433, 3306, 3389, 5432,
          5900, 6379, 8080, 8443, 8888, 9200, 27017]


def _probe_port(host: str, port: int, timeout: float = 0.3) -> dict:
    """Teste si un port est ouvert — inoffensif"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return {"port": port, "open": result == 0,
                "service": _port_service(port)}
    except Exception:
        return {"port": port, "open": False, "service": _port_service(port)}


def _port_service(port: int) -> str:
    services = {21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
                53: "DNS", 80: "HTTP", 110: "POP3", 135: "RPC",
                139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
                993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 3306: "MySQL",
                3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
                6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
                8888: "Jupyter", 9200: "Elasticsearch", 27017: "MongoDB"}
    return services.get(port, "Unknown")


def run(target: str = "127.0.0.1", callback=None) -> dict:
    global _running
    _running = True
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {"module": MODULE_NAME, "target": target,
               "started": datetime.now().isoformat(),
               "events": [], "open_ports": [], "files": [], "status": "running"}

    def log(msg):
        results["events"].append(msg)
        if callback: callback(msg)

    log(f"🔍 Démarrage Recon sur {target}...")
    log(f"   {len(_PORTS)} ports à scanner — intranet/localhost uniquement")

    # ── Scan de ports ─────────────────────────────────────────────────────
    open_ports = []
    for i, port in enumerate(_PORTS):
        if not _running:
            break
        probe = _probe_port(target, port)
        if probe["open"]:
            open_ports.append(probe)
            results["open_ports"].append(probe)
            log(f"  🟢 Port {port}/tcp OUVERT — {probe['service']}")
        if i % 8 == 0 and i > 0:
            log(f"  Scan : {i}/{len(_PORTS)} ports...")
        time.sleep(0.05)

    log(f"✅ Scan terminé : {len(open_ports)} port(s) ouvert(s) sur {target}")

    # ── Rapport recon JSON ────────────────────────────────────────────────
    import json
    time.sleep(0.2)
    f1 = _OUT_DIR / f"recon_{target.replace('.','_')}.json"
    report = {
        "note":       "KERBEROS_PENTEST_TEST — rapport de reconnaissance",
        "target":     target,
        "timestamp":  datetime.now().isoformat(),
        "platform":   platform.system(),
        "open_ports": open_ports,
        "total":      len(open_ports),
    }
    f1.write_text(json.dumps(report, indent=2), encoding="utf-8")
    results["files"].append(str(f1))
    log(f"✅ Rapport JSON : {f1.name}")

    # ── Script recon signé (YARA AI_Powered_Recon_Script) ────────────────
    time.sleep(0.2)
    f2 = _OUT_DIR / "fake_ai_recon.py"
    f2.write_text(
        "#!/usr/bin/env python3\n"
        "# KERBEROS PENTEST TEST — Signature recon IA (inoffensif)\n\n"
        "# YARA $scan3 : socket.connect_ex\n"
        "# YARA $ai3  : ollama.chat\n"
        "# YARA $auto2 : for target in\n\n"
        "FAKE_TARGETS = ['192.168.1.1', '192.168.1.2']\n\n"
        "def fake_recon():\n"
        "    for target in FAKE_TARGETS:  # YARA $auto2\n"
        "        # socket.connect_ex((target, 80))  # YARA $scan3 — commenté\n"
        "        # ollama.chat({'prompt': f'analyse {target}'})  # YARA $ai3 — commenté\n"
        "        print(f'[FAKE] scan simulé : {target}')\n\n"
        "if __name__ == '__NEVER__':\n"
        "    fake_recon()\n",
        encoding="utf-8")
    results["files"].append(str(f2))
    log(f"✅ Script : {f2.name}")
    log("   → YARA doit détecter : AI_Powered_Recon_Script")

    log(f"📊 Recon terminé — {len(open_ports)} ports ouverts")
    log("   → guard_ai_shield.py scan_processes() doit logger le scan")

    results["status"] = "completed"
    results["finished"] = datetime.now().isoformat()
    _running = False
    return results


def stop():
    global _running
    _running = False


def get_info() -> dict:
    return {"name": MODULE_NAME, "label": MODULE_LABEL,
            "description": "Port scan localhost + signatures recon IA",
            "version": "1.0", "targets": ["guard_ai_shield.py", "guard_netshield"]}
