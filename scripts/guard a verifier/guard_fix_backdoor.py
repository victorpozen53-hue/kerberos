# guard_fix_backdoor.py — Kerberos v1.0 — GPLv3
# 🛡️ Correction silencieuse des backdoors Windows 7/10
# 📜 Licence : GNU GPLv3 — https://liberapay.com/EthicalKerberos/
# 💀 White hat only. Pas de trace. Pas de nuage.
# (-; — Victor.Pozen

import ctypes
import sys
import subprocess
import os
import json
import time
import hashlib
import socket
import uuid

# === CHEMIN PORTABLE ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
STATE_FILE = os.path.join(LOGS_DIR, "backdoor_state.ybride")
WHITELIST_FILE = os.path.join(LOGS_DIR, "machine_whitelist.vkr")
os.makedirs(LOGS_DIR, exist_ok=True)

# === EMPREINTE MACHINE (HDD + MAC) ===
def get_hdd_serial():
    try:
        # WMI pour serial du disque système (portable Win7+)
        res = subprocess.run(
            'wmic diskdrive where "bootvolume=true" get SerialNumber /value',
            shell=True, capture_output=True, text=True, timeout=5
        )
        if "SerialNumber=" in res.stdout:
            return res.stdout.strip().split("=")[-1].strip()
    except:
        pass
    return "UNKNOWN_HDD"

def get_mac():
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)])
        return mac.upper()
    except:
        return "00:00:00:00:00:00"

def machine_fingerprint():
    hdd = get_hdd_serial()
    mac = get_mac()
    raw = f"{hdd}|{mac}|{os.environ.get('COMPUTERNAME', 'PC')}"
    return hashlib.sha3_256(raw.encode()).hexdigest()[:16]

def is_machine_whitelisted():
    if not os.path.exists(WHITELIST_FILE):
        return False
    try:
        with open(WHITELIST_FILE, "rb") as f:
            data = f.read()
        # Format : [magic 4B][fingerprint 16B][timestamp 8B][signature 32B]
        if len(data) != 60 or data[:4] != b"VKRW":
            return False
        fp = data[4:20].decode()
        return fp == machine_fingerprint()
    except:
        return False

def whitelist_current_machine():
    fp = machine_fingerprint()
    timestamp = int(time.time()).to_bytes(8, 'little')
    header = b"VKRW" + fp.encode() + timestamp
    # Signature simple (pas RSA pour v1.0 — à améliorer en v2.4)
    signature = hashlib.sha3_256(header + b"KRBv1.0").digest()
    with open(WHITELIST_FILE, "wb") as f:
        f.write(header + signature)
    return fp

# === LISTE DES CORRECTIFS ===
FIXES = [
    {"id": "smb_server", "label": "🔒 Désactiver le serveur SMB", "default": True},
    {"id": "smb1", "label": "🧱 Désactiver SMBv1", "default": True},
    {"id": "spooler", "label": "🖨️ Désactiver le Spooler", "default": True},
    {"id": "rdp", "label": "💻 Désactiver le Bureau à distance", "default": True},
    {"id": "port_135", "label": "🚪 Bloquer port 135 (RPC) en entrée", "default": True},
    {"id": "port_445", "label": "🚪 Bloquer port 445 (SMB) en entrée", "default": True},
    {"id": "llmnr", "label": "📡 Désactiver LLMNR", "default": True},
    {"id": "guest", "label": "👤 Désactiver le compte Invité", "default": True},
]

# === SAUVEGARDE REGISTRE ===
def save_registry_snapshot():
    with open(STATE_FILE, "w", encoding="utf-16") as f:
        f.write("Windows Registry Editor Version 5.00\n\n")
    keys = [
        r"HKLM\SYSTEM\CurrentControlSet\Services",
        r"HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server",
        r"HKLM\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient",
        r"HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters",
        r"HKLM\SYSTEM\CurrentControlSet\Control\Lsa"
    ]
    for key in keys:
        try:
            temp = STATE_FILE + ".tmp"
            subprocess.run(["regedit", "/e", temp, key], shell=True, timeout=15)
            if os.path.exists(temp):
                with open(temp, "r", encoding="utf-16") as t, open(STATE_FILE, "a", encoding="utf-16") as f:
                    f.write(t.read() + "\n")
                os.remove(temp)
        except: pass

