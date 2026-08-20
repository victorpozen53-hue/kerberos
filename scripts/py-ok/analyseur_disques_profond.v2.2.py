# -*- coding: utf-8 -*-
# analyseur_disques_profond.py
# GPLv3 – Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)
# 🛡️ https://liberapay.com/EthicalKerberos/ | Licence : GNU GPLv3

import sys
import os
import platform
import traceback
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# === GESTIONNAIRE D'ERREUR GLOBAL – KERBEROS ===
def kerberos_excepthook(exc_type, exc_value, exc_tb):
    err = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("💥 ERREUR KERBEROS :\n" + err, file=sys.stderr)
    try:
        tmp = tk.Tk()
        tmp.withdraw()
        messagebox.showerror("💥 Kerberos – Erreur critique",
                             f"{exc_type.__name__}: {exc_value}\n\nVoir la console pour les détails.")
        tmp.destroy()
    except: pass
    if not getattr(sys, 'frozen', False):
        try:
            input("\n🔴 Appuyez sur Entrée pour quitter...")
        except: pass
sys.excepthook = kerberos_excepthook
# ==============================================

# === CONFIGURATION ===
BG = "#1e1e1e"
FG = "#00ff00"
FONT_UI = ("Tahoma", 10)
FONT_MONO = ("Consolas", 10)
EXT_IMPORTANTES = {'.py', '.txt', '.log', '.json', '.csv', '.html', '.exe', '.bat', '.ini', '.xml', '.yml'}
MAX_DEPTH = 4

# === DÉTECTION DES LECTEURS (WINDOWS SEULEMENT – SANS PSUTIL) ===
def lister_lecteurs_windows():
    """Retourne les lettres de lecteur disponibles (C:, D:, etc.) sans psutil."""
    if platform.system() != "Windows":
        return []
    try:
        import string
        lecteurs = []
        for lettre in string.ascii_uppercase:
            chemin = f"{lettre}:\\"
            if os.path.exists(chemin):
                lecteurs.append(chemin)
        return lecteurs if lecteurs else ["C:\\"]
    except Exception:
        return ["C:\\"]

# === LECTURE SÉCURISÉE DE L'ESPACE DISQUE (WINDOWS) ===
def espace_disque_win(lecteur):
    """Retourne l'espace utilisé / total en Go, sans psutil."""
    if platform.system() != "Windows":
        return "N/A"
    try:
        import ctypes
        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(lecteur),
            ctypes.pointer(_),
            ctypes.pointer(total),
            ctypes.pointer(free)
        )
        used = (total.value - free.value) / (1024**3)
        total_gb = total.value / (1024**3)
        return f"{used:.1f} / {total_gb:.1f} Go"
    except Exception:
        return "⚠️ Indisponible"

# === ARBRE DE FICHIERS SÉCURISÉ ===
def arbre_securise(racine, prefix="", prof=0, max_prof=4):
    if prof >= max_prof:
        return [f"{prefix}└── [...] (limite profondeur)"]
    lignes = []
    try:
        elements = sorted(os.listdir(racine))
    except (OSError, PermissionError, FileNotFoundError):
        return [f"{prefix}📁 [accès refusé]"]

    dossiers = []
    fichiers_imp = []
    autres = 0

    for e in elements:
        chemin = os.path.join(racine, e)
        try:
            if os.path.isdir(chemin):
                dossiers.append(e)
            elif os.path.isfile(chemin):
                _, ext = os.path.splitext(e)
                if ext.lower() in EXT_IMPORTANTES:
                    fichiers_imp.append(e)
                else:
                    autres += 1
        except (OSError, ValueError):
            continue

    total = len(dossiers) + len(fichiers_imp) + (1 if autres > 0 else 0)
    idx = 0

    # Dossiers
    for d in dossiers:
        idx += 1
        marque = "└── " if idx == total else "├── "
        lignes.append(f"{prefix}{marque}📁 {d}")
        suite = prefix + ("    " if idx == total else "│   ")
        lignes.extend(arbre_securise(os.path.join(racine, d), suite, prof + 1, max_prof))

    # Fichiers importants
    for f in sorted(fichiers_imp):
        idx += 1
        marque = "└── " if idx == total else "├── "
        icone = "🐍" if f.endswith('.py') else "📄"
        lignes.append(f"{prefix}{marque}{icone} {f}")

    # Autres fichiers
    if autres > 0:
        idx += 1
        marque = "└── " if idx == total else "├── "
        lignes.append(f"{prefix}{marque}📄 [{autres} autre(s) fichier(s)]")

    return lignes

