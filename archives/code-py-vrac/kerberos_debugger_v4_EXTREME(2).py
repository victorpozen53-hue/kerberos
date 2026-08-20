# -*- coding: utf-8 -*-
"""
🐺 KERBEROS DEBUGGER v4.0 - Débogueur Python Ultime Édition EXTREME
====================================================================
Fonctionnalités ULTIMES :
- 🔍 Recherche d'erreurs multi-format (Python, CSV, JSON, TXT)
- 🚀 Exécution de scripts Python avec capture complète
- 📝 Éditeur de code avec coloration syntaxique avancée
- 🔧 Traceback amélioré avec contexte et suggestions IA
- 👁️ Surveillance de fichiers (auto-reload)
- 🎯 Correction assistée par IA (suggestions intelligentes)
- 📊 Analyse statique (détection d'erreurs sans exécution)
- 💾 Historique des exécutions
- 🎨 Interface dark cyberpunk personnalisable
- 🔴 BREAKPOINTS VISUELS (clic gauche sur numéro de ligne)
- ⏯️  MODE STEP-BY-STEP (exécution ligne par ligne)
- 📈 PROFILEUR DE PERFORMANCE (temps d'exécution par ligne)
- 🖥️ TERMINAL INTÉGRÉ (exécute bash, pip, git...)
- 🎨 THÈMES PERSONNALISABLES (Matrix, Cyberpunk, Nord, Dracula...)
- 🤖 AUTO-CORRECTION IA (propose le code corrigé)
- 📊 GRAPHIQUES DE PERFORMANCE EN TEMPS RÉEL
- 📤 EXPORT HTML/PDF des rapports
- 🔬 ANALYSE MÉMOIRE (détection de fuites)
- 🌐 EXÉCUTION DANS VENV (environnements virtuels)

Licence : GPLv3 modifiée – Victor Pozen 🐺
"""

import os
import sys
import re
import ast
import subprocess
import threading
import time
import traceback as tb_module
import cProfile
import pstats
import io
import json
from pathlib import Path
from datetime import datetime
from collections import deque, defaultdict
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, colorchooser, simpledialog
from tkinter.font import Font
import importlib.util

# ============================================================
# THÈMES DE COULEURS
# ============================================================

THEMES = {
    "Cyberpunk": {
        "bg": "#1a1a1a",
        "fg": "#e0e0e0",
        "accent": "#00ffcc",
        "error": "#ff5252",
        "success": "#4CAF50",
        "warning": "#ff9800",
        "info": "#00bcd4",
        "editor_bg": "#0d0d0d",
        "console_bg": "#0d0d0d",
        "button_bg": "#2d5a2d",
        "keyword": "#bb86fc",
        "builtin": "#4fc3f7",
        "string": "#4CAF50",
        "comment": "#666666",
        "number": "#ff9800",
    },
    "Matrix": {
        "bg": "#0d0d0d",
        "fg": "#00ff00",
        "accent": "#00ff00",
        "error": "#ff0000",
        "success": "#00ff00",
        "warning": "#ffff00",
        "info": "#00ffff",
        "editor_bg": "#000000",
        "console_bg": "#000000",
        "button_bg": "#003300",
        "keyword": "#00ff00",
        "builtin": "#00cc00",
        "string": "#00ff00",
        "comment": "#006600",
        "number": "#00ff00",
    },
    "Dracula": {
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "accent": "#ff79c6",
        "error": "#ff5555",
        "success": "#50fa7b",
        "warning": "#ffb86c",
        "info": "#8be9fd",
        "editor_bg": "#1e1f29",
        "console_bg": "#1e1f29",
        "button_bg": "#44475a",
        "keyword": "#ff79c6",
        "builtin": "#8be9fd",
        "string": "#f1fa8c",
        "comment": "#6272a4",
        "number": "#bd93f9",
    },
    "Nord": {
        "bg": "#2e3440",
        "fg": "#eceff4",
        "accent": "#88c0d0",
        "error": "#bf616a",
        "success": "#a3be8c",
        "warning": "#ebcb8b",
        "info": "#81a1c1",
        "editor_bg": "#3b4252",
        "console_bg": "#3b4252",
        "button_bg": "#4c566a",
        "keyword": "#81a1c1",
        "builtin": "#88c0d0",
        "string": "#a3be8c",
        "comment": "#616e88",
        "number": "#b48ead",
    },
    "Monokai": {
        "bg": "#272822",
        "fg": "#f8f8f2",
        "accent": "#66d9ef",
        "error": "#f92672",
        "success": "#a6e22e",
        "warning": "#e6db74",
        "info": "#66d9ef",
        "editor_bg": "#1e1f1c",
        "console_bg": "#1e1f1c",
        "button_bg": "#49483e",
        "keyword": "#f92672",
        "builtin": "#66d9ef",
        "string": "#e6db74",
        "comment": "#75715e",
        "number": "#ae81ff",
    },
    "Solarized Dark": {
        "bg": "#002b36",
        "fg": "#839496",
        "accent": "#2aa198",
        "error": "#dc322f",
        "success": "#859900",
        "warning": "#b58900",
        "info": "#268bd2",
        "editor_bg": "#073642",
        "console_bg": "#073642",
        "button_bg": "#586e75",
        "keyword": "#268bd2",
        "builtin": "#2aa198",
        "string": "#859900",
        "comment": "#586e75",
        "number": "#d33682",
    }
}

# ============================================================
# ANALYSEUR STATIQUE D'ERREURS
# ============================================================

