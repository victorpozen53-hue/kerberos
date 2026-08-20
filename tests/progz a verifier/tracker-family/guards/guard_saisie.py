# ============================================================
#  guard_saisie.py — Saisir une cible SANS toucher au JSON
#  ✅ CORRIGÉ : fonction run() ajoutée (plus d'erreur au scan)
# ============================================================
import json
import tkinter as tk
from tkinter import ttk, messagebox

NAME = "saisie"
TYPE = "saisie"        # type spécial : ouvre un formulaire
UI = True              # dit au moteur : "je suis une interface"
DESCRIPTION = "📝 Formulaire pour rentrer nom, prénom, lieu, pays — zéro JSON"
FRONTS = None

def open_ui(root, ctx):
    """Ouvre la fenêtre de saisie (appelé par le moteur)."""
    config = ctx["config"]
    config_path = ctx["config_path"]

    win = tk.Toplevel(root)
    win.title("📝 Saisir une cible")
    win.geometry("560x620")
    win.configure(bg='#1a1a2e')

    tk.Label(win, text="📝 NOUVELLE RECHERCHE", bg='#16213e', fg='#00ffcc',
             font=("Consolas", 16, "bold")).pack(pady=15, fill=tk.X)

    # ---- formulaire ----
    form = tk.LabelFrame(win, text=" Remplis les infos ", bg='#1e1e2e', fg='#00ffcc',
                         font=("Consolas", 11, "bold"))
    form.pack(fill=tk.X, padx=15, pady=10)

    vars_ = {}
    champs = [("nom", "Nom :"),
              ("prenom", "Prénom :"),
              ("naissance", "Année de naissance :"),
              ("lieu", "Lieu / Ville :"),
              ("pays", "Pays :")]
    for i, (cle, label) in enumerate(champs):
        tk.Label(form, text=label, bg='#1e1e2e', fg='#bb86fc',
                 font=("Consolas", 10, "bold")).grid(row=i, column=0, sticky="w", padx=10, pady=6)
        var = tk.StringVar()
        tk.Entry(form, textvariable=var, width=30, bg='#333333', fg='white',
                 insertbackground='white').grid(row=i, column=1, padx=10, pady=6)
        vars_[cle] = var

    # ---- type de recherche (liste déroulante) ----
    tk.Label(form, text="Type de recherche :", bg='#1e1e2e', fg='#bb86fc',
             font=("Consolas", 10, "bold")).grid(row=len(champs), column=0, sticky="w", padx=10, pady=6)
    var_front = tk.StringVar(value="France")
    ttk.Combobox(form, textvariable=var_front, width=27,
                 values=["France", "Italie", "Mer", "Belgique", "Autre"]
                 ).grid(row=len(champs), column=1, padx=10, pady=6)

    def enregistrer():
        nom = vars_["nom"].get().strip()
        prenom = vars_["prenom"].get().strip()
        if not nom and not prenom:
            messagebox.showwarning("Oups", "Mets au moins un nom ou un prénom !")
            return
        try:
            naissance = int(vars_["naissance"].get().strip() or 0) or None
        except ValueError:
            naissance = None
        cible = {"nom": nom.upper(), "prenom": prenom, "naissance": naissance,
                 "lieu": vars_["lieu"].get().strip(), "pays": vars_["pays"].get().strip(),
                 "front": var_front.get()}
        config.setdefault("cibles", []).append(cible)
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        messagebox.showinfo("✅ Enregistré", f"{prenom} {nom} ajouté au dossier !")
        rafraichir_liste()
        for v in vars_.values():
            v.set("")

    tk.Button(form, text="➕ ENREGISTRER CETTE CIBLE", bg='#2d7b5a', fg='white',
              font=("Consolas", 12, "bold"), command=enregistrer
              ).grid(row=len(champs)+1, column=0, columnspan=2, pady=15)

    # ---- liste des cibles déjà dans le dossier ----
    list_frame = tk.LabelFrame(win, text=" 🎯 Déjà dans le dossier ", bg='#1e1e2e', fg='#00ffcc',
                               font=("Consolas", 11, "bold"))
    list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    def supprimer(idx):
        cs = config.get("cibles", [])
        if 0 <= idx < len(cs):
            cs.pop(idx)
            config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
            rafraichir_liste()

    def rafraichir_liste():
        for w in list_frame.winfo_children():
            w.destroy()
        cibles = config.get("cibles", [])
        if not cibles:
            tk.Label(list_frame, text="(vide)", bg='#1e1e2e', fg='#666666').pack(pady=10)
            return
        for i, c in enumerate(cibles):
            row = tk.Frame(list_frame, bg='#161a2e', relief=tk.RIDGE, bd=1)
            row.pack(fill=tk.X, padx=8, pady=4)
            txt = f"{c.get('prenom','')} {c.get('nom','')} ({c.get('naissance','?')}) [{c.get('front','?')}]"
            tk.Label(row, text=txt, bg='#161a2e', fg='white', font=("Consolas", 10)
                     ).pack(side=tk.LEFT, padx=8, pady=6)
            tk.Button(row, text="🗑", bg='#7b2d2d', fg='white', width=3,
                      command=lambda idx=i: supprimer(idx)).pack(side=tk.RIGHT, padx=8)

    rafraichir_liste()


# ============================================================
#  ✅ CORRECTION — le moteur appelle run() pendant le scan.
#  Ce guard est une interface (formulaire), il n'a rien à scanner.
# ============================================================
def run(cible, ctx, emit):
    # Guard d'interface : rien à scanner
    return