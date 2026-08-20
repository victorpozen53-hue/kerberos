#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  KERBEROS FAMILY TRACE v1.1 — MOTEUR COMPLET CORRIGÉ
#  - Compatible Python 3.8
#  - Barre de boutons (guard_boutons.py) + commande "cherche"
#  - Sidebar avec section 📝 SAISIE
#  - Scan tolérant (guards sans run() ignorés)
#  - Aucune donnée perso dans le code (tout dans kerberos_config.json)
# ============================================================================
import sys, json, threading, time, webbrowser, logging, importlib.util, re
from urllib.parse import quote
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from garde import GardeJournal, GardeIdentite, GardeRobots, GardeCadence, Portier

ROOT       = Path(__file__).parent.resolve()
GUARDS_DIR = ROOT / "guards"
RESULTS    = ROOT / "kerberos_results"
CONFIG     = ROOT / "kerberos_config.json"
RESULTS.mkdir(exist_ok=True)

def _logger():
    logging.basicConfig(filename=RESULTS/"kerberos.log", level=logging.INFO,
                        format="%(asctime)s | %(message)s")
    return logging.getLogger("kerberos")

class FamilyTraceApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛡️ KERBEROS FAMILY TRACE — Moteur")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1e1e1e')
        self._closing = False
        self._gestion_window = None
        self._heart = 0
        self.logger = _logger()
        self.config = self._load_config()
        ctx = {"logger": self.logger,
               "ua": "KerberosFamilyTrace/1.1 (recherche familiale personnelle)",
               "pause": self.config.get("pause", 1.5)}
        self.portier = Portier([GardeJournal(), GardeIdentite(),
                                GardeRobots(), GardeCadence()], ctx)
        self.ctx = {"portier": self.portier, "config": self.config,
                    "logger": self.logger, "config_path": CONFIG,
                    "root": self.root, "app": self}
        self.guards = self._decouvrir_guards()
        self.results = []
        self._setup_styles()
        self._show_boot_animation()
        self._setup_ui()
        self._heartbeat()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    # ---------- config ----------
    def _load_config(self):
        if not CONFIG.exists():
            CONFIG.write_text(json.dumps({"pause":1.5,"bateau":"","termes_extra":[],
                "cibles":[{"nom":"NOM","prenom":"PRENOM","naissance":1909,
                           "lieu":"VILLE","front":"Italie"}]}, indent=2), encoding="utf-8")
        try: return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception: return {"cibles":[]}

    def _sauver_config(self):
        CONFIG.write_text(json.dumps(self.config, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---------- découverte des guards ----------
    def _decouvrir_guards(self):
        guards = {}
        GUARDS_DIR.mkdir(exist_ok=True)
        for f in sorted(GUARDS_DIR.glob("*.py")):
            try:
                spec = importlib.util.spec_from_file_location(f.stem, f)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                guards[getattr(mod, "NAME", f.stem)] = mod
            except Exception as e:
                print(f"⚠️ guard {f.name} : {e}")
        return guards

    # ---------- styles ----------
    def _setup_styles(self):
        style = ttk.Style()
        try: style.theme_use('clam')
        except Exception: pass
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', background='#1e1e1e', foreground='#00ffcc', font=('Consolas',10))
        style.configure('TButton', background='#2d5a7b', foreground='#00ffcc', font=('Consolas',10))
        style.configure('TNotebook', background='#1e1e1e')
        style.configure('TNotebook.Tab', background='#2d2d3d', foreground='#00ffcc', padding=[12,6])
        style.map('TNotebook.Tab', background=[('selected','#3d3d4d')])

    # ---------- boot ----------
    def _show_boot_animation(self):
        bw = tk.Toplevel(self.root); bw.title("BOOT"); bw.geometry("700x420")
        bw.configure(bg='#0a0a0a'); bw.overrideredirect(True); bw.update_idletasks()
        bw.geometry(f"+{bw.winfo_screenwidth()//2-350}+{bw.winfo_screenheight()//2-210}")
        bt = tk.Text(bw, bg='#0a0a0a', fg='#00ff00', font=("Courier",10), relief=tk.FLAT)
        bt.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        lines = ["╔══════════════════════════════════════════╗",
                 "║   KERBEROS FAMILY TRACE — BOOT           ║",
                 "╚══════════════════════════════════════════╝","",
                 "[████████████████████] Police (garde.py)...",
                 "  ✓ Garde Journal     [OK]","  ✓ Garde Identité    [OK]",
                 "  ✓ Garde Robots.txt  [OK]","  ✓ Garde Cadence     [OK]","",
                 "[████████████████████] Guards découverts..."]
        for n, m in self.guards.items():
            lines.append(f"  ✓ {n} [{getattr(m,'TYPE','?')}]")
        lines += ["","✅ MOTEUR OPÉRATIONNEL","","   Cliquez pour continuer..."]
        def anim(i=0):
            if i < len(lines):
                bt.insert(tk.END, lines[i]+"\n"); bt.see(tk.END)
                self.root.after(70, lambda: anim(i+1))
            else: self.root.after(1200, bw.destroy)
        bt.bind("<Button-1>", lambda e: bw.destroy())
        bt.bind("<Key>", lambda e: bw.destroy()); bt.focus_set(); anim()

    # ---------- UI ----------
    def _setup_ui(self):
        menubar = tk.Menu(self.root)
        menubar.add_command(label="⚙️ Gestion", command=self.show_gestion)
        menubar.add_command(label="❌ Quitter", command=self._on_close)
        self.root.config(menu=menubar)

        # Barre de boutons (remplie par guard_boutons.py)
        self.toolbar_frame = tk.Frame(self.root, bg='#16213e', height=50)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5,0))

        pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg='#1e1e1e', sashrelief=tk.RAISED)
        pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # sidebar : guards groupés (SAISIE inclus)
        self.sidebar = ttk.Frame(pane, width=250); pane.add(self.sidebar)
        self.sidebar.pack_propagate(False)
        for tag, titre in [("saisie","📝 SAISIE"), ("auto","⚙️ GUARDS AUTO"), ("lien","🔗 GUARDS LIEN")]:
            ttk.Label(self.sidebar, text=titre, font=("Consolas",11,"bold")).pack(pady=(12,2))
            for n, m in self.guards.items():
                if getattr(m,"TYPE","") == tag:
                    ttk.Button(self.sidebar, text=n,
                               command=lambda mm=m: self._scan_guard(mm)).pack(fill=tk.X, padx=8, pady=2)
        ttk.Button(self.sidebar, text="🚀 TOUT SCANNER",
                   command=self._scan_tout).pack(fill=tk.X, padx=8, pady=15)

        # console
        nb = ttk.Notebook(pane); pane.add(nb)
        fc = ttk.Frame(nb); nb.add(fc, text='🧠 CONSOLE')
        self.console = scrolledtext.ScrolledText(fc, wrap=tk.WORD, font=('Consolas',11),
                                                 bg='#2d2d2d', fg='#ffffff')
        self.console.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._print(f"Moteur prêt. {len(self.guards)} guards découverts.\n"
                    "Commandes : help, scan, guards, rapport, cherche <termes>\n")
        self.console.configure(state='disabled')
        iframe = ttk.Frame(fc); iframe.pack(fill=tk.X, padx=8, pady=(0,8))
        ttk.Label(iframe, text=">>> ", foreground="lightgreen").pack(side=tk.LEFT)
        self.user_input = tk.Text(iframe, height=1, font=('Consolas',11),
                                  bg='#333333', fg='white', insertbackground='white')
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_input.bind("<Return>", self._handle_input)

        self._injecter_barre_boutons()

        self.heartbeat = tk.Label(self.root, text="🫀 Cœur actif", bg='#16213e',
                                  fg='#00ffcc', font=("Consolas",11,"bold"))
        self.heartbeat.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0,5))
        ttk.Label(self.root, text='✅ Moteur Family Trace', relief=tk.SUNKEN,
                  anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)

    def _injecter_barre_boutons(self):
        for n, m in self.guards.items():
            if getattr(m, "TYPE", "") == "ui" and hasattr(m, "inject_buttons"):
                try: m.inject_buttons(self)
                except Exception as e: print(f"⚠️ injection boutons {n} : {e}")

    def _heartbeat(self):
        if self._closing: return
        self._heart = (self._heart+1) % 3
        ic = ["💗","","🫁"][self._heart]
        self.heartbeat.config(text=f"🫀 {ic} {datetime.now():%H:%M:%S}")
        self.root.after(3000, self._heartbeat)

    def _print(self, txt):
        self.console.configure(state='normal')
        self.console.insert(tk.END, txt+"\n"); self.console.see(tk.END)
        self.console.configure(state='disabled')

    def _handle_input(self, event=None):
        txt = self.user_input.get("1.0","end-1c").strip()
        if not txt: return "break"
        self._print(f"\n>>> {txt}")
        self.user_input.delete("1.0", tk.END)
        if txt == "help":
            self._print("Commandes : help, scan, guards, rapport, cherche <termes>")
        elif txt == "scan": self._scan_tout()
        elif txt == "guards":
            self._print("\n".join(f"• {n} [{getattr(m,'TYPE','?')}]" for n,m in self.guards.items()))
        elif txt == "rapport": self._open_rapport()
        elif txt.startswith("cherche "): self._cherche(txt[8:].strip())
        else: self._print("❓ Tapez 'help'.")
        return "break"

    # ---------- recherche manuelle ----------
    def _cherche(self, q):
        self._print(f"🔎 Recherche manuelle : {q}")
        threading.Thread(target=self._thread_cherche, args=(q,), daemon=True).start()

    def _thread_cherche(self, q):
        r = self.portier.get("https://gallica.bnf.fr/services/engine/search/sru",
                             params={"version":"1.2","operation":"searchRetrieve",
                                     "query": q, "startRecord":1, "maximumRecords":10})
        if r:
            titres = re.findall(r"<dc:title>(.*?)</dc:title>", r.text, re.S)
            for t in titres[:8]:
                self._emit(f"   [gallica] {re.sub(r'<.*?>','',t).strip()}")
            if not titres: self._emit("   [gallica] 0 résultat")
        qq = quote(q)
        webbrowser.open(f"https://archive.org/search?query={qq}")
        webbrowser.open(f"https://www.delpher.nl/nl/kranten/results?query={qq}")
        self._emit("   🌐 archive.org + delpher ouverts dans le navigateur")

    # ---------- scans ----------
    def _emit(self, t):
        self.results.append(t)
        self.root.after(0, lambda x=t: self._print(x))

    def _scan_tout(self):
        threading.Thread(target=self._thread_tout, daemon=True).start()

    def _thread_tout(self):
        for c in self.config.get("cibles", []):
            self._emit(f"\n▶ CIBLE {c.get('prenom')} {c.get('nom')} [{c.get('front')}]")
            for n, m in self.guards.items():
                if getattr(m, "TYPE", "") == "ui": continue
                fronts = getattr(m, "FRONTS", None)
                if fronts and c.get("front") not in fronts: continue
                if not hasattr(m, "run"): continue
                try: m.run(c, self.ctx, self._emit)
                except Exception as e: self._emit(f"   ❌ [{n}] {e}")
        self._ecrire_rapport()
        self._emit("\n✅ Scan terminé — RAPPORT.md généré")

    def _scan_guard(self, mod):
        if getattr(mod, "UI", False):
            self.root.after(0, lambda m=mod: m.open_ui(self.root, self.ctx))
            return
        threading.Thread(target=self._thread_guard, args=(mod,), daemon=True).start()

    def _thread_guard(self, mod):
        for c in self.config.get("cibles", []):
            fronts = getattr(mod, "FRONTS", None)
            if fronts and c.get("front") not in fronts: continue
            self._emit(f"\n▶ {c.get('prenom')} {c.get('nom')}")
            if not hasattr(mod, "run"): continue
            try: mod.run(c, self.ctx, self._emit)
            except Exception as e: self._emit(f"   ❌ {e}")

    def _ecrire_rapport(self):
        (RESULTS/"RAPPORT.md").write_text("# RAPPORT KERBEROS FAMILY TRACE\n"
            f"Généré le {datetime.now():%d/%m/%Y %H:%M}\n\n"+"\n".join(self.results),
            encoding="utf-8")

    def _open_rapport(self):
        f = RESULTS/"RAPPORT.md"
        if f.exists(): webbrowser.open(f.as_uri()); self._print("📄 RAPPORT.md ouvert")
        else: self._print("⚠️ Aucun rapport. Lancez 'scan'.")

    # ---------- panneau gestion ----------
    def show_gestion(self):
        if self._gestion_window and self._gestion_window.winfo_exists():
            self._gestion_window.lift(); return
        win = tk.Toplevel(self.root); win.title("⚙️ Gestion")
        win.geometry("900x650"); win.configure(bg='#1a1a2e')
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_gestion(win))
        self._gestion_window = win
        tk.Label(win, text="🛡️ KERBEROS FAMILY TRACE — Panneau", bg='#16213e', fg='#00ffcc',
                 font=("Consolas",16,"bold")).pack(pady=12, fill=tk.X)
        nb = ttk.Notebook(win); nb.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        self._tab_cibles(nb); self._tab_guards(nb); self._tab_rapports(nb)
        self._tab_logs(nb); self._tab_params(nb)

    def _close_gestion(self, win):
        self._gestion_window = None
        try: win.destroy()
        except Exception: pass

    def _tab_cibles(self, nb):
        tab = ttk.Frame(nb); nb.add(tab, text=' 🔍 Cibles ')
        form = tk.LabelFrame(tab, text=" ➕ Ajouter une cible ", bg='#1e1e2e', fg='#00ffcc',
                             font=("Consolas",11,"bold"))
        form.pack(fill=tk.X, padx=10, pady=10)
        self._entry_vars = {}
        champs = [("nom","Nom :"), ("prenom","Prénom :"), ("naissance","Année :"),
                  ("lieu","Lieu :"), ("front","Front :")]
        for i, (cle, label) in enumerate(champs):
            tk.Label(form, text=label, bg='#1e1e2e', fg='#bb86fc',
                     font=("Consolas",10,"bold")).grid(row=i, column=0, sticky="w", padx=8, pady=4)
            if cle == "front":
                var = tk.StringVar(value="France")
                ttk.Combobox(form, textvariable=var, width=20,
                             values=["France","Italie","Mer","Belgique","Autre"]
                             ).grid(row=i, column=1, padx=8, pady=4)
            else:
                var = tk.StringVar()
                tk.Entry(form, textvariable=var, width=22, bg='#333333', fg='white',
                         insertbackground='white').grid(row=i, column=1, padx=8, pady=4)
            self._entry_vars[cle] = var
        tk.Button(form, text="➕ AJOUTER", bg='#2d7b5a', fg='white',
                  font=("Consolas",11,"bold"),
                  command=self._ajouter_cible).grid(row=len(champs), column=0, columnspan=2, pady=10)
        self._cibles_frame = tk.LabelFrame(tab, text=" 🎯 Cibles du dossier ", bg='#1e1e2e',
                                           fg='#00ffcc', font=("Consolas",11,"bold"))
        self._cibles_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._rafraichir_liste_cibles()

    def _rafraichir_liste_cibles(self):
        for w in self._cibles_frame.winfo_children(): w.destroy()
        for i, c in enumerate(self.config.get("cibles", [])):
            row = tk.Frame(self._cibles_frame, bg='#161a2e', relief=tk.RIDGE, bd=1)
            row.pack(fill=tk.X, padx=8, pady=4)
            tk.Label(row, text=f"{c.get('prenom','')} {c.get('nom','')} "
                               f"({c.get('naissance','?')}) [{c.get('front','?')}] {c.get('lieu','')}",
                     bg='#161a2e', fg='white', font=("Consolas",10)).pack(side=tk.LEFT, padx=8, pady=6)
            tk.Button(row, text="🗑", bg='#7b2d2d', fg='white', width=3,
                      command=lambda idx=i: self._supprimer_cible(idx)).pack(side=tk.RIGHT, padx=8)

    def _ajouter_cible(self):
        v = self._entry_vars
        nom, prenom = v["nom"].get().strip(), v["prenom"].get().strip()
        if not nom and not prenom:
            messagebox.showwarning("Cible", "Il faut au moins un nom ou un prénom."); return
        try: naissance = int(v["naissance"].get().strip() or 0) or None
        except ValueError: naissance = None
        cible = {"nom": nom.upper(), "prenom": prenom, "naissance": naissance,
                 "lieu": v["lieu"].get().strip(), "front": v["front"].get()}
        self.config.setdefault("cibles", []).append(cible)
        self._sauver_config()
        for k, var in v.items():
            if k != "front": var.set("")
        self._rafraichir_liste_cibles()
        self._print(f"➕ Cible ajoutée : {cible['prenom']} {cible['nom']} [{cible['front']}]")

    def _supprimer_cible(self, idx):
        cs = self.config.get("cibles", [])
        if 0 <= idx < len(cs):
            c = cs.pop(idx)
            self._sauver_config(); self._rafraichir_liste_cibles()
            self._print(f"🗑 Cible supprimée : {c.get('prenom')} {c.get('nom')}")

    def _tab_guards(self, nb):
        tab = ttk.Frame(nb); nb.add(tab, text=' 🛡️ Guards ')
        fr = tk.LabelFrame(tab, text=" 🛡️ Guards découverts ", bg='#1e1e2e', fg='#00ffcc',
                           font=("Consolas",11,"bold"))
        fr.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for n, m in self.guards.items():
            row = tk.Frame(fr, bg='#161a2e', relief=tk.RIDGE, bd=1)
            row.pack(fill=tk.X, padx=8, pady=4)
            tk.Label(row, text=f"{'⚙️' if getattr(m,'TYPE','')=='auto' else '🔗'} {n}",
                     bg='#161a2e', fg='#4CAF50', font=("Consolas",11,"bold")).pack(side=tk.LEFT, padx=8, pady=6)
            tk.Label(row, text=getattr(m,"DESCRIPTION",""), bg='#161a2e', fg='#a0a0c0',
                     font=("Consolas",9)).pack(side=tk.LEFT, padx=8)

    def _tab_rapports(self, nb):
        tab = ttk.Frame(nb); nb.add(tab, text=' 📊 Rapports ')
        fr = tk.LabelFrame(tab, text=" 📄 Résultats ", bg='#1e1e2e', fg='#00ffcc',
                           font=("Consolas",11,"bold"))
        fr.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Button(fr, text="🚀 TOUT SCANNER", bg='#2d7b5a', fg='white',
                  font=("Consolas",12,"bold"), command=self._scan_tout).pack(pady=15)
        tk.Button(fr, text="📂 Ouvrir RAPPORT.md", bg='#2d5a7b', fg='white',
                  command=self._open_rapport).pack(pady=5)

    def _tab_logs(self, nb):
        tab = ttk.Frame(nb); nb.add(tab, text=' 📜 Logs ')
        fr = tk.LabelFrame(tab, text=" 📄 Journaux ", bg='#1e1e2e', fg='#00ffcc',
                           font=("Consolas",11,"bold"))
        fr.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        logs = scrolledtext.ScrolledText(fr, height=20, font=("Consolas",9),
                                         bg='#0a0a0a', fg='#00ff00')
        logs.pack(fill=tk.BOTH, expand=True)
        lf = RESULTS/"kerberos.log"
        if lf.exists():
            try:
                for line in lf.read_text(encoding="utf-8").splitlines()[-60:]:
                    logs.insert(tk.END, line+"\n")
            except Exception: pass
        logs.configure(state='disabled')

    def _tab_params(self, nb):
        tab = ttk.Frame(nb); nb.add(tab, text=' ⚙️ Params ')
        fr = tk.LabelFrame(tab, text=" 🧭 Paramètres de recherche ", bg='#1e1e2e',
                           fg='#00ffcc', font=("Consolas",11,"bold"))
        fr.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(fr, text="Bateau :", bg='#1e1e2e', fg='#bb86fc',
                 font=("Consolas",10,"bold")).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self._var_bateau = tk.StringVar(value=self.config.get("bateau",""))
        tk.Entry(fr, textvariable=self._var_bateau, width=30, bg='#333333', fg='white',
                 insertbackground='white').grid(row=0, column=1, padx=8, pady=4)
        tk.Label(fr, text="Mots-clés (virgules) :", bg='#1e1e2e', fg='#bb86fc',
                 font=("Consolas",10,"bold")).grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self._var_termes = tk.StringVar(value=", ".join(self.config.get("termes_extra",[])))
        tk.Entry(fr, textvariable=self._var_termes, width=30, bg='#333333', fg='white',
                 insertbackground='white').grid(row=1, column=1, padx=8, pady=4)
        tk.Button(fr, text="💾 Enregistrer", bg='#2d7b5a', fg='white',
                  command=self._sauver_params).grid(row=2, column=0, columnspan=2, pady=10)

    def _sauver_params(self):
        self.config["bateau"] = self._var_bateau.get().strip()
        self.config["termes_extra"] = [t.strip() for t in self._var_termes.get().split(",") if t.strip()]
        self._sauver_config()
        self._print("💾 Paramètres enregistrés")

    def _on_close(self):
        self._closing = True
        if self._gestion_window:
            try: self._gestion_window.destroy()
            except Exception: pass
        try: self.root.quit(); self.root.destroy()
        except Exception: pass

if __name__ == '__main__':
    FamilyTraceApp()