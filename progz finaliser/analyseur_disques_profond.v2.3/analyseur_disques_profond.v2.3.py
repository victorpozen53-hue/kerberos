#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyseur_disques_profond.v3.0.py — Générateur d'Arborescence de Projet
GPLv3 – Projet Kerberos
White hat only. Pas de trace. Pas de nuage. Juste du code qui protège. (-; — Victor.Pozen
"""
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

# ==============================================================================
# === CONFIGURATION ===
# ==============================================================================
BG = "#1e1e1e"
FG = "#00ff00"
FONT_UI = ("Tahoma", 10)
FONT_MONO = ("Consolas", 10)

# Extensions à mettre en avant dans l'arborescence
EXT_IMPORTANTES = {
    '.py': '🐍',     # Python
    '.json': '📋',   # JSON
    '.html': '🌐',   # HTML
    '.js': '⚡',     # JavaScript
    '.txt': '📄',    # Texte
    '.ini': '️',    # Config
    '.log': '📝',    # Logs
    '.xml': '📄',    # XML
    '.yml': '🔧',    # YAML
    '.bat': '🦇',    # Batch
    '.exe': '⚙️',    # Exécutable
    '.md': '',     # Markdown
    '.css': '🎨',    # CSS
    '.sql': '🗄️',    # SQL
}

# Extensions à ignorer complètement
EXT_IGNORE = {'.dll', '.sys', '.pdb', '.tmp', '.db', '.sqlite'}

MAX_DEPTH = 4

# ==============================================================================
# === DÉTECTION DES LECTEURS (WINDOWS SEULEMENT) ===
# ==============================================================================
def lister_lecteurs_windows():
    """Liste les lecteurs disponibles sur Windows"""
    if platform.system() != "Windows":
        return []
    try:
        import string
        return [f"{c}:\\" for c in string.ascii_uppercase if os.path.exists(f"{c}:\\")] or ["C:\\"]
    except:
        return ["C:\\"]

def espace_disque_win(lecteur):
    """Retourne l'espace disque utilisé/libre"""
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
    except:
        return "Indisponible"

# ==============================================================================
# === GÉNÉRATEUR D'ARBORESCENCE ===
# ==============================================================================
def arbre_securise(racine, prefix="", prof=0, max_prof=4, ignore_recycle=True):
    """Génère une arborescence visuelle propre"""
    if prof >= max_prof:
        return [f"{prefix}── [...] (limite profondeur)"]
    
    lignes = []
    try:
        elements = sorted(os.listdir(racine))
    except (OSError, PermissionError, FileNotFoundError):
        return [f"{prefix}[accès refusé]"]

    if ignore_recycle and os.path.basename(racine).startswith("$RECYCLE.BIN"):
        return [f"{prefix}📁 $RECYCLE.BIN (exclu)"]

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
                elif ext.lower() not in EXT_IGNORE:
                    autres += 1
        except (OSError, ValueError):
            continue

    total = len(dossiers) + len(fichiers_imp) + (1 if autres > 0 else 0)
    idx = 0
    
    # 1. Dossiers
    for d in dossiers:
        if ignore_recycle and d.upper() == "$RECYCLE.BIN":
            idx += 1
            marque = "└── " if idx == total else "├── "
            lignes.append(f"{prefix}{marque}📁 $RECYCLE.BIN (exclu)")
            continue
        idx += 1
        marque = "└── " if idx == total else "├── "
        lignes.append(f"{prefix}{marque} {d}")
        suite = prefix + ("    " if idx == total else "│   ")
        lignes.extend(arbre_securise(os.path.join(racine, d), suite, prof + 1, max_prof, ignore_recycle))

    # 2. Fichiers importants (mis en avant)
    for f in sorted(fichiers_imp):
        idx += 1
        marque = "└── " if idx == total else "├── "
        _, ext = os.path.splitext(f)
        icone = EXT_IMPORTANTES.get(ext.lower(), "📄")
        lignes.append(f"{prefix}{marque}{icone} {f}")

    # 3. Autres fichiers (regroupés)
    if autres > 0:
        idx += 1
        marque = "└── " if idx == total else "├── "
        lignes.append(f"{prefix}{marque}📦 [{autres} autre(s) fichier(s) non listés]")
        
    return lignes

def generer_rapport_txt(cibles, ignore_recycle):
    """Génère le fichier TXT avec l'arborescence pure"""
    now = datetime.now()
    rapport_id = now.strftime("%Y%m%d_%H%M%S")
    rapport_dir = Path("reports") / "txt"
    rapport_dir.mkdir(parents=True, exist_ok=True)
    
    lignes = []
    lignes.append("="*70)
    lignes.append("RAPPORT D'ARBORESCENCE KERBEROS")
    lignes.append("="*70)
    lignes.append(f"Date : {now.strftime('%d/%m/%Y %H:%M:%S')}")
    lignes.append(f"Système : {platform.system()} {platform.release()}")
    lignes.append(f"Profondeur max : {MAX_DEPTH} niveaux")
    lignes.append(f"Extensions suivies : {', '.join(sorted(EXT_IMPORTANTES.keys()))}")
    lignes.append("="*70)
    
    for cible in cibles:
        lignes.append(f"\n📁 CIBLE : {cible}")
        if os.path.exists(cible) and len(cible) == 3 and cible[1:] == ":\\":
            lignes.append(f"   └─ Espace disque : {espace_disque_win(cible)}")
        lignes.append("-"*70)
        
        # Génération de l'arbre
        arbre = arbre_securise(cible, max_prof=MAX_DEPTH, ignore_recycle=ignore_recycle)
        lignes.extend(arbre)
        lignes.append("") # Saut de ligne entre les cibles

    # Sauvegarde du fichier
    rapport_path = rapport_dir / f"arborescence_{rapport_id}.txt"
    rapport_path.write_text("\n".join(lignes), encoding="utf-8")
    
    return rapport_path

# ==============================================================================
# === INTERFACE GRAPHIQUE ===
# ==============================================================================
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        root.title("🔍 Kerberos – Générateur d'Arborescence v3.0")
        root.geometry("900x700")
        root.configure(bg=BG)

        tk.Label(root, text="KERBEROS – Générateur d'Arborescence (v3.0)", 
                 fg=FG, bg=BG, font=("Consolas", 13, "bold")).pack(pady=8)
        
        opt_frame = tk.Frame(root, bg=BG)
        opt_frame.pack(pady=5, padx=15, fill=tk.X)
        
        tk.Label(opt_frame, text="✅ Sélectionnez :", fg=FG, bg=BG, font=FONT_UI).pack(anchor="w")
        tk.Label(opt_frame, text="  Lecteurs :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(5,0))
        
        self.vars = {}
        self.lecteurs = lister_lecteurs_windows()
        drv_frame = tk.Frame(opt_frame, bg=BG)
        drv_frame.pack(anchor="w")
        
        for drv in self.lecteurs:
            var = tk.BooleanVar(value=(drv == "C:\\"))
            self.vars[drv] = var
            tk.Checkbutton(drv_frame, text=drv, variable=var,
                           bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT, padx=3)
        
        tk.Label(opt_frame, text="  Options :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(5,0))
        self.ignore_recycle = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="🗑️ Ignorer $RECYCLE.BIN", variable=self.ignore_recycle,
                       bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(anchor="w")

        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=8)
        
        tk.Button(btn_frame, text=" Générer Arborescence", command=self.analyser,
                  bg="#8b0000", fg="white", font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📂 Choisir un dossier", command=self.choisir_dossier,
                  bg="#2d2d2d", fg="white", font=FONT_UI).pack(side=tk.LEFT, padx=5)

        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=FONT_MONO,
            bg="#0a0a0a", fg=FG, insertbackground=FG
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        self.console.bind("<Key>", lambda e: "break")
        
        self.console.insert(tk.END, " Kerberos v3.0 (Générateur d'Arborescence)\n")
        self.console.insert(tk.END, "   📝 Génère un fichier TXT avec l'arborescence du disque.\n")
        self.console.insert(tk.END, "   🐍 Met en avant les fichiers .py, .json, .html, etc.\n")
        self.console.insert(tk.END, "   🗑️ Ignore la corbeille et les fichiers système.\n\n")

    def analyser(self):
        cibles = [d for d, v in self.vars.items() if v.get()] or (["C:\\"] if self.lecteurs else [])
        if not cibles and self.lecteurs:
            messagebox.showwarning("Sélection requise", "Cochez au moins un lecteur.")
            return
        self.generer_rapport(cibles)

    def choisir_dossier(self):
        dossier = filedialog.askdirectory(title="Sélectionner un dossier à analyser")
        if dossier:
            self.generer_rapport([dossier])

    def generer_rapport(self, cibles):
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "🌳 Génération de l'arborescence en cours…\n\n")
        
        try:
            txt_path = generer_rapport_txt(cibles, self.ignore_recycle.get())
            
            self.console.insert(tk.END, "✅ Arborescence générée avec succès !\n\n")
            self.console.insert(tk.END, f"📝 Rapport TXT sauvegardé :\n")
            self.console.insert(tk.END, f"   {txt_path}\n\n")
            self.console.insert(tk.END, "👉 Le fichier contient l'arborescence complète avec les icônes pour les fichiers importants.\n")
            
            # Ouvre le rapport TXT dans le bloc-notes (Windows)
            if platform.system() == "Windows":
                os.startfile(txt_path)
                
        except Exception as e:
            self.console.insert(tk.END, f"\n❌ Erreur génération rapport :\n   {e}\n")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiskAnalyzer(root)
    root.mainloop()