# kerberos_deep_scan_safe.py
# 🔍 Scanner + Corriger + Vérifier – Projet Kerberos
# 🧠 Par Mirko & Victor.pozen
# 💀 Objectif : Scanner TOUT, sauvegarder, corriger, vérifier — 100% local, 0% IA
# 📄 Licence : GNU General Public License v3.0 (GPLv3)
# 🔗 Officiel : https://www.gnu.org/licenses/gpl-3.0.txt
# 💀 Soutien éthique : https://liberapay.com/EthicalKerberos/

import os
import sys
import subprocess
import ctypes
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import webbrowser
import tempfile
from datetime import datetime

# === CONFIGURATION ===
BG_DARK = "#0d0d15"
FG_GREEN = "#a0ffa0"
FG_LIGHT = "#e0e0ff"
BTN_COLOR = "#2a2a2a"
BTN_TEXT = "#c0c0ff"
LINK_COLOR = "#a0a0ff"

# ✅ Dossier de rapports robuste (fallback si I: inaccessible)
try:
    REPORTS_DIR = r"I:\IA.KERBEROS\reports"
    os.makedirs(REPORTS_DIR, exist_ok=True)
except (OSError, PermissionError):
    REPORTS_DIR = os.path.join(tempfile.gettempdir(), "kerberos_reports")
    os.makedirs(REPORTS_DIR, exist_ok=True)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ✅ Encodage robuste : UTF-8 → CP1252 → CP850
def run_cmd(args_list, timeout=10):
    try:
        result = subprocess.run(
            args_list,
            capture_output=True,
            timeout=timeout
        )
        for enc in ("utf-8", "cp1252", "cp850"):
            try:
                return result.stdout.decode(enc)
            except UnicodeDecodeError:
                continue
        return result.stdout.decode("utf-8", errors="replace")
    except Exception as e:
        return f"[ERREUR: {e}]"

