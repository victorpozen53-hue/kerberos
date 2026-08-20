import tkinter as tk

NAME = "boutons"
TYPE = "ui"
UI = False
FRONTS = None
DESCRIPTION = "🔘 Barre de boutons d'action rapide"

def _ouvrir_guard(app, nom):
    mod = app.guards.get(nom)
    if mod and hasattr(mod, "open_ui"):
        mod.open_ui(app.root, app.ctx)

def _effacer_console(app):
    app.console.configure(state='normal')
    app.console.delete('1.0', tk.END)
    app.console.configure(state='disabled')
    app._print("🧹 Console effacée")

def inject_buttons(app):
    tb = getattr(app, "toolbar_frame", None)
    if tb is None or tb.winfo_children(): return
    boutons = [
        ("🚀 Scan complet",   '#2d7b5a', app._scan_tout),
        ("📝 Nouvelle cible", '#2d5a7b', lambda: _ouvrir_guard(app, "saisie")),
        ("🌍 Archives libres",'#2d5a7b', lambda: _ouvrir_guard(app, "archives_libres")),
        ("📄 Rapport",        '#2d7b7b', app._open_rapport),
        ("🧹 Effacer",        '#7b5a2d', lambda: _effacer_console(app)),
    ]
    for texte, couleur, cmd in boutons:
        tk.Button(tb, text=texte, bg=couleur, fg='white',
                  font=("Consolas",10,"bold"), relief=tk.RAISED, bd=1,
                  command=cmd).pack(side=tk.LEFT, padx=4, pady=6)

def run(cible, ctx, emit):
    return