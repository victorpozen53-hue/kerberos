import os
import psutil
import platform
import sys
import traceback
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


# ==============================
# Fonction utilitaire : rapport de crash
# ==============================

def sauvegarder_rapport_plantage(exception, context="Inconnu"):
    rapport = f"""
{'='*60}
RAPPORT DE PLANTAGE – Outil d'analyse de disques (GUI)
{'='*60}
Date/Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Système    : {platform.system()} {platform.release()} ({platform.machine()})
Python     : {platform.python_version()}
Contexte   : {context}
{'-'*60}
Erreur détectée :
{type(exception).__name__}: {exception}

Traceback complet :
{traceback.format_exc()}
{'='*60}
"""
    try:
        with open("crash_report_gui.txt", "w", encoding="utf-8") as f:
            f.write(rapport)
        messagebox.showerror("Erreur", "Une erreur s'est produite !\nUn rapport a été sauvegardé dans 'crash_report_gui.txt'")
    except Exception as e:
        print("Impossible de sauvegarder le rapport :", e)
        print(rapport)


# ==============================
# Logique principale
# ==============================

def get_mount_points():
    system = platform.system()
    partitions = psutil.disk_partitions(all=False)
    
    if system == "Windows":
        return [p.mountpoint for p in partitions if 'cdrom' not in p.opts and p.fstype != '']
    else:
        skip = ('tmpfs', 'devtmpfs', 'proc', 'sysfs', 'cgroup', 'snap', 'squashfs', 'overlay')
        return [p.mountpoint for p in partitions if p.fstype not in skip and not p.mountpoint.startswith('/snap')]


def generate_disk_report(disks_to_analyze):
    """Génère le contenu textuel complet du rapport (sans interface)."""
    lines = []
    lines.append("="*60)
    lines.append("RAPPORT D'ANALYSE DES DISQUES")
    lines.append("="*60)
    lines.append(f"Date/Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Système    : {platform.system()} {platform.release()} ({platform.machine()})")
    lines.append(f"Python     : {platform.python_version()}")
    lines.append("="*60)
    lines.append("")

    if not disks_to_analyze:
        lines.append("❌ Aucun disque sélectionné.")
        return "\n".join(lines)

    for mount in disks_to_analyze:
        lines.append("="*60)
        lines.append(f"DISQUE : {mount}")
        lines.append("="*60)
        try:
            usage = psutil.disk_usage(mount)
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            lines.append(f"📊 Espace : {used_gb:.1f} Go utilisés / {total_gb:.1f} Go total (libre : {free_gb:.1f} Go)")
        except (OSError, PermissionError, ValueError) as e:
            lines.append(f"⚠️ Impossible de lire l'espace disque : {e}")
        
        lines.append("")
        lines.append("Arborescence (2 niveaux) :")
        lines.extend(_get_tree_lines(mount, max_depth=2))
        lines.append("")

    lines.append("✅ Analyse terminée !")
    return "\n".join(lines)


def _get_tree_lines(path, prefix="", max_depth=2, current_depth=0, output=None):
    """Retourne une liste de lignes pour l’arborescence (version texte)."""
    if output is None:
        output = []
    if current_depth > max_depth:
        return output
    try:
        entries = sorted(os.listdir(path))
    except (PermissionError, OSError, FileNotFoundError):
        output.append(f"{prefix}📁 [accès refusé ou non disponible]")
        return output

    dirs = []
    files = []
    for e in entries:
        full_path = os.path.join(path, e)
        try:
            if os.path.isdir(full_path):
                dirs.append(e)
            elif os.path.isfile(full_path):
                files.append(e)
        except (OSError, ValueError):
            continue

    total_dirs = len(dirs)
    for i, dirname in enumerate(dirs):
        is_last = (i == total_dirs - 1 and not files)
        connector = "└── " if is_last else "├── "
        output.append(f"{prefix}{connector}📁 {dirname}")
        next_prefix = prefix + ("    " if is_last else "│   ")
        _get_tree_lines(os.path.join(path, dirname), next_prefix, max_depth, current_depth + 1, output)

    if files and current_depth < max_depth:
        connector = "└── " if not dirs else "├── "
        output.append(f"{prefix}{connector}📄 [{len(files)} fichier(s)]")
    
    return output


def analyze_and_save_report(disks_to_analyze, text_output):
    """Analyse les disques, affiche dans l’interface ET sauvegarde dans un fichier."""
    if not disks_to_analyze:
        messagebox.showwarning("Aucune sélection", "Veuillez cocher au moins un disque à analyser.")
        return

    # Générer le rapport texte complet
    rapport_texte = generate_disk_report(disks_to_analyze)

    # Afficher dans l’interface
    text_output.delete(1.0, tk.END)
    text_output.insert(tk.END, "✅ Analyse terminée ! Résultat ci-dessous :\n\n")
    text_output.insert(tk.END, rapport_texte)

    # Sauvegarder dans un fichier
    nom_fichier = "rapport_disques.txt"
    try:
        with open(nom_fichier, "w", encoding="utf-8") as f:
            f.write(rapport_texte)
        text_output.insert(tk.END, f"\n\n💾 Rapport sauvegardé dans : {os.path.abspath(nom_fichier)}")
        messagebox.showinfo("Succès", f"Le rapport a été enregistré sous :\n{os.path.abspath(nom_fichier)}")
    except Exception as e:
        err_msg = f"⚠️ Impossible de sauvegarder le rapport : {e}"
        text_output.insert(tk.END, f"\n\n{err_msg}")
        messagebox.showerror("Erreur de sauvegarde", err_msg)


# ==============================
# Interface graphique
# ==============================

def create_gui():
    root = tk.Tk()
    root.title("🔍 Analyseur de disques interactif")
    root.geometry("850x650")
    root.resizable(True, True)

    try:
        mounts = get_mount_points()
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de détecter les disques :\n{e}")
        mounts = []

    if not mounts:
        messagebox.showwarning("Aucun disque", "Aucun disque n’a été détecté.")
        root.destroy()
        return

    disk_vars = {mount: tk.BooleanVar(value=True) for mount in mounts}

    # Frame de sélection
    frame_check = tk.Frame(root)
    frame_check.pack(padx=15, pady=10, fill=tk.X)

    tk.Label(frame_check, text="✅ Sélectionnez les disques à analyser :", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 10))

    for mount in mounts:
        cb = tk.Checkbutton(frame_check, text=mount, variable=disk_vars[mount], anchor="w", font=("Arial", 10))
        cb.pack(anchor="w", padx=5, pady=2)

    # Bouton
    def on_analyze():
        selected = [mount for mount, var in disk_vars.items() if var.get()]
        analyze_and_save_report(selected, text_output)

    btn = tk.Button(root, text="🚀 Lancer l'analyse et générer le rapport", command=on_analyze, bg="#2196F3", fg="white", font=("Arial", 10, "bold"), height=2)
    btn.pack(pady=10)

    # Zone de texte
    text_output = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 9))
    text_output.pack(padx=15, pady=(0, 15), fill=tk.BOTH, expand=True)

    text_output.insert(tk.END, "ℹ️ Cochez les disques, puis cliquez sur le bouton pour analyser et générer 'rapport_disques.txt'.\n")

    root.mainloop()


# ==============================
# Point d'entrée
# ==============================

if __name__ == "__main__":
    try:
        create_gui()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sauvegarder_rapport_plantage(e, context="Interface graphique")
        sys.exit(1)