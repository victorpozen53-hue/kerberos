# -*- coding: utf-8 -*-
"""
🐺 KERBEROS DEBUGGER v4.1 - Architecture Modulaire & Privacy First
═══════════════════════════════════════════════════════════════════
• IA désactivée par défaut — toggle explicite requis
• Création auto des dossiers au premier démarrage
• Module gerex intégré (analyse regex 100% locale)
• Liens web uniquement (pas d'API silencieuse)
• Chemins génériques (X:\debug-plus\ → adaptable à D:, E:, etc.)
• Tkinter GUI préservé — zéro casse d'interface
License: GPLv3 - Victor Pozen 🐺
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
# 🔒 CRÉATION AUTO DES DOSSIERS AU PREMIER DÉMARRAGE
# ============================================================
DEBUG_ROOT = Path(__file__).parent.resolve()  # Ex: X:\debug-plus\

REQUIRED_DIRS = [
    DEBUG_ROOT / "temp" / "debug",
    DEBUG_ROOT / "modules",
    DEBUG_ROOT / "IA" / "embarquees",
    DEBUG_ROOT / "IA" / "providers"
]

for d in REQUIRED_DIRS:
    try:
        d.mkdir(parents=True, exist_ok=True)
        print(f"✅ Dossier créé : {d.relative_to(DEBUG_ROOT)}")
    except Exception as e:
        print(f"⚠️ Impossible de créer {d}: {e}")

# ============================================================
# COLOR THEMES
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
# 🔍 MODULE GEREX - Analyse Regex 100% Locale
# ============================================================
class GerexAnalyzer:
    """
    Analyseur regex léger pour erreurs Python courantes
    → 100% local, zéro dépendance réseau
    → Patterns optimisés pour le debugging rapide
    → Intégré dans l'onglet "Traceback + Auto-Fix"
    """
    
    def __init__(self):
        self.patterns = {
            # Syntaxe
            r"SyntaxError:.*invalid syntax": {
                "cause": "Erreur de syntaxe Python",
                "fix": "Vérifie les parenthèses non fermées, deux-points manquants ou guillemets incomplets",
                "emoji": "✏️"
            },
            r"IndentationError:": {
                "cause": "Mauvaise indentation",
                "fix": "Utilise 4 espaces par niveau — pas de mélange espaces/tabulations",
                "emoji": "↹"
            },
            # Noms
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
            # Modules
            r"ModuleNotFoundError: No module named '(\w+)'": {
                "cause": "Module Python non installé",
                "fix": "pip install {0} → puis redémarre le script",
                "emoji": "📦"
            },
            r"ImportError: cannot import name '(\w+)'": {
                "cause": "Import circulaire ou nom incorrect",
                "fix": "Vérifie l'orthographe et l'ordre des imports — évite les imports circulaires",
                "emoji": "🔄"
            },
            # Données
            r"KeyError: (\S+)": {
                "cause": "Clé absente dans le dictionnaire",
                "fix": "Utilise .get('{0}', valeur_par_defaut) ou vérifie les clés avec 'in'",
                "emoji": "🔑"
            },
            r"IndexError: list index out of range": {
                "cause": "Accès à un index inexistant dans une liste",
                "fix": "Vérifie la longueur avec len() avant d'accéder à un index",
                "emoji": "📏"
            },
            r"TypeError: '(\w+)' object is not iterable": {
                "cause": "Objet utilisé dans une boucle mais non itérable",
                "fix": "Convertir en liste/tuple ou vérifier le type avec isinstance()",
                "emoji": "🔄"
            },
            # Fichiers
            r"FileNotFoundError:.*Errno 2": {
                "cause": "Fichier ou chemin introuvable",
                "fix": "Vérifie le chemin avec os.path.exists() et utilise des chemins absolus",
                "emoji": "📁"
            },
            # Runtime
            r"ZeroDivisionError:": {
                "cause": "Division par zéro",
                "fix": "Vérifie que le diviseur n'est pas égal à 0 avant la division",
                "emoji": "➗"
            },
            r"TypeError: unsupported operand type": {
                "cause": "Opération sur des types incompatibles",
                "fix": "Convertis les valeurs au bon type (int, str, float) avant l'opération",
                "emoji": "🔢"
            }
        }
        self.enabled = False
    
    def toggle(self, state: bool):
        """Active/désactive l'analyse gerex"""
        self.enabled = state
        return "🟢 ACTIVÉ" if state else "🔴 DÉSACTIVÉ"
    
    def analyze(self, error_text: str) -> dict | None:
        """Analyse l'erreur avec les patterns regex"""
        if not self.enabled:
            return None
        
        for pattern, solution in self.patterns.items():
            match = re.search(pattern, error_text, re.IGNORECASE)
            if match:
                fix = solution["fix"]
                for i, group in enumerate(match.groups(), 1):
                    fix = fix.replace(f"{{{i-1}}}", str(group))
                
                return {
                    "source": "gerex",
                    "emoji": solution["emoji"],
                    "cause": solution["cause"],
                    "fix": fix,
                    "confidence": 0.95
                }
        return None

