import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import os
import sys

# --- Configuration du thème Kerberos ---
BG_COLOR = "#0d1117"       # Fond sombre (style GitHub Dark)
TEXT_COLOR = "#c9d1d9"     # Texte clair
ACCENT_COLOR = "#00ff41"   # Vert hacker
BTN_COLOR = "#238636"      # Vert bouton GitHub
BTN_HOVER = "#2ea043"

def log(message, color=TEXT_COLOR):
    """Ajoute un message dans la zone de log"""
    log_area.config(state=tk.NORMAL)
    log_area.insert(tk.END, message + "\n", color)
    log_area.see(tk.END) # Scroll automatique vers le bas
    log_area.config(state=tk.DISABLED)
    root.update_idletasks() # Force la mise à jour de l'interface

def run_git_command(command):
    """Exécute une commande Git et affiche la sortie en temps réel"""
    try:
        # On utilise Popen pour lire la sortie ligne par ligne
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            log(line.strip())
            
        process.wait()
        return process.returncode
    except Exception as e:
        log(f"❌ ERREUR SYSTÈME: {e}", "red")
        return 1

def deploy():
    """Fonction principale déclenchée par le bouton"""
    message = entry_message.get().strip()
    
    if not message:
        messagebox.showwarning("Attention", "Tu dois entrer un message de commit !")
        return

    # Désactiver le bouton pendant le déploiement
    btn_deploy.config(state=tk.DISABLED, text="Déploiement en cours...")
    entry_message.config(state=tk.DISABLED)
    
    # Vider les logs précédents
    log_area.config(state=tk.NORMAL)
    log_area.delete(1.0, tk.END)
    log_area.config(state=tk.DISABLED)

    log("🚀 === DÉPLOIEMENT KERBEROS VERS GITHUB ===", ACCENT_COLOR)
    log(f" Dossier de travail : {os.getcwd()}\n")

    # 1. Git Add
    log("📦 Étape 1 : Préparation des fichiers (git add)...", ACCENT_COLOR)
    run_git_command("git add .")
    log("")

    # 2. Git Commit
    log(f"🔒 Étape 2 : Sauvegarde locale (commit)...", ACCENT_COLOR)
    code = run_git_command(f'git commit -m "{message}"')
    
    if code != 0:
        log("⚠️ Aucun changement détecté ou erreur de commit. Annulation de l'envoi.", "orange")
        reset_ui()
        return
    log("")

    # 3. Git Push
    log(" Étape 3 : Envoi vers GitHub (git push)...", ACCENT_COLOR)
    run_git_command("git push -u origin main")
    
    log("\n✅ === TERMINÉ ! Ton binôme peut voir les modifs. ===", ACCENT_COLOR)
    reset_ui()

def reset_ui():
    """Réactive l'interface"""
    btn_deploy.config(state=tk.NORMAL, text="🚀 Déployer vers GitHub")
    entry_message.config(state=tk.NORMAL)

# --- Création de la fenêtre Tkinter ---
root = tk.Tk()
root.title("Kerberos Git Deployer v1.0")
root.geometry("700x500")
root.configure(bg=BG_COLOR)
root.resizable(False, False)

# Titre
title_label = tk.Label(root, text="️ KERBEROS GIT DEPLOYER", font=("Consolas", 16, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
title_label.pack(pady=15)

# Zone de saisie du message
frame_input = tk.Frame(root, bg=BG_COLOR)
frame_input.pack(pady=10, padx=20, fill=tk.X)

tk.Label(frame_input, text="Message du commit :", font=("Consolas", 10), bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor=tk.W)
entry_message = tk.Entry(frame_input, font=("Consolas", 12), bg="#161b22", fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief=tk.FLAT, bd=2)
entry_message.pack(fill=tk.X, pady=5, ipady=5)

# Bouton de déploiement
btn_deploy = tk.Button(root, text="🚀 Déployer vers GitHub", font=("Consolas", 12, "bold"), bg=BTN_COLOR, fg="white", activebackground=BTN_HOVER, activeforeground="white", relief=tk.FLAT, command=deploy, cursor="hand2")
btn_deploy.pack(pady=10, ipadx=20, ipady=5)

# Zone de logs (Console)
log_area = scrolledtext.ScrolledText(root, font=("Consolas", 10), bg="#161b22", fg=TEXT_COLOR, insertbackground=TEXT_COLOR, relief=tk.FLAT, state=tk.DISABLED, wrap=tk.WORD)
log_area.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

# Configurer les couleurs de texte pour les tags
log_area.tag_config("red", foreground="red")
log_area.tag_config("orange", foreground="orange")
log_area.tag_config(ACCENT_COLOR, foreground=ACCENT_COLOR)

# S'assurer qu'on est dans le bon dossier au démarrage
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Lancer l'application
root.mainloop()