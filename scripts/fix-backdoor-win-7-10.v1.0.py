# fix-backdoor-win-7-10.py
# 🔐 Sécurité éthique locale pour Windows 7 & 10
# 🧠 Par  Victor.pozen – Projet Kerberos
# 💀 Objectif : Corriger les backdoors sans cacher, sans casser, sans HDD imposé
# 📄 Licence : GNU General Public License v3.0 (GPLv3)
# 💀 Soutien éthique : https://liberapay.com/EthicalKerberos/

import ctypes
import sys
import subprocess
import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
import webbrowser

# === CHEMIN PORTABLE – PAS DE I:\ ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
STATE_FILE = os.path.join(LOGS_DIR, "backdoor_state.ybride")
os.makedirs(LOGS_DIR, exist_ok=True)

# === STYLE KERBEROS ===
BG_DARK = "#0d0d15"
FG_LIGHT = "#e0e0ff"
FG_GREEN = "#a0ffa0"
BTN_COLOR = "#2a2a2a"
BTN_TEXT = "#c0c0ff"
BTN_SAFE = "#2e7d32"
LINK_COLOR = "#a0a0ff"

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

# === SAUVEGARDE DU REGISTRE VIA REDEDIT (PORTABLE) ===
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

# === APPLICATION DES CORRECTIFS ===
def apply_selected_fixes(selected):
    save_registry_snapshot()
    if selected.get("smb_server"): 
        subprocess.run("net stop LanmanServer /y", shell=True)
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer" /v Start /t REG_DWORD /d 4 /f', shell=True)
    if selected.get("spooler"): 
        subprocess.run("net stop Spooler /y", shell=True)
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Spooler" /v Start /t REG_DWORD /d 4 /f', shell=True)
    if selected.get("rdp"): 
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 1 /f', shell=True)
    if selected.get("smb1"):
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" /v SMB1 /t REG_DWORD /d 0 /f', shell=True)
        subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\mrxsmb10" /v Start /t REG_DWORD /d 4 /f', shell=True)
    if selected.get("guest"):
        subprocess.run('net user Guest /active:no', shell=True)
    if selected.get("llmnr"):
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\DNSClient" /v EnableMulticast /t REG_DWORD /d 0 /f', shell=True)

    ports = []
    if selected.get("port_445"): ports.append(445)
    if selected.get("port_135"): ports.append(135)
    for port in ports:
        subprocess.run(f'netsh advfirewall firewall delete rule name="Kerberos_Block_{port}"', shell=True)
        subprocess.run(f'netsh advfirewall firewall add rule name="Kerberos_Block_{port}" dir=in action=block protocol=TCP localport={port}', shell=True)

# === RESTAURATION ===
def restore_registry_snapshot():
    if os.path.exists(STATE_FILE):
        subprocess.run(["regedit", "/s", STATE_FILE], shell=True)
        messagebox.showinfo("✅ Restauration", "Registre restauré.\nRedémarrez pour appliquer.", parent=root)
    else:
        messagebox.showerror("❌ Erreur", "Fichier .ybride introuvable dans 'logs'.", parent=root)

# === UTILITAIRES ===
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

# === LICENCE GPLv3 ===
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
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>."""
    
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

# === INTERFACE PRINCIPALE ===
def create_gui():
    global root
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
            apply_selected_fixes(selected)
            log_text.configure(state='normal')
            log_text.delete(1.0, tk.END)
            log_text.insert(tk.END, "✅ Correctifs appliqués avec succès.\n")
            log_text.configure(state='disabled')
            messagebox.showinfo("✅ Succès", "Les failles sélectionnées ont été corrigées.", parent=root)
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
              command=restore_registry_snapshot,
              width=45, height=1, bg=BTN_COLOR, fg=BTN_TEXT, font=("Consolas", 9)).pack(pady=3)

    info_frame = tk.Frame(root, bg=BG_DARK)
    info_frame.pack(pady=5)
    tk.Button(info_frame, text="📜 Licence GPLv3", command=show_license,
              width=22, height=1, bg=BTN_COLOR, fg=BTN_TEXT, font=("Consolas", 9)).pack(side="left", padx=5)
    tk.Button(info_frame, text="ℹ️ Soutien éthique", command=open_liberapay,
              width=22, height=1, bg=BTN_COLOR, fg=LINK_COLOR, font=("Consolas", 9)).pack(side="left", padx=5)

    tk.Label(root, text="💀 Projet Kerberos – Portable – GPLv3 – Rien n’est caché", 
             font=("Segoe UI", 8), fg="#707090", bg=BG_DARK).pack(side="bottom", pady=5)

# === LANCEMENT ===
if __name__ == "__main__":
    if not is_admin():
        temp = tk.Tk(); temp.withdraw()
        messagebox.showinfo("KERBEROS", "Droits administrateur requis.", parent=temp)
        temp.destroy()
        run_as_admin()
    create_gui()
    root.mainloop()
