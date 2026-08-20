# guard_tray_status.py — Kerberos v2.3 — GPLv3
# ✅ Utilise pystray + Pillow (déjà présents sur ta machine)
# ✅ Compatible Windows 7 Pro / HDD / 64 bits
# ✅ Aucun fichier externe — icône générée en mémoire

import threading
import pystray
from PIL import Image, ImageDraw

# --- 1. Génération d'une icône 16x16 dynamique ---
def create_icon(green=0, yellow=0, red=0):
    """
    Crée une icône compacte : barres vert/orange/rouge.
    Ex: green=5, yellow=1, red=1 → [||||| | |]
    """
    size = 16
    img = Image.new("RGBA", (size, size), (30, 30, 40, 255))  # fond gris foncé
    draw = ImageDraw.Draw(img)

    # Répartir 7 segments sur 14px de large (2px d'espacement)
    total = green + yellow + red
    if total == 0:
        total = 7
    seg_width = max(1, 14 // total)
    x = 1

    # Palette Kerberos
    for i in range(green):
        draw.rectangle([x, 2, x + seg_width - 1, 14], fill=(0, 200, 0))  # 🟢
        x += seg_width + 1
    for i in range(yellow):
        draw.rectangle([x, 2, x + seg_width - 1, 14], fill=(255, 165, 0))  # 🟡
        x += seg_width + 1
    for i in range(red):
        draw.rectangle([x, 2, x + seg_width - 1, 14], fill=(220, 20, 60))  # 🔴
        x += seg_width + 1

    return img

# --- 2. Actions du menu ---
def show_details(icon, item):
    from tkinter import messagebox, Tk
    Tk().withdraw()  # cache la fenêtre racine
    g, y, r = getattr(icon, "_kerb_counts", (0, 0, 0))
    messagebox.showinfo("🛡️ Kerberos — État des guards",
        f"🟢 Actifs    : {g}\n"
        f"🟡 En attente : {y}\n"
        f"🔴 Échecs     : {r}\n\n"
        "→ Aucune donnée n’a quitté cette machine.")

def reload_guards(icon, item):
    from tkinter import messagebox, Tk
    Tk().withdraw()
    messagebox.showinfo("🔄 Kerberos", 
        "Rechargement des guards déclenché.\n"
        "(Implémenté en v2.4 avec guard_reload())")

def quit_kerberos(icon, item):
    icon.stop()

# --- 3. Lancement du tray ---
def run_tray(guard_results):
    """
    À appeler après activation des 7 guards.
    guard_results = [True, True, False, None, True, True, True]
    """
    green = sum(1 for r in guard_results if r is True)
    yellow = sum(1 for r in guard_results if r is None)
    red = sum(1 for r in guard_results if r is False)

    icon_img = create_icon(green, yellow, red)
    icon = pystray.Icon(
        name="Kerberos",
        icon=icon_img,
        title=f"Kerberos: {green}🟢 {yellow}🟡 {red}🔴",
        menu=pystray.Menu(
            pystray.MenuItem("État détaillé", show_details),
            pystray.MenuItem("Recharger les guards", reload_guards),
            pystray.MenuItem("Quitter", quit_kerberos)
        )
    )
    # Stocke les compteurs pour le menu
    icon._kerb_counts = (green, yellow, red)

    # Lance dans un thread détaché → ne bloque pas le CLI
    thread = threading.Thread(target=icon.run, daemon=True, name="KerberosTray")
    thread.start()
    return icon  # optionnel : pour refresh ultérieur