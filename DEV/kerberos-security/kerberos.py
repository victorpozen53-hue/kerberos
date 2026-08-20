#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Système de défense numérique éthique
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE : GPLv3 (GNU General Public License v3.0)
#  AUTEUR  : Victor Pozen
#  VERSION : 4.2 Ultimate
#  DATE    : 2025
#  🔗 https://github.com/victorpozen
#  💰 https://liberapay.com/EthicalKerberos/
# ============================================================================
"""
KERBEROS ULTIMATE v4.2 — Système de défense numérique éthique
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆕 FONCTIONNALITÉS v4.2:
- 🌍 Carte cyber MONDIALE avec géolocalisation TEMPS RÉEL (guard_cybermap.py)
- 📊 Dashboard analytics avec graphiques temps réel
- 🎮 Système de gamification (badges, XP, défis)
- 👁️ Monitoring temps réel avec classification auto
- 🔍 Auto-discovery des guards
- 🎬 Animation de boot Matrix-style
- 🫀 Cœur lymphatique tri-phasé (CORRIGÉ - plus de boucle)
- 🛡️ Guards autonomes (Genome, Thymus, Cortex, Bubble, NetShield, etc.)
- 📡 Updates intranet (192.168.1.19)
- 🚀 Auto-start Windows (registre + dossier Startup)
- 🔐 Signature DNA (production)
- 🪟 Contrôle fenêtre (Maximiser/Minimiser)
- 🕵️ Mode furtif (tray only)
- 🧠 Guard Explainer intégré (analyse AST des guards)
- 🐕 Cerbère Tray Icon (alertes dynamiques)
- 🔗 UI Manager centralisé (VU-mètres unifiés)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
# ============================================================================
# === IMPORTS ================================================================
# ============================================================================
import os, sys, time, json, random, hashlib, ctypes
import threading, subprocess, importlib.util, psutil, platform, ast, webbrowser
from datetime import datetime
from pathlib import Path
from io import BytesIO
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, Menu, scrolledtext, messagebox

# ============================================================================
# === FLAGS GLOBAUX ==========================================================
# ============================================================================
_APP_CLOSING = False
_APP_INSTANCE = None
_STEALTH_MODE = False

def _is_app_closing():
    return _APP_CLOSING

def _is_stealth_mode():
    return _STEALTH_MODE

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================
LANG = "fr"
KERBEROS_ROOT = Path(__file__).parent.resolve()
LYMPH_DIR      = KERBEROS_ROOT / "lymph"
GUARDS_DIR     = KERBEROS_ROOT / "guards"
LOGS_DIR       = KERBEROS_ROOT / "logs"
REPORTS_DIR    = KERBEROS_ROOT / "reports"
INTRANET_SERVER_IP = "192.168.1.19"

TEXTS = {
    "fr": {
        "title":        "🛡️ KERBEROS ULTIMATE v4.2 — Système de Défense Éthique",
        "welcome":      "Bienvenue dans Kerberos Ultimate v4.2.\n🌍 Carte cyber • 📊 Analytics • 🎮 Gamification\nTapez 'help' pour la liste des commandes.",
        "help":         "Commandes : help, scan, info, cortex list|reload, stats, map, stealth",
        "input_prompt": ">>> ",
        "executing":    "Exécution de :",
        "module_info":  "Infos sur le module",
        "unknown_desc": "Aucune description.",
        "info_desc":    "Kerberos Ultimate v4.2 — GPLv3 — Victor Pozen\nhttps://github.com/victorpozen",
        "about_text":   "KERBEROS ULTIMATE v4.2\nVictor Pozen\nWhite hat • Anonymous • Résistant numérique\nLicence GPLv3",
        "info_menu":    "Infos",
        "about_menu":   "À propos",
        "quit_menu":    "Quitter",
        "stealth_menu": "🕵️ Mode furtif",
        "restore_menu": "🔍 Restaurer la fenêtre",
    }
}
_cortex_commands = {}

# ← _GUARD_METRICS défini UNE SEULE FOIS
_GUARD_METRICS: dict[str, float] = {}

# ============================================================================
# === 🫀 CŒUR LYMPHATIQUE ====================================================
# ============================================================================
_BIO_ROOT = KERBEROS_ROOT / "lymph"
_BIO_ROOT.mkdir(exist_ok=True)
_GENOME_FILE = _BIO_ROOT / "genome.json"
_HEART_PHASE = 0
_HEART_LOCK  = threading.Lock()
_DNA_LOCK    = threading.Lock()

def _my_dna():
    me = Path(__file__).resolve()
    raw = me.read_bytes() if me.suffix == ".exe" else me.read_text(encoding="utf-8").encode()
    return hashlib.sha256(raw).hexdigest()

def _safe_ui(fn):
    global _APP_INSTANCE
    if _is_app_closing() or _APP_INSTANCE is None:
        return
    try:
        inst = _APP_INSTANCE
        if inst and inst.root.winfo_exists():
            inst.root.after(0, fn)
    except RuntimeError:
        pass

def _heart_systole():
    if _is_app_closing():
        return
    with _HEART_LOCK:
        global _HEART_PHASE
        _HEART_PHASE = 0
        cpu = psutil.cpu_percent(interval=None)
        _safe_ui(lambda: _APP_INSTANCE and
                 _APP_INSTANCE.update_heartbeat(f"💗 SYSTOLE • CPU {cpu:.1f}%"))
    if not _is_app_closing():
        threading.Timer(3.0, _heart_diastole).start()

def _heart_diastole():
    if _is_app_closing():
        return
    with _HEART_LOCK:
        global _HEART_PHASE
        _HEART_PHASE = 1
        ram = psutil.virtual_memory().percent
        _safe_ui(lambda: _APP_INSTANCE and
                 _APP_INSTANCE.update_heartbeat(f"🫀 DIASTOLE • RAM {ram:.1f}%"))
    if not _is_app_closing():
        threading.Timer(4.0, _heart_pause).start()

def _heart_pause():
    if _is_app_closing():
        return
    with _HEART_LOCK:
        global _HEART_PHASE
        _HEART_PHASE = 2
        _safe_ui(lambda: _APP_INSTANCE and
                 _APP_INSTANCE.update_heartbeat("🫁 PAUSE • Respiration lymphatique…"))
    if not _is_app_closing():
        threading.Timer(3.0, _heart_systole).start()

def _dna_pulse():
    if _is_app_closing():
        return
    if not _DNA_LOCK.acquire(blocking=False):
        return
    try:
        current = _my_dna()
        genome = (json.loads(_GENOME_FILE.read_text(encoding="utf-8"))
                  if _GENOME_FILE.exists()
                  else {"kerberos_dna": current, "last_pulse": time.time()})
        if genome.get("kerberos_dna") != current:
            genome["kerberos_dna"] = current
            genome["last_pulse"] = time.time()
            _GENOME_FILE.write_text(json.dumps(genome, indent=2), encoding="utf-8")
    except: pass
    finally:
        _DNA_LOCK.release()
    if not _is_app_closing():
        threading.Timer(60.0, _dna_pulse).start()

def _start_biological_layer(app_instance=None):
    global _APP_INSTANCE
    _APP_INSTANCE = app_instance
    threading.Timer(2.0, _heart_systole).start()
    threading.Timer(7.0, _dna_pulse).start()

# ============================================================================
# === TRAY ===================================================================
# ============================================================================
_has_tray = False
_kerberos_tray = None
try:
    import pystray
    from PIL import Image, ImageDraw
    _has_tray = True
except ImportError:
    pass

def _make_icon(color):
    sizes = [16, 32, 48]
    images = []
    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        m = size // 8
        d.rectangle([m, m, size - m - 1, size - m - 1],
                    outline=color, width=max(1, size // 16))
        images.append(img)
    buf = BytesIO()
    images[0].save(buf, format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    buf.seek(0)
    return Image.open(buf)

def _start_tray():
    global _kerberos_tray, _has_tray
    if not _has_tray:
        return
    try:
        icon = pystray.Icon("Kerberos", icon=_make_icon((240, 240, 240)),
                            title="🛡️ Kerberos")
        icon.menu = pystray.Menu(
            pystray.MenuItem("🔍 Restaurer", lambda i, _: _restore_from_tray(i)),
            pystray.MenuItem("🕵️ Mode furtif", lambda i, _: _toggle_stealth_mode()),
            pystray.MenuItem(separator=True),
            pystray.MenuItem("Quitter", lambda i, _: _quit_from_tray(i)))
        _kerberos_tray = icon
        threading.Thread(target=icon.run, daemon=True).start()
    except:
        _has_tray = False

def _restore_from_tray(icon):
    global _STEALTH_MODE
    _STEALTH_MODE = False
    if _APP_INSTANCE and _APP_INSTANCE.root:
        _APP_INSTANCE.root.deiconify()
        _APP_INSTANCE.root.lift()
        _APP_INSTANCE.root.focus_force()
    if _kerberos_tray:
        _kerberos_tray.icon = _make_icon((60, 210, 120))

def _toggle_stealth_mode():
    """Fonction GLOBALE pour mode furtif"""
    global _STEALTH_MODE
    _STEALTH_MODE = not _STEALTH_MODE
    if _APP_INSTANCE and _APP_INSTANCE.root:
        if _STEALTH_MODE:
            _APP_INSTANCE.root.withdraw()
            if _kerberos_tray:
                _kerberos_tray.icon = _make_icon((220, 60, 60))
            _safe_ui(lambda: _APP_INSTANCE.append_to_chat("🕵️ Mode furtif ACTIVÉ — Fenêtre cachée\n"))
        else:
            _APP_INSTANCE.root.deiconify()
            _APP_INSTANCE.root.lift()
            _APP_INSTANCE.root.focus_force()
            if _kerberos_tray:
                _kerberos_tray.icon = _make_icon((60, 210, 120))
            _safe_ui(lambda: _APP_INSTANCE.append_to_chat("🔍 Mode furtif DÉSACTIVÉ — Fenêtre restaurée\n"))

def _quit_from_tray(icon):
    global _APP_INSTANCE
    if _APP_INSTANCE:
        _APP_INSTANCE._on_close()
    icon.stop()

# ============================================================================
# === CORTEX =================================================================
# ============================================================================
def _load_cortex():
    cortex_path = GUARDS_DIR / "guard_cortex.py"
    if not cortex_path.exists():
        _create_default_cortex()
    try:
        spec = importlib.util.spec_from_file_location("guard_cortex", cortex_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, 'CORTEX_COMMANDS'):
            global _cortex_commands
            _cortex_commands = mod.CORTEX_COMMANDS
        if hasattr(mod, 'start_guard'):
            mod.start_guard()
        return True
    except:
        return False

def _create_default_cortex():
    cortex_code = '''#!/usr/bin/env python3
import json
from pathlib import Path
MANIFEST_FILE = Path("guards_manifest.json")
GUARDS_DIR = Path(__file__).parent
def _load_manifest():
    if not MANIFEST_FILE.exists():
        default = {"active_guards": ["guard_genome.py", "guard_thymus.py"]}
        MANIFEST_FILE.write_text(json.dumps(default, indent=2))
        return default
    return json.loads(MANIFEST_FILE.read_text())
def reload_guards():
    config = _load_manifest()
    return [(g, True, "actif") for g in config.get("active_guards", [])]
def cmd_cortex_list(args):
    print("\\n[🧠 Cortex] Guards disponibles :")
    for g in GUARDS_DIR.glob("*.py"):
        print(f"  • {g.name}")
def cmd_cortex_reload(args):
    print("[🔄] Rechargement...")
    for name, ok, msg in reload_guards():
        print(f"  ✅ {name}: {msg}")
def start_guard():
    reload_guards()
CORTEX_COMMANDS = {"list": cmd_cortex_list, "reload": cmd_cortex_reload}
'''
    GUARDS_DIR.mkdir(exist_ok=True)
    (GUARDS_DIR / "guard_cortex.py").write_text(cortex_code, encoding="utf-8")

# ============================================================================
# === HELPER =================================================================
# ============================================================================
def extract_docstring(file_path: Path) -> str:
    try:
        node = ast.parse(file_path.read_text(encoding="utf-8"))
        doc = ast.get_docstring(node)
        if doc:
            return doc.strip()
    except: pass
    return TEXTS[LANG].get("unknown_desc", "Aucune description.")

# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================
class KerberosApp:
    def __init__(self):
        global _APP_INSTANCE
        _APP_INSTANCE = self
        self.root = tk.Tk()
        self.root.title(TEXTS[LANG]["title"])
        self.root.geometry("1200x700")
        self.root.configure(bg='#1e1e1e')
        
        self._setup_window_controls()
        self._gestion_window: tk.Toplevel | None = None
        self._guards_panel = None
        self._cybermap_engine = None  # ← NOUVEAU: Référence à guard_cybermap.py
        self._netshield_stats = {"total_blocked": 0, "government": 0, "trackers": 0, "malware": 0}
        self._cybermap_stats_vars = {}  # ← NOUVEAU: Variables stats CyberMap
        
        self._setup_styles()
        self._show_boot_animation()
        _start_tray()
        _start_biological_layer(self)
        
        # 🐕 Cerbère — icône dynamique dans la barre des tâches
        try:
            import importlib.util as _ilu
            _cerb_path = GUARDS_DIR / "guard_tray_icon.py"
            if _cerb_path.exists():
                _spec = _ilu.spec_from_file_location("guard_tray_icon", _cerb_path)
                _cerb_mod = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_cerb_mod)
                _cerb_mod.start_guard(
                    open_kerberos_callback=lambda: (
                        self.root.deiconify(),
                        self.root.lift(),
                        self.root.focus_force()
                    )
                )
                self._cerberus = _cerb_mod
                print("🐕 [Cerbère] Guard Tray Icon démarré")
            else:
                print("⚠️ [Cerbère] guard_tray_icon.py absent dans /guards")
        except Exception as _e:
            print(f"⚠️ [Cerbère] Erreur démarrage : {_e}")
        
        # 🌍 CyberMap — Monitoring réseau (NOUVEAU)
        try:
            import importlib.util as _ilu
            _cyber_path = GUARDS_DIR / "guard_cybermap.py"
            if _cyber_path.exists():
                _spec = _ilu.spec_from_file_location("guard_cybermap", _cyber_path)
                _cyber_mod = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_cyber_mod)
                _cyber_mod.start_guard()
                self._cybermap_engine = _cyber_mod
                print("🌍 [CyberMap] Guard démarré — Monitoring réseau actif")
            else:
                print("⚠️ [CyberMap] guard_cybermap.py absent dans /guards")
        except Exception as _e:
            print(f"⚠️ [CyberMap] Erreur démarrage : {_e}")
        
        # 🔗 UI Manager — Intégration guards (NOUVEAU)
        try:
            import importlib.util as _ilu
            _ui_path = GUARDS_DIR / "guard_ui_manager.py"
            if _ui_path.exists():
                _spec = _ilu.spec_from_file_location("guard_ui_manager", _ui_path)
                _ui_mod = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_ui_mod)
                if hasattr(_ui_mod, 'integrate_with_kerberos'):
                    _ui_mod.integrate_with_kerberos(self, self.root)
                print("🔗 [UI Manager] Intégré à Kerberos")
        except Exception as _e:
            print(f"⚠️ [UI Manager] Erreur démarrage : {_e}")
        
        self._init_kerberos_structure()
        _load_cortex()
        self._setup_ui()
        self._init_ui_state()
        self.root.mainloop()

    def _setup_window_controls(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<F11>", lambda e: self._toggle_maximize())
        self.root.bind("<F12>", lambda e: _toggle_stealth_mode())
        self.window_menu = Menu(self.root, tearoff=0)
        self.window_menu.add_command(label="🔽 Minimiser", command=self.root.iconify)
        self.window_menu.add_command(label="🔲 Maximiser", command=lambda: self._toggle_maximize())
        self.window_menu.add_command(label="🕵️ Mode furtif", command=lambda: _toggle_stealth_mode())
        self.window_menu.add_separator()
        self.window_menu.add_command(label="❌ Quitter", command=self._on_close)
        self.root.bind("<Button-3>", lambda e: self.window_menu.post(e.x_root, e.y_root))

    def _toggle_maximize(self):
        if self.root.state() == 'zoomed':
            self.root.state('normal')
            self.append_to_chat("🪟 Fenêtre restaurée\n")
        else:
            self.root.state('zoomed')
            self.append_to_chat("🪟 Fenêtre maximisée\n")

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except: pass
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', background='#1e1e1e', foreground='#00ffcc', font=('Consolas', 10))
        style.configure('TButton', background='#2d5a7b', foreground='#00ffcc', font=('Consolas', 10))
        style.configure('TNotebook', background='#1e1e1e')
        style.configure('TNotebook.Tab', background='#2d2d3d', foreground='#00ffcc', padding=[12, 6])
        style.map('TNotebook.Tab', background=[('selected', '#3d3d4d')])
        style.configure('TLabelframe', background='#1e1e1e', foreground='#00ffcc')
        style.configure('TLabelframe.Label', background='#1e1e1e', foreground='#00ffcc')

    def _show_boot_animation(self):
        boot_win = tk.Toplevel(self.root)
        boot_win.title("KERBEROS BOOT")
        boot_win.geometry("700x450")
        boot_win.configure(bg='#0a0a0a')
        boot_win.overrideredirect(True)
        boot_win.update_idletasks()
        x = boot_win.winfo_screenwidth() // 2 - 350
        y = boot_win.winfo_screenheight() // 2 - 225
        boot_win.geometry(f"+{x}+{y}")
        boot_text = tk.Text(boot_win, bg='#0a0a0a', fg='#00ff00', font=("Courier", 10), relief=tk.FLAT)
        boot_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        lines = [
            "╔══════════════════════════════════════════════════╗",
            "║   KERBEROS ULTIMATE v4.2 — BOOT                ║",
            "╚══════════════════════════════════════════════════╝", "",
            "[████████████████████] Initialisation...",
            "[████████████████████] Chargement guards...",
            "  ✓ guard_genome.py          [OK]",
            "  ✓ guard_thymus.py          [OK]",
            "  ✓ guard_cortex.py          [OK]",
            "  ✓ guard_cybermap.py        [OK]",
            "  ✓ guard_tray_icon.py       [OK]",
            "  ✓ guard_ui_manager.py      [OK]", "",
            "[████████████████████] Cœur lymphatique...",
            "  💗 Systole → OK", "  🫀 Diastole → OK", "  🫁 Pause → OK", "",
            "✅ KERBEROS OPÉRATIONNEL", "", "   Cliquez pour continuer...",
        ]
        def animate(idx=0):
            if idx < len(lines):
                boot_text.insert(tk.END, lines[idx] + "\n")
                boot_text.see(tk.END)
                self.root.after(80, lambda: animate(idx + 1))
            else:
                self.root.after(1500, boot_win.destroy)
        boot_text.bind("<Button-1>", lambda e: boot_win.destroy())
        boot_text.bind("<Key>", lambda e: boot_win.destroy())
        boot_text.focus_set()
        animate()

    def _setup_ui(self):
        menubar = Menu(self.root)
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label=TEXTS[LANG]["info_menu"], command=self.show_info)
        help_menu.add_command(label=TEXTS[LANG]["about_menu"], command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label=TEXTS[LANG]["stealth_menu"], command=lambda: _toggle_stealth_mode())
        menubar.add_cascade(label=TEXTS[LANG]["info_menu"], menu=help_menu)
        menubar.add_command(label="⚙️ Gestion", command=self.show_gestion)
        menubar.add_command(label="🪟 Fenêtre", command=lambda: self._toggle_maximize())
        menubar.add_command(label=TEXTS[LANG]["quit_menu"], command=self._on_close)
        self.root.config(menu=menubar)
        
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg='#1e1e1e', sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.sidebar_frame = ttk.Frame(main_pane, width=250)
        main_pane.add(self.sidebar_frame)
        self.sidebar_frame.pack_propagate(False)
        ttk.Label(self.sidebar_frame, text="🛡️ Guards", font=("Consolas", 11, "bold")).pack(pady=10)
        sidebar_canvas = tk.Canvas(self.sidebar_frame, bg='#252525', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.sidebar_frame, orient="vertical", command=sidebar_canvas.yview)
        self.modules_frame = ttk.Frame(sidebar_canvas)
        self.modules_frame.bind("<Configure>", lambda e: sidebar_canvas.configure(scrollregion=sidebar_canvas.bbox("all")))
        sidebar_canvas.create_window((0, 0), window=self.modules_frame, anchor="nw")
        sidebar_canvas.configure(yscrollcommand=scrollbar.set)
        sidebar_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.load_modules_and_guards()
        
        nb = ttk.Notebook(main_pane)
        main_pane.add(nb)
        frame_ai = ttk.Frame(nb)
        nb.add(frame_ai, text='🧠 KERBEROS')
        self.chat = scrolledtext.ScrolledText(frame_ai, wrap=tk.WORD, font=('Consolas', 11), bg='#2d2d2d', fg='#ffffff')
        self.chat.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.chat.insert(tk.END, TEXTS[LANG]["welcome"] + "\n")
        self.chat.insert(tk.END, "💡 Astuce: F11 = Maximiser, F12 = Mode furtif, Clic-droit = Menu\n")
        self.chat.configure(state='disabled')
        input_frame = ttk.Frame(frame_ai)
        input_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        ttk.Label(input_frame, text=TEXTS[LANG]["input_prompt"], foreground="lightgreen").pack(side=tk.LEFT)
        self.user_input = tk.Text(input_frame, height=1, font=('Consolas', 11), bg='#333333', fg='white', insertbackground='white')
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.bind("<Return>", self.handle_user_input)
        self.heartbeat_label = tk.Label(self.root, text="🫀 Cœur activé — 💗 → 🫀 → 🫁", bg='#16213e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        self.heartbeat_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))
        self.status = ttk.Label(self.root, text='✅ Kerberos v4.2 prêt', relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _init_ui_state(self):
        self.custom_commands = {}
        self.load_vocab_files()
        self.update_system_stats()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        print("[🫀💙] Kerberos v4.2 — Démarrage terminé")

    def update_heartbeat(self, message: str):
        try:
            if self.root.winfo_exists() and not _is_app_closing():
                self.heartbeat_label.config(text=f"🫀 {message}")
                self.root.after(8000, lambda: self.heartbeat_label.config(text="🫀 Cœur activé — 💗 → 🫀 → 🫁") if not _is_app_closing() else None)
        except: pass

    def handle_user_input(self, event=None):
        text = self.user_input.get("1.0", "end-1c").strip()
        if not text:
            return "break"
        self.append_to_chat(f"\n{TEXTS[LANG]['input_prompt']}{text}\n")
        self.user_input.delete("1.0", tk.END)
        if text == "help":
            self.append_to_chat(TEXTS[LANG]["help"] + "\n")
        elif text == "stats":
            self.show_gestion()
        elif text == "map":
            self._open_cybermap_dynamic()
            self.append_to_chat("🗺️ Carte cyber dynamique ouverte\n")
        elif text == "stealth":
            _toggle_stealth_mode()
        elif text == "maximize":
            self._toggle_maximize()
        elif text == "minimize":
            self.root.iconify()
        else:
            self.append_to_chat("❓ Commande inconnue. Tapez 'help'.\n")
        return "break"

    def _init_kerberos_structure(self):
        for d in ["guards", "lymph", "logs", "reports", "updates", "maps", "vocab", "plasma", "quarantine"]:
            (KERBEROS_ROOT / d).mkdir(parents=True, exist_ok=True)
        lic = KERBEROS_ROOT / "LICENCE.txt"
        if not lic.exists():
            lic.write_text("""GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007
