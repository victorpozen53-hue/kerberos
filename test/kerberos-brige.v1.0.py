import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import os
import sys
import webbrowser

# --- Configuration du thème Kerberos ---
BG_COLOR = "#0d1117"       # Fond sombre (style GitHub Dark)
TEXT_COLOR = "#c9d1d9"     # Texte clair
ACCENT_COLOR = "#00ff41"   # Vert hacker
BTN_COLOR = "#238636"      # Vert bouton GitHub
BTN_HOVER = "#2ea043"
LINK_COLOR = "#58a6ff"     # Bleu lien

# --- Constantes du projet ---
DEFAULT_DIR = r""
GITHUB_URL = "https://github.com/victorpozen53-hue/kerberos"
LIBERAPAY_URL = "https://liberapay.com/victor-pozen"

def log(message, color=TEXT_COLOR):
    """Ajoute un message dans la zone de log"""
    log_area.config(state=tk.NORMAL)
    log_area.insert(tk.END, message + "\n", color)
    log_area.see(tk.END) # Scroll automatique vers le bas
    log_area.config(state=tk.DISABLED)
    root.update_idletasks()

def run_git_command(command):
    """Exécute une commande Git et affiche la sortie en temps réel"""
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        for line in process.stdout:
            log(line.strip())
        process.wait()
        return process.returncode
    except Exception as e:
        log(f"❌ ERREUR SYSTÈME: {e}", "red")
        return 1

def toggle_lock():
    """Verrouille ou déverrouille le chemin du disque"""
    if lock_var.get():
        entry_path.config(state=tk.DISABLED)
        log("🔒 Chemin verrouillé. Sécurisé pour le déploiement.", ACCENT_COLOR)
    else:
        entry_path.config(state=tk.NORMAL)
        log("🔓 Chemin déverrouillé. Attention aux modifications.", "orange")

def deploy():
    """Fonction principale déclenchée par le bouton"""
    # Vérification du verrou
    if not lock_var.get():
        if not messagebox.askyesno("⚠️ Sécurité", 
            "Le chemin n'est pas verrouillé !\nEs-tu sûr de vouloir déployer depuis ce dossier ?"):
            return

    message = entry_message.get().strip()
    if not message:
        messagebox.showwarning("Attention", "Tu dois entrer un message de commit !")
        return

    current_dir = entry_path.get().strip()
    if not os.path.isdir(current_dir):
        messagebox.showerror("Erreur", f"Le dossier n'existe pas :\n{current_dir}")
        return

    # Forcer le changement de dossier
    os.chdir(current_dir)

    # Désactiver l'interface pendant le travail
    btn_deploy.config(state=tk.DISABLED, text="⏳ Déploiement en cours...")
    entry_message.config(state=tk.DISABLED)
    
    # Vider les anciens logs
    log_area.config(state=tk.NORMAL)
    log_area.delete(1.0, tk.END)
    log_area.config(state=tk.DISABLED)

    log("🚀 === DÉPLOIEMENT KERBEROS VERS GITHUB ===", ACCENT_COLOR)
    log(f"📁 Dossier cible : {current_dir}")
    log(f"🌐 Repository   : {GITHUB_URL}\n")

    log("📦 Étape 1 : Préparation des fichiers (git add)...", ACCENT_COLOR)
    run_git_command("git add .")
    log("")

    log("🔒 Étape 2 : Sauvegarde locale (commit)...", ACCENT_COLOR)
    code = run_git_command(f'git commit -m "{message}"')
    
    if code != 0:
        log("⚠️ Aucun changement détecté ou erreur. Annulation de l'envoi.", "orange")
        reset_ui()
        return
    log("")

    log("📬 Étape 3 : Envoi vers GitHub (git push)...", ACCENT_COLOR)
    run_git_command("git push -u origin main")
    
    log("\n✅ === TERMINÉ !  ===", ACCENT_COLOR)
    reset_ui()

def reset_ui():
    """Réactive l'interface"""
    btn_deploy.config(state=tk.NORMAL, text="🚀 Déployer vers GitHub")
    entry_message.config(state=tk.NORMAL)

# --- Création de la fenêtre Tkinter ---
root = tk.Tk()
root.title("Kerberos Deploy Bridge v2.0")
root.geometry("800x600")
root.configure(bg=BG_COLOR)
root.resizable(False, False)