# ============================================================
# STATIC CODE ANALYZER (Corrigé - sans faux positifs)
# ============================================================
class StaticAnalyzer:
    """Analyzes Python code without execution to detect errors"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        # Modules stdlib à ignorer
        self.stdlib_modules = {
            'os', 'sys', 're', 'json', 'datetime', 'time', 'math', 'random',
            'tkinter', 'threading', 'subprocess', 'pathlib', 'tempfile',
            'hashlib', 'urllib', 'socket', 'webbrowser', 'typing',
            'collections', 'itertools', 'functools', 'inspect', 'traceback',
            'builtins', 'types', 'enum', 'dataclasses', 'decimal', 'fractions',
            'statistics', 'bisect', 'heapq', 'copy', 'pickle', 'shutil', 'zipfile',
            'csv', 'xml', 'html', 'secrets', 'uuid', 'ipaddress', 'argparse',
            'configparser', 'logging', 'getpass', 'platform', 'locale', 'zoneinfo'
        }
        # Mots-clés Python à ignorer
        self.python_keywords = {
            'if', 'else', 'elif', 'for', 'while', 'def', 'class', 'return',
            'try', 'except', 'finally', 'raise', 'import', 'from', 'as',
            'with', 'lambda', 'yield', 'break', 'continue', 'pass', 'global',
            'nonlocal', 'assert', 'del', 'and', 'or', 'not', 'is', 'in',
            'True', 'False', 'None'
        }
    
    def analyze(self, code, filename="<string>"):
        """Static analysis of code"""
        self.errors.clear()
        self.warnings.clear()
        
        # 1. Check syntax
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
        
        # 2. Detect missing imports (sans faux positifs)
        try:
            tree = ast.parse(code, filename)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split('.')[0]
                        if module not in self.stdlib_modules and module not in self.python_keywords:
                            imports.add(module)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module.split('.')[0]
                        if module not in self.stdlib_modules and module not in self.python_keywords:
                            imports.add(module)
            
            # Vérifier les imports manquants (sans stdlib)
            for module in imports:
                try:
                    importlib.import_module(module)
                except ImportError:
                    # Ignorer les modules internes (commençant par minuscule)
                    if not module[0].islower():
                        self.warnings.append({
                            "type": "MissingImport",
                            "line": 1,
                            "msg": f"Module '{module}' non installé — pip install {module}",
                            "severity": "medium"
                        })
        except:
            pass  # Ignore parsing errors for analysis
        
        return len(self.errors) == 0
    
    def get_report(self):
        """Generate readable report"""
        report = []
        if self.errors:
            report.append("🔴 CRITICAL ERRORS:")
            for err in self.errors:
                report.append(f"  Line {err['line']}: {err['type']} - {err['msg']}")
                if err.get('text'):
                    report.append(f"    {err['text'].strip()}")
                if err.get('offset'):
                    report.append(f"    {' ' * (err['offset'] - 1)}^")
        if self.warnings:
            report.append("\n⚠️  WARNINGS:")
            for w in self.warnings:
                report.append(f"  🔸 Line {w['line']}: {w['msg']}")
        return '\n'.join(report) if report else "✅ No errors detected"

# ============================================================
# PERFORMANCE PROFILER
# ============================================================
class PerformanceProfiler:
    """Profiles Python code performance"""
    
    def __init__(self):
        self.profiler = None
        self.stats = None
        self.line_timings = {}
    
    def start(self):
        """Start profiling"""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
    
    def stop(self):
        """Stop profiling"""
        if self.profiler:
            self.profiler.disable()
    
    def get_stats(self, limit=20):
        """Get formatted statistics"""
        if not self.profiler:
            return "No profiling performed"
        stream = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.print_stats(limit)
        return stream.getvalue()
    
    def get_top_functions(self, limit=10):
        """Get slowest functions"""
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
# BREAKPOINT MANAGER
# ============================================================
class BreakpointManager:
    """Manages visual breakpoints"""
    
    def __init__(self):
        self.breakpoints = set()  # Line numbers
        self.enabled = True
    
    def toggle(self, line_num):
        """Toggle breakpoint"""
        if line_num in self.breakpoints:
            self.breakpoints.remove(line_num)
            return False
        else:
            self.breakpoints.add(line_num)
            return True
    
    def clear_all(self):
        """Remove all breakpoints"""
        self.breakpoints.clear()
    
    def has_breakpoint(self, line_num):
        """Check if line has breakpoint"""
        return line_num in self.breakpoints
    
    def get_all(self):
        """Get all breakpoints"""
        return sorted(self.breakpoints)

# ============================================================
# CODE EDITOR WITH SYNTAX HIGHLIGHTING
# ============================================================
class CodeEditor(scrolledtext.ScrolledText):
    """Code editor with Python syntax highlighting and breakpoints"""
    
    def __init__(self, master, breakpoint_manager=None, theme=None, **kwargs):
        super().__init__(master, **kwargs)
        self.breakpoint_manager = breakpoint_manager
        self.theme = theme or THEMES["Cyberpunk"]
        
        # Base configuration
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
            tabs=('1c',)  # 4 spaces
        )
        
        # Line numbers with breakpoint support
        self.line_numbers = tk.Canvas(master, width=50, bg="#1a1a1a", highlightthickness=0)
        self.line_numbers.bind('<Button-1>', self.on_line_click)
        
        # Syntax highlighting tags
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
        
        # Highlighting patterns
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
        
        # Initial update
        self.after(100, self.update_line_numbers)
    
    def apply_theme(self, theme):
        """Apply new theme"""
        self.theme = theme
        self.configure(
            bg=self.theme["editor_bg"],
            fg=self.theme["fg"],
            insertbackground=self.theme["accent"]
        )
        # Reconfigure tags
        self.tag_configure("keyword", foreground=self.theme["keyword"])
        self.tag_configure("builtin", foreground=self.theme["builtin"])
        self.tag_configure("string", foreground=self.theme["string"])
        self.tag_configure("comment", foreground=self.theme["comment"])
        self.tag_configure("number", foreground=self.theme["number"])
        self.highlight_syntax()
    
    def on_line_click(self, event):
        """Handle line number click (toggle breakpoint)"""
        if not self.breakpoint_manager:
            return
        # Calculate clicked line number
        y = event.y
        total_lines = max(1, int(self.index('end-1c').split('.')[0]))
        line_height = max(1, self.winfo_height() / total_lines)
        line_num = int(y / line_height) + 1
        # Toggle breakpoint
        is_active = self.breakpoint_manager.toggle(line_num)
        self.update_line_numbers()
        return is_active
    
    def insert_tab(self, event):
        """Insert 4 spaces instead of tab"""
        self.insert(tk.INSERT, "    ")
        return "break"
    
    def auto_indent(self, event):
        """Smart auto-indentation"""
        # Get current line
        line = self.get("insert linestart", "insert lineend")
        indent = len(line) - len(line.lstrip())
        # If line ends with ':', increase indent
        if line.rstrip().endswith(':'):
            indent += 4
        self.insert(tk.INSERT, '\n' + ' ' * indent)
        return "break"
    
    def duplicate_line(self, event):
        """Duplicate current line (Ctrl+D)"""
        line = self.get("insert linestart", "insert lineend")
        self.insert("insert lineend", '\n' + line)
        return "break"
    
    def toggle_comment(self, event):
        """Toggle comment on current line (Ctrl+/)"""
        line_start = self.index("insert linestart")
        line_end = self.index("insert lineend")
        line = self.get(line_start, line_end)
        if line.lstrip().startswith('#'):
            # Uncomment
            new_line = line.replace('#', '', 1)
        else:
            # Comment
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + '# ' + line.lstrip()
        self.delete(line_start, line_end)
        self.insert(line_start, new_line)
        return "break"
    
    def on_key_release(self, event):
        """Update after key press"""
        if event.keysym not in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R'):
            self.after_idle(self.highlight_syntax)
            self.after_idle(self.update_line_numbers)
    
    def highlight_syntax(self):
        """Syntax highlighting"""
        # Remove all tags
        for tag in ('keyword', 'builtin', 'string', 'comment', 'number', 'decorator', 'class', 'function'):
            self.tag_remove(tag, "1.0", tk.END)
        content = self.get("1.0", tk.END)
        # Comments (first to avoid highlighting inside comments)
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
        """Update line numbering with breakpoints"""
        self.line_numbers.delete('all')
        line_count = int(self.index('end-1c').split('.')[0])
        for i in range(1, line_count):
            y = (i - 1) * 16 + 2  # 16px per line
            # Breakpoint?
            if self.breakpoint_manager and self.breakpoint_manager.has_breakpoint(i):
                # Red circle
                self.line_numbers.create_oval(5, y, 15, y+10, fill='#ff5252', outline='#ff0000')
            # Line number
            color = '#00ffcc' if (self.breakpoint_manager and self.breakpoint_manager.has_breakpoint(i)) else '#666'
            self.line_numbers.create_text(25, y+5, text=str(i), anchor='w',
                                         fill=color, font=("Consolas", 9))
    
    def highlight_error_line(self, line_num):
        """Highlight error line"""
        self.tag_remove("error_line", "1.0", tk.END)
        if line_num:
            self.tag_add("error_line", f"{line_num}.0", f"{line_num}.end")
            self.see(f"{line_num}.0")
    
    def highlight_current_line(self, line_num):
        """Highlight current execution line (step mode)"""
        self.tag_remove("current_line", "1.0", tk.END)
        if line_num:
            self.tag_add("current_line", f"{line_num}.0", f"{line_num}.end")
            self.see(f"{line_num}.0")

# ============================================================
# EMBEDDED TERMINAL
# ============================================================
class EmbeddedTerminal:
    """Embedded bash terminal in the interface"""
    
    def __init__(self, output_widget):
        self.output = output_widget
        self.process = None
        self.cwd = os.path.expanduser("~")
    
    def execute_command(self, command):
        """Execute shell command"""
        if command.strip().startswith('cd '):
            # Special cd command
            path = command.strip()[3:].strip()
            try:
                new_path = os.path.expanduser(path)
                if os.path.isdir(new_path):
                    self.cwd = new_path
                    self.output.insert(tk.END, f"📁 {self.cwd}\n", "success")
                else:
                    self.output.insert(tk.END, f"❌ Directory not found: {path}\n", "error")
            except Exception as e:
                self.output.insert(tk.END, f"❌ Error: {e}\n", "error")
            return
        
        # Other commands
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
            self.output.insert(tk.END, f"❌ Error: {e}\n", "error")

# ============================================================
# DEBUGGER ENGINE
# ============================================================
class PythonDebugger:
    """Python debugging engine with step-by-step execution"""
    
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
        self.temp_dir = DEBUG_ROOT / "temp" / "debug"
    
    def execute_code(self, code, filename="<editor>", args=None, profile=False):
        """Execute Python code and capture outputs"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to history
        self.execution_history.append({
            "timestamp": timestamp,
            "filename": filename,
            "code": code,
            "args": args or [],
            "profiled": profile
        })
        
        # Profiling?
        if profile:
            self.profiler.start()
        
        # Create temporary file in debug folder
        temp_file = self.temp_dir / f"kerberos_debug_{int(time.time())}.py"
        temp_file.write_text(code, encoding='utf-8')
        
        # Prepare command
        cmd = [sys.executable, str(temp_file)]
        if args:
            cmd.extend(args)
        
        try:
            # Execute with stdout/stderr capture
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Thread for stdout
            def read_stdout():
                for line in iter(self.process.stdout.readline, ''):
                    if self.output_callback:
                        self.output_callback(line)
                self.process.stdout.close()
            
            # Thread for stderr
            def read_stderr():
                stderr_content = []
                for line in iter(self.process.stderr.readline, ''):
                    stderr_content.append(line)
                    if self.output_callback:
                        self.output_callback(line, is_error=True)
                self.process.stderr.close()
                # Analyze errors
                if stderr_content and self.error_callback:
                    full_error = ''.join(stderr_content)
                    self.error_callback(full_error, code, filename)
            
            # Launch threads
            threading.Thread(target=read_stdout, daemon=True).start()
            threading.Thread(target=read_stderr, daemon=True).start()
            
            # Wait for completion
            def wait_finish():
                self.process.wait()
                # Stop profiler
                if profile:
                    self.profiler.stop()
                if self.finish_callback:
                    self.finish_callback(self.process.returncode, profile)
                # Cleanup temp file (keep last 10 files for debugging)
                self._cleanup_temp_files()
            
            threading.Thread(target=wait_finish, daemon=True).start()
            return True
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e), code, filename)
            temp_file.unlink(missing_ok=True)
            return False
    
    def _cleanup_temp_files(self):
        """Keep only last 10 temp files"""
        files = sorted(self.temp_dir.glob("kerberos_debug_*.py"), key=os.path.getmtime, reverse=True)
        for f in files[10:]:
            f.unlink(missing_ok=True)
    
    def stop_execution(self):
        """Stop current execution"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
    
    def parse_traceback(self, error_text, code, filename):
        """Parse Python traceback and extract information"""
        lines = error_text.strip().split('\n')
        # Find last line (error message)
        error_type = "UnknownError"
        error_msg = "Unknown error"
        for line in reversed(lines):
            if ':' in line and not line.strip().startswith('File'):
                parts = line.split(':', 1)
                error_type = parts[0].strip()
                error_msg = parts[1].strip() if len(parts) > 1 else parts[0]
                break
        # Find line number
        line_num = None
        file_context = None
        for line in lines:
            if 'File' in line and 'line' in line:
                match = re.search(r'line (\d+)', line)
                if match:
                    line_num = int(match.group(1))
                    # Next line contains code
                    idx = lines.index(line)
                    if idx + 1 < len(lines):
                        file_context = lines[idx + 1].strip()
        # Generate suggestions
        suggestions = self.generate_suggestions(error_type, error_msg, file_context)
        # AI AUTO-CORRECTION (gerex-based)
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
        """Generate automatic code correction"""
        if not line_num or not context:
            return None
        lines = full_code.split('\n')
        if line_num > len(lines):
            return None
        error_line = lines[line_num - 1]
        fix = None
        # NameError: define variable
        if error_type == "NameError":
            var_match = re.search(r"name '(\w+)' is not defined", error_msg)
            if var_match:
                var_name = var_match.group(1)
                # Find indentation
                indent = len(error_line) - len(error_line.lstrip())
                fix = ' ' * indent + f"{var_name} = None  # 🤖 Auto-fix: Variable defined"
        # ZeroDivisionError: add check
        elif error_type == "ZeroDivisionError":
            indent = len(error_line) - len(error_line.lstrip())
            # Extract divisor
            if '/' in error_line:
                parts = error_line.split('/')
                divisor = parts[1].strip().split()[0]
                fix = ' ' * indent + f"if {divisor} != 0:  # 🤖 Auto-fix: Division by zero check\n"
                fix += ' ' * (indent + 4) + error_line.strip()
        # TypeError: type conversion
        elif error_type == "TypeError" and "unsupported operand" in error_msg:
            # Try to detect missing conversion
            if '+' in error_line:
                fix = error_line + "  # 🤖 Use str() for conversion"
        return fix
    
    def generate_suggestions(self, error_type, error_msg, context):
        """Generate correction suggestions"""
        suggestions = []
        # NameError
        if error_type == "NameError":
            var_match = re.search(r"name '(\w+)' is not defined", error_msg)
            if var_match:
                var_name = var_match.group(1)
                suggestions.append(f"💡 Declare variable '{var_name}' before use")
                suggestions.append(f"💡 Check spelling of '{var_name}'")
                suggestions.append(f"💡 Import module if it's an external function")
        # SyntaxError
        elif error_type == "SyntaxError":
            if "invalid syntax" in error_msg:
                suggestions.append("💡 Check parentheses, brackets and quotes")
                suggestions.append("💡 Check indentation (4 spaces per level)")
            if "EOL while scanning" in error_msg:
                suggestions.append("💡 Missing closing quote")
        # IndentationError
        elif error_type == "IndentationError":
            suggestions.append("💡 Use 4 spaces for indentation (no tabs)")
            suggestions.append("💡 Verify all blocks are properly indented")
        # AttributeError
        elif error_type == "AttributeError":
            suggestions.append("💡 Object doesn't have this attribute/method")
            suggestions.append("💡 Use dir(object) to see available attributes")
        # TypeError
        elif error_type == "TypeError":
            if "unsupported operand" in error_msg:
                suggestions.append("💡 Trying to operate on incompatible types")
                suggestions.append("💡 Convert values to correct type (int, str, float)")
        # ImportError / ModuleNotFoundError
        elif error_type in ("ImportError", "ModuleNotFoundError"):
            module_match = re.search(r"No module named '(\w+)'", error_msg)
            if module_match:
                module = module_match.group(1)
                suggestions.append(f"💡 Install module: pip install {module}")
        # KeyError
        elif error_type == "KeyError":
            suggestions.append("💡 Key doesn't exist in dictionary")
            suggestions.append("💡 Use .get(key, default) to avoid error")
        # IndexError
        elif error_type == "IndexError":
            suggestions.append("💡 Index out of list bounds")
            suggestions.append("💡 Check length with len() before accessing")
        # ZeroDivisionError
        elif error_type == "ZeroDivisionError":
            suggestions.append("💡 Dividing by zero")
            suggestions.append("💡 Verify divisor is not equal to 0")
        return suggestions

# ============================================================
# MAIN APPLICATION
# ============================================================
class KerberosDebuggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🐺 Kerberos Debugger v4.1 - Architecture Modulaire & Privacy First")
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
        self.gerex_analyzer = GerexAnalyzer()  # Module gerex intégré
        
        # Apply theme to main window
        self.root.configure(bg=self.current_theme["bg"])
        
        # Interface creation
        self.create_menu()
        self.create_notebook()
        
        # Debugger callbacks
        self.debugger.output_callback = self.on_output
        self.debugger.error_callback = self.on_error
        self.debugger.finish_callback = self.on_finish
        
        # Keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<F5>', lambda e: self.run_code())
        self.root.bind('<F6>', lambda e: self.analyze_code())
        self.root.bind('<F7>', lambda e: self.run_with_profiling())
        self.root.bind('<F9>', lambda e: self.toggle_breakpoint_current_line())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
        # Terminal
        self.terminal = None
        
        # Status bar
        self.create_statusbar()
        
        # Welcome message
        self.log_console("🐺 Kerberos Debugger v4.1 démarré\n", "info")
        self.log_console(f"✅ Dossiers créés : temp/debug, modules, IA/embarquees, IA/providers\n", "success")
        self.log_console("🔒 IA désactivée par défaut — privacy respectée\n", "info")
        self.log_console("🔍 Module gerex disponible — toggle dans l'onglet Traceback\n\n", "info")
    
    def create_statusbar(self):
        """Status bar at bottom"""
        statusbar = tk.Frame(self.root, bg=self.current_theme["bg"], height=25)
        statusbar.pack(side="bottom", fill="x", padx=5, pady=2)
        self.status_file = tk.Label(statusbar, text="📄 No file", bg=self.current_theme["bg"],
                                   fg=self.current_theme["accent"], font=("Consolas", 9), anchor="w")
        self.status_file.pack(side="left", padx=10)
        self.status_theme = tk.Label(statusbar, text=f"🎨 {self.current_theme_name}", bg=self.current_theme["bg"],
                                   fg=self.current_theme["fg"], font=("Consolas", 9))
        self.status_theme.pack(side="right", padx=10)
        self.status_line = tk.Label(statusbar, text="Line: 1, Col: 0", bg=self.current_theme["bg"],
                                   fg=self.current_theme["fg"], font=("Consolas", 9))
        self.status_line.pack(side="right", padx=10)
    
    def setup_style(self):
        """Style configuration"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        # Standard widgets
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
        """Enhanced menu bar"""
        menubar = tk.Menu(self.root, bg="#2d2d2d", fg="#e0e0e0", activebackground="#3a3a3a")
        self.root.config(menu=menubar)
        
        # File
        file_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="📁 File", menu=file_menu)
        file_menu.add_command(label="New (Ctrl+N)", command=self.new_file)
        file_menu.add_command(label="Open (Ctrl+O)", command=self.open_file)
        file_menu.add_command(label="Save (Ctrl+S)", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export HTML Report", command=self.export_html_report)
        file_menu.add_separator()
        file_menu.add_command(label="Quit (Ctrl+Q)", command=self.root.quit())
        
        # Edit
        edit_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="✏️ Edit", menu=edit_menu)
        edit_menu.add_command(label="Duplicate Line (Ctrl+D)", command=lambda: self.code_editor.event_generate('<Control-d>'))
        edit_menu.add_command(label="Toggle Comment (Ctrl+/)", command=lambda: self.code_editor.event_generate('<Control-slash>'))
        edit_menu.add_separator()
        edit_menu.add_command(label="Find (Ctrl+F)", command=self.show_find_dialog)
        edit_menu.add_command(label="Replace (Ctrl+H)", command=self.show_replace_dialog)
        
        # Run
        run_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="▶️ Run", menu=run_menu)
        run_menu.add_command(label="Run (F5)", command=self.run_code)
        run_menu.add_command(label="Run with Profiling (F7)", command=self.run_with_profiling)
        run_menu.add_command(label="Static Analysis (F6)", command=self.analyze_code)
        run_menu.add_command(label="Stop", command=self.stop_code)
        run_menu.add_separator()
        run_menu.add_command(label="Clear Console", command=self.clear_console)
        run_menu.add_separator()
        run_menu.add_command(label="Configure Arguments...", command=self.configure_args)
        
        # Debug
        debug_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="🐛 Debug", menu=debug_menu)
        debug_menu.add_command(label="Toggle Breakpoint (F9)", command=self.toggle_breakpoint_current_line)
        debug_menu.add_command(label="Clear All Breakpoints", command=self.clear_all_breakpoints)
        debug_menu.add_command(label="Breakpoints List", command=self.show_breakpoints_list)
        debug_menu.add_separator()
        debug_menu.add_command(label="Apply AI Auto-Fix", command=self.apply_auto_fix)
        
        # Tools
        tools_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="🔧 Tools", menu=tools_menu)
        tools_menu.add_command(label="Error Search", command=lambda: self.notebook.select(1))
        tools_menu.add_command(label="History", command=self.show_history)
        tools_menu.add_command(label="Embedded Terminal", command=lambda: self.notebook.select(3))
        tools_menu.add_separator()
        self.watch_var = tk.BooleanVar(value=False)
        tools_menu.add_checkbutton(label="👁️ Auto Watch", variable=self.watch_var, command=self.toggle_watch)
        tools_menu.add_separator()
        tools_menu.add_command(label="Performance Report", command=self.show_performance_report)
        
        # Appearance
        appearance_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="🎨 Theme", menu=appearance_menu)
        for theme_name in THEMES.keys():
            appearance_menu.add_command(label=theme_name, command=lambda t=theme_name: self.change_theme(t))
        appearance_menu.add_separator()
        appearance_menu.add_command(label="Customize Colors...", command=self.customize_colors)
        
        # Help
        help_menu = tk.Menu(menubar, tearoff=0, bg="#2d2d2d", fg="#e0e0e0")
        menubar.add_cascade(label="❓ Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_notebook(self):
        """Enhanced main tabs"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        # Tab 1: Debugger
        self.create_debugger_tab()
        
        # Tab 2: Error Search
        self.create_search_tab()
        
        # Tab 3: History
        self.create_history_tab()
        
        # Tab 4: Embedded Terminal
        self.create_terminal_tab()
    
    def create_debugger_tab(self):
        """Enhanced debugger tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🚀 Debugger")
        
        # Vertical PanedWindow
        paned = tk.PanedWindow(frame, orient=tk.VERTICAL, bg=self.current_theme["bg"], sashwidth=5, sashrelief=tk.RAISED)
        paned.pack(fill="both", expand=True)
        
        # === TOP PART: EDITOR ===
        editor_container = ttk.Frame(paned)
        paned.add(editor_container, height=500)
        
        # Enhanced toolbar
        toolbar = ttk.Frame(editor_container)
        toolbar.pack(fill="x", pady=(0, 5))
        
        # Current file
        self.file_label = tk.Label(toolbar, text="📄 No file", bg=self.current_theme["bg"],
                                 fg=self.current_theme["accent"], font=("Consolas", 10, "bold"), anchor="w")
        self.file_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # Buttons
        ttk.Button(toolbar, text="📂 Open", command=self.open_file, width=12).pack(side="left", padx=2)
        ttk.Button(toolbar, text="💾 Save", command=self.save_file, width=12).pack(side="left", padx=2)
        ttk.Button(toolbar, text="▶️ Run (F5)", command=self.run_code, width=14).pack(side="left", padx=2)
        ttk.Button(toolbar, text="📊 Profile (F7)", command=self.run_with_profiling, width=16).pack(side="left", padx=2)
        ttk.Button(toolbar, text="🔍 Analyze (F6)", command=self.analyze_code, width=16).pack(side="left", padx=2)
        ttk.Button(toolbar, text="⏹️ Stop", command=self.stop_code, style="Danger.TButton", width=12).pack(side="left", padx=2)
        
        # Arguments
        arg_frame = ttk.Frame(toolbar)
        arg_frame.pack(side="right", padx=5)
        tk.Label(arg_frame, text="Args:", bg=self.current_theme["bg"], fg=self.current_theme["fg"],
               font=("Consolas", 9)).pack(side="left")
        self.args_entry = tk.Entry(arg_frame, width=20, bg=self.current_theme["editor_bg"],
                                 fg=self.current_theme["accent"], font=("Consolas", 9))
        self.args_entry.pack(side="left", padx=5)
        
        # Editor + line numbers with breakpoints
        editor_frame = ttk.Frame(editor_container)
        editor_frame.pack(fill="both", expand=True)
        self.code_editor = CodeEditor(editor_frame, height=20,
                                    breakpoint_manager=self.breakpoint_manager,
                                    theme=self.current_theme)
        self.code_editor.line_numbers.pack(side="left", fill="y")
        self.code_editor.pack(side="right", fill="both", expand=True)
        
        # Cursor position binding
        self.code_editor.bind('<KeyRelease>', self.update_cursor_position)
        self.code_editor.bind('<ButtonRelease-1>', self.update_cursor_position)
        
        # Example code
        example_code = '''# 🐺 Kerberos Debugger v4.1 - Architecture Modulaire & Privacy First
# Write your code here and press F5 to run!
# F9 on a line = toggle breakpoint 🔴
# F7 = run with performance profiling 📊

def greet(name):
    """Greeting function"""
    message = f"Hello {name}! 👋"
    return message

# Try new features:
user_name = "Victor"
print(greet(user_name))

# 1. Click line number to add breakpoint 🔴
# 2. Press F7 to see performance metrics
# 3. Toggle gerex in Traceback tab for regex analysis
# 4. IA remains OFF by default — privacy first!

print("✅ Everything works! Try breakpoints and profiling.")
'''
        self.code_editor.insert("1.0", example_code)
        self.code_editor.highlight_syntax()
        self.code_editor.update_line_numbers()
        
        # === BOTTOM PART: CONSOLE + ANALYSIS ===
        bottom_container = ttk.Frame(paned)
        paned.add(bottom_container, height=300)
        
        # Sub-tabs
        bottom_notebook = ttk.Notebook(bottom_container)
        bottom_notebook.pack(fill="both", expand=True)
        
        # Console output
        console_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(console_frame, text="📟 Console")
        
        # Console status bar
        console_status = ttk.Frame(console_frame)
        console_status.pack(fill="x", pady=(0, 5))
        self.status_label = tk.Label(console_status, text="⚪ Ready", bg=self.current_theme["bg"],
                                    fg=self.current_theme["success"], font=("Consolas", 9, "bold"), anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        ttk.Button(console_status, text="🗑️ Clear", command=self.clear_console, width=10).pack(side="right")
        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, font=("Consolas", 9),
                                               bg=self.current_theme["console_bg"], fg=self.current_theme["fg"], height=15)
        self.console.pack(fill="both", expand=True)
        self.console.tag_configure("output", foreground=self.current_theme["fg"])
        self.console.tag_configure("error", foreground=self.current_theme["error"])
        self.console.tag_configure("success", foreground=self.current_theme["success"])
        self.console.tag_configure("info", foreground=self.current_theme["info"])
        
        # Static analysis
        analysis_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(analysis_frame, text="🔍 Static Analysis")
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap=tk.WORD, font=("Consolas", 9),
                                                     bg=self.current_theme["console_bg"], fg="#ffcc00", height=15)
        self.analysis_text.pack(fill="both", expand=True, pady=5)
        self.analysis_text.tag_configure("error", foreground=self.current_theme["error"], font=("Consolas", 9, "bold"))
        self.analysis_text.tag_configure("warning", foreground=self.current_theme["warning"])
        self.analysis_text.tag_configure("success", foreground=self.current_theme["success"])
        
        # Detailed traceback with gerex + auto-fix
        traceback_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(traceback_frame, text="🐛 Traceback + Auto-Fix")
        
        # gerex bar (NOUVEAU)
        gerex_bar = ttk.Frame(traceback_frame)
        gerex_bar.pack(fill="x", pady=(0, 5))
        
        self.gerex_enabled = tk.BooleanVar(value=False)
        gerex_toggle = tk.Checkbutton(
            gerex_bar,
            text="🔍 gerex (Regex Analyzer)",
            variable=self.gerex_enabled,
            command=self.toggle_gerex,
            bg=self.current_theme["bg"],
            fg="#00ffcc",
            selectcolor="#1a1a1a",
            font=("Consolas", 10, "bold")
        )
        gerex_toggle.pack(side="left", padx=10)
        
        self.gerex_status_label = tk.Label(
            gerex_bar,
            text="🔴 DÉSACTIVÉ",
            bg=self.current_theme["bg"],
            fg="#ff5252",
            font=("Consolas", 9, "bold")
        )
        self.gerex_status_label.pack(side="left", padx=5)
        
        tk.Label(
            gerex_bar,
            text="ℹ️ Analyse 100% locale — zéro connexion réseau",
            bg=self.current_theme["bg"],
            fg="#666",
            font=("Consolas", 8)
        ).pack(side="left", padx=10)
        
        # Auto-fix bar
        autofix_bar = ttk.Frame(traceback_frame)
        autofix_bar.pack(fill="x", pady=(0, 5))
        tk.Label(autofix_bar, text="🤖 AI Auto-Correction:", bg=self.current_theme["bg"],
               fg=self.current_theme["accent"], font=("Consolas", 9, "bold")).pack(side="left", padx=10)
        ttk.Button(autofix_bar, text="✨ Apply Fix", command=self.apply_auto_fix).pack(side="left", padx=5)
        ttk.Button(autofix_bar, text="📋 Copy Fixed Code", command=self.copy_auto_fix).pack(side="left", padx=5)
        
        self.traceback_text = scrolledtext.ScrolledText(traceback_frame, wrap=tk.WORD, font=("Consolas", 9),
                                                      bg=self.current_theme["console_bg"],
                                                      fg=self.current_theme["error"], height=15)
        self.traceback_text.pack(fill="both", expand=True, pady=5)
        self.traceback_text.tag_configure("suggestion", foreground=self.current_theme["accent"],
                                        font=("Consolas", 9, "bold"))
        self.traceback_text.tag_configure("line", foreground="#ffcc00", background="#3d1f1f")
        self.traceback_text.tag_configure("autofix", foreground=self.current_theme["success"],
                                        font=("Consolas", 9, "bold"))
        self.traceback_text.tag_configure("gerex", foreground="#00ffcc", font=("Consolas", 9, "bold"))
        
        # Performance (NEW!)
        perf_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(perf_frame, text="📊 Performance")
        perf_toolbar = ttk.Frame(perf_frame)
        perf_toolbar.pack(fill="x", pady=(0, 5))
        tk.Label(perf_toolbar, text="⏱️ Performance Profiling", bg=self.current_theme["bg"],
               fg=self.current_theme["info"], font=("Consolas", 10, "bold")).pack(side="left", padx=10)
        ttk.Button(perf_toolbar, text="📈 Graph", command=self.show_performance_graph).pack(side="right", padx=5)
        ttk.Button(perf_toolbar, text="💾 Export CSV", command=self.export_performance_csv).pack(side="right", padx=5)
        self.perf_text = scrolledtext.ScrolledText(perf_frame, wrap=tk.WORD, font=("Consolas", 9),
                                                 bg=self.current_theme["console_bg"],
                                                 fg=self.current_theme["info"], height=15)
        self.perf_text.pack(fill="both", expand=True, pady=5)
        self.perf_text.tag_configure("fast", foreground=self.current_theme["success"])
        self.perf_text.tag_configure("slow", foreground=self.current_theme["warning"])
        self.perf_text.tag_configure("critical", foreground=self.current_theme["error"],
                                   font=("Consolas", 9, "bold"))
        
        # Breakpoints (NEW!)
        bp_frame = ttk.Frame(bottom_notebook)
        bottom_notebook.add(bp_frame, text="🔴 Breakpoints")
        bp_toolbar = ttk.Frame(bp_frame)
        bp_toolbar.pack(fill="x", pady=(0, 5))
        tk.Label(bp_toolbar, text="🔴 Active Breakpoints", bg=self.current_theme["bg"],
               fg=self.current_theme["error"], font=("Consolas", 10, "bold")).pack(side="left", padx=10)
        ttk.Button(bp_toolbar, text="🗑️ Clear All", command=self.clear_all_breakpoints).pack(side="right", padx=5)
        ttk.Button(bp_toolbar, text="🔄 Refresh", command=self.refresh_breakpoints_list).pack(side="right", padx=5)
        self.bp_list = tk.Listbox(bp_frame, font=("Consolas", 9), bg=self.current_theme["console_bg"],
                                fg=self.current_theme["error"], height=15)
        self.bp_list.pack(fill="both", expand=True, pady=5)
        self.bp_list.bind('<Double-Button-1>', self.goto_breakpoint)
    
    def create_search_tab(self):
        """Error search tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔍 Search")
        main = tk.Frame(frame, bg="#1a1a1a", padx=20, pady=15)
        main.pack(fill="both", expand=True)
        
        # Title
        tk.Label(main, text="🔍 MULTI-FORMAT ERROR SEARCH",
               bg="#1a1a1a", fg="#bb86fc", font=("Consolas", 16, "bold")).pack(pady=(0, 15))
        
        # Error input
        err_frame = tk.Frame(main, bg="#1a1a1a")
        err_frame.pack(fill="x", pady=(0, 12))
        tk.Label(err_frame, text="Error to search (e.g., ' background'):", bg="#1a1a1a", fg="#4fc3f7", font=("Consolas", 11)).pack(anchor="w")
        self.err_entry = tk.Entry(err_frame, font=("Consolas", 11), width=70,
                                bg="#252525", fg="#00ffcc", insertbackground="#00ffcc")
        self.err_entry.pack(pady=(5, 0), fill="x")
        
        # Folder + Extensions
        path_ext_frame = tk.Frame(main, bg="#1a1a1a")
        path_ext_frame.pack(fill="x", pady=(0, 12))
        # Folder
        path_frame = tk.Frame(path_ext_frame, bg="#1a1a1a")
        path_frame.pack(side="left", fill="x", expand=True)
        tk.Label(path_frame, text="Folder to analyze:", bg="#1a1a1a", fg="#e0e0e0").pack(anchor="w")
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
        tk.Label(ext_frame, text="Extensions:", bg="#1a1a1a", fg="#bb86fc", font=("Consolas", 10, "bold")).pack(anchor="w")
        self.ext_py = tk.BooleanVar(value=True)
        self.ext_csv = tk.BooleanVar(value=True)
        self.ext_json = tk.BooleanVar(value=False)
        self.ext_txt = tk.BooleanVar(value=False)
        ttk.Checkbutton(ext_frame, text=".py", variable=self.ext_py).pack(anchor="w")
        ttk.Checkbutton(ext_frame, text=".csv", variable=self.ext_csv).pack(anchor="w")
        ttk.Checkbutton(ext_frame, text=".json", variable=self.ext_json).pack(anchor="w")
        ttk.Checkbutton(ext_frame, text=".txt", variable=self.ext_txt).pack(anchor="w")
        
        # Buttons
        btn_frame = tk.Frame(main, bg="#1a1a1a")
        btn_frame.pack(fill="x", pady=(0, 15))
        ttk.Button(btn_frame, text="🚀 START SEARCH", command=self.start_search, width=22).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="💾 TXT REPORT", command=self.save_search_report, width=18).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ CLEAR", command=self.clear_search, width=12).pack(side="right", padx=5)
        
        # Results
        tk.Label(main, text="Results:", bg="#1a1a1a", fg="#4CAF50", font=("Consolas", 11, "bold")).pack(anchor="w")
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
        """Execution history tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📚 History")
        # Toolbar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", pady=10, padx=10)
        tk.Label(toolbar, text="📚 Last 50 Executions", bg="#1a1a1a", fg="#bb86fc",
               font=("Consolas", 12, "bold")).pack(side="left", padx=10)
        ttk.Button(toolbar, text="🗑️ Clear History", command=self.clear_history).pack(side="right", padx=5)
        ttk.Button(toolbar, text="🔄 Refresh", command=self.refresh_history).pack(side="right", padx=5)
        # List
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
        # Details
        details_frame = ttk.Frame(frame)
        details_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(details_frame, text="Details:", bg="#1a1a1a", fg="#4fc3f7", font=("Consolas", 10, "bold")).pack(anchor="w")
        self.history_details = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, font=("Consolas", 9),
                                                       bg="#0d0d0d", fg="#e0e0e0", height=8)
        self.history_details.pack(fill="both", expand=True, pady=5)
    
    def create_terminal_tab(self):
        """Embedded terminal tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🖥️ Terminal")
        # Title bar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", pady=(10, 5), padx=10)
        tk.Label(toolbar, text="🖥️ EMBEDDED BASH TERMINAL", bg=self.current_theme["bg"],
               fg=self.current_theme["info"], font=("Consolas", 12, "bold")).pack(side="left", padx=10)
        ttk.Button(toolbar, text="🗑️ Clear", command=self.clear_terminal).pack(side="right", padx=5)
        ttk.Button(toolbar, text="📁 PWD", command=self.show_pwd).pack(side="right", padx=5)
        # Output area
        self.terminal_output = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 10),
                                                       bg=self.current_theme["console_bg"],
                                                       fg=self.current_theme["fg"], height=25)
        self.terminal_output.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.terminal_output.tag_configure("output", foreground=self.current_theme["fg"])
        self.terminal_output.tag_configure("error", foreground=self.current_theme["error"])
        self.terminal_output.tag_configure("success", foreground=self.current_theme["success"])
        self.terminal_output.tag_configure("prompt", foreground=self.current_theme["accent"], font=("Consolas", 10, "bold"))
        # Command bar
        cmd_frame = ttk.Frame(frame)
        cmd_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(cmd_frame, text="$", bg=self.current_theme["bg"], fg=self.current_theme["accent"],
               font=("Consolas", 11, "bold")).pack(side="left", padx=(0, 5))
        self.terminal_entry = tk.Entry(cmd_frame, font=("Consolas", 10), bg=self.current_theme["editor_bg"],
                                     fg=self.current_theme["accent"], insertbackground=self.current_theme["accent"])
        self.terminal_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.terminal_entry.bind('<Return>', self.execute_terminal_command)
        ttk.Button(cmd_frame, text="▶️ Run", command=lambda: self.execute_terminal_command(None)).pack(side="right")
        # Initialize terminal
        self.terminal = EmbeddedTerminal(self.terminal_output)
        # Welcome message
        welcome = f"""
