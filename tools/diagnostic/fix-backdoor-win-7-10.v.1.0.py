#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix-backdoor-win-7-10.py — Correctif éthique pour backdoors Windows
Licence : GNU General Public License v3.0 (GPLv3)
Copyright (C) 2025 Victor.pozen & Mirko — Projet Kerberos

Ce programme est un logiciel libre : vous pouvez le redistribuer
et/ou le modifier selon les termes de la Licence Publique Générale
GNU telle que publiée par la Free Software Foundation, soit la
version 3 de la licence, ou (à votre choix) toute version ultérieure.

Ce programme est distribué dans l'espoir qu'il sera utile,
mais SANS AUCUNE GARANTIE ; sans même la garantie implicite de
QUALITÉ MARCHANDE ou D'ADÉQUATION À UN USAGE PARTICULIER.
Voir la Licence Publique Générale GNU pour plus de détails.

Vous devriez avoir reçu une copie de la Licence Publique Générale
GNU avec ce programme. Si ce n'est pas le cas, consultez :
<https://www.gnu.org/licenses/gpl-3.0.txt>
"""

import os
import sys
import subprocess
import ctypes
import datetime
import tempfile

# === CONFIGURATION ===
LOG_FILE = os.path.join(tempfile.gettempdir(), "fix-backdoor.log")
BACKUP_DIR = os.path.join(tempfile.gettempdir(), "kerberos_backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run(args, timeout=10):
    """Exécute une commande CMD, retourne (code, stdout, stderr)"""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="cp850",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def backup_registry(key_path, value_name=None):
    """Backup une clé ou valeur du registre → .reg.bak"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = key_path.replace("\\", "_").replace(" ", "_")
        if value_name:
            safe_name += f"_{value_name}"
        backup_path = os.path.join(BACKUP_DIR, f"reg_{safe_name}_{timestamp}.reg.bak")
        # Export complet de la clé
        code, out, err = run([
            "reg", "export", key_path, backup_path, "/y"
        ])
        if code == 0:
            log(f"✅ Backup registre : {key_path} → {os.path.basename(backup_path)}", "DEBUG")
            return backup_path
        else:
            log(f"⚠️ Backup échoué : {key_path} ({err})", "WARN")
    except Exception as e:
        log(f"❌ Erreur backup : {e}", "ERROR")
    return None

def set_reg_value(key, value, data, typ="REG_DWORD"):
    """Définit une valeur dans le registre (avec backup)"""
    backup_registry(key)
    code, out, err = run([
        "reg", "add", key, "/v", value, "/t", typ, "/d", str(data), "/f"
    ])
    if code == 0:
        log(f"✅ Registre : {key}\\{value} = {data} ({typ})", "INFO")
    else:
        log(f"❌ Registre échoué : {key}\\{value} ({err})", "ERROR")
    return code == 0

def stop_and_disable(service):
    """Arrête et désactive un service (avec backup de l'état)"""
    # Sauvegarde état actuel
    code, out, _ = run(["sc", "query", service])
    was_running = "RUNNING" in out or "START_PENDING" in out
    log(f"🔧 Service {service} : état initial = {'actif' if was_running else 'inactif'}", "DEBUG")

    # Arrêt
    run(["sc", "stop", service])
    # Désactivation
    code, _, err = run(["sc", "config", service, "start=", "disabled"])
    if code == 0:
        log(f"✅ Service {service} : arrêté + désactivé", "INFO")
    else:
        log(f"❌ Service {service} : échec désactivation ({err})", "ERROR")
    return code == 0

def add_firewall_rule(name, port, protocol="TCP", action="block"):
    """Ajoute une règle pare-feu (safe : autorise localhost)"""
    # Autorise localhost
    run([
        "netsh", "advfirewall", "firewall", "add", "rule",
        "name=" + name + "_Local",
        "dir=in",
        "action=allow",
        "protocol=" + protocol,
        "localport=" + str(port),
        "remoteip=127.0.0.1,::1",
        "profile=any",
        "enable=yes"
    ])
    # Bloque le reste
    code, _, err = run([
        "netsh", "advfirewall", "firewall", "add", "rule",
        "name=" + name,
        "dir=in",
        "action=" + action,
        "protocol=" + protocol,
        "localport=" + str(port),
        "remoteip=any",
        "profile=private,public",
        "enable=yes"
    ])
    if code == 0:
        log(f"✅ Pare-feu : {name} → port {port}/{protocol} bloqué (sauf localhost)", "INFO")
    else:
        log(f"❌ Pare-feu échoué : {name} ({err})", "ERROR")
    return code == 0

def rollback():
    """Restaure les backups .reg.bak les plus récents"""
    log("🔄 Rollback : restauration des backups...", "INFO")
    backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".reg.bak")]
    backups.sort(reverse=True)  # plus récents d'abord
    for bak in backups[:5]:  # max 5 restores
        path = os.path.join(BACKUP_DIR, bak)
        code, _, err = run(["reg", "import", path])
        if code == 0:
            log(f"✅ Restauré : {bak}", "INFO")
        else:
            log(f"⚠️ Échec restauration : {bak} ({err})", "WARN")
    log("✅ Rollback terminé.", "INFO")

def apply_fixes():
    log("🛡️ Démarrage de Kerberos Fix Backdoor — Win7/10", "INFO")
    log(f"📝 Log : {LOG_FILE}", "DEBUG")
    log(f"📁 Backups : {BACKUP_DIR}", "DEBUG")

    if not is_admin():
        log("❌ Erreur : exécution requise en Administrateur.", "ERROR")
        return False

    success = True

    # 1. SMB / LanmanServer
    success &= stop_and_disable("LanmanServer")

    # 2. SMBv1
    success &= set_reg_value(
        r"HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters",
        "SMB1", 0, "REG_DWORD"
    )

    # 3. Spooler (PrintNightmare)
    success &= stop_and_disable("Spooler")

    # 4. RDP (BlueKeep)
    success &= set_reg_value(
        r"HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server",
        "fDenyTSConnections", 1, "REG_DWORD"
    )

    # 5. Pare-feu RPC 135 (safe)
    success &= add_firewall_rule("Kerberos_RPC_135_Block", 135, "TCP", "block")

    # 6. DCOM
    success &= set_reg_value(
        r"HKLM\SOFTWARE\Microsoft\Ole",
        "EnableDCOM", "N", "REG_SZ"
    )

    # 7. LLMNR
    success &= set_reg_value(
        r"HKLM\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient",
        "EnableMulticast", 0, "REG_DWORD"
    )

    # 8. Pare-feu ON
    run(["netsh", "advfirewall", "set", "allprofiles", "state", "on"])
    log("✅ Pare-feu : activé", "INFO")

    log("✅ Correctifs appliqués." if success else "⚠️ Certains correctifs ont échoué.", "INFO")
    return success

# === LANCEMENT ===
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="🛡️ Kerberos Fix Backdoor — Win7/10 (GPLv3)",
        epilog="Projet éthique — Aucune dépendance réseau — 100% local"
    )
    parser.add_argument("--rollback", action="store_true", help="Restaurer les backups")
    parser.add_argument("--quiet", action="store_true", help="Mode silencieux (log uniquement)")
    args = parser.parse_args()

    if args.quiet:
        sys.stdout = open(os.devnull, 'w')

    if args.rollback:
        rollback()
    else:
        apply_fixes()
        log("ℹ️ Redémarrage recommandé pour appliquer tous les correctifs.", "INFO")

    if not args.quiet:
        input("Appuyez sur Entrée pour quitter...")