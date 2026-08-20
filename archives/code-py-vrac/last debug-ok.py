#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kerberos Debugger v4.0
Licence: GPLv3
Développé par Victor Pozen © 2026
🐞 Analyse AI embarquée + Détection auto des dépendances manquantes
"""

import sys
import os
import re
import importlib
import subprocess
import traceback
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import threading
import json
from pathlib import Path

# ============================================================================
# 🔍 MODULE DE DÉTECTION DES DÉPENDANCES MANQUANTES
# ============================================================================
class DependencyChecker:
    """Détecte les modules Python manquants dans le code source"""
    
    def __init__(self, logger):
        self.logger = logger
        self.known_modules = {
            'numpy': 'numpy',
            'pandas': 'pandas',
            'matplotlib': 'matplotlib',
            'requests': 'requests',
            'tkintermapview': 'tkintermapview',
            'geopy': 'geopy',
            'overpass': 'overpass',
            'emoji': 'emoji',
            'PIL': 'Pillow',
            'openai': 'openai',
            'anthropic': 'anthropic',
            'google.generativeai': 'google-generativeai'
        }
    
    def scan_code(self, code: str) -> list:
        """Analyse le code pour détecter les imports et modules requis"""
        missing = []
        imports = set()
        
        # Extraire tous les imports
        import_patterns = [
            r'^import\s+([\w\.]+)',
            r'^from\s+([\w\.]+)\s+import',
            r'import\s+([\w\.]+)',
            r'from\s+([\w\.]+)\s+import'
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE):
                module = match.group(1).split('.')[0]
                if module and module not in imports:
                    imports.add(module)
        
        # Vérifier chaque module
        for module in imports:
            if module in ['os', 'sys', 're', 'json', 'datetime', 'tkinter', 'threading']:
                continue  # Modules stdlib - toujours présents
            
            try:
                importlib.import_module(module)
                self.logger(f"✅ Module trouvé: {module}")
            except ImportError:
                pkg = self.known_modules.get(module, module)
                missing.append({
                    'module': module,
                    'package': pkg,
                    'install_cmd': f"pip install {pkg}"
                })
                self.logger(f"❌ Module manquant: {module} → '{pkg}'")
        
        return missing
    
    def generate_fix_suggestions(self, missing: list) -> str:
        """Génère des suggestions de correction formatées"""
        if not missing:
            return "✅ Tous les modules requis sont installés.\n"
        
        suggestions = "⚠️  Modules manquants détectés :\n\n"
        for i, dep in enumerate(missing, 1):
            suggestions += f"{i}. 📦 {dep['module']}\n"
            suggestions += f"   → pip install {dep['package']}\n\n"
        
        suggestions += "\n💡 Conseil Kerberos : Exécute ces commandes dans ton terminal avant de lancer le script.\n"
        return suggestions


# ============================================================================
# 🧠 MODULE D'ANALYSE AI EMBARQUÉE (sans API externe)
# ============================================================================
class AILocalAnalyzer:
    """Analyseur d'erreurs avec IA embarquée (règles + patterns)"""
    
    def __init__(self, logger):
        self.logger = logger
        self.ai_enabled = True  # Toggle ON/OFF
        
        # Base de connaissances embarquée
        self.error_patterns = {
            r"NameError: name '(\w+)' is not defined": {
                "cause": "Variable non définie ou faute de frappe",
                "fix": "Vérifie l'orthographe de '{0}' ou initialise-la avant utilisation",
                "emoji": "🔤"
            },
            r"AttributeError: '(\w+)' object has no attribute '(\w+)'": {
                "cause": "Méthode/attribut inexistant sur l'objet",
                "fix": "Vérifie que '{1}' existe dans la classe '{0}' ou utilise dir({0}) pour explorer",
                "emoji": "🧩"
            },
            r"KeyError: (\S+)": {
                "cause": "Clé absente dans le dictionnaire",
                "fix": "Utilise .get('{0}', valeur_par_defaut) ou vérifie les clés avec 'in'",
                "emoji": "🔑"
            },
            r"IndexError: list index out of range": {
                "cause": "Accès à un index inexistant dans une liste",
                "fix": "Vérifie la longueur de la liste avec len() avant d'accéder à un index",
                "emoji": "📏"
            },
            r"TypeError: '(\w+)' object is not iterable": {
                "cause": "Objet utilisé dans une boucle mais non itérable",
                "fix": "Convertir en liste/tuple ou vérifier le type avec isinstance()",
                "emoji": "🔄"
            },
            r"ModuleNotFoundError: No module named '(\w+)'": {
                "cause": "Module Python non installé",
                "fix": "pip install {0}  → puis redémarre le script",
                "emoji": "📦"
            },
            r"FileNotFoundError: \[Errno 2\]": {
                "cause": "Fichier ou chemin introuvable",
                "fix": "Vérifie le chemin avec os.path.exists() et utilise des chemins absolus",
                "emoji": "📁"
            },
            r"IndentationError:": {
                "cause": "Mauvaise indentation (mélange espaces/tabulations)",
                "fix": "Utilise 4 espaces par niveau d'indentation - pas de tabulations",
                "emoji": "↹"
            },
            r"SyntaxError: invalid syntax": {
                "cause": "Erreur de syntaxe Python",
                "fix": "Vérifie les parenthèses, deux-points, et guillemets non fermés",
                "emoji": "✏️"
            }
        }
    
    def toggle_ai(self, state: bool):
        """Active/désactive l'analyse AI"""
        self.ai_enabled = state
        status = "🟢 ACTIVÉE" if state else "🔴 DÉSACTIVÉE"
        self.logger(f"🧠 IA embarquée {status}")
        return status
    
    def analyze(self, error_type: str, error_msg: str, tb_lines: list) -> dict:
        """Analyse l'erreur avec la base de connaissances embarquée"""
        if not self.ai_enabled:
            return {
                "ai_status": "❌ IA désactivée",
                "analysis": "Analyse AI désactivée par l'utilisateur",
                "suggestion": "Active l'IA avec le bouton 🧠 pour obtenir des suggestions intelligentes"
            }
        
        self.logger("🧠 Analyse AI embarquée en cours...")
        
        # Recherche de pattern
        for pattern, solution in self.error_patterns.items():
            match = re.search(pattern, error_msg)
            if match:
                # Formatage de la suggestion avec les groupes capturés
                fix = solution["fix"]
                for i, group in enumerate(match.groups(), 1):
                    fix = fix.replace(f"{{{i-1}}}", str(group))
                
                return {
                    "ai_status": f"✅ {solution['emoji']} Pattern reconnu",
                    "analysis": solution["cause"],
                    "suggestion": fix,
                    "confidence": "Haute (pattern embarqué)"
                }
        
        # Analyse contextuelle basique si pas de match
        context = self._contextual_analysis(error_type, error_msg, tb_lines)
        return context
    
    def _contextual_analysis(self, error_type: str, error_msg: str, tb_lines: list) -> dict:
        """Analyse contextuelle de secours"""
        hints = []
        
        if "NoneType" in error_msg:
            hints.append("🔍 L'objet est None → vérifie les retours de fonction")
        if "int" in error_msg and "str" in error_msg:
            hints.append("🔢 Conversion type requise: int() ou str()")
        if "list" in error_msg.lower() and "dict" in error_msg.lower():
            hints.append("📋 Mauvais type de structure de données")
        
        return {
            "ai_status": "🟡 Analyse contextuelle",
            "analysis": f"Erreur {error_type}: {error_msg[:80]}...",
            "suggestion": " → ".join(hints) if hints else "Examine le contexte d'appel dans le traceback",
            "confidence": "Moyenne (analyse heuristique)"
        }