# 1. En-tête avec Licence et Lien
header_frame = tk.Frame(root, bg=BG_COLOR)
header_frame.pack(fill=tk.X, pady=10)

tk.Label(header_frame, text="🛡️ KERBEROS DEPLOY BRIDGE v2.0", 
         font=("Consolas", 16, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR).pack()

tk.Label(header_frame, text="Licence : GPLv3 — Code ouvert, éthique et local.", 
         font=("Consolas", 9), bg=BG_COLOR, fg="#8b949e").pack(pady=2)

liberapay_link = tk.Label(header_frame, text=f"❤️ Soutenir le projet : {LIBERAPAY_URL}", 
                          font=("Consolas", 9, "underline"), bg=BG_COLOR, fg=LINK_COLOR, cursor="hand2")
liberapay_link.pack(pady=2)
liberapay_link.bind("<Button-1>", lambda e: webbrowser.open(LIBERAPAY_URL))

# Séparateur
tk.Label(root, text="─" * 90, font=("Consolas", 8), bg=BG_COLOR, fg="#30363d").pack(pady=5)

# 2. Sélection du disque et Verrouillage
path_frame = tk.Frame(root, bg=BG_COLOR)
path_frame.pack(pady=5, padx=20, fill=tk.X)

tk.Label(path_frame, text="📁 Chemin du projet :", font=("Consolas", 10, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor=tk.W)

path_inner_frame = tk.Frame(path_frame, bg=BG_COLOR)
path_inner_frame.pack(fill=tk.X, pady=5)

entry_path = tk.Entry(path_inner_frame, font=("Consolas", 11), bg="#161b22", fg=TEXT_COLOR, 
                      insertbackground=TEXT_COLOR, relief=tk.FLAT, bd=2)
entry_path.insert(0, DEFAULT_DIR)
entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

lock_var = tk.BooleanVar(value=True) # Verrouillé par défaut pour la sécurité
chk_lock = tk.Checkbutton(path_inner_frame, text="🔒 Verrouiller", variable=lock_var, 
                          command=toggle_lock, bg=BG_COLOR, fg=ACCENT_COLOR, 
                          selectcolor="#161b22", font=("Consolas", 9, "bold"))
chk_lock.pack(side=tk.RIGHT, padx=5)

# 3. Message de commit
msg_frame = tk.Frame(root, bg=BG_COLOR)
msg_frame.pack(pady=5, padx=20, fill=tk.X)

tk.Label(msg_frame, text="📝 Message du commit :", font=("Consolas", 10, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor=tk.W)
entry_message = tk.Entry(msg_frame, font=("Consolas", 11), bg="#161b22", fg=TEXT_COLOR, 
                         insertbackground=TEXT_COLOR, relief=tk.FLAT, bd=2)
entry_message.pack(fill=tk.X, pady=5, ipady=5)
entry_message.insert(0, "feat: mise à jour du projet") # Message par défaut

# 4. Bouton de déploiement
btn_deploy = tk.Button(root, text="🚀 Déployer vers GitHub", font=("Consolas", 12, "bold"), 
                       bg=BTN_COLOR, fg="white", activebackground=BTN_HOVER, activeforeground="white", 
                       relief=tk.FLAT, command=deploy, cursor="hand2")
btn_deploy.pack(pady=10, ipadx=20, ipady=5)

# 5. Zone de logs (Console)
log_area = scrolledtext.ScrolledText(root, font=("Consolas", 10), bg="#161b22", fg=TEXT_COLOR, 
                                     insertbackground=TEXT_COLOR, relief=tk.FLAT, state=tk.DISABLED, wrap=tk.WORD)
log_area.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

# Configurer les couleurs de texte pour les tags
log_area.tag_config("red", foreground="#ff7b72")
log_area.tag_config("orange", foreground="#d29922")
log_area.tag_config(ACCENT_COLOR, foreground=ACCENT_COLOR)

# S'assurer qu'on est dans le bon dossier au démarrage
if os.path.isdir(DEFAULT_DIR):
    os.chdir(DEFAULT_DIR)
    toggle_lock() # Appliquer le verrouillage au démarrage

# Lancer l'application
root.mainloop()
