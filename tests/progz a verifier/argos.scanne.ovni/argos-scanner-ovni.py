#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👁️ ARGOS ORBITAL v5.0 — ERGONOMIQUE (une fenêtre, des onglets, une barre)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3
- Barre de contrôle en haut (Redécouvrir / Rapport / Tree / reports/)
- Notebook central : les organes s'intègrent en ONGLETS via build_tab()
- Sidebar : 1 bouton = 1 organe intégré ; 🗔 = fenêtre séparée (subprocess)
- Console + 🫀 cœur + 🔐 ADN + 🧬 thymus conservés
- Module sans build_tab -> subprocess (fenêtre propre, jamais de thread Tk)
"""
import sys
import ast
import json
import time
import shutil
import hashlib
import logging
import subprocess
import threading
import traceback
import importlib.util
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


def _excepthook(t, v, tb):
    print("❌ ERREUR CRITIQUE:\n" + "".join(traceback.format_exception(t, v, tb)))
    input("Appuyez sur Entrée pour fermer...")


sys.excepthook = _excepthook

try:
    import psutil
    HAS_PSUTIL = True
except Exception:
    HAS_PSUTIL = False

ARGOS_ROOT = Path(__file__).resolve().parent
LYMPH = ARGOS_ROOT / "lymph_argos"; PLASMA = LYMPH / "plasma"
MODULES_DIR = ARGOS_ROOT / "modules"; REPORTS_DIR = ARGOS_ROOT / "reports"
IMG_DIR = ARGOS_ROOT / "img"; CIBLES_DIR = IMG_DIR / "cibles"
EXPORTS_DIR = ARGOS_ROOT / "exports"; LOGS_DIR = ARGOS_ROOT / "logs"
LOG_FILE = LOGS_DIR / "argos.log"; GENOME = LYMPH / "genome_argos.json"
MANIFEST = ARGOS_ROOT / "argos_manifest.json"
DIRS = {MODULES_DIR: "Organes (onglets ou fenêtres)", REPORTS_DIR: "Rapports + tree",
        IMG_DIR: "Images auditées", CIBLES_DIR: "Cibles confirmées",
        EXPORTS_DIR: "Sorties des organes", LOGS_DIR: "Journal",
        LYMPH: "Biologie", PLASMA: "Sauvegardes"}
for _d in DIRS:
    _d.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")])
logger = logging.getLogger("Argos")

_CLOSING = False
_HEART_LOCK = threading.Lock()


def _my_dna():
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except Exception:
        return "0" * 64


def _thymus_cycle():
    vital = [Path(__file__).resolve(), MANIFEST,
             ARGOS_ROOT / "doctrine.txt", ARGOS_ROOT / "war_doctrine.txt"]
    saved, healed = 0, 0
    for f in vital:
        plasma = PLASMA / f.name
        try:
            if f.exists():
                if not plasma.exists() or plasma.read_bytes() != f.read_bytes():
                    plasma.write_bytes(f.read_bytes())
                    saved += 1
            elif plasma.exists():
                f.write_bytes(plasma.read_bytes())
                healed += 1
        except Exception:
            pass
    return f"{saved} sauvegarde(s), {healed} régénération(s)"


def _dna_pulse():
    if _CLOSING:
        return
    try:
        cur = _my_dna()
        g = json.loads(GENOME.read_text(encoding="utf-8")) if GENOME.exists() else {}
        if g.get("argos_dna") != cur:
            g["argos_dna"] = cur
            g["last_pulse"] = time.time()
            GENOME.write_text(json.dumps(g, indent=2), encoding="utf-8")
    except Exception:
        pass
    threading.Timer(60.0, _dna_pulse).start()


def _safe(app, fn):
    try:
        if app is not None and app.root.winfo_exists():
            app.root.after(0, fn)
    except Exception:
        pass


def _start_heart(app):
    def systole():
        if _CLOSING:
            return
        with _HEART_LOCK:
            cpu = psutil.cpu_percent(interval=None) if HAS_PSUTIL else 0.0
            _safe(app, lambda: app.update_heartbeat(f"💗 SYSTOLE • CPU {cpu:.0f}%"))
        threading.Timer(3.0, diastole).start()

    def diastole():
        if _CLOSING:
            return
        with _HEART_LOCK:
            ram = psutil.virtual_memory().percent if HAS_PSUTIL else 0.0
            _safe(app, lambda: app.update_heartbeat(f"🫀 DIASTOLE • RAM {ram:.0f}%"))
        threading.Timer(4.0, pause).start()

    def pause():
        if _CLOSING:
            return
        with _HEART_LOCK:
            _safe(app, lambda: app.update_heartbeat("🫁 PAUSE • respiration orbitale…"))
        threading.Timer(3.0, systole).start()

    threading.Timer(2.0, systole).start()


def _load_manifest(discovered):
    try:
        if MANIFEST.exists():
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        pass
    m = {"version": "5.0", "active_modules": [p.name for p in discovered]}
    try:
        MANIFEST.write_text(json.dumps(m, indent=2), encoding="utf-8")
    except Exception:
        pass
    return m


def build_tree():
    lines = ["ARGOS_ORBITAL/"]
    items = list(DIRS.items())
    for i, (d, desc) in enumerate(items):
        branch = "└──" if i == len(items) - 1 else "├──"
        n = len([p for p in d.glob("*") if p.is_file()]) if d.exists() else 0
        lines.append(f"{branch} {d.name}/ ({n} fichiers) — {desc}")
    return "\n".join(lines)


class ArgosEngine:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("👁️ ARGOS ORBITAL v5.0 — ERGONOMIQUE")
        self.root.geometry("1150x800")
        self.root.configure(bg=self.BG)
        self.embedded = {}
        self._build()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._chat("👁️ ARGOS v5.0 — une fenêtre, des onglets, une barre de contrôle")
        self._chat("🧬 Thymus: " + _thymus_cycle())
        self._chat("Clique un organe = onglet intégré • 🗔 = fenêtre séparée")
        _start_heart(self)
        _dna_pulse()
        self.root.mainloop()

    # --- barre de contrôle + layout ---
    def _build(self):
        bar = tk.Frame(self.root, bg=self.BG2)
        bar.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(bar, text="👁️ ARGOS v5.0", bg=self.BG2, fg=self.CY,
                 font=("Consolas", 13, "bold")).pack(side=tk.LEFT, padx=8)
        tk.Button(bar, text="🔄 Redécouvrir", bg=self.BTN, fg=self.WH,
                  command=self.load_modules).pack(side=tk.LEFT, padx=2)
        tk.Button(bar, text="📊 Rapport", bg=self.BTN, fg=self.WH,
                  command=self._report).pack(side=tk.LEFT, padx=2)
        tk.Button(bar, text="🌳 Tree", bg=self.BTN, fg=self.WH,
                  command=self._tree).pack(side=tk.LEFT, padx=2)
        tk.Button(bar, text="📂 reports/", bg=self.BTN, fg=self.WH,
                  command=self._open_reports).pack(side=tk.LEFT, padx=2)
        self.tabs_label = tk.Label(bar, text="onglets: 0", bg=self.BG2, fg=self.OR,
                                   font=("Consolas", 9))
        self.tabs_label.pack(side=tk.RIGHT, padx=8)

        pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.BG, sashrelief=tk.RAISED)
        pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        side = tk.Frame(pane, width=230, bg=self.BG2)
        pane.add(side)
        side.pack_propagate(False)
        tk.Label(side, text="👁️ ORGANES", bg=self.BG2, fg=self.OR,
                 font=("Consolas", 11, "bold")).pack(pady=8)
        self.mods_frame = tk.Frame(side, bg=self.BG2)
        self.mods_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        self.load_modules()

        right = tk.Frame(pane, bg=self.BG)
        pane.add(right)
        self.nb = ttk.Notebook(right)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        home = ttk.Frame(self.nb)
        self.nb.add(home, text=' 🏠 ACCUEIL ')
        tk.Label(home, text="👁️ ARGOS ORBITAL v5.0\n\nClique un organe dans la sidebar :\nil s'ouvre EN ONGLET ici.\n\n🗔 = fenêtre séparée si tu préfères.",
                 bg=self.BG, fg=self.CY, font=("Consolas", 12), justify=tk.CENTER).pack(expand=True)

        cf = tk.Frame(right, bg=self.BG)
        cf.pack(fill=tk.X, padx=4, pady=(0, 4))
        tk.Label(cf, text=">>>", bg=self.BG, fg='#7CFC00', font=("Consolas", 11)).pack(side=tk.LEFT)
        self.user_input = tk.Text(cf, height=1, bg='#20262c', fg=self.WH,
                                  insertbackground=self.WH, font=("Consolas", 11))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.user_input.bind("<Return>", self._handle_input)
        self.chat = scrolledtext.ScrolledText(right, height=5, bg=self.BG2, fg='#4CAF50',
                                              font=('Consolas', 10), state='disabled')
        self.chat.pack(fill=tk.X, padx=4, pady=(0, 4))

        self.status = tk.Label(self.root, text="⏳ Prêt", bg=self.BG, fg=self.OR, font=("Consolas", 10))
        self.status.pack(pady=2)
        self.heartbeat_label = tk.Label(self.root, text="🫀 Cœur orbital", bg='#16213e', fg=self.CY,
                                        font=("Consolas", 11, "bold"))
        self.heartbeat_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

    # --- sidebar ---
    def load_modules(self):
        for w in self.mods_frame.winfo_children():
            w.destroy()
        disc = sorted(MODULES_DIR.glob("argos_*.py"))
        man = _load_manifest(disc)
        shown = [p for p in disc if p.name in man.get("active_modules", [])] or disc
        if not shown:
            tk.Label(self.mods_frame, text="aucun organe", bg=self.BG2,
                     fg='#ff5252', font=("Consolas", 9)).pack(pady=10)
            return
        for p in shown:
            f = tk.Frame(self.mods_frame, bg=self.BG2)
            f.pack(fill=tk.X, pady=2)
            tk.Button(f, text=p.stem.replace("argos_", "👁️ ").replace("_", " ").title(),
                      bg=self.BTN, fg=self.WH, font=("Consolas", 9),
                      command=lambda pp=p: self.embed_module(pp)).pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Button(f, text="🗔", width=3, bg=self.BG2, fg=self.CY,
                      command=lambda pp=p: self.window_module(pp)).pack(side=tk.RIGHT, padx=(3, 0))

    # --- activation des organes ---
    def embed_module(self, path):
        name = path.stem
        if name in self.embedded:
            self.nb.select(self.embedded[name])
            return
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:
            self._chat(f"❌ {path.name}: {e}")
            return
        if hasattr(mod, "build_tab"):
            t = ttk.Frame(self.nb)
            self.nb.add(t, text=f' {getattr(mod, "TAB_ICON", "👁️")} {getattr(mod, "TAB_NAME", name)} ')
            try:
                mod.build_tab(t, self)
                self.embedded[name] = t
                self.nb.select(t)
                self.tabs_label.config(text=f"onglets: {len(self.embedded)}")
                self._chat(f"✅ {path.name} intégré en onglet")
            except Exception as e:
                self._chat(f"❌ build_tab {path.name}: {e}")
        else:
            self._chat(f"⚠️ {path.name} sans build_tab -> 🗔 fenêtre")
            self.window_module(path)

    def window_module(self, path):
        try:
            subprocess.Popen([sys.executable, str(path)])
            self._chat(f"🗔 {path.name} en fenêtre séparée")
        except Exception as e:
            self._chat(f"❌ {path.name}: {e}")

    # --- console & barre ---
    def _chat(self, msg):
        try:
            self.chat.configure(state='normal')
            self.chat.insert(tk.END, msg + "\n")
            n = self.chat.get("1.0", tk.END).count('\n')
            if n > 60:
                self.chat.delete("1.0", f"{n - 60}.0")
            self.chat.see(tk.END)
            self.chat.configure(state='disabled')
        except Exception:
            pass

    def _handle_input(self, event=None):
        text = self.user_input.get("1.0", "end-1c").strip()
        if not text:
            return "break"
        self.user_input.delete("1.0", tk.END)
        self._chat(f">>> {text}")
        c = text.lower()
        if c == "help":
            self._chat("help, modules, tabs, report, tree, stats, dna, quit")
        elif c == "modules":
            self._chat("👁️ " + ", ".join(p.name for p in sorted(MODULES_DIR.glob("argos_*.py"))) or "aucun")
        elif c == "tabs":
            self._chat("🗂️ " + ", ".join(self.embedded.keys()) or "aucun onglet")
        elif c == "report":
            self._report()
        elif c == "tree":
            self._tree()
        elif c == "stats":
            cpu = psutil.cpu_percent(interval=None) if HAS_PSUTIL else 0.0
            ram = psutil.virtual_memory().percent if HAS_PSUTIL else 0.0
            self._chat(f"📈 CPU {cpu:.0f}% • RAM {ram:.0f}%")
        elif c == "dna":
            self._chat(f"🔐 {_my_dna()}")
        elif c == "quit":
            self._on_close()
        else:
            self._chat("❓ inconnu — tape 'help'")
        return "break"

    def _report(self):
        try:
            now = datetime.now()
            path = REPORTS_DIR / f"argos_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
            path.write_text(f"<html><body style='background:#0a0f14;color:#00ffcc;font-family:monospace'>"
                            f"<h1>👁️ ARGOS v5.0</h1><pre>ADN: {_my_dna()}\n{build_tree()}</pre>"
                            f"</body></html>", encoding="utf-8")
            self._chat(f"📊 Rapport: {path.name}")
        except Exception as e:
            self._chat(f"❌ {e}")

    def _tree(self):
        self._chat(build_tree())

    def _open_reports(self):
        try:
            import os
            os.startfile(REPORTS_DIR)
        except Exception as e:
            self._chat(f"⚠️ {e}")

    def update_heartbeat(self, m):
        try:
            if self.root.winfo_exists() and not _CLOSING:
                self.heartbeat_label.config(text=f"🫀 {m}")
        except Exception:
            pass

    def _on_close(self):
        global _CLOSING
        _CLOSING = True
        logger.info("🛑 ARGOS fermé proprement")
        self.root.destroy()


def run():
    ArgosEngine()
    return "✅ ARGOS v5.0 fermé"


def main():
    try:
        ArgosEngine()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()