# guard_no_shodan.py — v0.1 — (-;
# Bloque les requêtes vers Shodan/Censys/Zoomeye via hosts + netsh (Windows)

import os
import subprocess

SHODAN_HOSTS = [
    "shodan.io",
    "www.shodan.io",
    "censys.io",
    "www.censys.io",
    "zoomeye.org",
    "www.zoomeye.org",
    "fofa.so",
    "hunter.io"
]

def block_shodan():
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    backup_path = hosts_path + ".kerberos.bak"
    
    # Sauvegarde si pas déjà faite
    if not os.path.exists(backup_path):
        try:
            shutil.copy2(hosts_path, backup_path)
        except:
            pass
    
    # Lecture actuelle
    try:
        with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except:
        lines = []
    
    # Ajout des blocages (sans doublon)
    new_entries = []
    for host in SHODAN_HOSTS:
        entry = f"127.0.0.1 {host}\n"
        if entry not in lines and not any(host in line for line in lines):
            new_entries.append(entry)
    
    if new_entries:
        with open(hosts_path, "a", encoding="utf-8") as f:
            f.write("\n# === KERBEROS — guard_no_shodan.py — (-; ===\n")
            f.writelines(new_entries)
        print("[SHODAN] ✅ Bloqué via hosts — (-;")
    else:
        print("[SHODAN] ℹ️ Déjà bloqué — (-;")

    # Option : firewall Windows (netsh)
    try:
        for host in SHODAN_HOSTS:
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name=KERBEROS_block_{host}", "dir=out",
                "action=block", f"remoteip={host}"
            ], capture_output=True, text=True)
        print("[FIREWALL] 🔒 Règles netsh ajoutées — (-;")
    except:
        print("[FIREWALL] ⚠️ Accès refusé (exécuter en admin) — (-;")

if __name__ == "__main__":
    block_shodan()