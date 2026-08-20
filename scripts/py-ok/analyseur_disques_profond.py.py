# -*- coding: utf-8 -*-
# analyseur_disques_profond.py
# GPLv3 – Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)
# 🛡️ https://liberapay.com/EthicalKerberos/
# Licence : GNU General Public License v3.0

import os
import psutil
import platform
import sys
import traceback
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# ==============================
# Configuration visuelle Kerberos
# ==============================
BG_COLOR = "#1e1e1e"
FG_COLOR = "#00ff00"
FONT_CONSOLE = ("Consolas", 10)
FONT_UI = ("Tahoma", 10)  # compatible Windows 7
FONT_TITLE = ("Consolas", 12, "bold")

EXTENSIONS_IMPORTANTES = {'.py', '.txt', '.log', '.json', '.csv', '.html', '.exe', '.bat', '.sh', '.yaml', '.yml'}
MAX_DEPTH = 4

# ==============================
# Rapport de crash
# ==============================
def sauvegarder_rapport_plantage(exception, context="Inconnu"):
    rapport = f"""{'='*60}
RAPPORT DE PLANTAGE – Analyseur Disques (Kerberos)
{'='*60}
Date/Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Système    : {platform.system()} {platform.release()} ({platform.machine()})
Python     : {platform.python_version()}
Contexte   : {context}
{'-'*60}
Erreur : {type(exception).__name__}: {exception}
{'-'*60}
Traceback :
{traceback.format_exc()}
{'='*60}"""
    try:
        with open("crash_report_disques.txt", "w", encoding="utf-8") as f:
            f.write(rapport)
        messagebox.showerror("💥 Erreur", "Un crash est survenu !\nRapport sauvegardé : crash_report_disques.txt")
    except Exception as e:
        print("Échec sauvegarde rapport :", e)

# ==============================
# Logique disque
# ==============================
def get_mount_points():
    system = platform.system()
    partitions = psutil.disk_partitions(all=False)
    if system == "Windows":
        mounts = []
        for p in partitions:
            if p.fstype == '' or 'cdrom' in p.opts.lower():
                continue
            # Éviter les lecteurs A: B: souvent inutiles
            if p.mountpoint.upper().startswith(('A:\\', 'B:\\')):
                continue
            mounts.append(p.mountpoint)
        return sorted(mounts)
    else:
        skip = ('tmpfs', 'devtmpfs', 'proc', 'sysfs', 'cgroup')
        return [p.mountpoint for p in partitions if p.fstype not in skip and not p.mountpoint.startswith('/snap')]

def _get_tree_lines(path, prefix="", max_depth=4, current_depth=0, output=None):
    if output is None:
        output = []
    if current_depth >= max_depth:
        return output
    try:
        entries = sorted(os.listdir(path))
    except (PermissionError, OSError, FileNotFoundError):
        output.append(f"{prefix}📁 [accès refusé]")
        return output

    dirs = []
    important_files = []
    other_file_count = 0

    for e in entries:
        full = os.path.join(path, e)
        try:
            if os.path.isdir(full):
                dirs.append(e)
            elif os.path.isfile(full):
                _, ext = os.path.splitext(e)
                if ext.lower() in EXTENSIONS_IMPORTANTES:
                    important_files.append(e)
                else:
                    other_file_count += 1
        except (OSError, ValueError):
            continue

    total = len(dirs) + len(important_files) + (1 if other_file_count > 0 else 0)
    index = 0

    # Dossiers
    for d in dirs:
        index += 1
        is_last = (index == total)
        mark = "└── " if is_last else "├── "
        output.append(f"{prefix}{mark}📁 {d}")
        next_prefix = prefix + ("    " if is_last else "│   ")
        _get_tree_lines(os.path.join(path, d), next_prefix, max_depth, current_depth + 1, output)

    # Fichiers importants
    for f in sorted(important_files):
        index += 1
        is_last = (index == total)
        mark = "└── " if is_last else "├── "
        icon = "🐍" if f.endswith('.py') else "📄"
        output.append(f"{prefix}{mark}{icon} {f}")

    # Autres fichiers
    if other_file_count > 0:
        index += 1
        is_last = (index == total)
        mark = "└── " if is_last else "├── "
        output.append(f"{prefix}{mark}📄 [{other_file_count} autre(s) fichier(s)]")

    return output