class StaticAnalyzer:
    """Analyse le code Python sans l'exécuter pour détecter les erreurs"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def analyze(self, code, filename="<string>"):
        """Analyse statique du code"""
        self.errors.clear()
        self.warnings.clear()
        
        # 1. Vérifier la syntaxe
        try:
            ast.parse(code, filename)
        except SyntaxError as e:
            self.errors.append({
                "type": "SyntaxError",
                "line": e.lineno,
                "msg": e.msg,
                "text": e.text,
                "offset": e.offset
            })
            return False
        
        # 2. Détection de patterns dangereux
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            # Variables non utilisées après assignation
            if re.match(r'^\s*([a-zA-Z_]\w*)\s*=\s*.+$', line):
                var_name = re.match(r'^\s*([a-zA-Z_]\w*)', line).group(1)
                # Vérifier si utilisé après
                used = False
                for j in range(i, len(lines)):
                    if var_name in lines[j] and '=' not in lines[j].split(var_name)[0]:
                        used = True
                        break
                if not used and var_name not in ['_', '__']:
                    self.warnings.append({
                        "type": "UnusedVariable",
                        "line": i,
                        "msg": f"Variable '{var_name}' assignée mais jamais utilisée",
                        "severity": "low"
                    })
            
            # Imports inutilisés (simple détection)
            if re.match(r'^\s*import\s+(\w+)', line):
                module = re.match(r'^\s*import\s+(\w+)', line).group(1)
                if module not in '\n'.join(lines[i:]):
                    self.warnings.append({
                        "type": "UnusedImport",
                        "line": i,
                        "msg": f"Module '{module}' importé mais jamais utilisé",
                        "severity": "low"
                    })
            
            # Division par zéro évidente
            if re.search(r'/\s*0(?!\d)', line):
                self.warnings.append({
                    "type": "DivisionByZero",
                    "line": i,
                    "msg": "Division par zéro détectée",
                    "severity": "high"
                })
            
            # Comparaison avec None (mauvaise pratique)
            if re.search(r'==\s*None|None\s*==', line):
                self.warnings.append({
                    "type": "ComparisonWithNone",
                    "line": i,
                    "msg": "Utilise 'is None' au lieu de '== None'",
                    "severity": "medium"
                })
        
        return len(self.errors) == 0
    
    def get_report(self):
        """Génère un rapport lisible"""
        report = []
        if self.errors:
            report.append("🔴 ERREURS CRITIQUES :")
            for err in self.errors:
                report.append(f"  Ligne {err['line']}: {err['type']} - {err['msg']}")
                if err.get('text'):
                    report.append(f"    {err['text'].strip()}")
                    if err.get('offset'):
                        report.append(f"    {' ' * (err['offset'] - 1)}^")
        
        if self.warnings:
            report.append("\n⚠️  AVERTISSEMENTS :")
            # Grouper par sévérité
            high = [w for w in self.warnings if w.get('severity') == 'high']
            medium = [w for w in self.warnings if w.get('severity') == 'medium']
            low = [w for w in self.warnings if w.get('severity') == 'low']
            
            for w in high:
                report.append(f"  🔸 Ligne {w['line']}: {w['msg']}")
            for w in medium:
                report.append(f"  🔹 Ligne {w['line']}: {w['msg']}")
            for w in low:
                report.append(f"  ▫️  Ligne {w['line']}: {w['msg']}")
        
        return '\n'.join(report) if report else "✅ Aucune erreur détectée"


# ============================================================
# PROFILEUR DE PERFORMANCE
# ============================================================

class PerformanceProfiler:
    """Profile les performances du code Python"""
    
    def __init__(self):
        self.profiler = None
        self.stats = None
        self.line_timings = {}
    
    def start(self):
        """Démarrer le profilage"""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
    
    def stop(self):
        """Arrêter le profilage"""
        if self.profiler:
            self.profiler.disable()
    
    def get_stats(self, limit=20):
        """Obtenir les statistiques formatées"""
        if not self.profiler:
            return "Aucun profilage effectué"
        
        stream = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.print_stats(limit)
        
        return stream.getvalue()
    
    def get_top_functions(self, limit=10):
        """Obtenir les fonctions les plus lentes"""
        if not self.profiler:
            return []
        
        stats = pstats.Stats(self.profiler)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        
        results = []
        for func, (cc, nc, tt, ct, callers) in list(stats.stats.items())[:limit]:
            filename, line, func_name = func
            results.append({
                "function": func_name,
                "file": filename,
                "line": line,
                "calls": nc,
                "total_time": tt,
                "cumulative_time": ct
            })
        
        return results


# ============================================================
# GESTIONNAIRE DE BREAKPOINTS
# ============================================================

class BreakpointManager:
    """Gère les breakpoints visuels"""
    
    def __init__(self):
        self.breakpoints = set()  # Numéros de lignes
        self.enabled = True
    
    def toggle(self, line_num):
        """Activer/désactiver un breakpoint"""
        if line_num in self.breakpoints:
            self.breakpoints.remove(line_num)
            return False
        else:
            self.breakpoints.add(line_num)
            return True
    
    def clear_all(self):
        """Supprimer tous les breakpoints"""
        self.breakpoints.clear()
    
    def has_breakpoint(self, line_num):
        """Vérifier si une ligne a un breakpoint"""
        return line_num in self.breakpoints
    
    def get_all(self):
        """Obtenir tous les breakpoints"""
        return sorted(self.breakpoints)


# ============================================================
# ÉDITEUR DE CODE AVEC COLORATION SYNTAXIQUE
# ============================================================

class CodeEditor(scrolledtext.ScrolledText):
    """Éditeur de code avec coloration syntaxique Python et breakpoints"""
    
    def __init__(self, master, breakpoint_manager=None, theme=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.breakpoint_manager = breakpoint_manager
        self.theme = theme or THEMES["Cyberpunk"]
        
        # Configuration de base
        self.configure(
            wrap=tk.NONE,
            undo=True,
            maxundo=-1,
            font=("Consolas", 10),
            bg=self.theme["editor_bg"],
            fg=self.theme["fg"],
            insertbackground=self.theme["accent"],
            selectbackground="#3a3a3a",
            selectforeground="#ffffff",
            tabs=('1c',)  # 4 espaces
        )
        
        # Numérotation des lignes avec support breakpoints
        self.line_numbers = tk.Canvas(master, width=50, bg="#1a1a1a", highlightthickness=0)
        self.line_numbers.bind('<Button-1>', self.on_line_click)
        
        # Tags de coloration
        self.tag_configure("keyword", foreground=self.theme["keyword"])
        self.tag_configure("builtin", foreground=self.theme["builtin"])
        self.tag_configure("string", foreground=self.theme["string"])
        self.tag_configure("comment", foreground=self.theme["comment"], font=("Consolas", 10, "italic"))
        self.tag_configure("number", foreground=self.theme["number"])
        self.tag_configure("decorator", foreground="#ffcc00")
        self.tag_configure("class", foreground="#e91e63")
        self.tag_configure("function", foreground="#00bcd4")
        self.tag_configure("error_line", background="#3d1f1f")
        self.tag_configure("current_line", background="#2d2d2d")
        
        # Patterns de coloration
        self.keywords = r'\b(def|class|if|elif|else|for|while|try|except|finally|with|as|import|from|return|yield|pass|break|continue|raise|assert|lambda|and|or|not|in|is|None|True|False|self|async|await)\b'
        self.builtins = r'\b(print|len|range|str|int|float|list|dict|tuple|set|open|input|type|isinstance|hasattr|getattr|setattr|dir|help|abs|min|max|sum|all|any|enumerate|zip|map|filter|sorted|reversed)\b'
        self.string_pattern = r'(""".*?"""|\'\'\'.*?\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
        self.comment_pattern = r'#.*?$'
        self.number_pattern = r'\b\d+\.?\d*\b'
        self.decorator_pattern = r'@\w+'
        self.class_pattern = r'\bclass\s+(\w+)'
        self.function_pattern = r'\bdef\s+(\w+)'
        
        # Bindings
        self.bind('<KeyRelease>', self.on_key_release)
        self.bind('<Tab>', self.insert_tab)
        self.bind('<Return>', self.auto_indent)
        self.bind('<Control-s>', lambda e: self.event_generate('<<Save>>'))
        self.bind('<Control-f>', lambda e: self.event_generate('<<Find>>'))
        self.bind('<Control-d>', self.duplicate_line)
        self.bind('<Control-slash>', self.toggle_comment)
        
        # Mise à jour initiale
        self.after(100, self.update_line_numbers)
    
    def apply_theme(self, theme):
        """Appliquer un nouveau thème"""
        self.theme = theme
        self.configure(
            bg=self.theme["editor_bg"],
            fg=self.theme["fg"],
            insertbackground=self.theme["accent"]
        )
        
        # Reconfigurer les tags
        self.tag_configure("keyword", foreground=self.theme["keyword"])
        self.tag_configure("builtin", foreground=self.theme["builtin"])
        self.tag_configure("string", foreground=self.theme["string"])
        self.tag_configure("comment", foreground=self.theme["comment"])
        self.tag_configure("number", foreground=self.theme["number"])
        
        self.highlight_syntax()
    
    def on_line_click(self, event):
        """Gestion du clic sur numéro de ligne (toggle breakpoint)"""
        if not self.breakpoint_manager:
            return
        
        # Calculer le numéro de ligne cliqué
        y = event.y
        line_height = self.line_numbers.winfo_height() / int(self.index('end-1c').split('.')[0])
        line_num = int(y / line_height) + 1
        
        # Toggle breakpoint
        is_active = self.breakpoint_manager.toggle(line_num)
        self.update_line_numbers()
        
        return is_active
    
    def insert_tab(self, event):
        """Insérer 4 espaces au lieu de tab"""
        self.insert(tk.INSERT, "    ")
        return "break"
    
    def auto_indent(self, event):
        """Auto-indentation intelligente"""
        # Récupérer la ligne actuelle
        line = self.get("insert linestart", "insert lineend")
        indent = len(line) - len(line.lstrip())
        
        # Si la ligne se termine par ':', ajouter une indentation
        if line.rstrip().endswith(':'):
            indent += 4
        
        self.insert(tk.INSERT, '\n' + ' ' * indent)
        return "break"
    
    def duplicate_line(self, event):
        """Dupliquer la ligne courante (Ctrl+D)"""
        line = self.get("insert linestart", "insert lineend")
        self.insert("insert lineend", '\n' + line)
        return "break"
    
    def toggle_comment(self, event):
        """Commenter/décommenter la ligne (Ctrl+/)"""
        line_start = self.index("insert linestart")
        line_end = self.index("insert lineend")
        line = self.get(line_start, line_end)
        
        if line.lstrip().startswith('#'):
            # Décommenter
            new_line = line.replace('#', '', 1)
        else:
            # Commenter
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + '# ' + line.lstrip()
        
        self.delete(line_start, line_end)
        self.insert(line_start, new_line)
        return "break"
    
    def on_key_release(self, event):
        """Mise à jour après frappe"""
        if event.keysym not in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R'):
            self.after_idle(self.highlight_syntax)
            self.after_idle(self.update_line_numbers)
    
    def highlight_syntax(self):
        """Coloration syntaxique"""
        # Retirer tous les tags
        for tag in ('keyword', 'builtin', 'string', 'comment', 'number', 'decorator', 'class', 'function'):
            self.tag_remove(tag, "1.0", tk.END)
        
        content = self.get("1.0", tk.END)
        
        # Commentaires (en premier pour éviter la coloration dans les commentaires)
        for match in re.finditer(self.comment_pattern, content, re.MULTILINE):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.tag_add("comment", start_idx, end_idx)
        
        # Strings
        for match in re.finditer(self.string_pattern, content, re.DOTALL):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.tag_add("string", start_idx, end_idx)
        
        # Keywords
        for match in re.finditer(self.keywords, content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.tag_add("keyword", start_idx, end_idx)
        
        # Builtins
        for match in re.finditer(self.builtins, content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.tag_add("builtin", start_idx, end_idx)
        
        # Numbers
        for match in re.finditer(self.number_pattern, content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.tag_add("number", start_idx, end_idx)
        
        # Decorators
        for match in re.finditer(self.decorator_pattern, content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.tag_add("decorator", start_idx, end_idx)
    
    def update_line_numbers(self):
        """Mise à jour de la numérotation avec breakpoints"""
        self.line_numbers.delete('all')
        
        line_count = int(self.index('end-1c').split('.')[0])
        
        for i in range(1, line_count):
            y = (i - 1) * 16 + 2  # 16px par ligne
            
            # Breakpoint ?
            if self.breakpoint_manager and self.breakpoint_manager.has_breakpoint(i):
                # Cercle rouge
                self.line_numbers.create_oval(5, y, 15, y+10, fill='#ff5252', outline='#ff0000')
            
            # Numéro de ligne
            color = '#00ffcc' if (self.breakpoint_manager and self.breakpoint_manager.has_breakpoint(i)) else '#666'
            self.line_numbers.create_text(25, y+5, text=str(i), anchor='w', 
                                         fill=color, font=("Consolas", 9))
    
    def highlight_error_line(self, line_num):
        """Surligner une ligne d'erreur"""
        self.tag_remove("error_line", "1.0", tk.END)
        self.tag_add("error_line", f"{line_num}.0", f"{line_num}.end")
        self.see(f"{line_num}.0")
    
    def highlight_current_line(self, line_num):
        """Surligner la ligne en cours d'exécution (mode step)"""
        self.tag_remove("current_line", "1.0", tk.END)
        if line_num:
            self.tag_add("current_line", f"{line_num}.0", f"{line_num}.end")
            self.see(f"{line_num}.0")


# ============================================================
# TERMINAL INTÉGRÉ
# ============================================================

class EmbeddedTerminal:
    """Terminal bash intégré dans l'interface"""
    
    def __init__(self, output_widget):
        self.output = output_widget
        self.process = None
        self.cwd = os.path.expanduser("~")
    
    def execute_command(self, command):
        """Exécuter une commande shell"""
        if command.strip().startswith('cd '):
            # Commande cd spéciale
            path = command.strip()[3:].strip()
            try:
                new_path = os.path.expanduser(path)
                if os.path.isdir(new_path):
                    self.cwd = new_path
                    self.output.insert(tk.END, f"📁 {self.cwd}\n", "success")
                else:
                    self.output.insert(tk.END, f"❌ Dossier introuvable : {path}\n", "error")
            except Exception as e:
                self.output.insert(tk.END, f"❌ Erreur : {e}\n", "error")
            return
        
        # Autres commandes
        try:
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.cwd
            )
            
            stdout, stderr = self.process.communicate(timeout=30)
            
            if stdout:
                self.output.insert(tk.END, stdout, "output")
            if stderr:
                self.output.insert(tk.END, stderr, "error")
            
            self.output.see(tk.END)
            
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.output.insert(tk.END, "⏱️ Timeout (30s)\n", "error")
        except Exception as e:
            self.output.insert(tk.END, f"❌ Erreur : {e}\n", "error")


# ============================================================
# DÉBOGUEUR PRINCIPAL
# ============================================================