╔═══════════════════════════════════════════════════════════╗
║  🖥️  EMBEDDED BASH TERMINAL - Kerberos Debugger v4.1    ║
╚═══════════════════════════════════════════════════════════╝
Available commands:
• All bash commands: ls, cd, pwd, cat, grep...
• Python: python script.py, pip install module
• Git: git status, git commit, git push
• System: clear, echo, date, whoami
Examples:
$ python --version
$ pip list
$ ls -la
$ cd /my/project
$ git status
Type your command below and press Enter! 🚀
"""
        self.terminal_output.insert("1.0", welcome, "success")
    
    # ========== DEBUGGER METHODS ==========
    def new_file(self):
        """New file"""
        if messagebox.askyesno("New File", "Create new empty file?"):
            self.current_file = None
            self.file_label.config(text="📄 New file")
            self.code_editor.delete("1.0", tk.END)
            self.clear_console()
    
    def open_file(self):
        """Open file"""
        filename = filedialog.askopenfilename(
            title="Open Python File",
            filetypes=[("Python", "*.py"), ("All", "*.*")]
        )
        if filename:
            try:
                content = Path(filename).read_text(encoding='utf-8')
                self.code_editor.delete("1.0", tk.END)
                self.code_editor.insert("1.0", content)
                self.code_editor.highlight_syntax()
                self.current_file = filename
                self.file_label.config(text=f"📄 {Path(filename).name}")
                self.log_console(f"✅ File opened: {filename}\n", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open file:\n{e}")
    
    def save_file(self):
        """Save file"""
        if self.current_file:
            try:
                content = self.code_editor.get("1.0", tk.END)
                Path(self.current_file).write_text(content, encoding='utf-8')
                self.log_console(f"✅ File saved: {self.current_file}\n", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot save file:\n{e}")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Save as..."""
        filename = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("All", "*.*")]
        )
        if filename:
            try:
                content = self.code_editor.get("1.0", tk.END)
                Path(filename).write_text(content, encoding='utf-8')
                self.current_file = filename
                self.file_label.config(text=f"📄 {Path(filename).name}")
                self.log_console(f"✅ File saved: {filename}\n", "success")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot save file:\n{e}")
    
    def run_code(self):
        """Run code"""
        if self.is_executing:
            messagebox.showwarning("Warning", "Execution already in progress!")
            return
        code = self.code_editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Warning", "Code is empty!")
            return
        
        # Prepare
        self.clear_console()
        self.traceback_text.delete("1.0", tk.END)
        self.is_executing = True
        self.status_label.config(text="🟢 Running...", fg="#4CAF50")
        
        # Arguments
        args_text = self.args_entry.get().strip()
        args = args_text.split() if args_text else None
        
        # Log
        filename = self.current_file or "<editor>"
        self.log_console(f"{'='*60}\n", "info")
        self.log_console(f"▶️  Running: {Path(filename).name if self.current_file else 'Editor Code'}\n", "info")
        self.log_console(f"{'='*60}\n", "info")
        
        # Execute
        self.debugger.execute_code(code, filename, args)
    
    def stop_code(self):
        """Stop execution"""
        if self.is_executing:
            self.debugger.stop_execution()
            self.log_console("\n⏹️ Execution stopped by user\n", "error")
            self.status_label.config(text="🔴 Stopped", fg="#ff5252")
            self.is_executing = False
    
    def analyze_code(self):
        """Static code analysis"""
        code = self.code_editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Warning", "Code is empty!")
            return
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, "🔍 Static analysis in progress...\n", "info")
        # Analyze
        success = self.analyzer.analyze(code, self.current_file or "<editor>")
        report = self.analyzer.get_report()
        # Display
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
        # Select analysis tab
        self.notebook.select(0)  # Debugger
    
    def clear_console(self):
        """Clear console"""
        self.console.delete("1.0", tk.END)
    
    def log_console(self, message, tag="output"):
        """Log to console"""
        self.console.insert(tk.END, message, tag)
        self.console.see(tk.END)
    
    def on_output(self, line, is_error=False):
        """Debugger output callback"""
        tag = "error" if is_error else "output"
        self.log_console(line, tag)
    
    def on_error(self, error_text, code, filename):
        """Debugger error callback"""
        # Parse traceback
        error_info = self.debugger.parse_traceback(error_text, code, filename)
        
        # Display in traceback
        self.traceback_text.delete("1.0", tk.END)
        self.traceback_text.insert(tk.END, "🐛 DETAILED TRACEBACK\n", "error")
        self.traceback_text.insert(tk.END, "="*60 + "\n")
        self.traceback_text.insert(tk.END, error_info["full_traceback"] + "\n")
        
        # Summary
        self.traceback_text.insert(tk.END, f"❌ Type: {error_info['type']}\n", "error")
        self.traceback_text.insert(tk.END, f"💬 Message: {error_info['message']}\n")
        if error_info['line']:
            self.traceback_text.insert(tk.END, f"📍 Line {error_info['line']}\n", "line")
        if error_info['context']:
            self.traceback_text.insert(tk.END, f"   {error_info['context']}\n", "line")
        
        # Highlight in editor
        self.code_editor.highlight_error_line(error_info['line'])
        
        # 🔍 ANALYSE GEREX (si activé)
        if self.gerex_enabled.get():
            gerex_result = self.gerex_analyzer.analyze(error_text)
            if gerex_result:
                self.traceback_text.insert(tk.END, "\n" + "="*60 + "\n", "gerex")
                self.traceback_text.insert(tk.END, f"{gerex_result['emoji']} gerex ANALYSIS (Regex-Based)\n", "gerex")
                self.traceback_text.insert(tk.END, f"   Cause : {gerex_result['cause']}\n", "gerex")
                self.traceback_text.insert(tk.END, f"   Fix   : {gerex_result['fix']}\n", "gerex")
                self.traceback_text.insert(tk.END, f"   Confiance : {int(gerex_result['confidence'] * 100)}%\n", "gerex")
        
        # Suggestions
        if error_info['suggestions']:
            self.traceback_text.insert(tk.END, "💡 CORRECTION SUGGESTIONS\n", "suggestion")
            self.traceback_text.insert(tk.END, "="*60 + "\n", "suggestion")
            for sugg in error_info['suggestions']:
                self.traceback_text.insert(tk.END, f"{sugg}\n", "suggestion")
        
        # Auto-fix
        if error_info['auto_fix']:
            self.traceback_text.insert(tk.END, "\n🤖 AUTO-FIX SUGGESTION\n", "autofix")
            self.traceback_text.insert(tk.END, "="*60 + "\n", "autofix")
            self.traceback_text.insert(tk.END, error_info['auto_fix'] + "\n", "autofix")
    
    def on_finish(self, return_code, profiled=False):
        """Execution finish callback"""
        self.is_executing = False
        if return_code == 0:
            self.log_console(f"\n{'='*60}\n", "success")
            self.log_console("✅ Execution completed successfully (code 0)\n", "success")
            self.log_console(f"{'='*60}\n", "success")
            self.status_label.config(text="✅ Success", fg="#4CAF50")
        else:
            self.log_console(f"\n{'='*60}\n", "error")
            self.log_console(f"❌ Execution finished with error (code {return_code})\n", "error")
            self.log_console(f"{'='*60}\n", "error")
            self.status_label.config(text=f"❌ Error (code {return_code})", fg="#ff5252")
        # Display profiling results
        if profiled:
            self.show_profiling_results()
    
    def toggle_gerex(self):
        """Active/désactive l'analyse gerex"""
        state = self.gerex_enabled.get()
        status = self.gerex_analyzer.toggle(state)
        color = "#00ffcc" if state else "#ff5252"
        self.gerex_status_label.config(text=status, fg=color)
        
        if state:
            self.log_console("🔍 gerex → ACTIVÉ (analyse regex 100% locale)\n", "info")
        else:
            self.log_console("🔍 gerex → DÉSACTIVÉ\n", "info")
    
    # ========== FILE WATCHING ==========
    def toggle_watch(self):
        """Toggle file watching"""
        if self.watch_var.get():
            if not self.current_file:
                messagebox.showwarning("Warning", "Open a file first to enable watching!")
                self.watch_var.set(False)
                return
            self.start_watching()
        else:
            self.stop_watching()
    
    def start_watching(self):
        """Start file watching"""
        if not self.current_file:
            return
        self.watch_active = True
        self.log_console(f"👁️ Watching enabled for: {self.current_file}\n", "info")
        def watch_loop():
            last_mtime = os.path.getmtime(self.current_file)
            while self.watch_active:
                time.sleep(1)
                try:
                    current_mtime = os.path.getmtime(self.current_file)
                    if current_mtime > last_mtime:
                        last_mtime = current_mtime
                        # Reload and run
                        content = Path(self.current_file).read_text(encoding='utf-8')
                        self.code_editor.delete("1.0", tk.END)
                        self.code_editor.insert("1.0", content)
                        self.code_editor.highlight_syntax()
                        self.log_console("\n🔄 File modified, reloading...\n", "info")
                        self.run_code()
                except:
                    pass
        self.file_watcher = threading.Thread(target=watch_loop, daemon=True)
        self.file_watcher.start()
    
    def stop_watching(self):
        """Stop file watching"""
        self.watch_active = False
        if self.current_file:
            self.log_console(f"👁️ Watching disabled\n", "info")
    
    # ========== HISTORY ==========
    def show_history(self):
        """Show history"""
        self.notebook.select(2)
        self.refresh_history()
    
    def refresh_history(self):
        """Refresh history"""
        self.history_list.delete(0, tk.END)
        for i, entry in enumerate(reversed(self.debugger.execution_history)):
            filename = Path(entry['filename']).name if entry['filename'] != "<editor>" else "Editor"
            label = f"{i+1}. [{entry['timestamp']}] {filename}"
            self.history_list.insert(tk.END, label)
    
    def load_from_history(self, event):
        """Load from history"""
        selection = self.history_list.curselection()
        if not selection:
            return
        idx = len(self.debugger.execution_history) - 1 - selection[0]
        entry = list(self.debugger.execution_history)[idx]
        # Load code
        self.code_editor.delete("1.0", tk.END)
        self.code_editor.insert("1.0", entry['code'])
        self.code_editor.highlight_syntax()
        # Show details
        self.history_details.delete("1.0", tk.END)
        self.history_details.insert(tk.END, f"Date: {entry['timestamp']}\n")
        self.history_details.insert(tk.END, f"File: {entry['filename']}\n")
        self.history_details.insert(tk.END, f"Arguments: {' '.join(entry['args']) if entry['args'] else 'None'}\n")
        self.history_details.insert(tk.END, "Code:\n")
        self.history_details.insert(tk.END, "-"*60 + "\n")
        self.history_details.insert(tk.END, entry['code'])
        # Return to debugger
        self.notebook.select(0)
        messagebox.showinfo("History", "Code loaded from history!")
    
    def clear_history(self):
        """Clear history"""
        if messagebox.askyesno("Confirmation", "Clear entire history?"):
            self.debugger.execution_history.clear()
            self.refresh_history()
            self.history_details.delete("1.0", tk.END)
    
    # ========== TERMINAL ==========
    def execute_terminal_command(self, event):
        """Execute terminal command"""
        command = self.terminal_entry.get().strip()
        if not command:
            return
        # Display command
        self.terminal_output.insert(tk.END, f"\n$ {command}\n", "prompt")
        self.terminal_output.see(tk.END)
        # Special command: clear
        if command == "clear":
            self.terminal_output.delete("1.0", tk.END)
            self.terminal_entry.delete(0, tk.END)
            return
        # Execute
        self.terminal.execute_command(command)
        # Clear input
        self.terminal_entry.delete(0, tk.END)
        self.terminal_output.see(tk.END)
    
    def clear_terminal(self):
        """Clear terminal"""
        self.terminal_output.delete("1.0", tk.END)
    
    def show_pwd(self):
        """Show current directory"""
        self.terminal_output.insert(tk.END, f"\n📁 Current directory: {self.terminal.cwd}\n", "success")
        self.terminal_output.see(tk.END)
    
    # ========== ERROR SEARCH ==========
    def browse_search_folder(self):
        """Browse folder for search"""
        folder = filedialog.askdirectory(title="Select folder to analyze")
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)
    
    def start_search(self):
        """Start error search"""
        self.clear_search()
        dossier = self.path_entry.get().strip()
        motif = self.err_entry.get().strip()
        if not motif:
            messagebox.showwarning("⚠️ Warning", "Please enter error text to search")
            return
        if not os.path.isdir(dossier):
            messagebox.showerror("❌ Error", f"Folder does not exist:\n{dossier}")
            return
        
        # Extensions
        extensions = []
        if self.ext_py.get(): extensions.append((".py", "py"))
        if self.ext_csv.get(): extensions.append((".csv", "csv"))
        if self.ext_json.get(): extensions.append((".json", "json"))
        if self.ext_txt.get(): extensions.append((".txt", "txt"))
        if not extensions:
            messagebox.showwarning("⚠️ Warning", "Please check at least one extension")
            return
        
        self.log_search(f"🔍 Searching for: {repr(motif)}\n")
        self.log_search(f"📁 Folder: {dossier}\n")
        self.log_search(f"🗃️ Extensions: {', '.join(ext[0] for ext in extensions)}\n")
        self.log_search("="*80 + "\n", "sep")
        
        # Search
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
                    self.log_search(f"⚠️  Error: {chemin.name}\n")
        
        # Display
        total = sum(len(r) for r in resultats.values())
        if total:
            for ext_type in ["py", "csv", "json", "txt"]:
                if resultats[ext_type]:
                    self.log_search(f"\n📄 .{ext_type.upper()} FILES — {len(resultats[ext_type])} occurrence(s)\n", "fichier")
                    self.log_search("─"*80 + "\n", "sep")
                    for r in resultats[ext_type]:
                        self.log_search_result(r["fichier"], r["ligne"], r["contexte"], motif)
        else:
            self.log_search("✅ No occurrences found\n")
        self.log_search(f"\n{'='*80}\n", "sep")
        self.log_search(f"✅ TOTAL: {total} occurrence(s)\n")
    
    def log_search(self, msg, tag="normal"):
        """Log search"""
        self.search_results.insert(tk.END, msg, tag)
        self.search_results.see(tk.END)
    
    def log_search_result(self, fichier, ligne, contexte, motif):
        """Log search result"""
        self.log_search(f"\n📍 {fichier}\n", "fichier")
        self.log_search(f"   Line {ligne}\n", "ligne")
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
        """Clear search"""
        self.search_results.delete("1.0", tk.END)
    
    def save_search_report(self):
        """Save search report"""
        content = self.search_results.get("1.0", tk.END)
        if not content.strip():
            messagebox.showwarning("Warning", "No results to save")
            return
        filename = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt")]
        )
        if filename:
            try:
                Path(filename).write_text(content, encoding='utf-8')
                messagebox.showinfo("Success", f"Report saved:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot save report:\n{e}")
    
    # ========== UTILITIES ==========
    def show_shortcuts(self):
        """Show shortcuts"""
        shortcuts = """
🎹 KEYBOARD SHORTCUTS
═══════════════════════════════════════
📁 Files
Ctrl+O     : Open file
Ctrl+S     : Save
Ctrl+Q     : Quit
▶️ Execution
F5         : Run code
F6         : Static analysis
F7         : Run with profiling
✏️ Editing
Ctrl+A     : Select all
Ctrl+F     : Find
Tab        : Insert 4 spaces
Enter      : Auto-indent
🔴 Debugging
F9         : Toggle breakpoint
═══════════════════════════════════════
Kerberos Debugger v4.1 - Privacy First
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts)
    
    def update_cursor_position(self, event=None):
        """Update cursor position in status bar"""
        try:
            cursor_pos = self.code_editor.index(tk.INSERT)
            line, col = cursor_pos.split('.')
            self.status_line.config(text=f"Line: {line}, Col: {col}")
        except:
            pass
    
    def toggle_breakpoint_current_line(self):
        """Toggle breakpoint on current line"""
        try:
            cursor_pos = self.code_editor.index(tk.INSERT)
            line = int(cursor_pos.split('.')[0])
            is_active = self.breakpoint_manager.toggle(line)
            self.code_editor.update_line_numbers()
            self.refresh_breakpoints_list()
            if is_active:
                self.log_console(f"🔴 Breakpoint added on line {line}\n", "info")
            else:
                self.log_console(f"⚪ Breakpoint removed on line {line}\n", "info")
        except:
            pass
    
    def clear_all_breakpoints(self):
        """Clear all breakpoints"""
        if messagebox.askyesno("Confirmation", "Remove all breakpoints?"):
            self.breakpoint_manager.clear_all()
            self.code_editor.update_line_numbers()
            self.refresh_breakpoints_list()
            self.log_console("🗑️ All breakpoints removed\n", "info")
    
    def show_breakpoints_list(self):
        """Show breakpoints list"""
        self.notebook.select(0)  # Debugger tab
        self.refresh_breakpoints_list()
    
    def refresh_breakpoints_list(self):
        """Refresh breakpoints list"""
        try:
            self.bp_list.delete(0, tk.END)
            breakpoints = self.breakpoint_manager.get_all()
            if not breakpoints:
                self.bp_list.insert(tk.END, "No active breakpoints")
            else:
                for bp in breakpoints:
                    # Get line content
                    try:
                        line_content = self.code_editor.get(f"{bp}.0", f"{bp}.end").strip()
                        if len(line_content) > 50:
                            line_content = line_content[:47] + "..."
                        self.bp_list.insert(tk.END, f"🔴 Line {bp}: {line_content}")
                    except:
                        self.bp_list.insert(tk.END, f"🔴 Line {bp}")
        except:
            pass
    
    def goto_breakpoint(self, event):
        """Go to breakpoint (double-click)"""
        try:
            selection = self.bp_list.curselection()
            if not selection:
                return
            text = self.bp_list.get(selection[0])
            if "Line" in text:
                line_num = int(text.split("Line ")[1].split(":")[0])
                self.code_editor.see(f"{line_num}.0")
                self.code_editor.mark_set(tk.INSERT, f"{line_num}.0")
                self.code_editor.highlight_current_line(line_num)
        except:
            pass
    
    def run_with_profiling(self):
        """Run with performance profiling"""
        if self.is_executing:
            messagebox.showwarning("Warning", "Execution already in progress!")
            return
        code = self.code_editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Warning", "Code is empty!")
            return
        
        # Prepare
        self.clear_console()
        self.perf_text.delete("1.0", tk.END)
        self.is_executing = True
        self.status_label.config(text="📊 Profiling...", fg=self.current_theme["info"])
        
        # Arguments
        args_text = self.args_entry.get().strip()
        args = args_text.split() if args_text else None
        
        # Log
        filename = self.current_file or "<editor>"
        self.log_console(f"{'='*60}\n", "info")
        self.log_console(f"📊 Profiling: {Path(filename).name if self.current_file else 'Editor Code'}\n", "info")
        self.log_console(f"{'='*60}\n", "info")
        
        # Execute with profiling
        self.debugger.execute_code(code, filename, args, profile=True)
    
    def show_profiling_results(self):
        """Show profiling results"""
        self.perf_text.delete("1.0", tk.END)
        # Title
        self.perf_text.insert(tk.END, "⏱️  PERFORMANCE REPORT\n", "fast")
        self.perf_text.insert(tk.END, "="*60 + "\n", "fast")
        # Full statistics
        stats = self.debugger.profiler.get_stats()
        self.perf_text.insert(tk.END, stats + "\n")
        # Top functions
        self.perf_text.insert(tk.END, "🎯 TOP 10 SLOWEST FUNCTIONS\n", "slow")
        self.perf_text.insert(tk.END, "="*60 + "\n", "slow")
        top_funcs = self.debugger.profiler.get_top_functions(10)
        for func in top_funcs:
            time_ms = func['cumulative_time'] * 1000
            # Color code by time
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
            self.perf_text.insert(tk.END, f"   Time: {time_ms:.2f} ms | Calls: {func['calls']}\n", tag)
            self.perf_text.insert(tk.END, f"   File: {func['file']}, line {func['line']}\n", tag)
    
    def show_performance_report(self):
        """Show performance report in window"""
        if not self.debugger.profiler.profiler:
            messagebox.showinfo("Info", "No profiling performed.\nPress F7 to run with profiling.")
            return
        # Create window
        report_win = tk.Toplevel(self.root)
        report_win.title("📊 Performance Report")
        report_win.geometry("800x600")
        report_win.configure(bg=self.current_theme["bg"])
        # Text
        report_text = scrolledtext.ScrolledText(report_win, wrap=tk.WORD, font=("Consolas", 9),
                                              bg=self.current_theme["console_bg"], fg=self.current_theme["fg"])
        report_text.pack(fill="both", expand=True, padx=10, pady=10)
        # Insert report
        stats = self.debugger.profiler.get_stats()
        report_text.insert("1.0", stats)
        # Close button
        ttk.Button(report_win, text="Close", command=report_win.destroy).pack(pady=10)
    
    def show_performance_graph(self):
        """Show performance graph (placeholder)"""
        messagebox.showinfo("Graph", "Feature in development!\nUse CSV export to create graphs with Excel/Python.")
    
    def export_performance_csv(self):
        """Export performance data to CSV"""
        if not self.debugger.profiler.profiler:
            messagebox.showinfo("Info", "No profiling performed.\nPress F7 to run with profiling.")
            return
        filename = filedialog.asksaveasfilename(
            title="Export Performance CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")]
        )
        if filename:
            try:
                import csv
                top_funcs = self.debugger.profiler.get_top_functions(50)
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Function', 'File', 'Line', 'Calls', 'Total Time (s)', 'Cumulative Time (s)'])
                    for func in top_funcs:
                        writer.writerow([
                            func['function'],
                            func['file'],
                            func['line'],
                            func['calls'],
                            f"{func['total_time']:.6f}",
                            f"{func['cumulative_time']:.6f}"
                        ])
                messagebox.showinfo("Success", f"Performance exported:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot export:\n{e}")
    
    def apply_auto_fix(self):
        """Apply AI auto-correction"""
        # Get last auto-fix
        traceback_content = self.traceback_text.get("1.0", tk.END)
        if "🤖 AUTO-FIX" not in traceback_content:
            messagebox.showinfo("Info", "No auto-correction available.\nRun code with error to see AI suggestions.")
            return
        # Find auto-fix code in traceback
        lines = traceback_content.split('\n')
        auto_fix_code = None
        for i, line in enumerate(lines):
            if "🤖 AUTO-FIX" in line:
                # Next line contains fixed code
                if i + 1 < len(lines):
                    auto_fix_code = lines[i + 1].strip()
                    break
        if auto_fix_code:
            # Confirmation
            if messagebox.askyesno("AI Auto-Correction",
                                 f"Apply this fix?\n{auto_fix_code}\nCode will be added to editor start."):
                # Insert at start
                self.code_editor.insert("1.0", auto_fix_code + "\n")
                self.code_editor.highlight_syntax()
                self.log_console("🤖 Auto-correction applied!\n", "success")
        else:
            messagebox.showinfo("Info", "Cannot find correction code.")
    
    def copy_auto_fix(self):
        """Copy auto-fix code to clipboard"""
        traceback_content = self.traceback_text.get("1.0", tk.END)
        if "🤖 AUTO-FIX" not in traceback_content:
            messagebox.showinfo("Info", "No auto-correction available.")
            return
        # Find auto-fix code
        lines = traceback_content.split('\n')
        auto_fix_code = None
        for i, line in enumerate(lines):
            if "🤖 AUTO-FIX" in line:
                if i + 1 < len(lines):
                    auto_fix_code = lines[i + 1].strip()
                    break
        if auto_fix_code:
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(auto_fix_code)
            self.log_console("📋 Fixed code copied to clipboard!\n", "success")
        else:
            messagebox.showinfo("Info", "Cannot find correction code.")
    
    def change_theme(self, theme_name):
        """Change interface theme"""
        if theme_name not in THEMES:
            return
        self.current_theme_name = theme_name
        self.current_theme = THEMES[theme_name]
        # Apply to root
        self.root.configure(bg=self.current_theme["bg"])
        # Apply to editor
        self.code_editor.apply_theme(self.current_theme)
        # Apply to widgets
        self.file_label.config(bg=self.current_theme["bg"], fg=self.current_theme["accent"])
        self.status_label.config(bg=self.current_theme["bg"])
        self.console.config(bg=self.current_theme["console_bg"], fg=self.current_theme["fg"])
        self.analysis_text.config(bg=self.current_theme["console_bg"])
        self.traceback_text.config(bg=self.current_theme["console_bg"], fg=self.current_theme["error"])
        self.perf_text.config(bg=self.current_theme["console_bg"], fg=self.current_theme["info"])
        # Reconfigure tags
        self.console.tag_configure("error", foreground=self.current_theme["error"])
        self.console.tag_configure("success", foreground=self.current_theme["success"])
        self.console.tag_configure("info", foreground=self.current_theme["info"])
        # Status bar
        self.status_file.config(bg=self.current_theme["bg"], fg=self.current_theme["accent"])
        self.status_theme.config(bg=self.current_theme["bg"], fg=self.current_theme["fg"], text=f"🎨 {theme_name}")
        self.status_line.config(bg=self.current_theme["bg"], fg=self.current_theme["fg"])
        self.log_console(f"🎨 Theme changed: {theme_name}\n", "info")
    
    def customize_colors(self):
        """Customize colors (placeholder)"""
        messagebox.showinfo("Customization",
                          "Feature in development!\n"
                          "Meanwhile, modify the THEMES dictionary\n"
                          "in source code to create custom themes.")
    
    def show_find_dialog(self):
        """Show find dialog (placeholder)"""
        messagebox.showinfo("Find", "Feature in development!\nUse your OS text editor's Ctrl+F.")
    
    def show_replace_dialog(self):
        """Show replace dialog (placeholder)"""
        messagebox.showinfo("Replace", "Feature in development!\nUse your OS text editor's Ctrl+H.")
    
    def configure_args(self):
        """Configure arguments (placeholder)"""
        current_args = self.args_entry.get()
        new_args = tk.simpledialog.askstring("Arguments", "Execution arguments:", initialvalue=current_args)
        if new_args is not None:
            self.args_entry.delete(0, tk.END)
            self.args_entry.insert(0, new_args)
    
    def export_html_report(self):
        """Export HTML report"""
        # Get content
        console_content = self.console.get("1.0", tk.END)
        analysis_content = self.analysis_text.get("1.0", tk.END)
        traceback_content = self.traceback_text.get("1.0", tk.END)
        if not console_content.strip() and not analysis_content.strip() and not traceback_content.strip():
            messagebox.showinfo("Info", "No content to export.\nRun code first (F5 or F7).")
            return
        filename = filedialog.asksaveasfilename(
            title="Export HTML Report",
            defaultextension=".html",
            filetypes=[("HTML", "*.html")]
        )
        if filename:
            try:
                html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Kerberos Debugger Report</title>
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
<h1>🐺 Kerberos Debugger v4.1 Report</h1>
<p><strong>Generated:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
<p><strong>File:</strong> {self.current_file or 'Editor'}</p>
<div class="section">
<h2>📟 Console</h2>
<pre>{console_content}</pre>
</div>
<div class="section">
<h2>🔍 Static Analysis</h2>
<pre>{analysis_content}</pre>
</div>
<div class="section">
<h2>🐛 Traceback</h2>
<pre class="error">{traceback_content}</pre>
</div>
<hr>
<p style="text-align: center; color: #666;">
Kerberos Debugger v4.1 - Victor Pozen 🐺 - Privacy First
</p>
</body>
</html>"""
                Path(filename).write_text(html, encoding='utf-8')
                messagebox.showinfo("Success", f"HTML report exported:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot export:\n{e}")
    
    def show_documentation(self):
        """Show documentation"""
        doc = """
🐺 KERBEROS DEBUGGER v4.1
═════════════════════════════════════
📖 MAIN SHORTCUTS:
F5  : Run code
F6  : Static analysis
F7  : Run with profiling
F9  : Toggle breakpoint on current line
Ctrl+O : Open file
Ctrl+S : Save
Ctrl+D : Duplicate line
Ctrl+/ : Toggle comment
🔴 BREAKPOINTS:
• Click line number
• F9 on current line
• Double-click in list to navigate
📊 PROFILING:
• F7 instead of F5
• See "Performance" tab
• Red = slow, Green = fast
🤖 AI AUTO-FIX:
• Run code with error
• Read AI suggestions
• Click "Apply Fix"
🎨 THEMES:
"Theme" menu → 6 themes available
🔍 GEREX:
• Toggle in "Traceback + Auto-Fix" tab
• 100% local regex analysis
• Zero network connection
🔒 PRIVACY:
• No IA by default
• No silent network calls
• Your code stays on your machine
Open README_KERBEROS_V4.md for full docs!
"""
        messagebox.showinfo("Documentation", doc)
    
    def show_about(self):
        """About"""
        about = """
🐺 KERBEROS DEBUGGER v4.1
═══════════════════════════════════════
Advanced Python Debugger with Privacy First
NEW IN v4.1:
• 🔒 Privacy First architecture
• 🔍 gerex module (regex analyzer)
• 📁 Auto folder creation (temp/debug, modules, IA/)
• 🧩 Modular design (no forced dependencies)
• 🌐 Web links only (no silent API calls)
• 🎨 6 customizable themes
• 🖥️ Embedded bash terminal
• 📈 Performance profiler
• 🔴 Visual breakpoints
License: GPLv3
Author: Victor Pozen 🐺
Version: 4.1
February 2026
═══════════════════════════════════════
"""
        messagebox.showinfo("About", about)

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = KerberosDebuggerApp(root)
        root.mainloop()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        tb_module.print_exc()
        input("\nPress Enter to exit...")