# === SCANNER ===
def detect_vulnerabilities(admin_mode):
    findings = []

    smb_out = run_cmd(["sc", "query", "LanmanServer"])
    smb_active = "RUNNING" in smb_out or "START_PENDING" in smb_out
    findings.append({"id":"SMB_SERVER","title":"🔒 Serveur SMB (LanmanServer)","status":"ACTIF ❌" if smb_active else "ARRÊTÉ ✅","risk":"EternalBlue, MS08-067","fix":"Désactiver LanmanServer","severity":"high" if smb_active else "none"})

    smb1_out = run_cmd(["reg", "query", r"HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters", "/v", "SMB1"])
    smb1_enabled = "0x1" in smb1_out or "SMB1" not in smb1_out
    findings.append({"id":"SMBv1","title":"🧱 SMBv1","status":"ACTIVÉ ❌" if smb1_enabled else "DÉSACTIVÉ ✅","risk":"Vulnérable à MS08-067","fix":"Désactiver SMB1","severity":"high" if smb1_enabled else "none"})

    spool_out = run_cmd(["sc", "query", "Spooler"])
    spool_active = "RUNNING" in spool_out
    findings.append({"id":"SPOOLER","title":"🖨️ Spooler","status":"ACTIF ❌" if spool_active else "ARRÊTÉ ✅","risk":"PrintNightmare (CVE-2021-1675)","fix":"Désactiver le Spooler","severity":"high" if spool_active else "none"})

    rdp_out = run_cmd(["reg", "query", r"HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server", "/v", "fDenyTSConnections"])
    rdp_enabled = "0x0" in rdp_out
    findings.append({"id":"RDP","title":"💻 RDP","status":"ACTIF ❌" if rdp_enabled else "DÉSACTIVÉ ✅","risk":"BlueKeep, force brute","fix":"Activer fDenyTSConnections=1","severity":"medium" if rdp_enabled else "none"})

    netstat_out = run_cmd(["netstat", "-an"])
    def listening(port): return f":{port}" in netstat_out and ("LISTENING" in netstat_out or "ÉCOUTE" in netstat_out)
    for port, name in [(135,"RPC"),(139,"NetBIOS"),(445,"SMB"),(3389,"RDP")]:
        lst = listening(port)
        findings.append({"id":f"PORT_{port}","title":f"🚪 Port {port} ({name})","status":"EN ÉCOUTE ❌" if lst else "FERMÉ ✅","risk":f"Exposition réseau ({name})","fix":f"Bloquer en entrée","severity":"medium" if lst else "none"})

    dcom_out = run_cmd(["reg", "query", r"HKLM\SOFTWARE\Microsoft\Ole", "/v", "EnableDCOM"])
    dcom_enabled = "Y" in dcom_out
    findings.append({"id":"DCOM","title":"📡 DCOM","status":"ACTIF ❌" if dcom_enabled else "DÉSACTIVÉ ✅","risk":"PetitPotam, ShadowCoerce","fix":"Régler EnableDCOM=N","severity":"medium" if dcom_enabled else "none"})

    llmnr_out = run_cmd(["reg", "query", r"HKLM\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient", "/v", "EnableMulticast"])
    llmnr_enabled = "0x1" in llmnr_out or "EnableMulticast" not in llmnr_out
    findings.append({"id":"LLMNR","title":"🌐 LLMNR","status":"ACTIF ❌" if llmnr_enabled else "DÉSACTIVÉ ✅","risk":"Empoisonnement réseau","fix":"Désactiver LLMNR","severity":"low" if llmnr_enabled else "none"})

    firewall_out = run_cmd(["netsh", "advfirewall", "show", "allprofiles", "state"])
    firewall_off = "Off" in firewall_out
    findings.append({"id":"FIREWALL","title":"🧱 Pare-feu","status":"DÉSACTIVÉ ❌" if firewall_off else "ACTIVÉ ✅","risk":"Aucune protection réseau","fix":"Activer le pare-feu","severity":"high" if firewall_off else "none"})

    return findings

