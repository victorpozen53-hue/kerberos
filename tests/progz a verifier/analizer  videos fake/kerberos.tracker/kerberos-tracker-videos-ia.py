#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ KERBEROS VIDEO ANALYZER v7.4 — Orchestrateur Principal (Tkinter)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Licence: GPLv3 | Author: Victor Pozen
Version: 7.4.0 — Architecture modulaire avec bootstrap

Nouveautés v7.4:
- ✅ Bootstrap automatique des dossiers modulaires (boutons/onglets)
- ✅ Chargement dynamique des guards modulaires
- ✅ Architecture 100% extensible sans modifier le core
- ✅ Sécurité renforcée (validation des imports)
"""
import sys
import json
import threading
import importlib.util
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, Menu, scrolledtext, messagebox

# ============================================================================
# 1. INITIALISATION SYSTÈME
# ============================================================================
KERBEROS_ROOT = Path(__file__).parent.resolve()
REQUIRED_DIRS = ["guards", "lymph", "logs", "reports", "videos", "evidence"]
for d in REQUIRED_DIRS:
    (KERBEROS_ROOT / d).mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(KERBEROS_ROOT / 'logs' / 'kerberos.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("KerberosApp")

_APP_CLOSING = False
_APP_INSTANCE = None
LANG = "fr"
GUARDS_DIR = KERBEROS_ROOT / "guards"

TEXTS = {
    "fr": {
        "title": "🎬 KERBEROS VIDEO ANALYZER v7.4",
        "welcome": "Bienvenue dans Kerberos Video Analyzer v7.4.\nArchitecture modulaire sécurisée.\nTapez 'help' pour l'aide.",
        "info_menu": "Infos", "about_menu": "À propos", "quit_menu": "Quitter",
        "info_desc": "Kerberos Video Analyzer v7.4 — GPLv3 — Victor Pozen",
        "about_text": "KERBEROS VIDEO ANALYZER v7.4\nVictor Pozen\nDétection de deepfakes et vidéos IA\nLicence GPLv3"
    }
}


# ============================================================================
# 2. GUARD MANAGER (Thread-Safe)
# ============================================================================
class GuardManager:
    """Gestionnaire centralisé des guards avec verrous pour la sécurité des threads."""
    
    def __init__(self) -> None:
        self.guards = {}
        self._lock = threading.Lock()
        logger.info("🛡️ GuardManager initialisé")

    def register_guard(self, name: str, guard_instance) -> bool:
        with self._lock:
            self.guards[name] = guard_instance
            return True

    def start_guard(self, name: str) -> bool:
        with self._lock:
            guard = self.guards.get(name)
            if not guard: return False
            try:
                if hasattr(guard, 'start'): guard.start()
                elif hasattr(guard, 'start_analysis'): guard.start_analysis()
                return True
            except Exception as e:
                logger.error(f"❌ Erreur démarrage {name}: {e}")
                return False

    def stop_guard(self, name: str) -> bool:
        with self._lock:
            guard = self.guards.get(name)
            if not guard: return False
            try:
                if hasattr(guard, 'stop'): guard.stop()
                elif hasattr(guard, 'stop_analysis'): guard.stop_analysis()
                return True
            except Exception as e:
                logger.error(f"❌ Erreur arrêt {name}: {e}")
                return False

    def pause_guard(self, name: str) -> bool:
        with self._lock:
            guard = self.guards.get(name)
            if guard and hasattr(guard, 'pause'): guard.pause(); return True
            return False

    def resume_guard(self, name: str) -> bool:
        with self._lock:
            guard = self.guards.get(name)
            if guard and hasattr(guard, 'resume'): guard.resume(); return True
            return False

    def stop_all_guards(self) -> None:
        with self._lock:
            for name, guard in list(self.guards.items()):
                try:
                    if hasattr(guard, 'stop'): guard.stop()
                    elif hasattr(guard, 'stop_analysis'): guard.stop_analysis()
                except: pass

    def get_all_stats(self) -> dict:
        with self._lock:
            return {name: guard.get_stats() for name, guard in self.guards.items() if hasattr(guard, 'get_stats')}

    def get_guard(self, name: str):
        with self._lock: return self.guards.get(name)

    def list_guards(self) -> list:
        with self._lock: return list(self.guards.keys())


# ============================================================================
# 3. APPLICATION PRINCIPALE
# ============================================================================
class KerberosApp:
    def __init__(self):
        global _APP_INSTANCE
        _APP_INSTANCE = self
        
        self.root = tk.Tk()
        self.root.title(TEXTS[LANG]["title"])
        self.root.geometry("1200x750")
        self.root.configure(bg='#1e1e1e')

        self.guard_manager = GuardManager()
        self._gestion_window = None
        self._video_analyzer_engine = None
        self._video_stats = {"total": 0, "real": 0, "suspicious": 0, "uncertain": 0}
        self._is_paused = False
        
        self._setup_styles()
        self._bootstrap_architecture()  # ✅ NOUVEAU: Bootstrap avant tout
        self._load_guards()
        self._setup_ui()
        self._load_ui_extensions()
        self._load_modular_tabs()  # ✅ NOUVEAU: Chargement des onglets modulaires
        self._refresh_video_stats()

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        logger.info("[✅] Kerberos Video Analyzer v7.4 — Démarrage terminé")
        self.root.mainloop()

    def _setup_styles(self) -> None:
        style = ttk.Style()
        try: style.theme_use('clam')
        except: pass
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabel', background='#1e1e1e', foreground='#00ffcc', font=('Consolas', 10))
        style.configure('TButton', background='#2d5a7b', foreground='#00ffcc', font=('Consolas', 10))

    def _bootstrap_architecture(self) -> None:
        """Exécute le guard bootstrap pour créer l'architecture modulaire"""
        logger.info("🌱 Exécution du bootstrap...")
        bootstrap_path = GUARDS_DIR / "guard_bootstrap.py"
        
        if bootstrap_path.exists():
            try:
                spec = importlib.util.spec_from_file_location("guard_bootstrap", bootstrap_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                if hasattr(mod, 'start_guard'):
                    bootstrap_guard = mod.start_guard(self)
                    if bootstrap_guard:
                        self.guard_manager.register_guard("bootstrap", bootstrap_guard)
                        logger.info("✅ Bootstrap exécuté avec succès")
            except Exception as e:
                logger.error(f" Erreur bootstrap: {e}")
        else:
            logger.warning("⚠️ guard_bootstrap.py introuvable")

    def _load_guards(self) -> None:
        logger.info("🔧 Chargement des guards...")
        self._load_video_analyzer_manual()

        manifest_path = GUARDS_DIR / "guards_manifest.json"
        if not manifest_path.exists(): return
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            for guard_file in manifest.get('active_guards', []):
                if 'video_analyzer' in guard_file and 'filtered' not in guard_file: continue
                if 'bootstrap' in guard_file: continue  # Déjà chargé
                
                guard_path = GUARDS_DIR / guard_file
                if not guard_path.exists(): continue

                try:
                    module_name = guard_file.replace('.py', '')
                    spec = importlib.util.spec_from_file_location(module_name, guard_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, 'start_guard'):
                            instance = module.start_guard(self)
                            if instance:
                                self.guard_manager.register_guard(module_name.replace('guard_', ''), instance)
                except Exception as e:
                    logger.error(f"❌ Erreur chargement {guard_file}: {e}")
        except Exception as e:
            logger.error(f"❌ Erreur lecture manifest: {e}")
        
        # ✅ NOUVEAU: Chargement des guards modulaires
        self._load_modular_guards()

    def _load_modular_guards(self) -> None:
        """Charge automatiquement les guards des dossiers boutons/onglets"""
        # Charger les guards de boutons
        boutons_dir = GUARDS_DIR / "boutons"
        if boutons_dir.exists():
            for guard_file in boutons_dir.glob("guard_*.py"):
                if guard_file.name.startswith("guard_") and not guard_file.name.startswith("guard___"):
                    try:
                        module_name = f"guards.boutons.{guard_file.stem}"
                        spec = importlib.util.spec_from_file_location(module_name, guard_file)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            if hasattr(module, 'start_guard'):
                                instance = module.start_guard(self)
                                if instance:
                                    self.guard_manager.register_guard(guard_file.stem.replace('guard_', ''), instance)
                                    logger.info(f"✅ Guard bouton chargé: {guard_file.name}")
                    except Exception as e:
                        logger.error(f"❌ Erreur chargement guard bouton {guard_file.name}: {e}")
        
        # Charger les guards d'onglets
        onglets_dir = GUARDS_DIR / "onglets"
        if onglets_dir.exists():
            for guard_file in onglets_dir.glob("guard_*.py"):
                if guard_file.name.startswith("guard_") and not guard_file.name.startswith("guard___"):
                    try:
                        module_name = f"guards.onglets.{guard_file.stem}"
                        spec = importlib.util.spec_from_file_location(module_name, guard_file)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            if hasattr(module, 'start_guard'):
                                instance = module.start_guard(self)
                                if instance:
                                    self.guard_manager.register_guard(guard_file.stem.replace('guard_', ''), instance)
                                    logger.info(f"✅ Guard onglet chargé: {guard_file.name}")
                    except Exception as e:
                        logger.error(f"❌ Erreur chargement guard onglet {guard_file.name}: {e}")

    def _load_video_analyzer_manual(self) -> None:
        _video_path = GUARDS_DIR / "guard_video_analyzer.py"
        if not _video_path.exists(): return
        try:
            spec = importlib.util.spec_from_file_location("guard_video_analyzer", _video_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, 'start_guard'):
                instance = mod.start_guard(self)
                if instance:
                    self.guard_manager.register_guard("video_analyzer", instance)
                    self._video_analyzer_engine = instance
        except Exception as e:
            logger.error(f"❌ Erreur chargement video_analyzer: {e}")

    def _load_ui_extensions(self) -> None:
        """Charge les guards qui étendent l'UI dynamiquement"""
        ui_guard = self.guard_manager.get_guard("ui_buttons")
        if not ui_guard:
            logger.warning("⚠️ Guard 'ui_buttons' introuvable")
            return
        if not hasattr(ui_guard, 'inject_buttons'):
            logger.warning("⚠️ Guard 'ui_buttons' sans méthode 'inject_buttons'")
            return
        if not getattr(self, 'btn_frame', None):
            logger.warning("⚠️ 'btn_frame' n'existe pas")
            return
        try:
            count = ui_guard.inject_buttons()
            if count > 0:
                logger.info(f"✅ {count} boutons UI injectés")
        except Exception as e:
            logger.error(f"❌ Erreur injection UI: {e}")

    def _load_modular_tabs(self) -> None:
        """Charge les guards qui gèrent les onglets de la fenêtre Gestion"""
        # Cette méthode sera appelée quand l'utilisateur ouvrira la fenêtre Gestion
        pass

    def _setup_ui(self) -> None:
        menubar = Menu(self.root)
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label=TEXTS[LANG]["info_menu"], command=self.show_info)
        help_menu.add_command(label=TEXTS[LANG]["about_menu"], command=self.show_about)
        menubar.add_cascade(label=TEXTS[LANG]["info_menu"], menu=help_menu)
        menubar.add_command(label="⚙️ Gestion", command=self.show_gestion)
        menubar.add_command(label=TEXTS[LANG]["quit_menu"], command=self._on_close)
        self.root.config(menu=menubar)

        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(main_frame, text="🎬 KERBEROS VIDEO ANALYZER", bg='#1e1e1e', fg='#00ffcc', font=("Consolas", 18, "bold")).pack(pady=10)

        stats_frame = tk.Frame(main_frame, bg='#161a2e')
        stats_frame.pack(fill=tk.X, pady=10)

        self._ui_stats_vars = {}
        for key, label, color in [("total", "Total", "#00ffcc"), ("real", "✅ Réelles", "#4CAF50"), ("suspicious", "🤖 IA", "#ff5252"), ("uncertain", "🎨 Incertain", "#ff9800")]:
            box = tk.Frame(stats_frame, bg='#1e1e2e', relief=tk.RIDGE, bd=1)
            box.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
            tk.Label(box, text=label, bg='#1e1e2e', fg='#a0a0c0', font=("Consolas", 9)).pack(pady=5)
            val = tk.Label(box, text="0", bg='#1e1e2e', fg=color, font=("Consolas", 16, "bold"))
            val.pack()
            self._ui_stats_vars[key] = val

        sensitivity_frame = tk.Frame(main_frame, bg='#161a2e')
        sensitivity_frame.pack(fill=tk.X, pady=10, padx=5)

        tk.Label(sensitivity_frame, text="🎚️ Sensibilité :", bg='#161a2e', fg='#00ffcc', font=("Consolas", 10)).pack(side=tk.LEFT, padx=10)
        self.threshold_var = tk.DoubleVar(value=65)
        self.threshold_slider = ttk.Scale(sensitivity_frame, from_=30, to=95, orient=tk.HORIZONTAL, variable=self.threshold_var, command=self._on_threshold_change)
        self.threshold_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.threshold_label = tk.Label(sensitivity_frame, text="65 (Moyen)", bg='#161a2e', fg='#ff9800', font=("Consolas", 10, "bold"))
        self.threshold_label.pack(side=tk.RIGHT, padx=10)

        url_frame = tk.Frame(main_frame, bg='#161a2e')
        url_frame.pack(fill=tk.X, pady=5, padx=5)

        tk.Label(url_frame, text="🌐 URL :", bg='#161a2e', fg='#00ffcc', font=("Consolas", 10)).pack(side=tk.LEFT, padx=10)
        self.url_var = tk.StringVar(value="")
        ttk.Entry(url_frame, textvariable=self.url_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        tk.Button(url_frame, text="📋 Coller", bg='#2d7b5a', fg='white', font=("Consolas", 10), command=self._paste_url).pack(side=tk.RIGHT, padx=5)
        tk.Button(url_frame, text="🔗 Ouvrir", bg='#2d5a7b', fg='white', font=("Consolas", 10), command=self._open_target_url).pack(side=tk.RIGHT, padx=5)

        self.chat = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=('Consolas', 11), bg='#2d2d2d', fg='#ffffff')
        self.chat.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.chat.insert(tk.END, TEXTS[LANG]["welcome"] + "\n")
        self.chat.configure(state='disabled')

        self.btn_frame = tk.Frame(main_frame, bg='#1e1e1e')
        self.btn_frame.pack(fill=tk.X, pady=10)

        self.btn_start = tk.Button(self.btn_frame, text="▶️ Démarrer", bg='#2d7b5a', fg='white', font=("Consolas", 11), command=self._start_video_analysis)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        self.btn_pause = tk.Button(self.btn_frame, text="️ Pause", bg='#ff9800', fg='white', font=("Consolas", 11), command=self._toggle_pause, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=5)
        self.btn_stop = tk.Button(self.btn_frame, text="⏹️ Arrêter", bg='#7b2d2d', fg='white', font=("Consolas", 11), command=self._stop_video_analysis, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        tk.Button(self.btn_frame, text="📊 Rapport", bg='#2d5a7b', fg='white', font=("Consolas", 11), command=self._generate_report).pack(side=tk.RIGHT, padx=5)

        self.status_label = tk.Label(main_frame, text="⏳ En attente", bg='#1e1e1e', fg='#666', font=("Consolas", 10, "bold"))
        self.status_label.pack(pady=5)
        self.status = ttk.Label(self.root, text='✅ Prêt', relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_threshold_change(self, value: str):
        threshold = int(float(value))
        level, color = ("Faible", "#4CAF50") if threshold < 50 else ("Moyen", "#ff9800") if threshold < 75 else ("Strict", "#ff5252")
        self.threshold_label.config(text=f"{threshold} ({level})", fg=color)
        if self._video_analyzer_engine and hasattr(self._video_analyzer_engine, 'set_threshold'):
            self._video_analyzer_engine.set_threshold(threshold)

    def _paste_url(self):
        try:
            url = self.root.clipboard_get()
            if url.startswith("http"):
                self.url_var.set(url)
                self.append_to_chat("📋 URL collée\n")
        except: pass

    def _open_target_url(self):
        url = self.url_var.get().strip()
        if url.startswith("http") and self._video_analyzer_engine and hasattr(self._video_analyzer_engine, 'navigate_to_url'):
            self._video_analyzer_engine.navigate_to_url(url)
            self.append_to_chat(f"🌐 Ouverture de : {url}\n")

    def _start_video_analysis(self):
        if self.guard_manager.start_guard("video_analyzer"):
            self.append_to_chat("▶️ Analyse démarrée\n")
            self.status.config(text='🎬 En cours...')
            self.status_label.config(text="▶️ En cours", fg='#4CAF50')
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
            self._is_paused = False

    def _toggle_pause(self):
        if not self._is_paused:
            self.guard_manager.pause_guard("video_analyzer")
            self._is_paused = True
            self.btn_pause.config(text="▶️ Reprendre", bg='#4CAF50')
            self.status_label.config(text="️ Pause", fg='#ff9800')
        else:
            self.guard_manager.resume_guard("video_analyzer")
            self._is_paused = False
            self.btn_pause.config(text="⏸️ Pause", bg='#ff9800')
            self.status_label.config(text="▶️ En cours", fg='#4CAF50')

    def _stop_video_analysis(self):
        self.guard_manager.stop_guard("video_analyzer")
        self.append_to_chat("️ Analyse arrêtée\n")
        self.status.config(text='⏹️ Arrêté')
        self.status_label.config(text="⏹️ Arrêté", fg='#ff5252')
        self.btn_start.config(state=tk.NORMAL)
        self.btn_pause.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.DISABLED)
        self._is_paused = False

    def _generate_report(self):
        try:
            videos = self._video_analyzer_engine.get_analyzed_videos() if self._video_analyzer_engine else []
            report_path = GUARDS_DIR / "guard_report_generator.py"
            if report_path.exists():
                spec = importlib.util.spec_from_file_location("gen", report_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, 'generate_report'):
                    mod.generate_report(self.guard_manager.get_all_stats(), videos)
                    self.append_to_chat("📊 Rapport généré\n")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def append_to_chat(self, text: str):
        self.chat.configure(state='normal')
        self.chat.insert(tk.END, text)
        self.chat.configure(state='disabled')
        self.chat.see(tk.END)

    def _refresh_video_stats(self):
        try:
            if self._video_analyzer_engine:
                stats = self._video_analyzer_engine.get_stats()
                for key, val in stats.items():
                    if key in self._ui_stats_vars:
                        self._ui_stats_vars[key].config(text=str(val))
        except: pass

        if not _APP_CLOSING:
            self.root.after(3000, self._refresh_video_stats)

    def show_info(self): messagebox.showinfo("Infos", TEXTS[LANG]["info_desc"])

    def show_about(self):
        win = tk.Toplevel(self.root)
        win.title("À propos")
        win.geometry("400x250")
        win.configure(bg='#1e1e1e')
        tk.Label(win, text=TEXTS[LANG]["about_text"], bg='#1e1e1e', fg='white', font=("Segoe UI", 10), justify=tk.LEFT).pack(padx=20, pady=20)
        tk.Button(win, text="Fermer", command=win.destroy).pack(pady=10)

    def show_gestion(self):
        if getattr(self, '_gestion_window', None) and self._gestion_window.winfo_exists():
            self._gestion_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("⚙️ Gestion & Réglages")
        win.geometry("900x700")
        win.configure(bg='#1a1a2e')
        self._gestion_window = win

        # Création du Notebook
        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Onglet 1: Guards Actifs
        tab_guards = tk.Frame(notebook, bg='#1a1a2e')
        notebook.add(tab_guards, text="️ Guards Actifs")
        
        header = tk.Frame(tab_guards, bg='#1a1a2e')
        header.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(header, text=f"🛡️ {len(self.guard_manager.list_guards())} guards actifs", 
                 bg='#1a1a2e', fg='#00ffcc', font=("Consolas", 11, "bold")).pack(side=tk.LEFT)
        
        listbox = tk.Listbox(tab_guards, bg='#0a0a0a', fg='#00ff00', font=("Consolas", 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for g in self.guard_manager.list_guards():
            listbox.insert(tk.END, f"✅ {g}")

        # Onglet 2: Réglages
        tab_settings = tk.Frame(notebook, bg='#1a1a2e')
        notebook.add(tab_settings, text="⚙️ Réglages")
        tk.Label(tab_settings, text="⚙️ Zone de réglages", bg='#1a1a2e', fg='#ff9800', font=("Consolas", 14)).pack(pady=50)

        # Onglet 3: Statistiques
        tab_stats = tk.Frame(notebook, bg='#1a1a2e')
        notebook.add(tab_stats, text="📊 Statistiques")
        tk.Label(tab_stats, text="📊 Statistiques en temps réel", bg='#1a1a2e', fg='#00ffcc', font=("Consolas", 14)).pack(pady=50)

        # ✅ NOUVEAU: Charger les onglets modulaires
        self._load_modular_tabs_to_notebook(notebook)

    def _load_modular_tabs_to_notebook(self, notebook: ttk.Notebook):
        """Charge les guards qui veulent ajouter des onglets"""
        # Cherche tous les guards qui ont une méthode build_tab
        for name, guard in self.guard_manager.guards.items():
            if hasattr(guard, 'build_tab') and callable(getattr(guard, 'build_tab')):
                try:
                    guard.build_tab(notebook)
                    logger.info(f"📑 Onglet ajouté par guard: {name}")
                except Exception as e:
                    logger.error(f"❌ Erreur ajout onglet guard {name}: {e}")

    def _on_close(self):
        global _APP_CLOSING, _APP_INSTANCE
        _APP_CLOSING = True
        _APP_INSTANCE = None

        self.guard_manager.stop_all_guards()
        try:
            if self._video_analyzer_engine and hasattr(self._video_analyzer_engine, '_cleanup'):
                self._video_analyzer_engine._cleanup()
        except: pass
        self.root.destroy()


def main():
    try: KerberosApp()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import traceback; traceback.print_exc()
        input("Appuyez sur Entrée...")

if __name__ == '__main__':
    main()