# === APPLICATION ===
def apply_selected_fixes(selected):
    save_registry_snapshot()
    log = []
    if selected.get("smb_server"):
        subprocess.run("net stop LanmanServer /y", shell=True, timeout=10)
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer" /v Start /t REG_DWORD /d 4 /f', shell=True)
        log.append("SMB désactivé")
    if selected.get("spooler"):
        subprocess.run("net stop Spooler /y", shell=True, timeout=10)
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Spooler" /v Start /t REG_DWORD /d 4 /f', shell=True)
        log.append("Spooler désactivé")
    if selected.get("rdp"):
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 1 /f', shell=True)
        log.append("RDP désactivé")
    if selected.get("smb1"):
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" /v SMB1 /t REG_DWORD /d 0 /f', shell=True)
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\mrxsmb10" /v Start /t REG_DWORD /d 4 /f', shell=True)
        log.append("SMBv1 désactivé")
    if selected.get("guest"):
        subprocess.run('net user Guest /active:no', shell=True)
        log.append("Invité désactivé")
    if selected.get("llmnr"):
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" /v EnableMulticast /t REG_DWORD /d 0 /f', shell=True)
        log.append("LLMNR désactivé")

    ports = []
    if selected.get("port_445"): ports.append(445)
    if selected.get("port_135"): ports.append(135)
    for port in ports:
        subprocess.run(f'netsh advfirewall firewall delete rule name="Kerberos_Block_{port}"', shell=True)
        subprocess.run(f'netsh advfirewall firewall add rule name="Kerberos_Block_{port}" dir=in action=block protocol=TCP localport={port}', shell=True)
        log.append(f"Port {port} bloqué")

    return log

# === MODE GUARD (sans GUI) ===
def run_as_guard(fix_list=None, dry_run=False, auto_whitelist=False):
    """
    À appeler depuis kerberos.py :
      from guards.guard_fix_backdoor import run_as_guard
      result = run_as_guard()
    """
    fp = machine_fingerprint()

    # 🔹 Si machine whitelistée → ne rien faire (sauf dry_run)
    if not dry_run and is_machine_whitelisted():
        return {"status": "skipped", "reason": "machine_whitelisted", "fp": fp}

    # 🔹 Dry-run : rapport d'état
    if dry_run:
        at_risk = []
        try:
            # SMB actif ?
            res = subprocess.run(
                'sc query LanmanServer', shell=True, capture_output=True, text=True, timeout=5
            )
            if "STATE" in res.stdout and "RUNNING" in res.stdout:
                at_risk.append("smb_server")
        except: pass

        try:
            res = subprocess.run('net user Guest', shell=True, capture_output=True, text=True, timeout=5)
            if "État du compte" in res.stdout and "actif" in res.stdout.lower():
                at_risk.append("guest")
        except: pass

        return {
            "status": "dry_run",
            "machine_fp": fp,
            "at_risk": at_risk,
            "whitelisted": is_machine_whitelisted()
        }

    # 🔹 Mode réel
    if fix_list is None:
        fix_list = [f["id"] for f in FIXES if f["default"]]

    selected = {fid: (fid in fix_list) for fid in [f["id"] for f in FIXES]}
    try:
        log = apply_selected_fixes(selected)
        if auto_whitelist:
            whitelist_current_machine()
        return {
            "status": "success",
            "fixed": fix_list,
            "log": log,
            "machine_fp": fp,
            "whitelisted": auto_whitelist
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "machine_fp": fp}

# === UTILITAIRES ADMIN ===
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

