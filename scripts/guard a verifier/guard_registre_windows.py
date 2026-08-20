#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
guard_registre_windows.py — v2 (sans subprocess, sans risque)
Analyse et correction éthique du registre Windows — local, transparent, HDD-safe.
GPLv3 – Victor Pozen `(-;`
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# === TENTATIVE D'IMPORT WINREG (safe) ===
try:
    import winreg as wr
    _HAS_WINREG = True
except ImportError:
    _HAS_WINREG = False

# === CONFIGURATION ===
KERBEROS_ROOT = Path(__file__).parent.parent
REPORTS_DIR = KERBEROS_ROOT / "guards" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# === VULNÉRABILITÉS À VÉRIFIER (HDD-friendly, pas de flood) ===
CHECKS = [
    {
        "name": "Run Keys",
        "path": r"Software\Microsoft\Windows\CurrentVersion\Run",
        "hkey": wr.HKEY_CURRENT_USER,
        "fix": True,
        "desc": "Programmes lancés au démarrage → possible persistence"
    },
    {
        "name": "RunOnce Keys",
        "path": r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
        "hkey": wr.HKEY_CURRENT_USER,
        "fix": True,
        "desc": "Exécution différée → attaque discrète"
    },
    {
        "name": "Shell Open Command",
        "path": r"Software\Classes\exefile\shell\open\command",
        "hkey": wr.HKEY_CURRENT_USER,
        "fix": False,
        "desc": "Redirection de .exe → risque d’injection"
    },
    {
        "name": "SChannel DES Cipher",
        "path": r"SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Ciphers\DES 56/56",
        "hkey": wr.HKEY_LOCAL_MACHINE,
        "fix": True,
        "desc": "Chiffrement faible (DES) → cassable par Grover (28 bits)"
    }
]

def _read_reg_value(hkey, path, name=""):
    """Lecture safe d'une valeur de registre."""
    if not _HAS_WINREG:
        return None
    try:
        with wr.OpenKey(hkey, path, 0, wr.KEY_READ) as key:
            value, _ = wr.QueryValueEx(key, name)
            return value
    except FileNotFoundError:
        return None
    except Exception:
        return None

def _write_reg_value(hkey, path, name, value, vtype=wr.REG_SZ):
    """Écriture safe — sans subprocess, sans shutil."""
    if not _HAS_WINREG:
        return False
    try:
        with wr.CreateKey(hkey, path) as key:
            wr.SetValueEx(key, name, 0, vtype, value)
        return True
    except Exception:
        return False

def _scan_registry():
    """Retourne une liste de vulnérabilités détectées."""
    issues = []
    for check in CHECKS:
        try:
            value = _read_reg_value(check["hkey"], check["path"])
            # Si la clé existe, elle est potentiellement active
            if value is not None:
                issues.append({
                    "check": check["name"],
                    "path": check["path"],
                    "value": str(value)[:100],
                    "risk": "Élevé" if "DES" in check["name"] else "Modéré",
                    "fixable": check["fix"]
                })
        except Exception as e:
            issues.append({
                "check": check["name"],
                "error": str(e),
                "risk": "Erreur",
                "fixable": False
            })
    return issues

def _generate_report(issues, fixed=[]):
    """Génère un rapport HTML local — jamais envoyé."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = REPORTS_DIR / f"registre_audit_{timestamp}.html"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Kerberos — Audit Registre</title>
<style>
body {{ font-family: Consolas, monospace; background: #0a0a0a; color: #00ccff; padding: 20px; }}
h1 {{ color: #ff6666; }}
.ok {{ color: #00ff99; }}
.warn {{ color: #ffcc00; }}
.crit {{ color: #ff3366; }}
pre {{ background: #111; padding: 10px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>🛡️ Kerberos — Audit Registre Windows</h1>
<p><b>Date :</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>
<b>Système :</b> Windows (local — aucun réseau utilisé)</p>

<h2>🔍 Vulnérabilités détectées ({len(issues)})</h2>
"""
    for i, issue in enumerate(issues, 1):
        color = "crit" if issue["risk"] == "Élevé" else "warn"
        html += f'<p><span class="{color}">⚠️ #{i} {issue["check"]}</span><br>'
        html += f'→ Chemin : <code>{issue["path"]}</code><br>'
        if "value" in issue:
            html += f'→ Valeur : <code>{issue["value"]}</code><br>'
        html += f'→ Risque : {issue["risk"]}'
        if issue.get("fixable"):
            html += ' <span class="ok">[🛠️ Correctible]</span>'
        html += '</p>'

    if fixed:
        html += f'<h2 class="ok">✅ Corrections appliquées ({len(fixed)})</h2>'
        for f in fixed:
            html += f'<p class="ok">→ {f}</p>'

    html += f"""
<hr>
<footer style="font-size:0.8em;color:#555">
Kerberos v2.0 — Audit local — White hat only.<br>
GPLv3 – <a href="https://github.com/victorpozen/kerberos">GitHub</a> • 
<a href="https://fr.liberapay.com/EthicalKerberos">Liberapay</a><br>
`(-;`
</footer>
</body>
</html>"""

    try:
        html_path.write_text(html, encoding="utf-8")
        return html_path
    except Exception:
        return None

def run(fix=False):
    """
    Lance l'audit du registre.
    - fix=False → rapport seul (mode éthique par défaut)
    - fix=True → correction des vulnérabilités marquées 'fixable'
    """
    print("[🔍] Guard Registre — Audit local (sans subprocess)…")
    
    if not _HAS_WINREG:
        print("[!] winreg indisponible → audit impossible (Win7/10 requis)")
        return {"status": "error", "reason": "winreg manquant"}

    issues = _scan_registry()
    
    fixed = []
    if fix:
        print("[🛠️] Correction des vulnérabilités éligibles…")
        for issue in issues:
            if issue.get("fixable"):
                for check in CHECKS:
                    if check["name"] == issue["check"] and check["fix"]:
                        # Désactiver DES ou effacer Run key
                        success = _write_reg_value(
                            check["hkey"], check["path"],
                            "Enabled", 0, wr.REG_DWORD
                        ) if "DES" in check["name"] else \
                        _write_reg_value(
                            check["hkey"], check["path"], "", "", wr.REG_SZ
                        )
                        if success:
                            fixed.append(f"Corrigé : {check['name']}")
                        else:
                            fixed.append(f"❌ Échec correction : {check['name']}")

    report_path = _generate_report(issues, fixed)
    if report_path:
        print(f"[📄] Rapport généré : {report_path.name}")
    else:
        print("[!] Échec génération rapport")

    return {
        "status": "ok" if not issues else "alert",
        "issues": len(issues),
        "fixed": len(fixed),
        "report": str(report_path) if report_path else None
    }

# === CLI (optionnel) ===
if __name__ == "__main__":
    fix_mode = "--fix" in sys.argv
    result = run(fix=fix_mode)
    if result["status"] == "ok":
        print("✅ Registre conforme.")
    else:
        print(f"⚠️ {result['issues']} vulnérabilité(s) détectée(s).")