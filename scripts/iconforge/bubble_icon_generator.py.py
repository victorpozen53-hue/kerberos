# -*- coding: utf-8 -*-
# bubble_icon_generator.py
# Générateur d'icônes pour la Bulle Protectrice – Kerberos v1.0
# GPLv3 – https://liberapay.com/EthicalKerberos/
# Par Victor & Mirko – IA de garde pour Windows
# Ce script crée 4 icônes (inactive, active, warning, alert) en format PostScript.
# Convertissez les .ps en .png ou .ico avec un outil externe (ex: cloudconvert.com).

import os
import sys
import tkinter as tk
from tkinter import Canvas

# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE_DIR, "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

# Taille de l'icône (32x32 pixels)
SIZE = 32
HALF = SIZE // 2

# Couleurs RGBA (R, G, B, Alpha) – Alpha non utilisé dans PostScript, mais conservé pour clarté
ICON_STATES = {
    "inactive": (100, 100, 100),   # Gris – bulle inactive
    "active":   (0, 200, 0),       # Vert – protection active
    "warning":  (255, 170, 0),     # Orange – alerte mineure
    "alert":    (255, 50, 50)      # Rouge – attaque détectée
}

# === DEBUG MAISON ===
def debug_log(msg):
    """Loggue un message dans la console et dans un fichier."""
    print(f"[BULLE ICON] {msg}")
    try:
        log_path = os.path.join(ICONS_DIR, "icon_generator.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
    except:
        pass

# === FONCTION DE DESSIN ===
def generate_icon(state_name, color_rgb):
    """Génère une icône au format PostScript via Tkinter."""
    try:
        # Créer fenêtre cachée
        root = tk.Tk()
        root.withdraw()

        # Canvas transparent (fond blanc temporaire – PostScript gère la transparence via fond)
        canvas = Canvas(root, width=SIZE, height=SIZE, bg='white', highlightthickness=0)
        canvas.pack()

        r, g, b = color_rgb
        hex_color = f"#{r:02x}{g:02x}{b:02x}"

        # 1. BULLE (cercle vide)
        canvas.create_oval(
            HALF - 14, HALF - 14,
            HALF + 14, HALF + 14,
            outline=hex_color, width=2, fill=''
        )

        # 2. HDD (corps + plateau)
        # Corps rectangulaire
        canvas.create_rectangle(
            HALF - 7, HALF - 4,
            HALF + 7, HALF + 4,
            outline=hex_color, fill='', width=1
        )
        # Plateau (disque qui tourne)
        canvas.create_oval(
            HALF - 2, HALF - 2,
            HALF + 2, HALF + 2,
            outline=hex_color, fill=hex_color, width=1
        )

        # Sauvegarde en PostScript
        ps_path = os.path.join(ICONS_DIR, f"bubble_{state_name}.ps")
        canvas.postscript(file=ps_path, colormode='color', width=SIZE, height=SIZE)

        root.destroy()
        debug_log(f"Icône '{state_name}' générée : {ps_path}")
        return True

    except Exception as e:
        debug_log(f"ERREUR génération '{state_name}': {e}")
        return False

# === LANCEMENT ===
def main():
    debug_log("=== DÉMARRAGE GÉNÉRATEUR D'ICÔNES KERBEROS ===")
    debug_log("Objectif : créer 4 icônes pour la Bulle Protectrice Multicouches.")
    debug_log("Format : PostScript (.ps) → à convertir manuellement en .png/.ico.")

    success_count = 0
    for state, color in ICON_STATES.items():
        if generate_icon(state, color):
            success_count += 1

    debug_log(f"✅ {success_count}/4 icônes générées dans : {ICONS_DIR}")
    debug_log("➡️  Prochaine étape : convertir les .ps en .ico (ex: avec Greenfish ou cloudconvert.com)")
    debug_log("ℹ️  Rappel : les icônes sont 100% libres de droits – GPLv3 compatible.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        debug_log(" INTERRUPTION MANUELLE – Génération annulée.")
    except Exception as e:
        debug_log(f" ERREUR FATALE : {e}")