# ============================================================================
# 🐞 CLASSE PRINCIPALE DU DEBUGGER
# ============================================================================
class KerberosDebugger:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🐞 Kerberos Debugger v4.0")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0a0e17")
        
        # États
        self.script_path = None
        self.process = None
        self.ai_analyzer = AILocalAnalyzer(self.log_message)
        self.dependency_checker = DependencyChecker(self.log_message)
        
        self.create_widgets()
        self.log_message("✨ Kerberos Debugger v4.0 initialisé")
        self.log_message("🧠 IA embarquée: PRÊTE (pas d'API externe requise)")
        self.log_message("🔍 Détection auto des dépendances: ACTIVE")
    
    def create_widgets(self):
        # Palette Kerberos
        bg_dark = "#0a0e17"
        bg_mid = "#121826"
        accent = "#6c5ce7"
        accent_hover = "#a29bfe"
        text = "#f7f9fc"
        error = "#ff7675"
        success = "#00b894"
        warning = "#fdcb6e"
        
        # ========== BARRE DE CONTRÔLE ==========
        control_frame = tk.Frame(self.root, bg=bg_mid, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Boutons principaux
        btn_style = {
            "bg": accent, "fg": text, "font": ("Consolas", 11, "bold"),
            "bd": 0, "padx": 15, "pady": 8, "relief": tk.FLAT
        }
        
        tk.Button(control_frame, text="📂 Ouvrir Script", command=self.open_script, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="🚀 Exécuter", command=self.run_script, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="⏹️  Stopper", command=self.stop_script, **btn_style).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="🗑️  Effacer Logs", command=self.clear_logs, **btn_style).pack(side=tk.LEFT, padx=5)
        
        # Toggle IA
        self.ai_toggle_var = tk.BooleanVar(value=True)
        ai_frame = tk.Frame(control_frame, bg=bg_mid)
        ai_frame.pack(side=tk.RIGHT, padx=20)
        
        self.ai_label = tk.Label(
            ai_frame, text="🧠 IA: ON", 
            bg=bg_mid, fg=success, font=("Consolas", 11, "bold")
        )
        self.ai_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.ai_toggle = tk.Checkbutton(
            ai_frame, 
            variable=self.ai_toggle_var,
            command=self.toggle_ai,
            bg=bg_mid, 
            fg=accent,
            selectcolor=bg_dark,
            activebackground=bg_mid,
            width=3
        )
        self.ai_toggle.pack(side=tk.LEFT)
        
        # ========== PANNEAU PATH ==========
        path_frame = tk.Frame(self.root, bg=bg_dark, pady=5)
        path_frame.pack(fill=tk.X, padx=10)
        
        self.path_label = tk.Label(
            path_frame, 
            text="📁 Aucun script chargé",
            bg=bg_dark, fg="#636e72", font=("Consolas", 9),
            anchor=tk.W
        )
        self.path_label.pack(fill=tk.X, padx=10)
        
        # ========== NOTEBOOK (Tabs) ==========
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=bg_dark, borderwidth=0)
        style.configure("TNotebook.Tab", 
            background=bg_mid, 
            foreground=text, 
            padding=[15, 8],
            font=("Consolas", 10)
        )
        style.map("TNotebook.Tab", 
            background=[("selected", accent)],
            foreground=[("selected", "white")]
        )
        
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # --- Tab 1: Console ---
        console_frame = tk.Frame(notebook, bg=bg_dark)
        notebook.add(console_frame, text=" 💻 Console ")
        
        self.console = scrolledtext.ScrolledText(
            console_frame, 
            bg="#1e273a", fg="#55efc4", 
            font=("Consolas", 11),
            insertbackground="#55efc4",
            wrap=tk.WORD,
            borderwidth=0
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console.tag_configure("error", foreground=error, font=("Consolas", 11, "bold"))
        self.console.tag_configure("warning", foreground=warning)
        self.console.tag_configure("success", foreground=success)
        self.console.tag_configure("ai", foreground="#00cec9", font=("Consolas", 11, "italic"))
        
        # --- Tab 2: Analyse AI ---
        ai_frame = tk.Frame(notebook, bg=bg_dark)
        notebook.add(ai_frame, text=" 🧠 Analyse IA ")
        
        self.ai_analysis = scrolledtext.ScrolledText(
            ai_frame,
            bg="#1e273a", fg="#dfe6e9",
            font=("Consolas", 11),
            wrap=tk.WORD,
            borderwidth=0
        )
        self.ai_analysis.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.ai_analysis.tag_configure("header", foreground=accent, font=("Consolas", 12, "bold"))
        self.ai_analysis.tag_configure("fix", foreground=success, font=("Consolas", 11, "bold"))
        
        # --- Tab 3: Dépendances ---
        dep_frame = tk.Frame(notebook, bg=bg_dark)
        notebook.add(dep_frame, text=" 🔍 Dépendances ")
        
        self.dep_analysis = scrolledtext.ScrolledText(
            dep_frame,
            bg="#1e273a", fg="#dfe6e9",
            font=("Consolas", 11),
            wrap=tk.WORD,
            borderwidth=0
        )
        self.dep_analysis.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.dep_analysis.tag_configure("missing", foreground=error, font=("Consolas", 11, "bold"))
        self.dep_analysis.tag_configure("ok", foreground=success)
        
        # ========== STATUS BAR ==========
        self.status_var = tk.StringVar(value="Prêt · GPLv3 · Kerberos v4.0")
        status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var,
            bg="#000000", fg="#636e72", 
            font=("Consolas", 9), 
            anchor=tk.W, 
            padx=10, pady=5
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def log_message(self, msg: str, tag=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}\n"
        self.console.insert(tk.END, formatted, tag)
        self.console.see(tk.END)
        self.root.update_idletasks()
    
    def toggle_ai(self):
        state = self.ai_toggle_var.get()
        status = self.ai_analyzer.toggle_ai(state)
        self.ai_label.config(
            text=f"🧠 IA: {'ON' if state else 'OFF'}",
            fg="#00b894" if state else "#ff7675"
        )
    
    def open_script(self):
        path = filedialog.askopenfilename(
            title="Sélectionner un script Python",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if path:
            self.script_path = path
            self.path_label.config(text=f"📁 {path}")
            self.log_message(f"📄 Script chargé: {os.path.basename(path)}", "success")
            
            # 🔍 SCAN AUTO DES DÉPENDANCES AU CHARGEMENT
            self.log_message("🔍 Scan des dépendances en cours...", "warning")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                missing = self.dependency_checker.scan_code(code)
                report = self.dependency_checker.generate_fix_suggestions(missing)
                
                self.dep_analysis.delete(1.0, tk.END)
                if missing:
                    self.dep_analysis.insert(tk.END, report, "missing")
                    self.log_message(f"⚠️  {len(missing)} module(s) manquant(s) détecté(s)", "error")
                else:
                    self.dep_analysis.insert(tk.END, report, "ok")
                    self.log_message("✅ Toutes les dépendances sont installées", "success")
            except Exception as e:
                self.log_message(f"❌ Erreur scan dépendances: {e}", "error")
    
    def run_script(self):
        if not self.script_path:
            messagebox.showwarning("⚠️ Attention", "Aucun script chargé !")
            return
        
        self.log_message(f"\n{'='*70}", "success")
        self.log_message(f"🚀 Exécution: {os.path.basename(self.script_path)}", "success")
        self.log_message(f"{'='*70}\n", "success")
        
        # Réinitialiser l'analyse IA
        self.ai_analysis.delete(1.0, tk.END)
        self.ai_analysis.insert(tk.END, "🧠 En attente d'une erreur à analyser...\n", "header")
        
        # Exécution dans un thread séparé
        threading.Thread(target=self._execute_script, daemon=True).start()
    
    def _execute_script(self):
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Lecture en temps réel
            for line in self.process.stdout:
                self.log_message(line.rstrip())
            
            # Récupération des erreurs
            stderr = self.process.stderr.read()
            if stderr:
                self.log_message("\n" + "="*70, "error")
                self.log_message("❌ ERREURS DÉTECTÉES", "error")
                self.log_message("="*70 + "\n", "error")
                
                for line in stderr.splitlines():
                    self.log_message(line, "error")
                
                # 🧠 ANALYSE AI DE L'ERREUR
                self._analyze_error(stderr)
            
            returncode = self.process.wait()
            status = "✅ Terminé avec succès" if returncode == 0 else f"⚠️  Code retour: {returncode}"
            self.log_message(f"\n{status}", "success" if returncode == 0 else "warning")
            
        except Exception as e:
            self.log_message(f"\n💥 Exception debugger: {e}", "error")
            self.log_message(traceback.format_exc(), "error")
        finally:
            self.process = None
    
    def _analyze_error(self, stderr: str):
        """Analyse l'erreur avec l'IA embarquée"""
        try:
            # Extraction des éléments clés
            lines = stderr.splitlines()
            error_line = None
            tb_lines = []
            
            for line in lines:
                if "Error:" in line or "Exception:" in line:
                    error_line = line.strip()
                if line.strip().startswith("File "):
                    tb_lines.append(line.strip())
            
            if not error_line:
                return
            
            # Parsing basique
            match = re.search(r'(\w+Error|\w+Exception): (.+)', error_line)
            if match:
                error_type = match.group(1)
                error_msg = match.group(2)
            else:
                error_type = "UnknownError"
                error_msg = error_line
            
            # Appel à l'IA embarquée
            analysis = self.ai_analyzer.analyze(error_type, error_msg, tb_lines)
            
            # Affichage dans le panneau AI
            self.ai_analysis.delete(1.0, tk.END)
            self.ai_analysis.insert(tk.END, "🧠 ANALYSE IA EMBARQUÉE\n", "header")
            self.ai_analysis.insert(tk.END, "="*70 + "\n\n")
            self.ai_analysis.insert(tk.END, f"Statut: {analysis['ai_status']}\n\n")
            self.ai_analysis.insert(tk.END, f"🔍 Cause probable:\n   {analysis['analysis']}\n\n")
            self.ai_analysis.insert(tk.END, f"💡 Suggestion de correction:\n   {analysis['suggestion']}\n\n")
            if 'confidence' in analysis:
                self.ai_analysis.insert(tk.END, f"📊 Confiance: {analysis['confidence']}\n")
            
            self.log_message(f"🧠 Analyse IA terminée → Voir l'onglet 'Analyse IA'", "ai")
            
        except Exception as e:
            self.log_message(f"❌ Erreur analyse IA: {e}", "error")
    
    def stop_script(self):
        if self.process:
            self.process.terminate()
            self.log_message("⏹️  Script stoppé par l'utilisateur", "warning")
            self.process = None
    
    def clear_logs(self):
        self.console.delete(1.0, tk.END)
        self.log_message("🗑️  Console vidée", "success")


# ============================================================================
# 🚀 POINT D'ENTRÉE
# ============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDebugger(root)
    
    # Style global
    root.tk_setPalette(background="#0a0e17", foreground="#f7f9fc")
    
    # Icône (optionnel)
    try:
        root.iconbitmap("kerberos.ico")  # À créer si désiré
    except:
        pass
    
    root.mainloop()