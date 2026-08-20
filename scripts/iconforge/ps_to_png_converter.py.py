# -*- coding: utf-8 -*-
# ps_to_png_converter.py
# Convertisseur PostScript → PNG – Kerberos v1.0
# GPLv3 – https://liberapay.com/EthicalKerberos/
# Par Victor & Mirko – IA de garde pour Windows
# Ce script convertit les fichiers .ps en .png via Ghostscript (libre et léger).

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# === DEBUG MAISON ===
def debug_log(msg):
    log_path = os.path.join(LOGS_DIR, "ps_converter.log")
    timestamp = __import__('time').strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

# === DÉTECTION DE GHOSTSCRIPT ===
def find_ghostscript():
    """Cherche Ghostscript dans les chemins courants."""
    possible_paths = [
        r"C:\Program Files\gs\gs10.03.0\bin\gswin64c.exe",
        r"C:\Program Files\gs\gs10.02.1\bin\gswin64c.exe",
        r"C:\Program Files (x86)\gs\gs10.03.0\bin\gswin32c.exe",
        r"C:\Program Files\gs\bin\gswin64c.exe",
        r"C:\gs\gs10.03.0\bin\gswin64c.exe",
        "gswin64c.exe",
        "gswin32c.exe",
        "gs"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            debug_log(f"Ghostscript trouvé : {path}")
            return path
        try:
            # Test si accessible via PATH
            subprocess.run([path, "-h"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
            debug_log(f"Ghostscript accessible via PATH : {path}")
            return path
        except:
            continue
    return None

# === CONVERSION ===
def convert_ps_to_png(ps_path, gs_exe):
    """Convertit un fichier .ps en .png avec Ghostscript."""
    if not ps_path.endswith(".ps"):
        debug_log(f"Ignoré (pas .ps) : {ps_path}")
        return False

    png_path = ps_path[:-3] + ".png"
    try:
        cmd = [
            gs_exe,
            "-dSAFER", "-dBATCH", "-dNOPAUSE",
            "-sDEVICE=png16m",
            "-r96",  # résolution (96 DPI = 1:1 pour 32x32)
            f"-sOutputFile={png_path}",
            ps_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            debug_log(f"✅ Converti : {png_path}")
            return True
        else:
            debug_log(f"❌ Erreur Ghostscript : {result.stderr}")
            return False
    except Exception as e:
        debug_log(f"❌ Exception : {e}")
        return False

# === INTERFACE TKINTER ===
class PSConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kerberos – Convertisseur PS → PNG")
        self.root.geometry("700x500")
        self.root.configure(bg="#1e1e1e")

        # Titre
        title = tk.Label(
            root, text="🖨️ CONVERTISSEUR POSTSCRIPT → PNG",
            fg="#00ff00", bg="#1e1e1e", font=("Consolas", 14, "bold")
        )
        title.pack(pady=10)

        # Boutons
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=10)

        self.btn_select = tk.Button(
            btn_frame, text="📂 Sélectionner .ps", command=self.select_files,
            bg="#2d2d2d", fg="white", font=("Consolas", 10)
        )
        self.btn_select.pack(side=tk.LEFT, padx=5)

        self.btn_convert = tk.Button(
            btn_frame, text="🟢 Convertir", command=self.convert_all,
            bg="#2d2d2d", fg="white", font=("Consolas", 10)
        )
        self.btn_convert.pack(side=tk.LEFT, padx=5)

        # Console
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Consolas", 10),
            bg="#0a0a0a", fg="#00ff00", height=20
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Rediriger print
        sys.stdout = self
        sys.stderr = self

        # État
        self.selected_files = []
        self.gs_exe = find_ghostscript()

        # Vérification initiale
        if not self.gs_exe:
            messagebox.showwarning(
                "Ghostscript manquant",
                "Ghostscript n'est pas installé.\n\n"
                "➡️ Téléchargez-le ici (libre et léger) :\n"
                "https://ghostscript.com/releases/gsdnld.html\n\n"
                "Installez-le, puis relancez ce convertisseur."
            )
            debug_log("Ghostscript non trouvé. Conversion impossible.")

    def write(self, msg):
        if msg.strip():
            self.console.configure(state='normal')
            self.console.insert(tk.END, msg)
            self.console.see(tk.END)
            self.console.configure(state='disabled')

    def flush(self):
        pass

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Sélectionner des fichiers .ps",
            filetypes=[("PostScript", "*.ps")]
        )
        self.selected_files = list(files)
        debug_log(f"{len(self.selected_files)} fichier(s) sélectionné(s).")

    def convert_all(self):
        if not self.gs_exe:
            messagebox.showerror("Erreur", "Ghostscript non installé. Voir les logs.")
            return
        if not self.selected_files:
            messagebox.showwarning("Avertissement", "Aucun fichier sélectionné.")
            return

        success = 0
        for ps_file in self.selected_files:
            if convert_ps_to_png(ps_file, self.gs_exe):
                success += 1
        debug_log(f"✅ Conversion terminée : {success}/{len(self.selected_files)} réussie(s).")

# === LANCEMENT ===
if __name__ == "__main__":
    debug_log("=== DÉMARRAGE CONVERTISSEUR PS → PNG KERBEROS ===")
    debug_log("ℹ️  Ce script nécessite Ghostscript (libre, 20 Mo, Windows 7 compatible).")
    debug_log("🔗 Téléchargement : https://ghostscript.com/releases/gsdnld.html")

    root = tk.Tk()
    app = PSConverterGUI(root)
    root.mainloop()