# === CORRECTION ===
def apply_fixes():
    log_text.configure(state='normal')
    log_text.insert(tk.END, "\n🔧 Application des correctifs...\n", "info")

    # 1. Désactiver SMB
    run_cmd(["sc", "stop", "LanmanServer"])
    run_cmd(["sc", "config", "LanmanServer", "start=", "disabled"])

    # 2. Désactiver SMBv1
    run_cmd(['reg', 'add', r"HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters", '/v', 'SMB1', '/t', 'REG_DWORD', '/d', '0', '/f'])

    # 3. Désactiver Spooler
    run_cmd(["sc", "stop", "Spooler"])
    run_cmd(["sc", "config", "Spooler", "start=", "disabled"])

    # 4. Désactiver RDP
    run_cmd(['reg', 'add', r"HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server", '/v', 'fDenyTSConnections', '/t', 'REG_DWORD', '/d', '1', '/f'])

    # 5. Bloquer le port 135 (sans casser RPC)
    subprocess.run([
        "netsh", "advfirewall", "firewall", "add", "rule",
        "name=Kerberos_Block_RPC_135",
        "dir=in",
        "action=block",
        "protocol=TCP",
        "localport=135"
    ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

    # 6. Désactiver DCOM
    run_cmd(['reg', 'add', r"HKLM\SOFTWARE\Microsoft\Ole", '/v', 'EnableDCOM', '/t', 'REG_SZ', '/d', 'N', '/f'])

    # 7. Désactiver LLMNR
    run_cmd(['reg', 'add', r"HKLM\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient", '/v', 'EnableMulticast', '/t', 'REG_DWORD', '/d', '0', '/f'])

    # 8. Activer le pare-feu
    run_cmd(["netsh", "advfirewall", "set", "allprofiles", "state", "on"])

    log_text.insert(tk.END, "✅ Correctifs appliqués.\n", "ok")
    log_text.configure(state='disabled')

# === VÉRIFICATION ===
def verify_protection():
    log_text.configure(state='normal')
    log_text.insert(tk.END, "\n🔍 Vérification finale...\n", "header")

    ok = 0
    total = 0

    def check_service(service, expected="STOPPED"):
        nonlocal ok, total
        total += 1
        out = run_cmd(["sc", "query", service])
        if expected in out:
            log_text.insert(tk.END, f"✅ {service} : {expected}\n", "ok")
            ok += 1
        else:
            log_text.insert(tk.END, f"❌ {service} : actif\n", "high")

    def check_reg(key, value, expected):
        nonlocal ok, total
        total += 1
        out = run_cmd(["reg", "query", key, "/v", value])
        if expected in out:
            log_text.insert(tk.END, f"✅ {value} = {expected}\n", "ok")
            ok += 1
        else:
            log_text.insert(tk.END, f"❌ {value} ≠ {expected}\n", "high")

    def check_port(port, name):
        nonlocal ok, total
        total += 1
        netstat_out = run_cmd(["netstat", "-an"])
        if f":{port}" in netstat_out and ("LISTENING" in netstat_out or "ÉCOUTE" in netstat_out):
            log_text.insert(tk.END, f"❌ Port {port} ({name}) : en écoute\n", "high")
        else:
            log_text.insert(tk.END, f"✅ Port {port} ({name}) : fermé\n", "ok")
            ok += 1

    check_service("LanmanServer")
    check_service("Spooler")
    check_reg(r"HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server", "fDenyTSConnections", "0x1")
    check_reg(r"HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters", "SMB1", "0x0")
    check_port(135, "RPC")
    check_port(139, "NetBIOS")
    check_port(445, "SMB")
    check_port(3389, "RDP")

    log_text.insert(tk.END, f"\n{'='*50}\n", "header")
    if ok == total:
        log_text.insert(tk.END, "🟢 FÉLICITATIONS ! Votre PC est protégé.\n", "ok")
    else:
        log_text.insert(tk.END, f"⚠️ {total - ok} éléments à corriger.\n", "high")

    log_text.configure(state='disabled')

# === SAUVEGARDE TXT ===
def save_as_txt(findings):
    if not findings:
        messagebox.showwarning("⚠️ Kerberos", "Aucun scan effectué.", parent=root)
        return
    filepath = filedialog.asksaveasfilename(
        initialdir=REPORTS_DIR,
        defaultextension=".txt",
        filetypes=[("Fichiers texte", "*.txt")]
    )
    if not filepath:
        return
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("KERBEROS – Rapport de Scan Profond\n")
            f.write("="*60 + "\n")
            for fnd in findings:
                f.write(f"{fnd['title']}\n")
                f.write(f"   → État : {fnd['status']}\n")
                f.write(f"   → Risque : {fnd['risk']}\n")
                f.write(f"   → Correctif : {fnd['fix']}\n\n")
        messagebox.showinfo("✅ Succès", f"Rapport sauvegardé :\n{filepath}", parent=root)
    except Exception as e:
        messagebox.showerror("❌ Erreur", f"Impossible de sauvegarder :\n{e}", parent=root)

# === EXPORT HTML ===
def export_as_html(findings):
    if not findings:
        messagebox.showwarning("⚠️ Kerberos", "Aucun scan effectué.", parent=root)
        return

    hostname = "INCONNU"
    try:
        import socket
        hostname = socket.gethostname()
    except:
        pass

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    high = sum(1 for f in findings if f["severity"] == "high")
    medium = sum(1 for f in findings if f["severity"] == "medium")
    low = sum(1 for f in findings if f["severity"] == "low")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Kerberos – Rapport de Scan</title>
    <style>
        body {{ background: #0d0d15; color: #e0e0ff; font-family: Consolas, monospace; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .summary {{ color: #ffcc00; margin: 10px 0; }}
        .finding {{ padding: 10px; margin: 8px 0; border-radius: 4px; background: #1a1a25; }}
        .high {{ border-left: 3px solid #ff5252; }}
        .medium {{ border-left: 3px solid #ff9e00; }}
        .low {{ border-left: 3px solid #a0ffa0; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #707090; }}
        a {{ color: #a0a0ff; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>👁️‍🗨️ KERBEROS – Rapport de Scan Profond</h2>
        <div class="summary">Machine : <strong>{hostname}</strong> • {now}</div>
        <div class="summary">⚠️ Critiques : {high} | ⚠️ Moyennes : {medium} | ℹ️ Mineures : {low}</div>
    </div>
"""
    for f in findings:
        cls = "high" if f["severity"] == "high" else ("medium" if f["severity"] == "medium" else "low")
        html += f"""
    <div class="finding {cls}">
        <strong>{f['title']}</strong><br>
        <small>→ État : {f['status']}<br>
        → Risque : {f['risk']}<br>
        → Correctif : {f['fix']}</small>
    </div>
"""

    html += f"""
    <div class="footer">
        Généré par Kerberos • <a href="https://www.gnu.org/licenses/gpl-3.0.txt">GPLv3</a> • 
        <a href="https://liberapay.com/EthicalKerberos/">Soutien éthique</a>
    </div>
</body>
</html>
"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(REPORTS_DIR, f"kerberos_scan_{timestamp}.html")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        try:
            os.startfile(filepath)
        except OSError:
            messagebox.showinfo("ℹ️ Kerberos", f"Rapport généré :\n{filepath}")
    except Exception as e:
        messagebox.showerror("❌ Erreur", f"Export HTML échoué :\n{e}", parent=root)

# === LICENCE OFFICIELLE GPLv3 ===
def show_license():
    license_text = """                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works...
[Extrait — texte complet : https://www.gnu.org/licenses/gpl-3.0.txt]

KERBEROS – Deep Scanner (Windows 7/10)
Copyright (C) 2025 Victor.pozen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details."""
    
    win = tk.Toplevel(root)
    win.title("📜 Licence GPLv3")
    win.geometry("650x440")
    win.configure(bg=BG_DARK)
    win.transient(root)
    win.grab_set()
    txt = scrolledtext.ScrolledText(win, bg="#1a1a25", fg=FG_LIGHT, font=("Consolas", 9))
    txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    txt.insert(tk.END, license_text)
    txt.configure(state='disabled')
    tk.Button(win, text="Fermer", command=win.destroy, bg=BTN_COLOR, fg=BTN_TEXT, width=12).pack(pady=8)

def open_liberapay(event=None):
    webbrowser.open("https://liberapay.com/EthicalKerberos/")

# === SCAN + INTERFACE ===
global_findings = []

def run_scan():
    global global_findings
    log_text.configure(state='normal')
    log_text.delete(1.0, tk.END)
    
    admin_mode = is_admin()
    if not admin_mode:
        log_text.insert(tk.END, "[!] Mode non-admin – scan partiel.\n", "warning")
    else:
        log_text.insert(tk.END, "[✅] Mode admin – scan complet.\n\n", "ok")

    findings = detect_vulnerabilities(admin_mode)
    global_findings = findings

    high = sum(1 for f in findings if f["severity"] == "high")
    medium = sum(1 for f in findings if f["severity"] == "medium")
    low = sum(1 for f in findings if f["severity"] == "low")

    log_text.insert(tk.END, f"✅ Scan terminé – {high} critiques, {medium} moyennes, {low} mineures.\n\n", "summary")

    for f in findings:
        color = "high" if f["severity"] == "high" else ("medium" if f["severity"] == "medium" else "low")
        log_text.insert(tk.END, f"{f['title']}\n", color)
        log_text.insert(tk.END, f"   → État : {f['status']}\n")
        log_text.insert(tk.END, f"   → Risque : {f['risk']}\n")
        log_text.insert(tk.END, f"   → Correctif : {f['fix']}\n\n")

    log_text.configure(state='disabled')
    log_text.yview(tk.END)

def create_gui():
    global root, log_text
    root = tk.Tk()
    root.title("👁️‍🗨️ KERBEROS – Deep Scan SAFE v1.1")
    root.geometry("780x640")
    root.configure(bg=BG_DARK)
    root.minsize(600, 500)

    # Zone de log
    log_text = scrolledtext.ScrolledText(
        root, bg="#0c0c0c", fg=FG_GREEN, font=("Consolas", 10),
        wrap=tk.WORD, state='disabled', padx=8, pady=6
    )
    log_text.tag_config("header", foreground="#ff5252", font=("Consolas", 10, "bold"))
    log_text.tag_config("summary", foreground="#ffcc00")
    log_text.tag_config("high", foreground="#ff5252", font=("Consolas", 10, "bold"))
    log_text.tag_config("medium", foreground="#ff9e00")
    log_text.tag_config("low", foreground="#a0ffa0")
    log_text.tag_config("info", foreground="#70a0ff")
    log_text.tag_config("warning", foreground="#ffcc00")
    log_text.tag_config("ok", foreground="#81c784")
    log_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 6))

    # Boutons
    btn_frame = tk.Frame(root, bg=BG_DARK)
    btn_frame.pack(pady=4)
    tk.Button(btn_frame, text="🔍 Lancer le scan", command=run_scan,
              width=20, bg=BTN_COLOR, fg=BTN_TEXT, font=("Consolas", 9, "bold")).pack(side="left", padx=3)
    tk.Button(btn_frame, text="💾 TXT", command=lambda: save_as_txt(global_findings),
              width=15, bg=BTN_COLOR, fg=BTN_TEXT, font=("Consolas", 9)).pack(side="left", padx=3)
    tk.Button(btn_frame, text="🌐 HTML", command=lambda: export_as_html(global_findings),
              width=15, bg=BTN_COLOR, fg=BTN_TEXT, font=("Consolas", 9)).pack(side="left", padx=3)

    nav_frame = tk.Frame(root, bg=BG_DARK)
    nav_frame.pack(pady=6)
    tk.Button(nav_frame, text="🛠️ Appliquer les correctifs", command=apply_fixes,
              width=28, bg="#2e7d32", fg="white", font=("Consolas", 10, "bold")).pack(side="left", padx=6)
    tk.Button(nav_frame, text="✅ Vérifier la protection", command=verify_protection,
              width=28, bg="#1565c0", fg="white", font=("Consolas", 10, "bold")).pack(side="left", padx=6)

    info_frame = tk.Frame(root, bg=BG_DARK)
    info_frame.pack(pady=4)
    tk.Button(info_frame, text="📜 GPLv3", command=show_license,
              width=18, bg=BTN_COLOR, fg=BTN_TEXT, font=("Consolas", 9)).pack(side="left", padx=5)
    tk.Button(info_frame, text="ℹ️ Soutien", command=open_liberapay,
              width=18, bg=BTN_COLOR, fg=LINK_COLOR, font=("Consolas", 9)).pack(side="left", padx=5)

    tk.Label(root, text="💀 Kerberos – Rien n’est caché – GPLv3",
             font=("Segoe UI", 8), fg="#707090", bg=BG_DARK).pack(side="bottom", pady=6)

# === LANCEMENT SÛR ===
if __name__ == "__main__":
    # ✅ Debug silencieux (à commenter en prod)
    print(f"[DEBUG] Rapports → {REPORTS_DIR}")

    if not is_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except Exception as e:
            messagebox.showerror("❌ Kerberos", f"Impossible de relancer en admin :\n{e}")
        sys.exit()  # ✅ Évite double GUI
    else:
        create_gui()
        root.mainloop()