def generate_disk_report(disks):
    lines = []
    lines.append("="*60)
    lines.append("KERBEROS – ANALYSEUR DE DISQUES (MODE PROFOND)")
    lines.append("="*60)
    lines.append(f"Date/Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Système    : {platform.system()} {platform.release()} ({platform.machine()})")
    lines.append(f"Profondeur : {MAX_DEPTH}")
    lines.append("Licence    : GNU GPLv3 – https://liberapay.com/EthicalKerberos/")
    lines.append("="*60)
    lines.append("")

    if not disks:
        lines.append("⚠️ Aucun disque sélectionné.")
        return "\n".join(lines)

    for mount in disks:
        lines.append("="*60)
        lines.append(f" DISQUE : {mount} ")
        lines.append("="*60)
        try:
            usage = psutil.disk_usage(mount)
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            lines.append(f"📊 Espace : {used_gb:.1f} Go / {total_gb:.1f} Go (libre : {free_gb:.1f} Go)")
        except Exception as e:
            lines.append(f"⚠️ Impossible de lire l'espace : {e}")
        lines.append("")
        lines.append("Arborescence :")
        lines.extend(_get_tree_lines(mount, max_depth=MAX_DEPTH))
        lines.append("")

    lines.append("✅ Analyse terminée – Projet Kerberos (GPLv3)")
    return "\n".join(lines)

# ==============================
# Fenêtre principale – Style Kerberos
# ==============================
class DiskAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Kerberos – Analyseur de Disques (Mode Profond)")
        self.root.geometry("900x680")
        self.root.configure(bg=BG_COLOR)

        title = tk.Label(root, text="KERBEROS – Analyse Profonde de Disques",
                         fg=FG_COLOR, bg=BG_COLOR, font=FONT_TITLE)
        title.pack(pady=10)

        # Détection des disques
        try:
            self.mounts = get_mount_points()
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec détection disques :\n{e}")
            self.mounts = []

        # Frame disques
        frame = tk.Frame(root, bg=BG_COLOR)
        frame.pack(pady=5, padx=15, fill=tk.X)

        tk.Label(frame, text="✅ Sélectionnez les disques à analyser :", 
                 fg=FG_COLOR, bg=BG_COLOR, font=FONT_UI).pack(anchor="w")

        self.vars = {}
        if self.mounts:
            for m in self.mounts:
                var = tk.BooleanVar(value=True)
                self.vars[m] = var
                cb = tk.Checkbutton(frame, text=m, variable=var,
                                    bg=BG_COLOR, fg=FG_COLOR,
                                    selectcolor="#333", font=FONT_UI)
                cb.pack(anchor="w", padx=5, pady=2)
        else:
            tk.Label(frame, text="⚠️ Aucun disque détecté (accès limité ou système restreint).",
                     fg="#ffaa00", bg=BG_COLOR, font=FONT_UI).pack(anchor="w", pady=5)

        # Bouton
        self.btn = tk.Button(root, text="🚀 Lancer l'analyse", command=self.run_analysis,
                             bg="#8b0000", fg="white", font=("Consolas", 11, "bold"))
        self.btn.pack(pady=10)

        # Console de sortie (copiable, debug-style)
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=FONT_CONSOLE,
            bg="#0a0a0a", fg=FG_COLOR, insertbackground=FG_COLOR,
            state="normal", height=20
        )
        self.console.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)
        self.console.bind("<Key>", lambda e: "break")  # lecture seule mais sélectionnable

        self.console.insert(tk.END, "ℹ️ Projet Kerberos – Licence GPLv3\n")
        self.console.insert(tk.END, "   Compatible Windows 7/10 – Analyse locale uniquement\n\n")

        if not self.mounts:
            self.console.insert(tk.END, "❗ Aucun disque fixe n'a été détecté. Vérifiez les permissions.\n")

    def run_analysis(self):
        selected = [m for m, var in self.vars.items() if var.get()]
        if not selected and self.mounts:
            messagebox.showwarning("Sélection requise", "Veuillez cocher au moins un disque.")
            return

        try:
            report = generate_disk_report(selected if self.mounts else [])
            self.console.delete(1.0, tk.END)
            self.console.insert(tk.END, report)

            # Sauvegarde
            out_file = "rapport_disques_profond.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(report)
            self.console.insert(tk.END, f"\n\n💾 Rapport sauvegardé : {os.path.abspath(out_file)}\n")

            messagebox.showinfo("✅ Terminé", f"Rapport enregistré :\n{os.path.abspath(out_file)}")
        except Exception as e:
            sauvegarder_rapport_plantage(e, "Analyse disques")

# ==============================
# Lancement
# ==============================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DiskAnalyzerGUI(root)
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        sauvegarder_rapport_plantage(e, "Lancement GUI")
        sys.exit(1)