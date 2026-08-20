# -*- coding: utf-8 -*-
# png_to_ico_converter.py
# Convertisseur PNG → ICO – Kerberos v1.0
# GPLv3 – https://liberapay.com/EthicalKerberos/
# Par Victor & Mirko – Outil local pour icônes Windows (Win7/10)

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# === DEBUG MAISON ===
def debug_log(msg):
    log_path = os.path.join(LOGS_DIR, "png_to_ico.log")
    timestamp = __import__('time').strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

# === VÉRIFICATION PILLOW (PIL) ===
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# === CONVERSION PNG → ICO ===
def convert_png_to_ico(png_path):
    """Convertit un .png en .ico avec plusieurs tailles."""
    if not png_path.lower().endswith(".png"):
        debug_log(f"Ignoré (pas .png) : {png_path}")
        return False

    ico_path = png_path[:-4] + ".ico"
    try:
        img = Image.open(png_path)
        # Génère plusieurs tailles courantes pour les icônes Windows
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        # Filtrer les tailles compatibles avec la résolution source
        available_sizes = []
        for size in icon_sizes:
            if img.width >= size[0] and img.height >= size[1]:
                available_sizes.append(size)
        if not available_sizes:
            available_sizes = [(img.width, img.height)]  # au moins la taille originale

        img.save(ico_path, format="ICO", sizes=available_sizes)
        debug_log(f"✅ Converti : {ico_path} (tailles: {available_sizes})")
        return True
    except Exception as e:
        debug_log(f"❌ Erreur Pillow : {e}")
        return False

# === INTERFACE TKINTER ===
class PNGtoICOConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kerberos – Convertisseur PNG → ICO")
        self.root.geometry("700x500")
        self.root.configure(bg="#1e1e1e")

        # Titre
        title = tk.Label(
            root, text="🖼️ CONVERTISSEUR PNG → ICO (Windows)",
            fg="#00ff00", bg="#1e1e1e", font=("Consolas", 14, "bold")
        )
        title.pack(pady=10)

        # Boutons
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=10)

        self.btn_select = tk.Button(
            btn_frame, text="📂 Sélectionner .png", command=self.select_files,
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

        # Vérification initiale de Pillow
        if not PIL_AVAILABLE:
            messagebox.showwarning(
                "Pillow (PIL) manquant",
                "La bibliothèque 'Pillow' n'est pas installée.\n\n"
                "➡️ Pour l'installer (léger, 3 Mo) :\n"
                "Ouvrez CMD en admin et tapez :\n"
                "pip install Pillow\n\n"
                "Puis relancez ce convertisseur."
            )
            debug_log("Pillow non trouvé. Conversion impossible.")

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
            title="Sélectionner des fichiers .png",
            filetypes=[("PNG", "*.png")]
        )
        self.selected_files = list(files)
        debug_log(f"{len(self.selected_files)} fichier(s) sélectionné(s).")

    def convert_all(self):
        if not PIL_AVAILABLE:
            messagebox.showerror("Erreur", "Pillow non installé. Voir les logs.")
            return
        if not self.selected_files:
            messagebox.showwarning("Avertissement", "Aucun fichier sélectionné.")
            return

        success = 0
        for png_file in self.selected_files:
            if convert_png_to_ico(png_file):
                success += 1
        debug_log(f"✅ Conversion terminée : {success}/{len(self.selected_files)} réussie(s).")

# === LANCEMENT ===
if __name__ == "__main__":
    debug_log("=== DÉMARRAGE CONVERTISSEUR PNG → ICO KERBEROS ===")
    debug_log("ℹ️  Ce script nécessite Pillow (PIL). Léger, libre, local.")
    debug_log("🔗 Installer avec : pip install Pillow (pas de dépendance cloud)")

    root = tk.Tk()
    app = PNGtoICOConverterGUI(root)
    root.mainloop()