# === MODE GUI (double-clic) ===
def _launch_gui():
    import tkinter as tk
    from tkinter import messagebox, scrolledtext
    import webbrowser

    BG_DARK = "#0d0d15"
    FG_LIGHT = "#e0e0ff"
    FG_GREEN = "#a0ffa0"
    BTN_COLOR = "#2a2a2a"
    BTN_TEXT = "#c0c0ff"
    BTN_SAFE = "#2e7d32"
    LINK_COLOR = "#a0a0ff"

    def show_license():
        license_text = """GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details."""
        win = tk.Toplevel(root)
        win.title("📜 Licence GPLv3")
        win.geometry("600x400")
        win.configure(bg=BG_DARK)
        txt = scrolledtext.ScrolledText(win, bg="#1a1a25", fg=FG_LIGHT, font=("Consolas", 10))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        txt.insert(tk.END, license_text)
        txt.configure(state='disabled')
        tk.Button(win, text="Fermer", command=win.destroy, bg=BTN_COLOR, fg=BTN_TEXT).pack(pady=5)

    def open_liberapay(event=None):
        webbrowser.open("https://liberapay.com/EthicalKerberos/")

    root = tk.Tk()
    root.title("🛡️ KERBEROS v1.0 – Correction Sélective")
    root.geometry("800x520")
    root.configure(bg=BG_DARK)
    root.resizable(False, False)

    tk.Label(root, text="👁️‍🗨️ SÉLECTIONNEZ LES FAILLES À CORRIGER", 
             font=("Consolas", 14, "bold"), fg="#ff5252", bg=BG_DARK).pack(pady=(10,5))

    main_frame = tk.Frame(root, bg=BG_DARK)
    main_frame.pack(pady=5, padx=15, fill=tk.BOTH, expand=True)

    left_frame = tk.Frame(main_frame, bg=BG_DARK)
    left_frame.pack(side="left", padx=(0,15), fill=tk.Y)
    right_frame = tk.Frame(main_frame, bg=BG_DARK)
    right_frame.pack(side="left", fill=tk.BOTH, expand=True)

    checkboxes = {}
    for fix in FIXES:
        var = tk.BooleanVar(value=fix["default"])
        checkboxes[fix["id"]] = var
        cb = tk.Checkbutton(
            left_frame, text=fix["label"], variable=var,
            bg=BG_DARK, fg=FG_LIGHT, selectcolor=BG_DARK,
            activebackground=BG_DARK, activeforeground=FG_GREEN,
            font=("Consolas", 10)
        )
        cb.pack(anchor="w", pady=3)

    log_text = scrolledtext.ScrolledText(root, height=6, bg="#1a1a25", fg=FG_GREEN, font=("Consolas", 9))
    log_text.pack(padx=15, pady=10, fill=tk.X)
    log_text.configure(state='disabled')

    def apply_fixes():
        selected = {k: v.get() for k, v in checkboxes.items() if v.get()}
        if not selected:
            messagebox.showwarning("⚠️ Kerberos", "Aucune faille sélectionnée.", parent=root)
            return
        if not messagebox.askyesno("✅ Confirmation", f"Corriger {len(selected)} failles ?\nUn fichier .ybride sera sauvegardé.", parent=root):
            return
        try:
            log = apply_selected_fixes(selected)
            log_text.configure(state='normal')
            log_text.delete(1.0, tk.END)
            log_text.insert(tk.END, "✅ Correctifs appliqués :\n" + "\n".join(log) + "\n")
            log_text.configure(state='disabled')
            if messagebox.askyesno("💾 Whitelist", "Ajouter cette machine à la whitelist ?", parent=root):
                whitelist_current_machine()
                log_text.configure(state='normal')
                log_text.insert(tk.END, "🔒 Machine whitelistée.\n")
                log_text.configure(state='disabled')
            messagebox.showinfo("✅ Succès", "Les failles ont été corrigées.", parent=root)
        except Exception as e:
            log_text.configure(state='normal')
            log_text.insert(tk.END, f"❌ Erreur : {e}\n")
            log_text.configure(state='disabled')

    btn_frame = tk.Frame(root, bg=BG_DARK)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="✅ Appliquer les correctifs sélectionnés", 
              command=apply_fixes,
              width=45, height=2, bg=BTN_SAFE, fg="white", font=("Consolas", 10, "bold")).pack(pady=5)
    tk.Button(btn_frame, text="🔄 Restaurer depuis .ybride", 
              command=lambda: subprocess.run(["regedit", "/s", STATE_FILE], shell=True),
              width=45, height=1, bg=BTN_COLOR, fg=BTN_TEXT, font=("Consolas", 9)).pack(pady=3)

    info_frame = tk.Frame(root, bg=BG_DARK)
    info_frame.pack(pady=5)
    tk.Button(info_frame, text="📜 Licence GPLv3", command=show_license,
              width=22, height=1, bg=BTN_COLOR, fg=BTN_TEXT, font=("Consolas", 9)).pack(side="left", padx=5)
    tk.Button(info_frame, text="ℹ️ Soutien éthique", command=open_liberapay,
              width=22, height=1, bg=BTN_COLOR, fg=LINK_COLOR, font=("Consolas", 9)).pack(side="left", padx=5)

    tk.Label(root, text="💀 Projet Kerberos – Portable – GPLv3 – Rien n’est caché", 
             font=("Segoe UI", 8), fg="#707090", bg=BG_DARK).pack(side="bottom", pady=5)
    root.mainloop()

# === LANCEMENT ===
if __name__ == "__main__":
    if not is_admin():
        temp = tk.Tk() if 'tkinter' in sys.modules else None
        if temp:
            temp.withdraw()
            messagebox.showinfo("KERBEROS", "Droits administrateur requis.", parent=temp)
            temp.destroy()
        run_as_admin()
    _launch_gui()