# === INTERFACE KERBEROS ===
class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        root.title("🔍 Kerberos – Analyseur de Disques (Mode Profond)")
        root.geometry("880x680")
        root.configure(bg=BG)

        tk.Label(root, text="KERBEROS – Analyse Profonde Locale", 
                 fg=FG, bg=BG, font=("Consolas", 13, "bold")).pack(pady=8)

        # Détection lecteurs
        self.lecteurs = lister_lecteurs_windows()
        frame = tk.Frame(root, bg=BG)
        frame.pack(pady=5, padx=15, fill=tk.X)

        tk.Label(frame, text="✅ Sélectionnez les lecteurs à analyser :", 
                 fg=FG, bg=BG, font=FONT_UI).pack(anchor="w")

        self.vars = {}
        if self.lecteurs:
            for drv in self.lecteurs:
                var = tk.BooleanVar(value=(drv == "C:\\"))
                self.vars[drv] = var
                tk.Checkbutton(frame, text=drv, variable=var,
                               bg=BG, fg=FG, selectcolor="#333",
                               font=FONT_UI).pack(anchor="w", padx=5, pady=1)
        else:
            tk.Label(frame, text="⚠️ Aucun lecteur détecté. Mode manuel activé.",
                     fg="#ffaa00", bg=BG, font=FONT_UI).pack(anchor="w")

        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="🚀 Analyser", command=self.analyser,
                  bg="#8b0000", fg="white", font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📂 Choisir un dossier", command=self.choisir_dossier,
                  bg="#2d2d2d", fg="white", font=FONT_UI).pack(side=tk.LEFT, padx=5)

        # Console
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=FONT_MONO,
            bg="#0a0a0a", fg=FG, insertbackground=FG
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        self.console.bind("<Key>", lambda e: "break")

        self.console.insert(tk.END, "ℹ️ Kerberos v2.0 – GPLv3\n")
        self.console.insert(tk.END, "   Analyse locale sécurisée – Compatible Windows 7/10\n\n")
        if not self.lecteurs:
            self.console.insert(tk.END, "❗ Mode restreint : utilisez 'Choisir un dossier'.\n")

    def analyser(self):
        cibles = [d for d, v in self.vars.items() if v.get()] if self.lecteurs else []
        if not cibles and self.lecteurs:
            messagebox.showwarning("Sélection requise", "Cochez au moins un lecteur.")
            return
        self.generer_rapport(cibles if cibles else ["C:\\"] if self.lecteurs else [])

    def choisir_dossier(self):
        dossier = filedialog.askdirectory(title="Sélectionner un dossier à analyser")
        if dossier:
            self.generer_rapport([dossier])

    def generer_rapport(self, cibles):
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "🔍 Génération du rapport en cours...\n\n")

        lignes = []
        lignes.append("=" * 60)
        lignes.append("RAPPORT KERBEROS – ANALYSE DE DISQUES")
        lignes.append("=" * 60)
        lignes.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lignes.append(f"Système : {platform.system()} {platform.release()}")
        lignes.append(f"Profondeur : {MAX_DEPTH}")
        lignes.append("Licence : GNU GPLv3 – https://liberapay.com/EthicalKerberos/")
        lignes.append("=" * 60)
        lignes.append("")

        for cible in cibles:
            lignes.append(f"\n{'='*60}\nCIBLE : {cible}\n{'='*60}")
            if os.path.exists(cible) and platform.system() == "Windows" and len(cible) == 3:
                lignes.append(f"📊 Espace : {espace_disque_win(cible)}")
            else:
                lignes.append("📊 Espace : N/A (dossier personnalisé)")
            lignes.append("\nArborescence :")
            lignes.extend(arbre_securise(cible, max_prof=MAX_DEPTH))
            lignes.append("")

        lignes.append("✅ Rapport généré – Projet Kerberos (GPLv3)")
        rapport = "\n".join(lignes)
        self.console.insert(tk.END, rapport)

        try:
            with open("rapport_disques_profond.txt", "w", encoding="utf-8") as f:
                f.write(rapport)
            self.console.insert(tk.END, f"\n\n💾 Sauvegardé : rapport_disques_profond.txt")
            messagebox.showinfo("✅ Succès", "Rapport sauvegardé avec succès !")
        except Exception as e:
            self.console.insert(tk.END, f"\n\n⚠️ Erreur sauvegarde : {e}")

# === LANCEMENT ===
if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiskAnalyzer(root)
    root.mainloop()