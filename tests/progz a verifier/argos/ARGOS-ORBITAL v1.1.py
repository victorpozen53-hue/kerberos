#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👁️ ARGOS ORBITAL v1.1 — CLÉ EN MAIN (système d'observation indépendant)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3
Jumeau indépendant de Kerberos : il observe la Terre, ne garde rien.
🆕 v1.1 CLÉ EN MAIN :
- 🏗️ Construit toute sa maison au 1er lancement (dossiers + README)
- 📊 Rapports HTML (commande report + bouton)
- 🌳 Arborescence ├── en chat + export txt (commande tree)
- 📜 Journal de bord logs/argos.log
- 🧬 Thymus : plasma de la doctrine + régénération
- 🫀 Cœur lymphatique + 🔐 ADN +  boot Matrix
- 🧠 Cortex interne : modules/argos_*.py lancés en threads
Usage : python argos.py
"""
import sys
import time
import json
import hashlib
import shutil
import logging
import threading
import traceback
import importlib.util
import webbrowser
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext


def _excepthook(t, v, tb):
    print("❌ ERREUR CRITIQUE:\n" + "".join(traceback.format_exception(t, v, tb)))
    input("Appuyez sur Entrée pour fermer...")


sys.excepthook = _excepthook

try:
    import psutil
    HAS_PSUTIL = True
except Exception:
    HAS_PSUTIL = False

# ============================================================================
# === 🏗️ LA MAISON ARGOS (clé en main) =======================================
# ============================================================================
ARGOS_ROOT = Path(__file__).resolve().parent
LYMPH = ARGOS_ROOT / "lymph_argos"
PLASMA = LYMPH / "plasma"
MODULES_DIR = ARGOS_ROOT / "modules"
REPORTS_DIR = ARGOS_ROOT / "reports"
IMG_DIR = ARGOS_ROOT / "img"
CIBLES_DIR = IMG_DIR / "cibles"
SCENES_DIR = IMG_DIR / "scenes"
CROPS_DIR = ARGOS_ROOT / "crops"
DB_DIR = ARGOS_ROOT / "db"
EXPORTS_DIR = ARGOS_ROOT / "exports"
LOGS_DIR = ARGOS_ROOT / "logs"
LOG_FILE = LOGS_DIR / "argos.log"
GENOME = LYMPH / "genome_argos.json"
DOCTRINE = ARGOS_ROOT / "war_doctrine.txt"

DIRS = {
    MODULES_DIR: "Flotte de vision (argos_*.py) — le LiDAR, le RECON, le sonar…",
    REPORTS_DIR: "Rapports HTML + arborescence.txt générés par ARGOS",
    IMG_DIR: "Images auditées",
    CIBLES_DIR: "Cibles confirmées (SMART JPEG des modules)",
    SCENES_DIR: "Scènes auditées (copies de travail)",
    CROPS_DIR: "Crops bruts VUS DU CIEL — matière première de la base",
    DB_DIR: "Base de données construite (rotations ×8 du DB builder)",
    EXPORTS_DIR: "Sorties mp4 / csv / jpeg des modules",
    LOGS_DIR: "Journal de bord ARGOS",
    LYMPH: "Biologie : génome + plasma",
    PLASMA: "Sauvegardes immunitaires (doctrine, etc.)",
}
for _d in DIRS:
    _d.mkdir(parents=True, exist_ok=True)
for _d, _desc in DIRS.items():
    _rd = _d / "README.txt"
    if not _rd.exists():
        try:
            _rd.write_text(f"ARGOS ORBITAL — { _d.name }/\n{_desc}\n(GPLv3 — Victor Pozen)\n",
                           encoding="utf-8")
        except Exception:
            pass

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")])
logger = logging.getLogger("Argos")

_CLOSING = False
_HEART_LOCK = threading.Lock()

DEFAULT_DOCTRINE = """# KERBEROS WAR DOCTRINE — une règle par ligne : forme;label;couleur
# formes reconnues : triangle rectangle carre croix x rond ligne
# couleurs : jaune orange magenta blanc rouge rouge_sombre cyan vert  ou  B,G,R
triangle;CHASSEUR DELTA;orange
rectangle;CAMION;jaune
carre;TANK;magenta
croix;AVION COMMERCIAL;blanc
x;HELICO;cyan
rond;DOME/RADAR;rouge
ligne;PISTE/ROUTE;rouge_sombre
"""

COLOR_NAMES = {
    "jaune": (0, 255, 255), "orange": (0, 165, 255), "magenta": (255, 0, 255),
    "blanc": (255, 255, 255), "rouge": (0, 0, 255), "rouge_sombre": (80, 80, 255),
    "cyan": (255, 255, 0), "vert": (0, 255, 0),
}


# ============================================================================
# === 🔐 ADN + 🧬 THYMUS + 🫀 CŒUR ===========================================
# ============================================================================
def _my_dna():
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except Exception:
        return "0" * 64


def _thymus_cycle():
    try:
        if DOCTRINE.exists():
            shutil.copy2(DOCTRINE, PLASMA / "war_doctrine.plasma")
            return "💉 doctrine sauvegardée dans le plasma"
        backup = PLASMA / "war_doctrine.plasma"
        if backup.exists():
            shutil.copy2(backup, DOCTRINE)
            return "🩹 doctrine RÉGÉNÉRÉE depuis le plasma"
        DOCTRINE.write_text(DEFAULT_DOCTRINE, encoding="utf-8")
        return " doctrine créée par défaut"
    except Exception as e:
        return f"⚠️ thymus: {e}"


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


# ============================================================================
# === 📖 DOCTRINE ============================================================
# ============================================================================
def _parse_doctrine(text):
    rules = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(";")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            continue
        color = (80, 80, 255)
        if len(parts) >= 3 and parts[2]:
            c = parts[2]
            if c in COLOR_NAMES:
                color = COLOR_NAMES[c]
            elif "," in c:
                try:
                    b, g, r = [int(x) for x in c.split(",")]
                    color = (b, g, r)
                except Exception:
                    pass
        rules[parts[0].lower()] = (parts[1], color)
    return rules


def load_doctrine():
    if not DOCTRINE.exists():
        try:
            DOCTRINE.write_text(DEFAULT_DOCTRINE, encoding="utf-8")
        except Exception:
            pass
    try:
        text = DOCTRINE.read_text(encoding="utf-8")
    except Exception:
        text = DEFAULT_DOCTRINE
    return _parse_doctrine(text) or _parse_doctrine(DEFAULT_DOCTRINE)


# ============================================================================
# === 🌳 ARBORESCENCE + 📊 RAPPORT HTML ======================================
# ============================================================================
def build_tree():
    lines = ["👁️ ARGOS_ORBITAL/"]
    items = list(DIRS.items())
    for i, (d, desc) in enumerate(items):
        branch = "└──" if i == len(items) - 1 else "├──"
        n = len([p for p in d.glob("*") if p.is_file()]) if d.exists() else 0
        lines.append(f"{branch} {d.name}/ ({n} fichiers) — {desc}")
    return "\n".join(lines)


def generate_html_report(chat_cb):
    now = datetime.now()
    path = REPORTS_DIR / f"argos_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    css = ("body{background:#0a0f14;color:#e0e0e0;font-family:Consolas,monospace;margin:0;}"
           "header{background:#16213e;padding:20px 30px;border-bottom:2px solid #00ffcc;}"
           "h1{color:#00ffcc;margin:0;}h2{color:#ffb347;}"
           ".card{background:#141a20;margin:15px 30px;padding:15px 20px;border-left:3px solid #00ffcc;}"
           "table{border-collapse:collapse;width:100%;}td,th{padding:6px 10px;text-align:left;border-bottom:1px solid #223;}"
           "pre{color:#7fdbca;}footer{padding:15px 30px;color:#667;font-size:12px;}")
    cpu = psutil.cpu_percent(interval=None) if HAS_PSUTIL else 0.0
    ram = psutil.virtual_memory().percent if HAS_PSUTIL else 0.0
    doc = load_doctrine()
    mods = sorted(MODULES_DIR.glob("argos_*.py"))
    cibles = sorted(CIBLES_DIR.glob("*.*"))[-10:]
    try:
        log_tail = LOG_FILE.read_text(encoding="utf-8").splitlines()[-15:]
    except Exception:
        log_tail = []

    html = ["<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>",
            "<title>ARGOS ORBITAL — Rapport</title><style>" + css + "</style></head><body>",
            f"<header><h1>👁️ ARGOS ORBITAL v1.1 — RAPPORT</h1>",
            f"<div>Généré le {now.strftime('%d/%m/%Y à %H:%M:%S')}</div></header>",
            "<div class='card'><h2>🔐 Identité</h2>",
            f"<table><tr><td>ADN</td><td>{_my_dna()}</td></tr>",
            f"<tr><td>CPU</td><td>{cpu:.0f}%</td></tr><tr><td>RAM</td><td>{ram:.0f}%</td></tr>",
            f"<tr><td>Thymus</td><td>{_thymus_cycle()}</td></tr></table></div>",
            "<div class='card'><h2>📖 Doctrine de guerre</h2><table>",
            "<tr><th>Forme</th><th>Label</th></tr>"]
    for k, (label, _) in doc.items():
        html.append(f"<tr><td>{k}</td><td>{label}</td></tr>")
    html.append("</table></div>")
    html.append("<div class='card'><h2>🧠 Flotte de vision</h2><table>")
    if mods:
        for m in mods:
            html.append(f"<tr><td>{m.name}</td></tr>")
    else:
        html.append("<tr><td>aucun module argos_*.py</td></tr>")
    html.append("</table></div>")
    html.append("<div class='card'><h2>🎯 Dernières cibles</h2><table>")
    if cibles:
        for c in cibles:
            html.append(f"<tr><td>{c.name}</td></tr>")
    else:
        html.append("<tr><td>aucune cible pour l'instant</td></tr>")
    html.append("</table></div>")
    html.append("<div class='card'><h2>🌳 Maison</h2><pre>" + build_tree().replace("👁️ ", "") + "</pre></div>")
    html.append("<div class='card'><h2>📜 Journal (15 dernières lignes)</h2><pre>")
    html += [l.replace("<", "&lt;") for l in log_tail]
    html.append("</pre></div>")
    html.append("<footer>GPLv3 • Victor Pozen • ARGOS ORBITAL — jumeau indépendant de Kerberos</footer>")
    html.append("</body></html>")
    path.write_text("\n".join(html), encoding="utf-8")
    logger.info(f"📊 Rapport HTML généré: {path.name}")
    if chat_cb:
        chat_cb(f"📊 Rapport HTML: {path.name}")
    return path


# ============================================================================
# === 👁️ APPLICATION ========================================================
# ============================================================================
class ArgosApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("👁️ ARGOS ORBITAL v1.1 — Système d'Observation Indépendant")
        self.root.geometry("1100x720")
        self.root.configure(bg=self.BG)
        self._show_boot()
        self._build()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._chat("👁️ ARGOS ORBITAL v1.1 CLÉ EN MAIN — maison construite, README partout")
        self._chat(f"🔐 ADN: {_my_dna()[:16]}…")
        self._chat("🧬 Thymus: " + _thymus_cycle())
        self._chat("Tape 'help' pour les commandes.")
        logger.info("👁️ ARGOS v1.1 démarré")
        _start_heart(self)
        _dna_pulse()
        self.root.mainloop()

    def _show_boot(self):
        boot = tk.Toplevel(self.root)
        boot.title("ARGOS BOOT")
        boot.geometry("560x320")
        boot.configure(bg='#0a0a0a')
        boot.overrideredirect(True)
        boot.update_idletasks()
        boot.geometry(f"+{boot.winfo_screenwidth() // 2 - 280}+{boot.winfo_screenheight() // 2 - 160}")
        txt = tk.Text(boot, bg='#0a0a0a', fg='#ffb347', font=("Courier", 10), relief=tk.FLAT)
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        lines = [
            "╔══════════════════════════════════════════╗",
            "║   👁️ ARGOS ORBITAL v1.1 — BOOT CLÉ EN MAIN ║",
            "╚══════════════════════════════════════════╝", "",
            "[████████████████████] Maison/dossiers.... OK",
            "[████████████████████] README partout..... OK",
            "[████████████████████] Cœur lymphatique... OK",
            "[████████████████████] ADN + Thymus....... OK",
            "[████████████████████] Cortex/modules..... OK",
            "[████████████████████] Rapports HTML...... OK", "",
            "✅ ARGOS VOIT — clic pour ouvrir les yeux",
        ]

        def anim(i=0):
            if i < len(lines):
                txt.insert(tk.END, lines[i] + "\n")
                txt.see(tk.END)
                self.root.after(60, lambda: anim(i + 1))
            else:
                self.root.after(900, boot.destroy)

        txt.bind("<Button-1>", lambda e: boot.destroy())
        txt.focus_set()
        anim()

    def _build(self):
        pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.BG, sashrelief=tk.RAISED)
        pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        side = tk.Frame(pane, width=260, bg=self.BG2)
        pane.add(side)
        side.pack_propagate(False)
        tk.Label(side, text="👁️ MODULES DE VISION", bg=self.BG2, fg=self.OR,
                 font=("Consolas", 11, "bold")).pack(pady=8)
        self.mods_frame = tk.Frame(side, bg=self.BG2)
        self.mods_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        tk.Button(side, text="🔄 Redécouvrir", bg=self.BTN, fg=self.WH,
                  command=self._load_modules).pack(pady=2)
        tk.Button(side, text="📊 Rapport HTML", bg=self.BTN, fg=self.WH,
                  command=self._do_report).pack(pady=2, fill=tk.X, padx=10)
        tk.Button(side, text="🌳 Arborescence", bg=self.BTN, fg=self.WH,
                  command=self._do_tree).pack(pady=2, fill=tk.X, padx=10)
        tk.Button(side, text="📂 Ouvrir reports/", bg=self.BTN, fg=self.WH,
                  command=self._open_reports).pack(pady=2, fill=tk.X, padx=10)

        right = tk.Frame(pane, bg=self.BG)
        pane.add(right)
        self.chat = scrolledtext.ScrolledText(right, wrap=tk.WORD, bg=self.BG2,
                                              fg=self.WH, font=('Consolas', 11))
        self.chat.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat.configure(state='disabled')
        inf = tk.Frame(right, bg=self.BG)
        inf.pack(fill=tk.X, padx=5, pady=(0, 5))
        tk.Label(inf, text=">>>", bg=self.BG, fg='#7CFC00', font=("Consolas", 11)).pack(side=tk.LEFT)
        self.user_input = tk.Text(inf, height=1, bg='#20262c', fg=self.WH,
                                  insertbackground=self.WH, font=("Consolas", 11))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.user_input.bind("<Return>", self._handle_input)

        self.heartbeat_label = tk.Label(self.root, text="🫀 Cœur orbital — 💗 → 🫀 → ",
                                        bg='#16213e', fg=self.CY, font=("Consolas", 11, "bold"))
        self.heartbeat_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))
        self._load_modules()

    def _load_modules(self):
        for w in self.mods_frame.winfo_children():
            w.destroy()
        mods = sorted(MODULES_DIR.glob("argos_*.py"))
        if not mods:
            tk.Label(self.mods_frame, text="Aucun module argos_*.py\ndans ./modules/",
                     bg=self.BG2, fg='#ff5252', font=("Consolas", 9)).pack(pady=10)
            return
        for m in mods:
            tk.Button(self.mods_frame, text=m.stem.replace("argos_", "👁️ ").replace("_", " ").title(),
                      bg=self.BTN, fg=self.WH, font=("Consolas", 10),
                      command=lambda p=m: self._run_module(p)).pack(fill=tk.X, pady=2)

    def _run_module(self, path):
        self._chat(f"▶️ {path.name}…")

        def work():
            try:
                spec = importlib.util.spec_from_file_location(path.stem, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                fn = getattr(mod, "run", None) or getattr(mod, "main", None)
                out = f"✅ {path.name} terminé" if fn else f"⚠️ {path.name}: pas de run()/main()"
                if fn:
                    fn()
            except Exception as e:
                out = f"❌ {path.name}: {e}"
            self.root.after(0, lambda: self._chat(out))

        threading.Thread(target=work, daemon=True).start()

    def _do_report(self):
        def work():
            p = generate_html_report(self._chat)
            self.root.after(0, lambda: webbrowser.open(p.as_uri()))
        threading.Thread(target=work, daemon=True).start()

    def _do_tree(self):
        tree = build_tree()
        self._chat(tree)
        try:
            (REPORTS_DIR / "arborescence.txt").write_text(tree, encoding="utf-8")
            self._chat("🌳 Exporté dans reports/arborescence.txt")
        except Exception:
            pass

    def _open_reports(self):
        try:
            import os
            os.startfile(REPORTS_DIR)
        except Exception as e:
            self._chat(f"⚠️ ouverture: {e}")

    def _chat(self, text):
        try:
            self.chat.configure(state='normal')
            self.chat.insert(tk.END, text + "\n")
            self.chat.see(tk.END)
            self.chat.configure(state='disabled')
        except Exception:
            pass

    def update_heartbeat(self, message):
        try:
            if self.root.winfo_exists() and not _CLOSING:
                self.heartbeat_label.config(text=f"🫀 {message}")
        except Exception:
            pass

    def _handle_input(self, event=None):
        text = self.user_input.get("1.0", "end-1c").strip()
        if not text:
            return "break"
        self.user_input.delete("1.0", tk.END)
        self._chat(f">>> {text}")
        cmd = text.lower()
        if cmd == "help":
            self._chat("Commandes: help, report, tree, modules, reload, doctrine, dna, stats, quit")
        elif cmd == "report":
            self._do_report()
        elif cmd == "tree":
            self._do_tree()
        elif cmd == "modules":
            mods = [m.name for m in sorted(MODULES_DIR.glob("argos_*.py"))]
            self._chat("👁️ Modules: " + (", ".join(mods) if mods else "aucun"))
        elif cmd == "reload":
            self._load_modules()
            self._chat("🔄 Modules redécouverts")
        elif cmd == "doctrine":
            self._chat(f"📖 Doctrine: {len(load_doctrine())} règles actives")
        elif cmd == "dna":
            self._chat(f"🔐 ADN Argos: {_my_dna()}")
        elif cmd == "stats":
            cpu = psutil.cpu_percent(interval=None) if HAS_PSUTIL else 0.0
            ram = psutil.virtual_memory().percent if HAS_PSUTIL else 0.0
            self._chat(f"📈 CPU {cpu:.0f}% • RAM {ram:.0f}%")
        elif cmd == "quit":
            self._on_close()
        else:
            self._chat("❓ Inconnu. Tape 'help'.")
        return "break"

    def _on_close(self):
        global _CLOSING
        _CLOSING = True
        logger.info("🛑 ARGOS fermé proprement")
        self.root.destroy()


def run():
    LidarGuardApp = ArgosApp
    LidarGuardApp()
    return "✅ ARGOS fermé proprement"


def start_guard():
    print("👁️ [ARGOS] Système indépendant — GUI via run() ou python argos.py")
    return None


def stop_guard():
    global _CLOSING
    _CLOSING = True


def main():
    try:
        ArgosApp()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()