class PythonDebugger:
    """Moteur de débogage Python avec mode step-by-step"""
    
    def __init__(self):
        self.process = None
        self.output_callback = None
        self.error_callback = None
        self.finish_callback = None
        self.current_file = None
        self.execution_history = deque(maxlen=50)
        self.profiler = PerformanceProfiler()
        self.step_mode = False
        self.current_step = 0
    
    def execute_code(self, code, filename="<editor>", args=None, profile=False):
        """Exécute du code Python et capture les sorties"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Sauvegarder dans l'historique
        self.execution_history.append({
            "timestamp": timestamp,
            "filename": filename,
            "code": code,
            "args": args or [],
            "profiled": profile
        })
        
        # Profiler ?
        if profile:
            self.profiler.start()
        
        # Créer un fichier temporaire
        temp_file = Path(f"/tmp/kerberos_debug_{int(time.time())}.py")
        temp_file.write_text(code, encoding='utf-8')
        
        # Préparer la commande
        cmd = [sys.executable, str(temp_file)]
        if args:
            cmd.extend(args)
        
        try:
            # Exécuter avec capture stdout/stderr
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Thread pour stdout
            def read_stdout():
                for line in iter(self.process.stdout.readline, ''):
                    if self.output_callback:
                        self.output_callback(line)
                self.process.stdout.close()
            
            # Thread pour stderr
            def read_stderr():
                stderr_content = []
                for line in iter(self.process.stderr.readline, ''):
                    stderr_content.append(line)
                    if self.output_callback:
                        self.output_callback(line, is_error=True)
                self.process.stderr.close()
                
                # Analyser les erreurs
                if stderr_content and self.error_callback:
                    full_error = ''.join(stderr_content)
                    self.error_callback(full_error, code, filename)
            
            # Lancer les threads
            threading.Thread(target=read_stdout, daemon=True).start()
            threading.Thread(target=read_stderr, daemon=True).start()
            
            # Attendre la fin
            def wait_finish():
                self.process.wait()
                
                # Arrêter le profiler
                if profile:
                    self.profiler.stop()
                
                if self.finish_callback:
                    self.finish_callback(self.process.returncode, profile)
                temp_file.unlink(missing_ok=True)
            
            threading.Thread(target=wait_finish, daemon=True).start()
            
            return True
            
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e), code, filename)
            temp_file.unlink(missing_ok=True)
            return False
    
    def stop_execution(self):
        """Arrêter l'exécution en cours"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
    
    def parse_traceback(self, error_text, code, filename):
        """Parse un traceback Python et extrait les informations"""
        lines = error_text.strip().split('\n')
        
        # Trouver la dernière ligne (message d'erreur)
        error_type = "UnknownError"
        error_msg = "Erreur inconnue"
        
        for line in reversed(lines):
            if ':' in line and not line.strip().startswith('File'):
                parts = line.split(':', 1)
                error_type = parts[0].strip()
                error_msg = parts[1].strip() if len(parts) > 1 else parts[0]
                break
        
        # Trouver le numéro de ligne
        line_num = None
        file_context = None
        
        for line in lines:
            if 'File' in line and 'line' in line:
                match = re.search(r'line (\d+)', line)
                if match:
                    line_num = int(match.group(1))
                    # Ligne suivante contient le code
                    idx = lines.index(line)
                    if idx + 1 < len(lines):
                        file_context = lines[idx + 1].strip()
        
        # Générer des suggestions
        suggestions = self.generate_suggestions(error_type, error_msg, file_context)
        
        # AUTO-CORRECTION IA
        auto_fix = self.generate_auto_fix(error_type, error_msg, file_context, code, line_num)
        
        return {
            "type": error_type,
            "message": error_msg,
            "line": line_num,
            "context": file_context,
            "full_traceback": error_text,
            "suggestions": suggestions,
            "auto_fix": auto_fix
        }
    
    def generate_auto_fix(self, error_type, error_msg, context, full_code, line_num):
        """Génère une correction automatique du code"""
        if not line_num or not context:
            return None
        
        lines = full_code.split('\n')
        if line_num > len(lines):
            return None
        
        error_line = lines[line_num - 1]
        fix = None
        
        # NameError: définir la variable
        if error_type == "NameError":
            var_match = re.search(r"name '(\w+)' is not defined", error_msg)
            if var_match:
                var_name = var_match.group(1)
                # Trouver l'indentation
                indent = len(error_line) - len(error_line.lstrip())
                fix = ' ' * indent + f"{var_name} = None  # 🤖 Auto-fix: Variable définie"
        
        # ZeroDivisionError: ajouter un check
        elif error_type == "ZeroDivisionError":
            indent = len(error_line) - len(error_line.lstrip())
            # Extraire le diviseur
            if '/' in error_line:
                parts = error_line.split('/')
                divisor = parts[1].strip().split()[0]
                fix = ' ' * indent + f"if {divisor} != 0:  # 🤖 Auto-fix: Check division par zéro\n"
                fix += ' ' * (indent + 4) + error_line.strip()
        
        # TypeError: conversion de type
        elif error_type == "TypeError" and "unsupported operand" in error_msg:
            # Essayer de détecter une conversion manquante
            if '+' in error_line:
                fix = error_line + "  # 🤖 Utilise str() pour convertir"
        
        return fix
    
    def generate_suggestions(self, error_type, error_msg, context):
        """Génère des suggestions de correction"""
        suggestions = []
        
        # NameError
        if error_type == "NameError":
            var_match = re.search(r"name '(\w+)' is not defined", error_msg)
            if var_match:
                var_name = var_match.group(1)
                suggestions.append(f"💡 Déclare la variable '{var_name}' avant de l'utiliser")
                suggestions.append(f"💡 Vérifie l'orthographe de '{var_name}'")
                suggestions.append(f"💡 Importe le module si c'est une fonction externe")
        
        # SyntaxError
        elif error_type == "SyntaxError":
            if "invalid syntax" in error_msg:
                suggestions.append("💡 Vérifie les parenthèses, crochets et guillemets")
                suggestions.append("💡 Vérifie l'indentation (4 espaces par niveau)")
            if "EOL while scanning" in error_msg:
                suggestions.append("💡 Il manque un guillemet fermant")
        
        # IndentationError
        elif error_type == "IndentationError":
            suggestions.append("💡 Utilise 4 espaces pour l'indentation (pas de tabulations)")
            suggestions.append("💡 Vérifie que tous les blocs sont correctement indentés")
        
        # AttributeError
        elif error_type == "AttributeError":
            suggestions.append("💡 L'objet n'a pas cet attribut/méthode")
            suggestions.append("💡 Utilise dir(objet) pour voir les attributs disponibles")
        
        # TypeError
        elif error_type == "TypeError":
            if "unsupported operand" in error_msg:
                suggestions.append("💡 Tu essaies d'opérer sur des types incompatibles")
                suggestions.append("💡 Convertis les valeurs au bon type (int, str, float)")
        
        # ImportError / ModuleNotFoundError
        elif error_type in ("ImportError", "ModuleNotFoundError"):
            module_match = re.search(r"No module named '(\w+)'", error_msg)
            if module_match:
                module = module_match.group(1)
                suggestions.append(f"💡 Installe le module : pip install {module}")
        
        # KeyError
        elif error_type == "KeyError":
            suggestions.append("💡 La clé n'existe pas dans le dictionnaire")
            suggestions.append("💡 Utilise .get(key, default) pour éviter l'erreur")
        
        # IndexError
        elif error_type == "IndexError":
            suggestions.append("💡 L'index est hors limites de la liste")
            suggestions.append("💡 Vérifie la longueur avec len() avant d'accéder")
        
        # ZeroDivisionError
        elif error_type == "ZeroDivisionError":
            suggestions.append("💡 Tu divises par zéro")
            suggestions.append("💡 Vérifie que le diviseur n'est pas égal à 0")
        
        return suggestions


# ============================================================
# APPLICATION PRINCIPALE
# ============================================================

class KerberosDebuggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🐺 Kerberos Debugger v4.0 EXTREME - Débogueur Python Ultime")
        self.root.geometry("1600x950")
        
        # Managers
        self.debugger = PythonDebugger()
        self.analyzer = StaticAnalyzer()
        self.breakpoint_manager = BreakpointManager()
        self.current_file = None
        self.is_executing = False
        self.file_watcher = None
        self.watch_active = False
        self.current_theme_name = "Cyberpunk"
        self.current_theme = THEMES[self.current_theme_name]
        
        # Appliquer le thème à la fenêtre principale
        self.root.configure(bg=self.current_theme["bg"])
        
        # Style
        self.setup_style()
        
        # Interface
        self.create_menu()
        self.create_notebook()
        
        # Callbacks du débogueur
        self.debugger.output_callback = self.on_output
        self.debugger.error_callback = self.on_error
        self.debugger.finish_callback = self.on_finish
        
        # Raccourcis clavier
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<F5>', lambda e: self.run_code())
        self.root.bind('<F6>', lambda e: self.analyze_code())
        self.root.bind('<F7>', lambda e: self.run_with_profiling())
        self.root.bind('<F9>', lambda e: self.toggle_breakpoint_current_line())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
        # Terminal intégré
        self.terminal = None
        
        # Statusbar
        self.create_statusbar()
    
    def create_statusbar(self):
        """Barre de statut en bas"""
        statusbar = tk.Frame(self.root, bg=self.current_theme["bg"], height=25)
        statusbar.pack(side="bottom", fill="x", padx=5, pady=2)
        
        self.status_file = tk.Label(statusbar, text="📄 Aucun fichier", bg=self.current_theme["bg"], 
                                    fg=self.current_theme["accent"], font=("Consolas", 9), anchor="w")
        self.status_file.pack(side="left", padx=10)
        
        self.status_theme = tk.Label(statusbar, text=f"🎨 {self.current_theme_name}", bg=self.current_theme["bg"],
                                     fg=self.current_theme["fg"], font=("Consolas", 9))
        self.status_theme.pack(side="right", padx=10)
        
        self.status_line = tk.Label(statusbar, text="Ligne: 1, Col: 0", bg=self.current_theme["bg"],
                                   fg=self.current_theme["fg"], font=("Consolas", 9))
        self.status_line.pack(side="right", padx=10)
    
    def setup_style(self):
        """Configuration du style"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        
        # Widgets standards
        style.configure("TLabel", background="#1a1a1a", foreground="#e0e0e0", font=("Consolas", 10))
        style.configure("TButton", background="#2d5a2d", foreground="white", font=("Consolas", 10, "bold"), padding=8)
        style.map("TButton", background=[("active", "#3a7a3a")])
        style.configure("Danger.TButton", background="#8b2828", foreground="white")
        style.map("Danger.TButton", background=[("active", "#a83232")])
        style.configure("TNotebook", background="#1a1a1a", borderwidth=0)
        style.configure("TNotebook.Tab", background="#2d2d2d", foreground="#e0e0e0", padding=[20, 10])
        style.map("TNotebook.Tab", background=[("selected", "#3a3a3a")], foreground=[("selected", "#00ffcc")])
        style.configure("TFrame", background="#1a1a1a")
        style.configure("TCheckbutton", background="#1a1a1a", foreground="#bb86fc")
    
    def create_menu(self):
        """Barre de menu améliorée"""
        menubar = tk.Menu(self.root, bg="#2d2d2d", fg="#e0e0e0", activebackground="#3a3a3a")
        self.root.config(menu=menubar)
        
        # Fichier
        file_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="📁 Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau (Ctrl+N)", command=self.new_file)
        file_menu.add_command(label="Ouvrir (Ctrl+O)", command=self.open_file)
        file_menu.add_command(label="Sauvegarder (Ctrl+S)", command=self.save_file)
        file_menu.add_command(label="Sauvegarder sous...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exporter rapport HTML", command=self.export_html_report)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter (Ctrl+Q)", command=self.root.quit)
        
        # Édition
        edit_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="✏️ Édition", menu=edit_menu)
        edit_menu.add_command(label="Dupliquer ligne (Ctrl+D)", command=lambda: self.code_editor.event_generate('<Control-d>'))
        edit_menu.add_command(label="Commenter/Décommenter (Ctrl+/)", command=lambda: self.code_editor.event_generate('<Control-slash>'))
        edit_menu.add_separator()
        edit_menu.add_command(label="Rechercher (Ctrl+F)", command=self.show_find_dialog)
        edit_menu.add_command(label="Remplacer (Ctrl+H)", command=self.show_replace_dialog)
        
        # Exécution
        run_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="▶️ Exécution", menu=run_menu)
        run_menu.add_command(label="Exécuter (F5)", command=self.run_code)
        run_menu.add_command(label="Exécuter avec profilage (F7)", command=self.run_with_profiling)
        run_menu.add_command(label="Analyser statiquement (F6)", command=self.analyze_code)
        run_menu.add_command(label="Arrêter", command=self.stop_code)
        run_menu.add_separator()
        run_menu.add_command(label="Vider la console", command=self.clear_console)
        run_menu.add_separator()
        run_menu.add_command(label="Configurer arguments...", command=self.configure_args)
        
        # Débogage
        debug_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="🐛 Débogage", menu=debug_menu)
        debug_menu.add_command(label="Toggle Breakpoint (F9)", command=self.toggle_breakpoint_current_line)
        debug_menu.add_command(label="Supprimer tous les breakpoints", command=self.clear_all_breakpoints)
        debug_menu.add_command(label="Liste des breakpoints", command=self.show_breakpoints_list)
        debug_menu.add_separator()
        debug_menu.add_command(label="Auto-correction IA", command=self.apply_auto_fix)
        
        # Outils
        tools_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="🔧 Outils", menu=tools_menu)
        tools_menu.add_command(label="Recherche d'erreurs", command=lambda: self.notebook.select(1))
        tools_menu.add_command(label="Historique", command=self.show_history)
        tools_menu.add_command(label="Terminal intégré", command=lambda: self.notebook.select(3))
        tools_menu.add_separator()
        self.watch_var = tk.BooleanVar(value=False)
        tools_menu.add_checkbutton(label="👁️ Surveillance auto", variable=self.watch_var, command=self.toggle_watch)
        tools_menu.add_separator()
        tools_menu.add_command(label="Rapport de performance", command=self.show_performance_report)
        
        # Apparence
        appearance_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="🎨 Thème", menu=appearance_menu)
        for theme_name in THEMES.keys():
            appearance_menu.add_command(label=theme_name, command=lambda t=theme_name: self.change_theme(t))
        appearance_menu.add_separator()
        appearance_menu.add_command(label="Personnaliser les couleurs...", command=self.customize_colors)
        
        # Aide
        help_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="❓ Aide", menu=help_menu)
        help_menu.add_command(label="Raccourcis clavier", command=self.show_shortcuts)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_separator()
        help_menu.add_command(label="À propos", command=self.show_about)
    
    def create_notebook(self):
        """Onglets principaux améliorés"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        # Onglet 1: Débogueur
        self.create_debugger_tab()
        
        # Onglet 2: Recherche d'erreurs
        self.create_search_tab()
        
        # Onglet 3: Historique
        self.create_history_tab()
        
        # Onglet 4: Terminal intégré (NOUVEAU!)
        self.create_terminal_tab()
    
    def create_debugger_tab(self):
        """Onglet débogueur amélioré"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🚀 Débogueur")
        
        # PanedWindow vertical
        paned = tk.PanedWindow(frame, orient=tk.VERTICAL, bg=self.current_theme["bg"], sashwidth=5, sashrelief=tk.RAISED)
        paned.pack(fill="both", expand=True)
        
        # === PARTIE HAUTE: ÉDITEUR ===
        editor_container = ttk.Frame(paned)
        paned.add(editor_container, height=500)
        
        # Barre d'outils améliorée
        toolbar = ttk.Frame(editor_container)
        toolbar.pack(fill="x", pady=(0, 5))
        
        # Fichier actuel
        self.file_label = tk.Label(toolbar, text="📄 Aucun fichier", bg=self.current_theme["bg"], 
                                   fg=self.current_theme["accent"], font=("Consolas", 10, "bold"), anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # Boutons
        ttk.Button(toolbar, text="📂 Ouvrir", command=self.open_file, width=12).pack(side="left", padx=2)
        ttk.Button(toolbar, text="💾 Sauver", command=self.save_file, width=12).pack(side="left", padx=2)
        ttk.Button(toolbar, text="▶️ Run (F5)", command=self.run_code, width=14).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📊 Profile (F7)", command=self.run_with_profiling, width=16).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔍 Analyse (F6)", command=self.analyze_code, width=16).pack(side="left", padx=2)
        ttk.Button(toolbar, text="⏹️ Stop", command=self.stop_code, style="Danger.TButton", width=12).pack(side="left", padx=2)
        
        # Arguments
        arg_frame = ttk.Frame(toolbar)
        arg_frame.pack(side="right", padx=5)
        tk.Label(arg_frame, text="Args:", bg=self.current_theme["bg"], fg=self.current_theme["fg"], 
                font=("Consolas", 9)).pack(side="left")
        self.args_entry = tk.Entry(arg_frame, width=20, bg=self.current_theme["editor_bg"], 
                                   fg=self.current_theme["accent"], font=("Consolas", 9))
        self.args_entry.pack(side="left", padx=5)
        
        # Éditeur + numéros de lignes avec breakpoints
        editor_frame = ttk.Frame(editor_container)
        editor_frame.pack(fill="both", expand=True)
        
        self.code_editor = CodeEditor(editor_frame, height=20, 
                                     breakpoint_manager=self.breakpoint_manager,
                                     theme=self.current_theme)
        self.code_editor.line_numbers.pack(side="left", fill="y")
        self.code_editor.pack(side="right", fill="both", expand=True)
        
        # Binding pour mise à jour position curseur
        self.code_editor.bind('<KeyRelease>', self.update_cursor_position)
        self.code_editor.bind('<ButtonRelease-1>', self.update_cursor_position)
        
        # Code d'exemple
        example_code = '''# 🐺 Kerberos Debugger v4.0 EXTREME Edition
# Écris ton code ici et appuie sur F5 pour l'exécuter !
# F9 sur une ligne = toggle breakpoint 🔴
# F7 = exécution avec profilage de performance 📊

def saluer(nom):
    """Fonction de salutation"""
    message = f"Bonjour {nom} ! 👋"
    return message

# Essaye les nouvelles fonctionnalités :
nom_utilisateur = "Victor"
print(saluer(nom_utilisateur))

# 1. Clique sur le numéro de ligne pour ajouter un breakpoint 🔴
# 2. Appuie sur F7 pour voir les performances
# 3. Décommenter une erreur ci-dessous pour voir l'auto-correction IA

# Exemples d'erreurs avec auto-fix :
# print(variable_inexistante)  # NameError → IA propose de définir la variable
# resultat = 10 / 0  # ZeroDivisionError → IA propose un check
# somme = "texte" + 42  # TypeError → IA propose str()

print("✅ Tout fonctionne ! Essaye les breakpoints et le profilage.")
'''
        self.code_editor.insert("1.0", example_code)
        self.code_editor.highlight_syntax()
        self.code_editor.update_line_numbers()
        
        # === PARTIE BASSE: CONSOLE + ANALYSE ===
        bottom_container = ttk.Frame(paned)
        paned.add(bottom_container, height=300)
        
        # Sous-onglets
        bottom_notebook = ttk.Notebook(bottom_container)
        bottom_notebook.pack(fill="both", expand=True)
        
        # Console de sortie
        console_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(console_frame, text="📟 Console")
        
        # Barre de statut console
        console_status = ttk.Frame(console_frame)
        console_status.pack(fill="x", pady=(0, 5))
        self.status_label = tk.Label(console_status, text="⚪ Prêt", bg=self.current_theme["bg"], 
                                     fg=self.current_theme["success"], font=("Consolas", 9, "bold"), anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        ttk.Button(console_status, text="🗑️ Vider", command=self.clear_console, width=10).pack(side="right")
        
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, font=("Consolas", 9),
                                                bg=self.current_theme["console_bg"], fg=self.current_theme["fg"], height=15)
        self.console.pack(fill="both", expand=True)
        self.console.tag_configure("output", foreground=self.current_theme["fg"])
        self.console.tag_configure("error", foreground=self.current_theme["error"])
        self.console.tag_configure("success", foreground=self.current_theme["success"])
        self.console.tag_configure("info", foreground=self.current_theme["info"])
        
        # Analyse statique
        analysis_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(analysis_frame, text="🔍 Analyse statique")
        
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD, font=("Consolas", 9),
                                                      bg=self.current_theme["console_bg"], fg="#ffcc00", height=15)
        self.analysis_text.pack(fill="both", expand=True, pady=5)
        self.analysis_text.tag_configure("error", foreground=self.current_theme["error"], font=("Consolas", 9, "bold"))
        self.analysis_text.tag_configure("warning", foreground=self.current_theme["warning"])
        self.analysis_text.tag_configure("success", foreground=self.current_theme["success"])
        
        # Traceback détaillé avec auto-fix
        traceback_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(traceback_frame, text="🐛 Traceback + Auto-Fix")
        
        # Bouton appliquer auto-fix
        autofix_bar = ttk.Frame(traceback_frame)
        autofix_bar.pack(fill="x", pady=(0, 5))
        tk.Label(autofix_bar, text="🤖 Auto-correction IA :", bg=self.current_theme["bg"],
                fg=self.current_theme["accent"], font=("Consolas", 9, "bold")).pack(side="left", padx=10)
        ttk.Button(autofix_bar, text="✨ Appliquer la correction", command=self.apply_auto_fix).pack(side="left", padx=5)
        ttk.Button(autofix_bar, text="📋 Copier le code corrigé", command=self.copy_auto_fix).pack(side="left", padx=5)
        
        self.traceback_text = scrolledtext.ScrolledText(traceback_frame, wrap=tk.WORD, font=("Consolas", 9),
                                                       bg=self.current_theme["console_bg"], 
                                                       fg=self.current_theme["error"], height=15)
        self.traceback_text.pack(fill="both", expand=True, pady=5)
        self.traceback_text.tag_configure("suggestion", foreground=self.current_theme["accent"], 
                                         font=("Consolas", 9, "bold"))
        self.traceback_text.tag_configure("line", foreground="#ffcc00", background="#3d1f1f")
        self.traceback_text.tag_configure("autofix", foreground=self.current_theme["success"], 
                                         font=("Consolas", 9, "bold"))
        
        # Performance (NOUVEAU!)
        perf_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(perf_frame, text="📊 Performance")
        
        perf_toolbar = ttk.Frame(perf_frame)
        perf_toolbar.pack(fill="x", pady=(0, 5))
        tk.Label(perf_toolbar, text="⏱️ Profilage de performance", bg=self.current_theme["bg"],
                fg=self.current_theme["info"], font=("Consolas", 10, "bold")).pack(side="left", padx=10)
        ttk.Button(perf_toolbar, text="📈 Graphique", command=self.show_performance_graph).pack(side="right", padx=5)
        ttk.Button(perf_toolbar, text="💾 Exporter CSV", command=self.export_performance_csv).pack(side="right", padx=5)
        
        self.perf_text = scrolledtext.ScrolledText(perf_frame, wrap=tk.WORD, font=("Consolas", 9),
                                                   bg=self.current_theme["console_bg"], 
                                                   fg=self.current_theme["info"], height=15)
        self.perf_text.pack(fill="both", expand=True, pady=5)
        self.perf_text.tag_configure("fast", foreground=self.current_theme["success"])
        self.perf_text.tag_configure("slow", foreground=self.current_theme["warning"])
        self.perf_text.tag_configure("critical", foreground=self.current_theme["error"], 
                                    font=("Consolas", 9, "bold"))
        
        # Breakpoints (NOUVEAU!)
        bp_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(bp_frame, text="🔴 Breakpoints")
        
        bp_toolbar = ttk.Frame(bp_frame)
        bp_toolbar.pack(fill="x", pady=(0, 5))
        tk.Label(bp_toolbar, text="🔴 Breakpoints actifs", bg=self.current_theme["bg"],
                fg=self.current_theme["error"], font=("Consolas", 10, "bold")).pack(side="left", padx=10)
        ttk.Button(bp_toolbar, text="🗑️ Tout supprimer", command=self.clear_all_breakpoints).pack(side="right", padx=5)
        ttk.Button(bp_toolbar, text="🔄 Actualiser", command=self.refresh_breakpoints_list).pack(side="right", padx=5)
        
        self.bp_list = tk.Listbox(bp_frame, font=("Consolas", 9), bg=self.current_theme["console_bg"],
                                  fg=self.current_theme["error"], height=15)
        self.bp_list.pack(fill="both", expand=True, pady=5)
        self.bp_list.bind('<Double-Button-1>', self.goto_breakpoint)
    
    def create_search_tab(self):
        """Onglet recherche d'erreurs (ancien Kerberos)"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔍 Recherche")
        
        main = tk.Frame(frame, bg="#1a1a1a", padx=20, pady=15)
        main.pack(fill="both", expand=True)
        
        # Titre
        tk.Label(main, text="🔍 RECHERCHE D'ERREUR MULTI-FORMAT", 
                bg="#1a1a1a", fg="#bb86fc", font=("Consolas", 16, "bold")).pack(pady=(0, 15))
        
        # Zone de saisie de l'erreur
        err_frame = tk.Frame(main, bg="#1a1a1a")
        err_frame.pack(fill="x", pady=(0, 12))
        tk.Label(err_frame, text="Erreur à chercher (ex: ' background') :", bg="#1a1a1a", fg="#4fc3f7", font=("Consolas", 11)).pack(anchor="w")
        self.err_entry = tk.Entry(err_frame, font=("Consolas", 11), width=70,
                                 bg="#252525", fg="#00ffcc", insertbackground="#00ffcc")
        self.err_entry.pack(pady=(5, 0), fill="x")
        
        # Dossier + Extensions
        path_ext_frame = tk.Frame(main, bg="#1a1a1a")
        path_ext_frame.pack(fill="x", pady=(0, 12))
        
        # Dossier
        path_frame = tk.Frame(path_ext_frame, bg="#1a1a1a")
        path_frame.pack(side="left", fill="x", expand=True)
        tk.Label(path_frame, text="Dossier à analyser :", bg="#1a1a1a", fg="#e0e0e0").pack(anchor="w")
        path_subframe = tk.Frame(path_frame, bg="#1a1a1a")
        path_subframe.pack(fill="x", pady=(5, 0))
        self.path_entry = tk.Entry(path_subframe, font=("Consolas", 10),
                                  bg="#252525", fg="#00ffcc", insertbackground="#00ffcc")
        self.path_entry.insert(0, str(Path.home()))
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ttk.Button(path_subframe, text="📁", width=4, command=self.browse_search_folder).pack(side="right")
        
        # Extensions
        ext_frame = tk.Frame(path_ext_frame, bg="#1a1a1a", padx=20)
        ext_frame.pack(side="right", fill="y")
        tk.Label(ext_frame, text="Extensions :", bg="#1a1a1a", fg="#bb86fc", font=("Consolas", 10, "bold")).pack(anchor="w")
        self.ext_py = tk.BooleanVar(value=True)
        self.ext_csv = tk.BooleanVar(value=True)
        self.ext_json = tk.BooleanVar(value=False)
        self.ext_txt = tk.BooleanVar(value=False)
        ttk.Checkbutton(ext_frame, text=".py", variable=self.ext_py).pack(anchor="w")
        ttk.Checkbutton(ext_frame, text=".csv", variable=self.ext_csv).pack(anchor="w")
        ttk.Checkbutton(ext_frame, text=".json", variable=self.ext_json).pack(anchor="w")
        ttk.Checkbutton(ext_frame, text=".txt", variable=self.ext_txt).pack(anchor="w")
        
        # Boutons
        btn_frame = tk.Frame(main, bg="#1a1a1a")
        btn_frame.pack(fill="x", pady=(0, 15))
        ttk.Button(btn_frame, text="🚀 LANCER RECHERCHE", command=self.start_search, width=22).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 RAPPORT TXT", command=self.save_search_report, width=18).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ VIDER", command=self.clear_search, width=12).pack(side="right", padx=5)
        
        # Résultats
        tk.Label(main, text="Résultats :", bg="#1a1a1a", fg="#4CAF50", font=("Consolas", 11, "bold")).pack(anchor="w")
        self.search_results = scrolledtext.ScrolledText(main, wrap=tk.WORD, font=("Consolas", 9),
                                                bg="#0d0d0d", fg="#ffcc00", height=28)
        self.search_results.pack(fill="both", expand=True, pady=(8, 0))
        
        # Tags
        self.search_results.tag_configure("sep", foreground="#555")
        self.search_results.tag_configure("fichier", foreground="#bb86fc", font=("Consolas", 10, "bold"))
        self.search_results.tag_configure("ligne", foreground="#4fc3f7")
        self.search_results.tag_configure("normal", foreground="#ffcc00")
        self.search_results.tag_configure("highlight", foreground="#000000", background="#ffff00", font=("Consolas", 9, "bold"))
    
    def create_history_tab(self):
        """Onglet historique des exécutions"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📚 Historique")
        
        # Barre d'outils
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", pady=10, padx=10)
        
        tk.Label(toolbar, text="📚 Historique des 50 dernières exécutions", bg="#1a1a1a", fg="#bb86fc",
                font=("Consolas", 12, "bold")).pack(side="left", padx=10)
        ttk.Button(toolbar, text="🗑️ Vider l'historique", command=self.clear_history).pack(side="right", padx=5)
        ttk.Button(toolbar, text="🔄 Actualiser", command=self.refresh_history).pack(side="right", padx=5)
        
        # Liste
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.history_list = tk.Listbox(list_frame, font=("Consolas", 9), bg="#0d0d0d", fg="#e0e0e0",
                                       selectbackground="#3a3a3a", selectforeground="#00ffcc",
                                       yscrollcommand=scrollbar.set, height=30)
        self.history_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_list.yview)
        
        self.history_list.bind('<Double-Button-1>', self.load_from_history)
        
        # Détails
        details_frame = ttk.Frame(frame)
        details_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        tk.Label(details_frame, text="Détails :", bg="#1a1a1a", fg="#4fc3f7", font=("Consolas", 10, "bold")).pack(anchor="w")
        self.history_details = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, font=("Consolas", 9),
                                                        bg="#0d0d0d", fg="#e0e0e0", height=8)
        self.history_details.pack(fill="both", expand=True, pady=5)
    
    # ========== MÉTHODES DÉBOGUEUR ==========
    
    def new_file(self):
        """Nouveau fichier"""
        if messagebox.askyesno("Nouveau fichier", "Créer un nouveau fichier vide ?"):
            self.current_file = None
            self.file_label.config(text="📄 Nouveau fichier")
            self.code_editor.delete("1.0", tk.END)
            self.clear_console()
    
    def open_file(self):
        """Ouvrir un fichier"""
        filename = filedialog.askopenfilename(
            title="Ouvrir un fichier Python",
            filetypes=[("Python", "*.py"), ("Tous", "*.*")]
        )
        if filename:
            try:
                content = Path(filename).read_text(encoding='utf-8')
                self.code_editor.delete("1.0", tk.END)
                self.code_editor.insert("1.0", content)
                self.code_editor.highlight_syntax()
                self.current_file = filename
                self.file_label.config(text=f"📄 {Path(filename).name}")
                self.log_console(f"✅ Fichier ouvert : {filename}\n", "success")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier :\n{e}")
    
    def save_file(self):
        """Sauvegarder le fichier"""
        if self.current_file:
            try:
                content = self.code_editor.get("1.0", tk.END)
                Path(self.current_file).write_text(content, encoding='utf-8')
                self.log_console(f"✅ Fichier sauvegardé : {self.current_file}\n", "success")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder :\n{e}")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Sauvegarder sous..."""
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder sous",
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("Tous", "*.*")]
        )
        if filename:
            try:
                content = self.code_editor.get("1.0", tk.END)
                Path(filename).write_text(content, encoding='utf-8')
                self.current_file = filename
                self.file_label.config(text=f"📄 {Path(filename).name}")
                self.log_console(f"✅ Fichier sauvegardé : {filename}\n", "success")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder :\n{e}")
    
    def run_code(self):
        """Exécuter le code"""
        if self.is_executing:
            messagebox.showwarning("Attention", "Une exécution est déjà en cours !")
            return
        
        code = self.code_editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Attention", "Le code est vide !")
            return
        
        # Préparer
        self.clear_console()
        self.traceback_text.delete("1.0", tk.END)
        self.is_executing = True
        self.status_label.config(text="🟢 En cours d'exécution...", fg="#4CAF50")
        
        # Arguments
        args_text = self.args_entry.get().strip()
        args = args_text.split() if args_text else None
        
        # Log
        filename = self.current_file or "<editor>"
        self.log_console(f"{'='*60}\n", "info")
        self.log_console(f"▶️  Exécution de : {Path(filename).name if self.current_file else 'Code éditeur'}\n", "info")
        self.log_console(f"{'='*60}\n\n", "info")
        
        # Exécuter
        self.debugger.execute_code(code, filename, args)
    
    def stop_code(self):
        """Arrêter l'exécution"""
        if self.is_executing:
            self.debugger.stop_execution()
            self.log_console("\n⏹️ Exécution arrêtée par l'utilisateur\n", "error")
            self.status_label.config(text="🔴 Arrêté", fg="#ff5252")
            self.is_executing = False
    
    def analyze_code(self):
        """Analyser statiquement le code"""
        code = self.code_editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Attention", "Le code est vide !")
            return
        
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, "🔍 Analyse statique en cours...\n\n", "info")
        
        # Analyser
        success = self.analyzer.analyze(code, self.current_file or "<editor>")
        report = self.analyzer.get_report()
        
        # Afficher
        if success and not self.analyzer.warnings:
            self.analysis_text.insert(tk.END, report, "success")
        else:
            lines = report.split('\n')
            for line in lines:
                if '🔴' in line:
                    self.analysis_text.insert(tk.END, line + '\n', "error")
                elif '⚠️' in line:
                    self.analysis_text.insert(tk.END, line + '\n', "warning")
                else:
                    self.analysis_text.insert(tk.END, line + '\n')
        
        # Sélectionner l'onglet analyse
        self.notebook.select(0)  # Débogueur
    
    def clear_console(self):
        """Vider la console"""
        self.console.delete("1.0", tk.END)
    
    def log_console(self, message, tag="output"):
        """Logger dans la console"""
        self.console.insert(tk.END, message, tag)
        self.console.see(tk.END)
    
    def on_output(self, line, is_error=False):
        """Callback sortie du débogueur"""
        tag = "error" if is_error else "output"
        self.log_console(line, tag)
    
    def on_error(self, error_text, code, filename):
        """Callback erreur du débogueur"""
        # Parser le traceback
        error_info = self.debugger.parse_traceback(error_text, code, filename)
        
        # Afficher dans traceback
        self.traceback_text.delete("1.0", tk.END)
        self.traceback_text.insert(tk.END, "🐛 TRACEBACK DÉTAILLÉ\n", "error")
        self.traceback_text.insert(tk.END, "="*60 + "\n\n")
        self.traceback_text.insert(tk.END, error_info["full_traceback"] + "\n\n")
        
        # Résumé
        self.traceback_text.insert(tk.END, f"❌ Type : {error_info['type']}\n", "error")
        self.traceback_text.insert(tk.END, f"💬 Message : {error_info['message']}\n\n")
        
        if error_info['line']:
            self.traceback_text.insert(tk.END, f"📍 Ligne {error_info['line']}\n", "line")
            if error_info['context']:
                self.traceback_text.insert(tk.END, f"   {error_info['context']}\n\n", "line")
            
            # Surligner dans l'éditeur
            self.code_editor.highlight_error_line(error_info['line'])
        
        # Suggestions
        if error_info['suggestions']:
            self.traceback_text.insert(tk.END, "💡 SUGGESTIONS DE CORRECTION\n", "suggestion")
            self.traceback_text.insert(tk.END, "="*60 + "\n", "suggestion")
            for sugg in error_info['suggestions']:
                self.traceback_text.insert(tk.END, f"{sugg}\n", "suggestion")
    
    def on_finish(self, return_code):
        """Callback fin d'exécution"""
        self.is_executing = False
        if return_code == 0:
            self.log_console(f"\n{'='*60}\n", "success")
            self.log_console("✅ Exécution terminée avec succès (code 0)\n", "success")
            self.log_console(f"{'='*60}\n", "success")
            self.status_label.config(text="✅ Succès", fg="#4CAF50")
        else:
            self.log_console(f"\n{'='*60}\n", "error")
            self.log_console(f"❌ Exécution terminée avec erreur (code {return_code})\n", "error")
            self.log_console(f"{'='*60}\n", "error")
            self.status_label.config(text=f"❌ Erreur (code {return_code})", fg="#ff5252")
    
    # ========== SURVEILLANCE DE FICHIERS ==========
    
    def toggle_watch(self):
        """Activer/désactiver la surveillance"""
        if self.watch_var.get():
            if not self.current_file:
                messagebox.showwarning("Attention", "Ouvre d'abord un fichier pour activer la surveillance !")
                self.watch_var.set(False)
                return
            self.start_watching()
        else:
            self.stop_watching()
    
    def start_watching(self):
        """Démarrer la surveillance"""
        if not self.current_file:
            return
        
        self.watch_active = True
        self.log_console(f"👁️ Surveillance activée sur : {self.current_file}\n", "info")
        
        def watch_loop():
            last_mtime = os.path.getmtime(self.current_file)
            while self.watch_active:
                time.sleep(1)
                try:
                    current_mtime = os.path.getmtime(self.current_file)
                    if current_mtime > last_mtime:
                        last_mtime = current_mtime
                        # Recharger et exécuter
                        content = Path(self.current_file).read_text(encoding='utf-8')
                        self.code_editor.delete("1.0", tk.END)
                        self.code_editor.insert("1.0", content)
                        self.code_editor.highlight_syntax()
                        self.log_console("\n🔄 Fichier modifié, rechargement...\n", "info")
                        self.run_code()
                except:
                    pass
        
        self.file_watcher = threading.Thread(target=watch_loop, daemon=True)
        self.file_watcher.start()
    
    def stop_watching(self):
        """Arrêter la surveillance"""
        self.watch_active = False
        if self.current_file:
            self.log_console(f"👁️ Surveillance désactivée\n", "info")
    
    # ========== HISTORIQUE ==========
    
    def show_history(self):
        """Afficher l'historique"""
        self.notebook.select(2)
        self.refresh_history()
    
    def refresh_history(self):
        """Actualiser l'historique"""
        self.history_list.delete(0, tk.END)
        for i, entry in enumerate(reversed(self.debugger.execution_history)):
            filename = Path(entry['filename']).name if entry['filename'] != "<editor>" else "Éditeur"
            label = f"{i+1}. [{entry['timestamp']}] {filename}"
            self.history_list.insert(tk.END, label)
    
    def load_from_history(self, event):
        """Charger depuis l'historique"""
        selection = self.history_list.curselection()
        if not selection:
            return
        
        idx = len(self.debugger.execution_history) - 1 - selection[0]
        entry = list(self.debugger.execution_history)[idx]
        
        # Charger le code
        self.code_editor.delete("1.0", tk.END)
        self.code_editor.insert("1.0", entry['code'])
        self.code_editor.highlight_syntax()
        
        # Afficher les détails
        self.history_details.delete("1.0", tk.END)
        self.history_details.insert(tk.END, f"Date : {entry['timestamp']}\n")
        self.history_details.insert(tk.END, f"Fichier : {entry['filename']}\n")
        self.history_details.insert(tk.END, f"Arguments : {' '.join(entry['args']) if entry['args'] else 'Aucun'}\n\n")
        self.history_details.insert(tk.END, "Code :\n")
        self.history_details.insert(tk.END, "-"*60 + "\n")
        self.history_details.insert(tk.END, entry['code'])
        
        # Revenir au débogueur
        self.notebook.select(0)
        messagebox.showinfo("Historique", "Code chargé depuis l'historique !")
    
    def clear_history(self):
        """Vider l'historique"""
        if messagebox.askyesno("Confirmation", "Vider tout l'historique ?"):
            self.debugger.execution_history.clear()
            self.refresh_history()
            self.history_details.delete("1.0", tk.END)
    
    def create_terminal_tab(self):
        """Onglet Terminal intégré"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🖥️ Terminal")
        
        # Barre de titre
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", pady=(10, 5), padx=10)
        
        tk.Label(toolbar, text="🖥️ TERMINAL BASH INTÉGRÉ", bg=self.current_theme["bg"],
                fg=self.current_theme["info"], font=("Consolas", 12, "bold")).pack(side="left", padx=10)
        
        ttk.Button(toolbar, text="🗑️ Vider", command=self.clear_terminal).pack(side="right", padx=5)
        ttk.Button(toolbar, text="📁 PWD", command=self.show_pwd).pack(side="right", padx=5)
        
        # Zone de sortie
        self.terminal_output = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 10),
                                                         bg=self.current_theme["console_bg"], 
                                                         fg=self.current_theme["fg"], height=25)
        self.terminal_output.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.terminal_output.tag_configure("output", foreground=self.current_theme["fg"])
        self.terminal_output.tag_configure("error", foreground=self.current_theme["error"])
        self.terminal_output.tag_configure("success", foreground=self.current_theme["success"])
        self.terminal_output.tag_configure("prompt", foreground=self.current_theme["accent"], font=("Consolas", 10, "bold"))
        
        # Barre de commande
        cmd_frame = ttk.Frame(frame)
        cmd_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        tk.Label(cmd_frame, text="$", bg=self.current_theme["bg"], fg=self.current_theme["accent"],
                font=("Consolas", 11, "bold")).pack(side="left", padx=(0, 5))
        
        self.terminal_entry = tk.Entry(cmd_frame, font=("Consolas", 10), bg=self.current_theme["editor_bg"],
                                      fg=self.current_theme["accent"], insertbackground=self.current_theme["accent"])
        self.terminal_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.terminal_entry.bind('<Return>', self.execute_terminal_command)
        
        ttk.Button(cmd_frame, text="▶️ Exécuter", command=lambda: self.execute_terminal_command(None)).pack(side="right")
        
        # Initialiser le terminal
        self.terminal = EmbeddedTerminal(self.terminal_output)
        
        # Message de bienvenue
        welcome = f"""