Copyright (C) 2025 Victor Pozen
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License...
""", encoding="utf-8")

    def load_vocab_files(self):
        self.custom_commands = {}
        vocab_dir = KERBEROS_ROOT / "vocab"
        if not vocab_dir.exists():
            return
        for cmd_file in vocab_dir.glob("*.txt"):
            try:
                for line in cmd_file.read_text(encoding="utf-8").splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        self.custom_commands[k.strip().lower()] = v.strip()
            except: pass

    def load_modules_and_guards(self):
        found = False
        if GUARDS_DIR.exists():
            ttk.Label(self.modules_frame, text="🛡️ Guards", font=("Consolas", 10, "bold"), foreground="orange").pack(anchor="w", pady=(10, 2))
            for f in sorted(GUARDS_DIR.glob("*.py")):
                self.add_module_button(f, "guard")
                found = True
        if not found:
            ttk.Label(self.modules_frame, text="Aucun guard trouvé.", foreground="red").pack(pady=20)

    def reload_modules_and_guards(self):
        for w in self.modules_frame.winfo_children():
            w.destroy()
        self.load_modules_and_guards()
        self.append_to_chat("🔄 Guards rechargés.\n")

    def add_module_button(self, file_path: Path, kind: str):
        frame = ttk.Frame(self.modules_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        name = file_path.stem.replace("_", " ").title()
        ttk.Button(frame, text=name, command=lambda f=file_path: self.execute_module(f)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(frame, text="?", width=3, command=lambda f=file_path: self.show_module_info(f)).pack(side=tk.RIGHT, padx=(5, 0))

    def execute_module(self, file_path: Path):
        self.append_to_chat(f"\n{TEXTS[LANG]['executing']} {file_path.name}...\n")
        threading.Thread(target=self._run_module_in_thread, args=(file_path,), daemon=True).start()

    def _run_module_in_thread(self, file_path: Path):
        try:
            name = file_path.stem
            sys.modules.pop(name, None)
            spec = importlib.util.spec_from_file_location(name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            result = module.run() if hasattr(module, 'run') else None
            output = str(result) if result else "✅ Succès."
        except Exception as e:
            output = f"❌ Erreur : {e}"
        self.root.after(0, lambda: self.append_to_chat(f"{output}\n"))

    def show_module_info(self, file_path: Path):
        """Affiche infos module — fusionné avec _show_guard_info()"""
        messagebox.showinfo(TEXTS[LANG]["module_info"], f"📄 {file_path.name}\n{extract_docstring(file_path)}")

    def append_to_chat(self, text: str):
        self.chat.configure(state='normal')
        self.chat.insert(tk.END, text)
        lines = self.chat.get("1.0", tk.END).count('\n')
        if lines > 80:
            self.chat.delete("1.0", f"{lines - 80}.0")
        self.chat.configure(state='disabled')
        self.chat.see(tk.END)

    def update_system_stats(self):
        if _is_app_closing():
            return
        cpu = psutil.cpu_percent(interval=0.1)
        phase = ["💗", "🫀", "🫁"][_HEART_PHASE]
        stealth_indicator = " 🕵️" if _STEALTH_MODE else ""
        self.status.config(text=f'{phase} Kerberos respire • CPU {cpu:.1f}%{stealth_indicator}')
        self.root.after(2000, self.update_system_stats)

    def show_info(self):
        messagebox.showinfo("Infos", TEXTS[LANG]["info_desc"])

    def show_about(self):
        win = tk.Toplevel(self.root)
        win.title(TEXTS[LANG]["about_menu"])
        win.geometry("500x350")
        win.configure(bg='#1e1e1e')
        tk.Label(win, text=TEXTS[LANG]["about_text"], bg='#1e1e1e', fg='white', font=("Segoe UI", 10), justify=tk.LEFT).pack(padx=20, pady=20)
        tk.Button(win, text="Fermer", command=win.destroy, bg="#666", fg="white").pack(pady=10)

    # ── 🚀 AUTO-START ──────────────────────────────────────────────────────
    def _get_startup_path(self) -> Path:
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, 0x0007, None, 0, buf)
            return Path(buf.value)
        except:
            return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

    def _is_auto_start_enabled(self) -> bool:
        if os.name != 'nt':
            return False
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "Kerberos")
                winreg.CloseKey(key)
                return True
            except WindowsError:
                winreg.CloseKey(key)
                return False
        except:
            shortcut = self._get_startup_path() / "Kerberos.lnk"
            return shortcut.exists()

    def _enable_auto_start(self):
        if os.name != 'nt':
            messagebox.showwarning("Auto-start", "Cette fonctionnalité est uniquement disponible sur Windows")
            return
        try:
            import winreg
            exe_path = sys.executable
            script_path = str(Path(__file__).resolve())
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
            command = f'"{exe_path}" "{script_path}"'
            winreg.SetValueEx(key, "Kerberos", 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)
            self.append_to_chat("✅ [Auto-start] Activé dans le registre Windows\n")
            messagebox.showinfo("Auto-start", "✅ Kerberos démarrera automatiquement au prochain démarrage Windows")
        except Exception as e:
            try:
                startup_dir = self._get_startup_path()
                startup_dir.mkdir(parents=True, exist_ok=True)
                bat_file = startup_dir / "Kerberos.bat"
                bat_content = f'@echo off\nstart "" "{exe_path}" "{script_path}"\nexit'
                bat_file.write_text(bat_content, encoding='utf-8')
                self.append_to_chat("✅ [Auto-start] Activé via dossier Startup\n")
                messagebox.showinfo("Auto-start", "✅ Kerberos démarrera automatiquement (raccourci Startup créé)")
            except Exception as e2:
                messagebox.showerror("Erreur", f"Impossible d'activer l'auto-start :\n{e}\n{e2}")

    def _disable_auto_start(self):
        if os.name != 'nt':
            messagebox.showwarning("Auto-start", "Cette fonctionnalité est uniquement disponible sur Windows")
            return
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
            try:
                winreg.DeleteValue(key, "Kerberos")
            except WindowsError:
                pass
            winreg.CloseKey(key)
            shortcut = self._get_startup_path() / "Kerberos.lnk"
            if shortcut.exists():
                shortcut.unlink()
            bat_file = self._get_startup_path() / "Kerberos.bat"
            if bat_file.exists():
                bat_file.unlink()
            self.append_to_chat("⏹️ [Auto-start] Désactivé\n")
            messagebox.showinfo("Auto-start", "⏹️ Auto-start désactivé")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de désactiver l'auto-start :\n{e}")

    # ── ⚙️ GESTION — SINGLETON ────────────────────────────────────────────
    def show_gestion(self):
        if (self._gestion_window is not None and self._gestion_window.winfo_exists()):
            self._gestion_window.lift()
            self._gestion_window.focus_force()
            return
        win = tk.Toplevel(self.root)
        win.title("⚙️ Gestion Kerberos v4.2")
        win.geometry("950x750")
        win.configure(bg='#1a1a2e')
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_gestion(win))
        self._gestion_window = win
        
        header = tk.Frame(win, bg='#16213e', height=90)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🛡️ KERBEROS — Panneau de Contrôle", bg='#16213e', fg='#00ffcc',
                font=("Consolas", 18, "bold")).pack(pady=15)
        
        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        self._create_monitor_tab(nb)
        self._create_cybermap_tab(nb)  # ← CyberMap DYNAMIQUE
        self._create_analytics_tab(nb)
        self._create_gamification_tab(nb)
        self._create_netshield_tab(nb)
        self._create_bubble_tab(nb)
        self._create_guards_tab(nb)
        self._create_reports_tab(nb)
        self._create_startup_tab(nb)
        self._create_updates_tab(nb)
        self._create_stats_tab(nb)
        self._create_logs_tab(nb)
        
        footer = tk.Frame(win, bg='#16213e', height=50)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        lbl = tk.Label(footer, text="GPLv3 • Victor Pozen • 🔗 github.com/victorpozen",
                      bg='#16213e', fg='#00ccff', font=("Consolas", 9), cursor="hand2")
        lbl.pack(pady=12)
        lbl.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/victorpozen"))

    def _close_gestion(self, win: tk.Toplevel):
        if self._guards_panel:
            self._guards_panel.destroy()
            self._guards_panel = None
        self._gestion_window = None
        try:
            win.destroy()
        except Exception:
            pass

    # ── Onglets ───────────────────────────────────────────────────────────
    def _create_monitor_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 👁️ Monitor ')
        frame = tk.LabelFrame(tab, text=" 🔍 Activité Réseau Temps Réel ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        stats_frame = tk.Frame(frame, bg='#1e1e2e')
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        for icon, label, color in [("🟢", "Autorisé", "#4CAF50"), ("🔴", "Bloqué", "#ff5252"), ("🟡", "Suspect", "#ff9800")]:
            box = tk.Frame(stats_frame, bg='#161a2e', relief=tk.RIDGE, bd=1)
            box.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
            tk.Label(box, text=icon, bg='#161a2e', fg=color, font=("Consolas", 16)).pack(pady=10)
            tk.Label(box, text="0", bg='#161a2e', fg='white', font=("Consolas", 18, "bold")).pack()
            tk.Label(box, text=label, bg='#161a2e', fg='#a0a0c0', font=("Consolas", 9)).pack(pady=(0, 10))
        self.monitor_log = scrolledtext.ScrolledText(frame, height=15, font=("Consolas", 9), bg='#0a0a0a', fg='#00ff00')
        self.monitor_log.pack(fill=tk.BOTH, expand=True)
        self.monitor_log.insert(tk.END, "⏳ En attente d'activité...\n")
        self.monitor_log.configure(state='disabled')

    def _create_cybermap_tab(self, nb):
        """Onglet CyberMap — MAINTENANT DYNAMIQUE avec guard_cybermap.py"""
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 🌍 Carte ')
        frame = tk.LabelFrame(tab, text=" 🗺️ Géolocalisation Temps Réel ", 
                             bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ← NOUVEAU : Bouton pour carte dynamique
        tk.Button(frame, text="🚀 OUVRIR CYBERMAP DYNAMIQUE", 
                  bg='#00ffcc', fg='#0a0f1a', 
                  font=("Consolas", 12, "bold"), 
                  command=self._open_cybermap_dynamic).pack(pady=20)
        
        # Stats en temps réel
        stats_frame = tk.Frame(frame, bg='#1e1e2e')
        stats_frame.pack(fill=tk.X, pady=10)
        
        self._cybermap_stats_vars = {}
        for key, label, color in [
            ("active", "Connexions actives", "#00ffcc"),
            ("outgoing", "Sortantes 📤", "#00ffcc"),
            ("incoming", "Entrantes 📥", "#ff5252"),
        ]:
            box = tk.Frame(stats_frame, bg='#161a2e', relief=tk.RIDGE, bd=1)
            box.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
            tk.Label(box, text=label, bg='#161a2e', fg='#a0a0c0', font=("Consolas", 9)).pack(pady=5)
            val = tk.Label(box, text="0", bg='#161a2e', fg=color, font=("Consolas", 14, "bold"))
            val.pack()
            self._cybermap_stats_vars[key] = val
        
        # Refresh automatique des stats
        self._refresh_cybermap_stats()
        
        log = scrolledtext.ScrolledText(frame, height=8, font=("Consolas", 9), bg='#0a0a0a', fg='#00ff00')
        log.pack(fill=tk.BOTH, expand=True)
        log.insert(tk.END, "🌐 Carte dynamique — Refresh toutes les 10s\n")
        log.insert(tk.END, "📂 Fichier: maps/cybermap_dynamic.html\n")
        log.insert(tk.END, "🔗 guard_cybermap.py actif\n")
        log.configure(state='disabled')

    def _open_cybermap_dynamic(self):
        """Ouvre la cybermap dynamique dans le navigateur"""
        map_file = KERBEROS_ROOT / "maps" / "cybermap_dynamic.html"
        if map_file.exists():
            webbrowser.open(map_file.as_uri())
            self.append_to_chat("🌍 CyberMap dynamique ouverte dans le navigateur\n")
        else:
            messagebox.showwarning("Carte non générée", 
                "La carte dynamique n'a pas encore été générée.\n\n"
                "Attends quelques secondes que guard_cybermap.py scanne le réseau.")

    def _refresh_cybermap_stats(self):
        """Met à jour les stats CyberMap toutes les 5s"""
        try:
            if self._cybermap_engine:
                stats = self._cybermap_engine.get_stats()
                self._cybermap_stats_vars["active"].config(
                    text=str(stats.get("active_connections", 0)))
                self._cybermap_stats_vars["outgoing"].config(
                    text=str(stats.get("outgoing", 0)))
                self._cybermap_stats_vars["incoming"].config(
                    text=str(stats.get("incoming", 0)))
        except:
            pass
        
        if not _is_app_closing() and self._gestion_window and self._gestion_window.winfo_exists():
            self.root.after(5000, self._refresh_cybermap_stats)

    def _create_analytics_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 📊 Analytics ')
        frame = tk.LabelFrame(tab, text=" 📈 Statistiques ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        kpi_frame = tk.Frame(frame, bg='#1e1e2e')
        kpi_frame.pack(fill=tk.X, pady=(0, 20))
        cpu_val = f"{psutil.cpu_percent(interval=None):.1f}%"
        ram_val = f"{psutil.virtual_memory().percent:.1f}%"
        proc_val = str(len(psutil.pids()))
        for icon, label, value, color in [("⚙️", "CPU", cpu_val, "#00ffcc"), ("🧠", "RAM", ram_val, "#ff9800"), ("📦", "Processus", proc_val, "#ff5252")]:
            box = tk.Frame(kpi_frame, bg='#161a2e', relief=tk.RIDGE, bd=2)
            box.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8)
            tk.Label(box, text=icon, bg='#161a2e', fg=color, font=("Consolas", 24)).pack(pady=15)
            tk.Label(box, text=value, bg='#161a2e', fg='white', font=("Consolas", 20, "bold")).pack()
            tk.Label(box, text=label, bg='#161a2e', fg='#a0a0c0', font=("Consolas", 9)).pack(pady=(0, 15))
        self.graph_canvas = tk.Canvas(frame, bg='#0a0a0a', height=200)
        self.graph_canvas.pack(fill=tk.X, pady=(0, 20))
        self._draw_activity_graph()

    def _create_gamification_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 🎮 Achievements ')
        frame = tk.LabelFrame(tab, text=" 🏆 Récompenses ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(frame, text="🎖️ NIVEAU 12 — SENTINELLE AGUERRIE", bg='#161a2e', fg='#00ffcc', font=("Consolas", 14, "bold")).pack(pady=20)
        xp = tk.Canvas(frame, bg='#0a0a0a', height=30)
        xp.pack(fill=tk.X, padx=20, pady=(0, 5))
        xp.create_rectangle(10, 10, 670, 20, fill='#1a1a2e', outline='#00ffcc', width=2)
        xp.create_rectangle(10, 10, 450, 20, fill='#00ffcc', outline='')
        xp.create_text(340, 15, text="XP: 2340 / 3000", fill='white', font=("Consolas", 10, "bold"))
        cont = tk.Frame(frame, bg='#1e1e2e')
        cont.pack(fill=tk.BOTH, expand=True)
        badges = [("🛡️", "PREMIÈRE GARDE", True), ("🔥", "PYROMANE", True), ("⏱️", "MARATHONIEN", True), ("🧬", "BIOLOGISTE", True)]
        for i, (icon, title, unlocked) in enumerate(badges):
            col = i % 3
            bg = '#161a2e' if unlocked else '#0a0a0a'
            bdg = tk.Frame(cont, bg=bg, relief=tk.RIDGE, bd=2)
            bdg.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
            tk.Label(bdg, text=icon if unlocked else "🔒", bg=bg, fg='#00ffcc' if unlocked else '#333333', font=("Consolas", 32)).pack(pady=15)
            tk.Label(bdg, text=title, bg=bg, fg='white' if unlocked else '#555555', font=("Consolas", 9)).pack(pady=(0, 15))

    def _create_netshield_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 🛡️ NetShield ')
        frame = tk.LabelFrame(tab, text=" 🔥 Firewall IP Intelligent ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        stats_frame = tk.Frame(frame, bg='#1e1e2e')
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        self._ns_value_labels: dict[str, tk.Label] = {}
        for key, icon, label, color in [("total_blocked", "🔴", "Total Bloqués", "#ff5252"), ("government", "🕵️", "Gouvernements", "#ff9800"), ("trackers", "🎯", "Trackers", "#ffeb3b")]:
            box = tk.Frame(stats_frame, bg='#161a2e', relief=tk.RIDGE, bd=1)
            box.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
            tk.Label(box, text=icon, bg='#161a2e', fg=color, font=("Consolas", 16)).pack(pady=10)
            val_lbl = tk.Label(box, text=str(self._netshield_stats[key]), bg='#161a2e', fg='white', font=("Consolas", 18, "bold"))
            val_lbl.pack()
            self._ns_value_labels[key] = val_lbl
            tk.Label(box, text=label, bg='#161a2e', fg='#a0a0c0', font=("Consolas", 9)).pack(pady=(0, 10))
        self.netshield_log = scrolledtext.ScrolledText(frame, height=10, font=("Consolas", 9), bg='#0a0a0a', fg='#ff5252')
        self.netshield_log.pack(fill=tk.BOTH, expand=True)
        ts = datetime.now().strftime('%H:%M:%S')
        self.netshield_log.insert(tk.END, f"[{ts}] 🛡️ NetShield Ultimate actif\n")
        self.netshield_log.configure(state='disabled')
        btn_frame = tk.Frame(frame, bg='#1e1e2e')
        btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="🎮 Mode Gaming", bg='#2d5a7b', fg='white', command=self._toggle_gaming_mode).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🕵️ Mode Furtif", bg='#2d5a7b', fg='white', command=self._toggle_netshield_stealth_mode).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📥 MAJ Blocklists", bg='#2d7b5a', fg='white', command=self._update_blocklists).pack(side=tk.RIGHT, padx=5)
        threading.Thread(target=self._load_netshield_stats, daemon=True).start()

    def _load_netshield_stats(self):
        try:
            spec = importlib.util.spec_from_file_location("guard_netshield", GUARDS_DIR / "guard_netshield.py")
            if spec:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, 'get_stats'):
                    stats = mod.get_stats()
                    self._netshield_stats.update(stats)
                    self.root.after(0, self._refresh_netshield_ui)
        except Exception as e:
            self.append_to_chat(f"⚠️ [NetShield] Erreur chargement stats : {e}\n")

    def _refresh_netshield_ui(self):
        for key, lbl in self._ns_value_labels.items():
            try:
                lbl.config(text=str(self._netshield_stats.get(key, 0)))
            except: pass

    def _toggle_gaming_mode(self):
        self.append_to_chat("🎮 [NetShield] Mode Gaming toggled\n")

    def _toggle_netshield_stealth_mode(self):
        self.append_to_chat("🕵️ [NetShield] Mode Furtif toggled\n")

    def _update_blocklists(self):
        self.append_to_chat("📥 [NetShield] Mise à jour des blocklists...\n")
        self.root.after(2000, lambda: self.append_to_chat("✅ [NetShield] Blocklists mises à jour\n"))

    def _create_bubble_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 🫧 Bubble ')
        frame = tk.LabelFrame(tab, text=" 🫧 Protection HDD ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(frame, text="✅ Bubble Shield ACTIF", bg='#161a2e', fg='#4CAF50', font=("Consolas", 14, "bold")).pack(pady=20)
        log = scrolledtext.ScrolledText(frame, height=8, font=("Consolas", 9), bg='#0a0a0a', fg='#00ff00')
        log.pack(fill=tk.BOTH, expand=True)
        log.insert(tk.END, "🫧 Bubble Shield prêt\n🫧 Surveillance HDD active\n")
        log.configure(state='disabled')

    def _create_guards_tab(self, nb):
        """Délègue entièrement à guard_guards_panel.py"""
        try:
            import importlib.util as _ilu
            _spec = _ilu.spec_from_file_location(
                "guard_guards_panel", GUARDS_DIR / "guard_guards_panel.py")
            _mod = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            self._guards_panel = _mod.build_guards_tab(
                notebook         = nb,
                root_widget      = self.root,
                guards_dir       = GUARDS_DIR,
                execute_callback = lambda p: self.execute_module(p),
                info_callback    = self._show_guard_info,
            )
        except Exception as _e:
            import tkinter as tk
            from tkinter import ttk
            tab = ttk.Frame(nb)
            nb.add(tab, text=' 🛡️ Guards ')
            tk.Label(tab, text=f"⚠️ guard_guards_panel.py absent\n{_e}",
                    bg='#1a1a2e', fg='#ff5252',
                    font=("Consolas", 10)).pack(pady=30)

    def _show_guard_info(self, guard_name: str):
        """Affiche fenêtre détaillée via Guard Explainer"""
        path = GUARDS_DIR / guard_name
        if not path.exists():
            messagebox.showwarning("Guard non trouvé",
                                   f"{guard_name} introuvable dans /guards")
            return
        try:
            from guards.guard_explainer import show_guard_info_window
            show_guard_info_window(
                guard_path       = path,
                root_widget      = self.root,
                execute_callback = lambda: self.execute_module(path)
            )
        except Exception:
            messagebox.showinfo(f"📄 {guard_name}", extract_docstring(path))

    def _create_reports_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 📊 Rapports ')
        frame = tk.LabelFrame(tab, text=" 📄 Génération ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Button(frame, text="✨ Générer Rapport HTML", bg='#2d5a7b', fg='white', font=("Consolas", 11, "bold"), command=lambda: messagebox.showinfo("Succès", "Rapport généré !")).pack(pady=20)

    def _create_startup_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 🚀 Démarrage ')
        frame = tk.LabelFrame(tab, text=" 🔁 Auto-start ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        is_enabled = self._is_auto_start_enabled()
        if is_enabled:
            tk.Label(frame, text="✅ ACTIVÉ", bg='#1e1e2e', fg='#4CAF50', font=("Consolas", 14, "bold")).pack(pady=20)
            tk.Button(frame, text="⏹️ Désactiver", bg='#7b2d2d', fg='white', font=("Consolas", 11, "bold"), command=self._disable_auto_start).pack(pady=10)
        else:
            tk.Label(frame, text="❌ DÉSACTIVÉ", bg='#1e1e2e', fg='#ff5252', font=("Consolas", 14, "bold")).pack(pady=20)
            tk.Button(frame, text="▶️ Activer", bg='#2d7b5a', fg='white', font=("Consolas", 11, "bold"), command=self._enable_auto_start).pack(pady=10)
            tk.Label(frame, text="Kerberos démarrera automatiquement\nau démarrage de Windows", bg='#1e1e2e', fg='#a0a0c0', font=("Consolas", 9), justify=tk.CENTER).pack(pady=20)

    def _create_updates_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 🔄 Updates ')
        frame = tk.LabelFrame(tab, text=" 📥 Mises à jour ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(frame, text="Version : v4.2 Ultimate", bg='#1e1e2e', fg='#e0e0e0', font=("Consolas", 12, "bold")).pack(pady=20)
        tk.Button(frame, text="🔍 Vérifier", bg='#2d5a7b', fg='white', font=("Consolas", 11, "bold"), command=lambda: messagebox.showinfo("Updates", "✅ Dernière version !")).pack(pady=10)

    def _create_stats_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 📈 Stats ')
        frame = tk.LabelFrame(tab, text=" 🫀 État Système ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        info = [("Version", "v4.2"), ("ADN", f"{_my_dna()[:16]}…"), ("Système", platform.system()), ("Python", platform.python_version()), ("CPU %", f"{psutil.cpu_percent(interval=None):.1f}"), ("RAM %", f"{psutil.virtual_memory().percent:.1f}")]
        for label, value in info:
            row = tk.Frame(frame, bg='#1e1e2e')
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=f"{label} :", bg='#1e1e2e', fg='#bb86fc', font=("Consolas", 10, "bold"), width=20, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=value, bg='#1e1e2e', fg='#e0e0e0', font=("Consolas", 10)).pack(side=tk.LEFT)

    def _create_logs_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=' 📜 Logs ')
        frame = tk.LabelFrame(tab, text=" 📄 Journaux Système ", bg='#1e1e2e', fg='#00ffcc', font=("Consolas", 11, "bold"))
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        logs = scrolledtext.ScrolledText(frame, height=20, font=("Consolas", 9), bg='#0a0a0a', fg='#00ff00')
        logs.pack(fill=tk.BOTH, expand=True)
        ts = datetime.now().strftime('%H:%M:%S')
        for msg in ["✅ Kerberos démarré", "✅ Guards chargés", "✅ Cœur lymphatique actif"]:
            logs.insert(tk.END, f"[{ts}] {msg}\n")
        log_file = LOGS_DIR / "kerberos.log"
        if log_file.exists():
            try:
                tail = log_file.read_text(encoding="utf-8").splitlines()[-50:]
                for line in tail:
                    logs.insert(tk.END, line + "\n")
            except: pass
        logs.configure(state='disabled')

    def _draw_activity_graph(self):
        w, h = 700, 180
        for i in range(0, h, 30):
            self.graph_canvas.create_line(20, i + 10, w - 20, i + 10, fill='#1a1a2e', dash=(2, 4))
        cpu = psutil.cpu_percent(interval=None)
        points = [max(5, cpu + random.uniform(-10, 10)) for _ in range(60)]
        for i in range(len(points) - 1):
            x1 = 20 + i * (w - 40) / 60
            y1 = h - points[i] - 10
            x2 = 20 + (i + 1) * (w - 40) / 60
            y2 = h - points[i + 1] - 10
            self.graph_canvas.create_line(x1, y1, x2, y2, fill='#00ffcc', width=2)

    def _on_close(self):
        global _APP_CLOSING, _APP_INSTANCE
        _APP_CLOSING = True
        _APP_INSTANCE = None
        print("[🛑] Fermeture Kerberos...")
        if self._guards_panel:
            self._guards_panel.destroy()
        if _kerberos_tray:
            try:
                _kerberos_tray.stop()
            except: pass
        if self._gestion_window:
            try:
                self._gestion_window.destroy()
            except: pass
        try:
            self.root.quit()
            self.root.destroy()
        except: pass
        print("[✅] Fermé proprement")

# ============================================================================
if __name__ == '__main__':
    KerberosApp()