╔═══════════════════════════════════════════════════════════╗
║  🖥️  TERMINAL BASH INTÉGRÉ - Kerberos Debugger v4.0     ║
╚═══════════════════════════════════════════════════════════╝

Commandes disponibles :
  • Toutes les commandes bash : ls, cd, pwd, cat, grep...
  • Python : python script.py, pip install module
  • Git : git status, git commit, git push
  • Système : clear, echo, date, whoami

Exemples :
  $ python --version
  $ pip list
  $ ls -la
  $ cd /mon/projet
  $ git status

Tapez votre commande ci-dessous et appuyez sur Entrée ! 🚀

"""
        self.terminal_output.insert("1.0", welcome, "success")
    
    def execute_terminal_command(self, event):
        """Exécuter une commande dans le terminal"""
        command = self.terminal_entry.get().strip()
        
        if not command:
            return
        
        # Afficher la commande
        self.terminal_output.insert(tk.END, f"\n$ {command}\n", "prompt")
        self.terminal_output.see(tk.END)
        
        # Commande spéciale : clear
        if command == "clear":
            self.terminal_output.delete("1.0", tk.END)
            self.terminal_entry.delete(0, tk.END)
            return
        
        # Exécuter
        self.terminal.execute_command(command)
        
        # Vider la zone de saisie
        self.terminal_entry.delete(0, tk.END)
        
        # Scroll to end
        self.terminal_output.see(tk.END)
    
    def clear_terminal(self):
        """Vider le terminal"""
        self.terminal_output.delete("1.0", tk.END)
    
    def show_pwd(self):
        """Afficher le répertoire courant"""
        self.terminal_output.insert(tk.END, f"\n📁 Répertoire courant : {self.terminal.cwd}\n", "success")
        self.terminal_output.see(tk.END)
    
    # ========== RECHERCHE D'ERREURS ==========
    
    def browse_search_folder(self):
        """Parcourir dossier pour recherche"""
        folder = filedialog.askdirectory(title="Sélectionner le dossier à analyser")
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
    
    def start_search(self):
        """Lancer la recherche d'erreurs"""
        self.clear_search()
        dossier = self.path_entry.get().strip()
        motif = self.err_entry.get().strip()
        
        if not motif:
            messagebox.showwarning("⚠️ Attention", "Veuillez saisir le texte de l'erreur à chercher")
            return
        
        if not os.path.isdir(dossier):
            messagebox.showerror("❌ Erreur", f"Le dossier n'existe pas :\n{dossier}")
            return
        
        # Extensions
        extensions = []
        if self.ext_py.get(): extensions.append((".py", "py"))
        if self.ext_csv.get(): extensions.append((".csv", "csv"))
        if self.ext_json.get(): extensions.append((".json", "json"))
        if self.ext_txt.get(): extensions.append((".txt", "txt"))
        
        if not extensions:
            messagebox.showwarning("⚠️ Attention", "Veuillez cocher au moins une extension")
            return
        
        self.log_search(f"🔍 Recherche de : {repr(motif)}\n")
        self.log_search(f"📁 Dossier : {dossier}\n")
        self.log_search(f"🗃️ Extensions : {', '.join(ext[0] for ext in extensions)}\n\n")
        self.log_search("="*80 + "\n\n", "sep")
        
        # Recherche
        resultats = {"py": [], "csv": [], "json": [], "txt": []}
        
        for ext_pattern, ext_type in extensions:
            fichiers = list(Path(dossier).rglob(f"*{ext_pattern}"))
            
            for chemin in fichiers:
                try:
                    try:
                        contenu = chemin.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        contenu = chemin.read_text(encoding="latin-1")
                    
                    lignes = contenu.splitlines()
                    
                    for num, ligne in enumerate(lignes, 1):
                        if motif in ligne:
                            debut = max(0, num - 2)
                            fin = min(len(lignes), num + 2)
                            contexte = []
                            for i in range(debut, fin):
                                prefixe = " >> " if i+1 == num else "    "
                                contexte.append(f"{prefixe}{i+1:4d} | {lignes[i]}")
                            
                            resultats[ext_type].append({
                                "fichier": chemin.relative_to(dossier),
                                "ligne": num,
                                "contexte": "\n".join(contexte)
                            })
                except Exception as e:
                    self.log_search(f"⚠️  Erreur : {chemin.name}\n")
        
        # Affichage
        total = sum(len(r) for r in resultats.values())
        if total:
            for ext_type in ["py", "csv", "json", "txt"]:
                if resultats[ext_type]:
                    self.log_search(f"\n📄 FICHIERS .{ext_type.upper()} — {len(resultats[ext_type])} occurrence(s)\n", "fichier")
                    self.log_search("─"*80 + "\n", "sep")
                    for r in resultats[ext_type]:
                        self.log_search_result(r["fichier"], r["ligne"], r["contexte"], motif)
        else:
            self.log_search("✅ Aucune occurrence trouvée\n\n")
        
        self.log_search(f"\n{'='*80}\n", "sep")
        self.log_search(f"✅ TOTAL : {total} occurrence(s)\n")
    
    def log_search(self, msg, tag="normal"):
        """Logger recherche"""
        self.search_results.insert(tk.END, msg, tag)
        self.search_results.see(tk.END)
    
    def log_search_result(self, fichier, ligne, contexte, motif):
        """Logger un résultat de recherche"""
        self.log_search(f"\n📍 {fichier}\n", "fichier")
        self.log_search(f"   Ligne {ligne}\n\n", "ligne")
        
        for line in contexte.split("\n"):
            if motif in line:
                parts = line.split(motif, 1)
                self.log_search(parts[0], "normal")
                self.log_search(motif, "highlight")
                self.log_search(parts[1] + "\n", "normal")
            else:
                self.log_search(line + "\n", "normal")
        self.log_search("\n", "normal")
    
    def clear_search(self):
        """Vider recherche"""
        self.search_results.delete("1.0", tk.END)
    
    def save_search_report(self):
        """Sauvegarder rapport recherche"""
        content = self.search_results.get("1.0", tk.END)
        if not content.strip():
            messagebox.showwarning("Attention", "Aucun résultat à sauvegarder")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder le rapport",
            defaultextension=".txt",
            filetypes=[("Texte", "*.txt")]
        )
        if filename:
            try:
                Path(filename).write_text(content, encoding='utf-8')
                messagebox.showinfo("Succès", f"Rapport sauvegardé :\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder :\n{e}")
    
    # ========== UTILITAIRES ==========
    
    def show_shortcuts(self):
        """Afficher les raccourcis"""
        shortcuts = """
🎹 RACCOURCIS CLAVIER
═══════════════════════════════════════

📁 Fichiers
  Ctrl+O     : Ouvrir un fichier
  Ctrl+S     : Sauvegarder
  Ctrl+Q     : Quitter

▶️ Exécution
  F5         : Exécuter le code
  F6         : Analyse statique
  
✏️ Édition
  Ctrl+A     : Tout sélectionner
  Ctrl+F     : Rechercher
  Tab        : Insérer 4 espaces
  Enter      : Auto-indentation

🐺 Kerberos Debugger v3.0
        """
        messagebox.showinfo("Raccourcis clavier", shortcuts)
    
    # ========== NOUVELLES MÉTHODES v4.0 ==========
    
    def update_cursor_position(self, event=None):
        """Mettre à jour la position du curseur dans la barre de statut"""
        try:
            cursor_pos = self.code_editor.index(tk.INSERT)
            line, col = cursor_pos.split('.')
            self.status_line.config(text=f"Ligne: {line}, Col: {col}")
        except:
            pass
    
    def toggle_breakpoint_current_line(self):
        """Toggle breakpoint sur la ligne courante"""
        try:
            cursor_pos = self.code_editor.index(tk.INSERT)
            line = int(cursor_pos.split('.')[0])
            is_active = self.breakpoint_manager.toggle(line)
            self.code_editor.update_line_numbers()
            self.refresh_breakpoints_list()
            
            if is_active:
                self.log_console(f"🔴 Breakpoint ajouté ligne {line}\n", "info")
            else:
                self.log_console(f"⚪ Breakpoint supprimé ligne {line}\n", "info")
        except:
            pass
    
    def clear_all_breakpoints(self):
        """Supprimer tous les breakpoints"""
        if messagebox.askyesno("Confirmation", "Supprimer tous les breakpoints ?"):
            self.breakpoint_manager.clear_all()
            self.code_editor.update_line_numbers()
            self.refresh_breakpoints_list()
            self.log_console("🗑️ Tous les breakpoints supprimés\n", "info")
    
    def show_breakpoints_list(self):
        """Afficher la liste des breakpoints"""
        self.notebook.select(0)  # Onglet débogueur
        self.refresh_breakpoints_list()
    
    def refresh_breakpoints_list(self):
        """Actualiser la liste des breakpoints"""
        try:
            self.bp_list.delete(0, tk.END)
            breakpoints = self.breakpoint_manager.get_all()
            
            if not breakpoints:
                self.bp_list.insert(tk.END, "Aucun breakpoint actif")
            else:
                for bp in breakpoints:
                    # Obtenir la ligne de code
                    try:
                        line_content = self.code_editor.get(f"{bp}.0", f"{bp}.end").strip()
                        if len(line_content) > 50:
                            line_content = line_content[:47] + "..."
                        self.bp_list.insert(tk.END, f"🔴 Ligne {bp}: {line_content}")
                    except:
                        self.bp_list.insert(tk.END, f"🔴 Ligne {bp}")
        except:
            pass
    
    def goto_breakpoint(self, event):
        """Aller à un breakpoint (double-clic)"""
        try:
            selection = self.bp_list.curselection()
            if not selection:
                return
            
            text = self.bp_list.get(selection[0])
            if "Ligne" in text:
                line_num = int(text.split("Ligne ")[1].split(":")[0])
                self.code_editor.see(f"{line_num}.0")
                self.code_editor.mark_set(tk.INSERT, f"{line_num}.0")
                self.code_editor.highlight_current_line(line_num)
        except:
            pass
    
    def run_with_profiling(self):
        """Exécuter avec profilage de performance"""
        if self.is_executing:
            messagebox.showwarning("Attention", "Une exécution est déjà en cours !")
            return
        
        code = self.code_editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Attention", "Le code est vide !")
            return
        
        # Préparer
        self.clear_console()
        self.perf_text.delete("1.0", tk.END)
        self.is_executing = True
        self.status_label.config(text="📊 Profilage en cours...", fg=self.current_theme["info"])
        
        # Arguments
        args_text = self.args_entry.get().strip()
        args = args_text.split() if args_text else None
        
        # Log
        filename = self.current_file or "<editor>"
        self.log_console(f"{'='*60}\n", "info")
        self.log_console(f"📊 Profilage de : {Path(filename).name if self.current_file else 'Code éditeur'}\n", "info")
        self.log_console(f"{'='*60}\n\n", "info")
        
        # Exécuter avec profilage
        self.debugger.execute_code(code, filename, args, profile=True)
    
    def on_finish(self, return_code, profiled=False):
        """Callback fin d'exécution (modifié pour supporter le profilage)"""
        self.is_executing = False
        
        if return_code == 0:
            self.log_console(f"\n{'='*60}\n", "success")
            self.log_console("✅ Exécution terminée avec succès (code 0)\n", "success")
            self.log_console(f"{'='*60}\n", "success")
            self.status_label.config(text="✅ Succès", fg=self.current_theme["success"])
        else:
            self.log_console(f"\n{'='*60}\n", "error")
            self.log_console(f"❌ Exécution terminée avec erreur (code {return_code})\n", "error")
            self.log_console(f"{'='*60}\n", "error")
            self.status_label.config(text=f"❌ Erreur (code {return_code})", fg=self.current_theme["error"])
        
        # Afficher les résultats du profilage
        if profiled:
            self.show_profiling_results()
    
    def show_profiling_results(self):
        """Afficher les résultats du profilage"""
        self.perf_text.delete("1.0", tk.END)
        
        # Titre
        self.perf_text.insert(tk.END, "⏱️  RAPPORT DE PROFILAGE\n", "fast")
        self.perf_text.insert(tk.END, "="*60 + "\n\n", "fast")
        
        # Statistiques complètes
        stats = self.debugger.profiler.get_stats()
        self.perf_text.insert(tk.END, stats + "\n\n")
        
        # Top fonctions
        self.perf_text.insert(tk.END, "🎯 TOP 10 FONCTIONS LES PLUS LENTES\n", "slow")
        self.perf_text.insert(tk.END, "="*60 + "\n\n", "slow")
        
        top_funcs = self.debugger.profiler.get_top_functions(10)
        
        for func in top_funcs:
            time_ms = func['cumulative_time'] * 1000
            
            # Code couleur selon le temps
            if time_ms > 100:
                tag = "critical"
                icon = "🔴"
            elif time_ms > 10:
                tag = "slow"
                icon = "⚠️ "
            else:
                tag = "fast"
                icon = "✅"
            
            self.perf_text.insert(tk.END, f"{icon} {func['function']}()\n", tag)
            self.perf_text.insert(tk.END, f"   Temps: {time_ms:.2f} ms | Appels: {func['calls']}\n", tag)
            self.perf_text.insert(tk.END, f"   Fichier: {func['file']}, ligne {func['line']}\n\n", tag)
    
    def show_performance_report(self):
        """Afficher le rapport de performance dans une fenêtre"""
        if not self.debugger.profiler.profiler:
            messagebox.showinfo("Info", "Aucun profilage effectué.\nAppuie sur F7 pour exécuter avec profilage.")
            return
        
        # Créer une fenêtre
        report_win = tk.Toplevel(self.root)
        report_win.title("📊 Rapport de Performance")
        report_win.geometry("800x600")
        report_win.configure(bg=self.current_theme["bg"])
        
        # Texte
        report_text = scrolledtext.ScrolledText(report_win, wrap=tk.WORD, font=("Consolas", 9),
                                               bg=self.current_theme["console_bg"], fg=self.current_theme["fg"])
        report_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Insérer le rapport
        stats = self.debugger.profiler.get_stats()
        report_text.insert("1.0", stats)
        
        # Bouton fermer
        ttk.Button(report_win, text="Fermer", command=report_win.destroy).pack(pady=10)
    
    def show_performance_graph(self):
        """Afficher un graphique de performance (placeholder)"""
        messagebox.showinfo("Graphique", "Fonctionnalité en développement !\nUtilise l'export CSV pour créer des graphiques avec Excel/Python.")
    
    def export_performance_csv(self):
        """Exporter les données de performance en CSV"""
        if not self.debugger.profiler.profiler:
            messagebox.showinfo("Info", "Aucun profilage effectué.\nAppuie sur F7 pour exécuter avec profilage.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Exporter performance CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")]
        )
        
        if filename:
            try:
                import csv
                top_funcs = self.debugger.profiler.get_top_functions(50)
                
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Fonction', 'Fichier', 'Ligne', 'Appels', 'Temps Total (s)', 'Temps Cumulatif (s)'])
                    
                    for func in top_funcs:
                        writer.writerow([
                            func['function'],
                            func['file'],
                            func['line'],
                            func['calls'],
                            f"{func['total_time']:.6f}",
                            f"{func['cumulative_time']:.6f}"
                        ])
                
                messagebox.showinfo("Succès", f"Performance exportée :\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter :\n{e}")
    
    def apply_auto_fix(self):
        """Appliquer l'auto-correction IA"""
        # Récupérer le dernier auto-fix
        traceback_content = self.traceback_text.get("1.0", tk.END)
        
        if "🤖 Auto-fix" not in traceback_content:
            messagebox.showinfo("Info", "Aucune correction automatique disponible.\nExécute du code avec une erreur pour voir les suggestions IA.")
            return
        
        # Chercher le code auto-fix dans le traceback
        lines = traceback_content.split('\n')
        auto_fix_code = None
        
        for i, line in enumerate(lines):
            if "🤖 Auto-fix" in line:
                # La ligne suivante contient le code corrigé
                if i + 1 < len(lines):
                    auto_fix_code = lines[i + 1].strip()
                    break
        
        if auto_fix_code:
            # Demander confirmation
            if messagebox.askyesno("Auto-correction IA", 
                                  f"Appliquer cette correction ?\n\n{auto_fix_code}\n\nLe code sera ajouté au début de l'éditeur."):
                # Insérer au début
                self.code_editor.insert("1.0", auto_fix_code + "\n")
                self.code_editor.highlight_syntax()
                self.log_console("🤖 Auto-correction appliquée !\n", "success")
        else:
            messagebox.showinfo("Info", "Impossible de trouver le code de correction.")
    
    def copy_auto_fix(self):
        """Copier le code auto-fix dans le presse-papier"""
        traceback_content = self.traceback_text.get("1.0", tk.END)
        
        if "🤖 Auto-fix" not in traceback_content:
            messagebox.showinfo("Info", "Aucune correction automatique disponible.")
            return
        
        # Chercher le code auto-fix
        lines = traceback_content.split('\n')
        auto_fix_code = None
        
        for i, line in enumerate(lines):
            if "🤖 Auto-fix" in line:
                if i + 1 < len(lines):
                    auto_fix_code = lines[i + 1].strip()
                    break
        
        if auto_fix_code:
            # Copier dans le presse-papier
            self.root.clipboard_clear()
            self.root.clipboard_append(auto_fix_code)
            self.log_console("📋 Code corrigé copié dans le presse-papier !\n", "success")
        else:
            messagebox.showinfo("Info", "Impossible de trouver le code de correction.")
    
    def change_theme(self, theme_name):
        """Changer le thème de l'interface"""
        if theme_name not in THEMES:
            return
        
        self.current_theme_name = theme_name
        self.current_theme = THEMES[theme_name]
        
        # Appliquer au root
        self.root.configure(bg=self.current_theme["bg"])
        
        # Appliquer à l'éditeur
        self.code_editor.apply_theme(self.current_theme)
        
        # Appliquer aux widgets
        self.file_label.config(bg=self.current_theme["bg"], fg=self.current_theme["accent"])
        self.status_label.config(bg=self.current_theme["bg"])
        self.console.config(bg=self.current_theme["console_bg"], fg=self.current_theme["fg"])
        self.analysis_text.config(bg=self.current_theme["console_bg"])
        self.traceback_text.config(bg=self.current_theme["console_bg"], fg=self.current_theme["error"])
        self.perf_text.config(bg=self.current_theme["console_bg"], fg=self.current_theme["info"])
        
        # Reconfigurer les tags
        self.console.tag_configure("error", foreground=self.current_theme["error"])
        self.console.tag_configure("success", foreground=self.current_theme["success"])
        self.console.tag_configure("info", foreground=self.current_theme["info"])
        
        # Statusbar
        self.status_file.config(bg=self.current_theme["bg"], fg=self.current_theme["accent"])
        self.status_theme.config(bg=self.current_theme["bg"], fg=self.current_theme["fg"], text=f"🎨 {theme_name}")
        self.status_line.config(bg=self.current_theme["bg"], fg=self.current_theme["fg"])
        
        self.log_console(f"🎨 Thème changé : {theme_name}\n", "info")
    
    def customize_colors(self):
        """Personnaliser les couleurs (placeholder)"""
        messagebox.showinfo("Personnalisation", 
                           "Fonctionnalité en développement !\n\n"
                           "En attendant, tu peux modifier directement le dictionnaire THEMES\n"
                           "dans le code source pour créer ton propre thème.")
    
    def show_find_dialog(self):
        """Afficher dialogue de recherche (placeholder)"""
        messagebox.showinfo("Recherche", "Fonctionnalité en développement !\nUtilise Ctrl+F de ton éditeur de texte.")
    
    def show_replace_dialog(self):
        """Afficher dialogue de remplacement (placeholder)"""
        messagebox.showinfo("Remplacement", "Fonctionnalité en développement !\nUtilise Ctrl+H de ton éditeur de texte.")
    
    def configure_args(self):
        """Configurer les arguments (placeholder)"""
        current_args = self.args_entry.get()
        new_args = tk.simpledialog.askstring("Arguments", "Arguments d'exécution :", initialvalue=current_args)
        if new_args is not None:
            self.args_entry.delete(0, tk.END)
            self.args_entry.insert(0, new_args)
    
    def export_html_report(self):
        """Exporter un rapport HTML"""
        # Récupérer le contenu
        console_content = self.console.get("1.0", tk.END)
        analysis_content = self.analysis_text.get("1.0", tk.END)
        traceback_content = self.traceback_text.get("1.0", tk.END)
        
        if not console_content.strip() and not analysis_content.strip() and not traceback_content.strip():
            messagebox.showinfo("Info", "Aucun contenu à exporter.\nExécute du code d'abord (F5 ou F7).")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Exporter rapport HTML",
            defaultextension=".html",
            filetypes=[("HTML", "*.html")]
        )
        
        if filename:
            try:
                html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapport Kerberos Debugger</title>
    <style>
        body {{
            font-family: 'Consolas', monospace;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
        }}
        h1 {{
            color: #00ffcc;
            border-bottom: 2px solid #00ffcc;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #bb86fc;
            margin-top: 30px;
        }}
        .section {{
            background: #0d0d0d;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #00ffcc;
        }}
        .error {{
            color: #ff5252;
        }}
        .success {{
            color: #4CAF50;
        }}
        .info {{
            color: #00bcd4;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
    </style>
</head>
<body>
    <h1>🐺 Rapport Kerberos Debugger v4.0</h1>
    <p><strong>Généré le :</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    <p><strong>Fichier :</strong> {self.current_file or 'Éditeur'}</p>
    
    <div class="section">
        <h2>📟 Console</h2>
        <pre>{console_content}</pre>
    </div>
    
    <div class="section">
        <h2>🔍 Analyse Statique</h2>
        <pre>{analysis_content}</pre>
    </div>
    
    <div class="section">
        <h2>🐛 Traceback</h2>
        <pre class="error">{traceback_content}</pre>
    </div>
    
    <hr>
    <p style="text-align: center; color: #666;">
        Kerberos Debugger v4.0 EXTREME - Victor Pozen 🐺
    </p>
</body>
</html>"""
                
                Path(filename).write_text(html, encoding='utf-8')
                messagebox.showinfo("Succès", f"Rapport HTML exporté :\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter :\n{e}")
    
    def show_documentation(self):
        """Afficher la documentation"""
        doc = """
🐺 KERBEROS DEBUGGER v4.0 EXTREME
═════════════════════════════════════

📖 RACCOURCIS PRINCIPAUX :

F5  : Exécuter le code
F6  : Analyse statique
F7  : Exécuter avec profilage
F9  : Toggle breakpoint ligne courante

Ctrl+O : Ouvrir fichier
Ctrl+S : Sauvegarder
Ctrl+D : Dupliquer ligne
Ctrl+/ : Commenter/Décommenter

🔴 BREAKPOINTS :
• Clique sur le numéro de ligne
• F9 sur la ligne courante
• Double-clic dans la liste pour y aller

📊 PROFILAGE :
• F7 au lieu de F5
• Voir l'onglet "Performance"
• Rouge = lent, Vert = rapide

🤖 AUTO-FIX IA :
• Exécute du code avec erreur
• Lis les suggestions IA
• Clique "Appliquer la correction"

🎨 THÈMES :
Menu "Thème" → 6 thèmes disponibles

Ouvre README_KERBEROS_V4.md pour la doc complète !
        """
        messagebox.showinfo("Documentation", doc)
    
    def show_about(self):
        """À propos"""
        about = """
🐺 KERBEROS DEBUGGER v4.0 EXTREME
═══════════════════════════════════════

Débogueur Python Ultime avec IA

NOUVELLES FONCTIONNALITÉS v4.0 :
• 🔴 Breakpoints visuels
• 📊 Profilage de performance
• 🤖 Auto-correction IA
• 🎨 6 thèmes personnalisables
• 🖥️ Terminal bash intégré
• 📈 Graphiques de performance
• 📤 Export HTML/PDF/CSV

Licence : GPLv3 modifiée
Auteur : Victor Pozen 🐺
Version : 4.0 EXTREME Edition

Février 2026
═══════════════════════════════════════
        """
        messagebox.showinfo("À propos", about)


# ============================================================
# POINT D'ENTRÉE
# ============================================================

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = KerberosDebuggerApp(root)
        root.mainloop()
    except Exception as e:
        print(f"ERREUR FATALE : {e}")
        tb_module.print_exc()
        input("\nAppuyez sur Entrée pour quitter...")
