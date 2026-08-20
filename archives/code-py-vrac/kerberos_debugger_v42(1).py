# -*- coding: utf-8 -*-
"""
🐺 KERBEROS DEBUGGER v4.2 — Architecture Modulaire & Privacy First
═══════════════════════════════════════════════════════════════════
• IA désactivée par défaut — toggle explicite requis
• Création auto des dossiers au premier démarrage
• Module gerex intégré (analyse regex 100% locale)
• Breakpoints visuels avec rafraîchissement automatique
• Find/Replace natif dans l'éditeur
• Syntax highlighting optimisé (zone visible uniquement)
• Correction bug menu quit()
• Thèmes appliqués à tous les widgets
• Chemins génériques adaptables
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
import csv
from pathlib import Path
from datetime import datetime
from collections import deque
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
import importlib.util

# ============================================================
# 📁 CRÉATION AUTO DES DOSSIERS
# ============================================================
DEBUG_ROOT = Path(__file__).parent.resolve()

REQUIRED_DIRS = [
    DEBUG_ROOT / "temp" / "debug",
    DEBUG_ROOT / "modules",
    DEBUG_ROOT / "IA" / "embarquees",
    DEBUG_ROOT / "IA" / "providers",
    DEBUG_ROOT / "reports",
]
for d in REQUIRED_DIRS:
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Impossible de créer {d}: {e}")

# ============================================================
# 🎨 THÈMES
# ============================================================
THEMES = {
    "Cyberpunk": {
        "bg": "#1a1a1a", "fg": "#e0e0e0", "accent": "#00ffcc",
        "error": "#ff5252", "success": "#4CAF50", "warning": "#ff9800",
        "info": "#00bcd4", "editor_bg": "#0d0d0d", "console_bg": "#0d0d0d",
        "button_bg": "#2d5a2d", "button_fg": "#ffffff",
        "select_bg": "#3a3a3a", "select_fg": "#ffffff",
        "keyword": "#bb86fc", "builtin": "#4fc3f7", "string": "#4CAF50",
        "comment": "#666666", "number": "#ff9800",
        "tab_bg": "#2d2d2d", "tab_fg": "#e0e0e0", "tab_sel": "#3a3a3a",
        "border": "#333333", "sash": "#2a2a2a",
    },
    "Matrix": {
        "bg": "#0d0d0d", "fg": "#00ff00", "accent": "#00ff00",
        "error": "#ff0000", "success": "#00ff00", "warning": "#ffff00",
        "info": "#00ffff", "editor_bg": "#000000", "console_bg": "#000000",
        "button_bg": "#003300", "button_fg": "#00ff00",
        "select_bg": "#004400", "select_fg": "#00ff00",
        "keyword": "#00ff00", "builtin": "#00cc00", "string": "#00ff00",
        "comment": "#006600", "number": "#00ff00",
        "tab_bg": "#001100", "tab_fg": "#00ff00", "tab_sel": "#003300",
        "border": "#004400", "sash": "#002200",
    },
    "Dracula": {
        "bg": "#282a36", "fg": "#f8f8f2", "accent": "#ff79c6",
        "error": "#ff5555", "success": "#50fa7b", "warning": "#ffb86c",
        "info": "#8be9fd", "editor_bg": "#1e1f29", "console_bg": "#1e1f29",
        "button_bg": "#44475a", "button_fg": "#f8f8f2",
        "select_bg": "#44475a", "select_fg": "#f8f8f2",
        "keyword": "#ff79c6", "builtin": "#8be9fd", "string": "#f1fa8c",
        "comment": "#6272a4", "number": "#bd93f9",
        "tab_bg": "#383a4a", "tab_fg": "#f8f8f2", "tab_sel": "#44475a",
        "border": "#44475a", "sash": "#383a4a",
    },
    "Nord": {
        "bg": "#2e3440", "fg": "#eceff4", "accent": "#88c0d0",
        "error": "#bf616a", "success": "#a3be8c", "warning": "#ebcb8b",
        "info": "#81a1c1", "editor_bg": "#3b4252", "console_bg": "#3b4252",
        "button_bg": "#4c566a", "button_fg": "#eceff4",
        "select_bg": "#4c566a", "select_fg": "#eceff4",
        "keyword": "#81a1c1", "builtin": "#88c0d0", "string": "#a3be8c",
        "comment": "#616e88", "number": "#b48ead",
        "tab_bg": "#3b4252", "tab_fg": "#eceff4", "tab_sel": "#4c566a",
        "border": "#4c566a", "sash": "#3b4252",
    },
    "Monokai": {
        "bg": "#272822", "fg": "#f8f8f2", "accent": "#66d9ef",
        "error": "#f92672", "success": "#a6e22e", "warning": "#e6db74",
        "info": "#66d9ef", "editor_bg": "#1e1f1c", "console_bg": "#1e1f1c",
        "button_bg": "#49483e", "button_fg": "#f8f8f2",
        "select_bg": "#49483e", "select_fg": "#f8f8f2",
        "keyword": "#f92672", "builtin": "#66d9ef", "string": "#e6db74",
        "comment": "#75715e", "number": "#ae81ff",
        "tab_bg": "#3d3d35", "tab_fg": "#f8f8f2", "tab_sel": "#49483e",
        "border": "#49483e", "sash": "#3d3d35",
    },
    "Solarized": {
        "bg": "#002b36", "fg": "#839496", "accent": "#2aa198",
        "error": "#dc322f", "success": "#859900", "warning": "#b58900",
        "info": "#268bd2", "editor_bg": "#073642", "console_bg": "#073642",
        "button_bg": "#586e75", "button_fg": "#fdf6e3",
        "select_bg": "#586e75", "select_fg": "#fdf6e3",
        "keyword": "#268bd2", "builtin": "#2aa198", "string": "#859900",
        "comment": "#586e75", "number": "#d33682",
        "tab_bg": "#073642", "tab_fg": "#839496", "tab_sel": "#586e75",
        "border": "#586e75", "sash": "#073642",
    },
}

# ============================================================
# 🔍 MODULE GEREX — Analyse Regex 100% Locale
# ============================================================
class GerexAnalyzer:
    """Analyseur regex léger pour erreurs Python — 100% local"""

    def __init__(self):
        self.enabled = False
        self.patterns = {
            r"SyntaxError:.*invalid syntax": {
                "cause": "Erreur de syntaxe Python",
                "fix":   "Vérifie les parenthèses non fermées, deux-points manquants ou guillemets incomplets",
                "emoji": "✏️"
            },
            r"IndentationError:": {
                "cause": "Mauvaise indentation",
                "fix":   "Utilise 4 espaces par niveau — pas de mélange espaces/tabulations",
                "emoji": "↹"
            },
            r"NameError: name '(\w+)' is not defined": {
                "cause": "Variable non définie ou faute de frappe",
                "fix":   "Vérifie l'orthographe de '{0}' ou initialise-la avant utilisation",
                "emoji": "🔤"
            },
            r"AttributeError: '(\w+)' object has no attribute '(\w+)'": {
                "cause": "Méthode/attribut inexistant sur l'objet",
                "fix":   "Vérifie que '{1}' existe dans la classe '{0}'",
                "emoji": "🧩"
            },
            r"ModuleNotFoundError: No module named '(\w+)'": {
                "cause": "Module Python non installé",
                "fix":   "pip install {0} → puis redémarre le script",
                "emoji": "📦"
            },
            r"ImportError: cannot import name '(\w+)'": {
                "cause": "Import circulaire ou nom incorrect",
                "fix":   "Vérifie l'orthographe et l'ordre des imports",
                "emoji": "🔄"
            },
            r"KeyError: (\S+)": {
                "cause": "Clé absente dans le dictionnaire",
                "fix":   "Utilise .get('{0}', valeur_par_defaut) ou vérifie avec 'in'",
                "emoji": "🔑"
            },
            r"IndexError: list index out of range": {
                "cause": "Accès à un index inexistant dans une liste",
                "fix":   "Vérifie la longueur avec len() avant d'accéder à un index",
                "emoji": "📏"
            },
            r"TypeError: '(\w+)' object is not iterable": {
                "cause": "Objet utilisé dans une boucle mais non itérable",
                "fix":   "Convertir en liste/tuple ou vérifier le type avec isinstance()",
                "emoji": "🔄"
            },
            r"FileNotFoundError:.*Errno 2": {
                "cause": "Fichier ou chemin introuvable",
                "fix":   "Vérifie le chemin avec os.path.exists() et utilise des chemins absolus",
                "emoji": "📁"
            },
            r"ZeroDivisionError:": {
                "cause": "Division par zéro",
                "fix":   "Vérifie que le diviseur n'est pas égal à 0 avant la division",
                "emoji": "➗"
            },
            r"RecursionError:": {
                "cause": "Récursion infinie détectée",
                "fix":   "Ajoute une condition d'arrêt dans ta fonction récursive",
                "emoji": "🌀"
            },
            r"MemoryError:": {
                "cause": "Mémoire insuffisante",
                "fix":   "Réduis la taille des données ou libère des ressources avec del/gc",
                "emoji": "🧠"
            },
        }

    def toggle(self, state: bool):
        self.enabled = state
        return "🟢 ACTIVÉ" if state else "🔴 DÉSACTIVÉ"

    def analyze(self, error_text: str) -> dict | None:
        if not self.enabled:
            return None
        for pattern, solution in self.patterns.items():
            match = re.search(pattern, error_text, re.IGNORECASE)
            if match:
                fix = solution["fix"]
                for i, group in enumerate(match.groups()):
                    fix = fix.replace(f"{{{i}}}", str(group))
                return {
                    "emoji":      solution["emoji"],
                    "cause":      solution["cause"],
                    "fix":        fix,
                    "confidence": 0.95,
                }
        return None

# ============================================================
# 🔬 ANALYSEUR STATIQUE
# ============================================================
class StaticAnalyzer:
    """Analyse statique Python sans exécution"""

    STDLIB = {
        'os','sys','re','json','datetime','time','math','random','tkinter',
        'threading','subprocess','pathlib','tempfile','hashlib','urllib',
        'socket','webbrowser','typing','collections','itertools','functools',
        'inspect','traceback','builtins','types','enum','dataclasses',
        'decimal','fractions','statistics','bisect','heapq','copy','pickle',
        'shutil','zipfile','csv','xml','html','secrets','uuid','ipaddress',
        'argparse','configparser','logging','getpass','platform','locale',
        'zoneinfo','io','abc','contextlib','weakref','gc','struct','array',
        'queue','asyncio','concurrent','multiprocessing','signal','ctypes',
        'importlib','ast','dis','tokenize','keyword','pstats','cProfile',
    }

    def __init__(self):
        self.errors   = []
        self.warnings = []

    def analyze(self, code: str, filename: str = "<string>") -> bool:
        self.errors.clear()
        self.warnings.clear()
        # Syntaxe
        try:
            tree = ast.parse(code, filename)
        except SyntaxError as e:
            self.errors.append({
                "type": "SyntaxError", "line": e.lineno,
                "msg": e.msg, "text": e.text, "offset": e.offset,
            })
            return False
        # Imports manquants
        try:
            for node in ast.walk(tree):
                mod = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod = alias.name.split('.')[0]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mod = node.module.split('.')[0]
                if mod and mod not in self.STDLIB:
                    try:
                        importlib.import_module(mod)
                    except ImportError:
                        self.warnings.append({
                            "type": "MissingImport", "line": 1,
                            "msg": f"Module '{mod}' non installé — pip install {mod}",
                            "severity": "medium",
                        })
        except Exception:
            pass
        return True

    def get_report(self) -> str:
        lines = []
        if self.errors:
            lines.append("🔴 ERREURS CRITIQUES :")
            for e in self.errors:
                lines.append(f"  Ligne {e['line']}: {e['type']} — {e['msg']}")
                if e.get('text'):
                    lines.append(f"    {e['text'].strip()}")
                if e.get('offset'):
                    lines.append(f"    {' ' * (e['offset'] - 1)}^")
        if self.warnings:
            lines.append("\n⚠️  AVERTISSEMENTS :")
            for w in self.warnings:
                lines.append(f"  🔸 Ligne {w['line']}: {w['msg']}")
        return '\n'.join(lines) if lines else "✅ Aucune erreur détectée"

# ============================================================
# 📊 PROFILER
# ============================================================
class PerformanceProfiler:
    def __init__(self):
        self.profiler = None

    def start(self):
        self.profiler = cProfile.Profile()
        self.profiler.enable()

    def stop(self):
        if self.profiler:
            self.profiler.disable()

    def get_stats(self, limit: int = 20) -> str:
        if not self.profiler:
            return "Aucun profilage effectué"
        stream = io.StringIO()
        stats  = pstats.Stats(self.profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        stats.print_stats(limit)
        return stream.getvalue()

    def get_top_functions(self, limit: int = 10) -> list:
        if not self.profiler:
            return []
        stats = pstats.Stats(self.profiler)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        results = []
        for func, (cc, nc, tt, ct, _) in list(stats.stats.items())[:limit]:
            filename, line, func_name = func
            results.append({
                "function":        func_name,
                "file":            filename,
                "line":            line,
                "calls":           nc,
                "total_time":      tt,
                "cumulative_time": ct,
            })
        return results

# ============================================================
# 🔴 BREAKPOINT MANAGER
# ============================================================
class BreakpointManager:
    def __init__(self):
        self.breakpoints: set[int] = set()

    def toggle(self, line: int) -> bool:
        if line in self.breakpoints:
            self.breakpoints.discard(line)
            return False
        self.breakpoints.add(line)
        return True

    def clear(self):
        self.breakpoints.clear()

    def has(self, line: int) -> bool:
        return line in self.breakpoints

    def all(self) -> list[int]:
        return sorted(self.breakpoints)

# ============================================================
# ✏️ ÉDITEUR DE CODE
# ============================================================
class CodeEditor(scrolledtext.ScrolledText):
    """Éditeur avec coloration syntaxique et breakpoints visuels"""

    KEYWORDS = r'\b(def|class|if|elif|else|for|while|try|except|finally|with|as|import|from|return|yield|pass|break|continue|raise|assert|lambda|and|or|not|in|is|None|True|False|self|async|await|global|nonlocal|del)\b'
    BUILTINS = r'\b(print|len|range|str|int|float|list|dict|tuple|set|open|input|type|isinstance|hasattr|getattr|setattr|dir|help|abs|min|max|sum|all|any|enumerate|zip|map|filter|sorted|reversed|repr|id|hash|hex|oct|bin|bool|bytes|complex|format|iter|next|vars|super|property|staticmethod|classmethod)\b'
    STRINGS  = r'(""".*?"""|\'\'\'.*?\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
    COMMENTS = r'#.*?$'
    NUMBERS  = r'\b\d+\.?\d*([eE][+-]?\d+)?\b'
    DECORATORS = r'@\w+'

    def __init__(self, master, bp_manager: BreakpointManager, theme: dict, **kwargs):
        super().__init__(master, **kwargs)
        self.bp_manager = bp_manager
        self.theme      = theme
        self._highlight_pending = False
        self._last_highlight    = 0

        self.configure(
            wrap=tk.NONE, undo=True, maxundo=-1,
            font=("Consolas", 10),
            bg=theme["editor_bg"], fg=theme["fg"],
            insertbackground=theme["accent"],
            selectbackground=theme["select_bg"],
            selectforeground=theme["select_fg"],
            tabs=('1c',), relief=tk.FLAT,
            borderwidth=0,
        )

        # Canvas numéros de lignes
        self.line_canvas = tk.Canvas(
            master, width=55, bg="#111111",
            highlightthickness=0, cursor="arrow")
        self.line_canvas.bind('<Button-1>', self._on_line_click)

        # Tags coloration
        self._setup_tags()

        # Bindings
        self.bind('<KeyRelease>',      self._on_key)
        self.bind('<ButtonRelease-1>', self._on_key)
        self.bind('<Tab>',             self._insert_tab)
        self.bind('<Return>',          self._auto_indent)
        self.bind('<Control-d>',       self._duplicate_line)
        self.bind('<Control-slash>',   self._toggle_comment)
        self.bind('<Control-f>',       lambda e: self.event_generate('<<Find>>'))
        self.bind('<Control-h>',       lambda e: self.event_generate('<<Replace>>'))

        self.after(100, self._update_lines)

    def _setup_tags(self):
        t = self.theme
        self.tag_configure("keyword",      foreground=t["keyword"])
        self.tag_configure("builtin",      foreground=t["builtin"])
        self.tag_configure("string",       foreground=t["string"])
        self.tag_configure("comment",      foreground=t["comment"],
                           font=("Consolas", 10, "italic"))
        self.tag_configure("number",       foreground=t["number"])
        self.tag_configure("decorator",    foreground="#ffcc00")
        self.tag_configure("error_line",   background="#3d1f1f")
        self.tag_configure("current_line", background="#2a2a2a")
        self.tag_configure("found",        background="#ffff00",
                           foreground="#000000")
        self.tag_configure("found_cur",    background="#ff9900",
                           foreground="#000000")

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(
            bg=theme["editor_bg"], fg=theme["fg"],
            insertbackground=theme["accent"],
            selectbackground=theme["select_bg"],
            selectforeground=theme["select_fg"],
        )
        self._setup_tags()
        self._highlight()

    def _on_line_click(self, event):
        """Toggle breakpoint au clic sur le numéro de ligne"""
        # Calcule la ligne cliquée via l'index du canvas
        try:
            # Convertit la position Y du canvas en position dans le texte
            text_y = event.y
            # Utilise dlineinfo pour trouver la ligne correspondante
            idx = self.line_canvas.canvasy(text_y)
            # Approximation : hauteur de ligne ≈ 16px
            approx_line = max(1, int(idx // 16) + 1)
            # Affine avec un scan sur les lignes visibles
            line_num = self._y_to_line(int(idx))
            if line_num:
                self.bp_manager.toggle(line_num)
                self._update_lines()
        except Exception:
            pass

    def _y_to_line(self, y: int) -> int | None:
        """Convertit une coordonnée Y canvas en numéro de ligne"""
        try:
            total = int(self.index('end-1c').split('.')[0])
            height = self.line_canvas.winfo_height()
            if height <= 0:
                return None
            line = max(1, min(total, int(y * total / height) + 1))
            return line
        except Exception:
            return None

    def _on_key(self, event=None):
        if event and event.keysym in (
            'Shift_L','Shift_R','Control_L','Control_R',
            'Alt_L','Alt_R','Caps_Lock',
        ):
            return
        now = time.time()
        if now - self._last_highlight > 0.1:
            self._last_highlight = now
            self.after_idle(self._highlight)
            self.after_idle(self._update_lines)

    def _insert_tab(self, event):
        self.insert(tk.INSERT, "    ")
        return "break"

    def _auto_indent(self, event):
        line = self.get("insert linestart", "insert lineend")
        indent = len(line) - len(line.lstrip())
        if line.rstrip().endswith(':'):
            indent += 4
        self.insert(tk.INSERT, '\n' + ' ' * indent)
        return "break"

    def _duplicate_line(self, event):
        line = self.get("insert linestart", "insert lineend")
        self.insert("insert lineend", '\n' + line)
        return "break"

    def _toggle_comment(self, event):
        start = self.index("insert linestart")
        end   = self.index("insert lineend")
        line  = self.get(start, end)
        if line.lstrip().startswith('#'):
            new = line.replace('#', '', 1).replace('  ', ' ', 1)
        else:
            indent = len(line) - len(line.lstrip())
            new = ' ' * indent + '# ' + line.lstrip()
        self.delete(start, end)
        self.insert(start, new)
        return "break"

    def _highlight(self):
        """Coloration syntaxique — zone visible uniquement pour performance"""
        try:
            # Obtenir les lignes visibles
            first = self.index("@0,0")
            last  = self.index(f"@0,{self.winfo_height()}")
            # Étendre légèrement le contexte
            first_line = max(1, int(first.split('.')[0]) - 5)
            last_line  = int(last.split('.')[0]) + 5
            region_start = f"{first_line}.0"
            region_end   = f"{last_line}.end"

            content = self.get(region_start, region_end)
            offset  = len(self.get("1.0", region_start))

            for tag in ("keyword","builtin","string","comment","number","decorator"):
                self.tag_remove(tag, region_start, region_end)

            def add(pattern, tag, flags=0):
                for m in re.finditer(pattern, content, flags):
                    s = f"1.0+{offset + m.start()}c"
                    e = f"1.0+{offset + m.end()}c"
                    self.tag_add(tag, s, e)

            add(self.COMMENTS,   "comment",   re.MULTILINE)
            add(self.STRINGS,    "string",    re.DOTALL)
            add(self.KEYWORDS,   "keyword")
            add(self.BUILTINS,   "builtin")
            add(self.NUMBERS,    "number")
            add(self.DECORATORS, "decorator")
        except Exception:
            pass

    def _update_lines(self):
        """Mise à jour numéros de lignes + indicateurs breakpoints"""
        try:
            self.line_canvas.delete('all')
            total  = int(self.index('end-1c').split('.')[0])
            first  = int(self.index("@0,0").split('.')[0])
            height = self.winfo_height()
            if height <= 0 or total <= 0:
                return

            line_h = height / max(total, 1)

            for i in range(first, min(total + 1, first + int(height / max(line_h, 1)) + 2)):
                y = (i - first) * line_h + line_h / 2
                has_bp = self.bp_manager.has(i)
                if has_bp:
                    # Cercle rouge breakpoint
                    self.line_canvas.create_oval(
                        3, y - 6, 13, y + 6,
                        fill='#ff3333', outline='#ff0000', width=1)
                color = '#ff5252' if has_bp else '#555555'
                self.line_canvas.create_text(
                    38, y, text=str(i), anchor='e',
                    fill=color, font=("Consolas", 9))
        except Exception:
            pass

    def highlight_error_line(self, line: int | None):
        self.tag_remove("error_line", "1.0", tk.END)
        if line:
            self.tag_add("error_line", f"{line}.0", f"{line}.end")
            self.see(f"{line}.0")

    def highlight_current_line(self, line: int | None):
        self.tag_remove("current_line", "1.0", tk.END)
        if line:
            self.tag_add("current_line", f"{line}.0", f"{line}.end")
            self.see(f"{line}.0")

    def find_text(self, query: str, start: str = "1.0",
                  case_sensitive: bool = False) -> str | None:
        """Cherche query depuis start, retourne l'index ou None"""
        flags = 0 if case_sensitive else re.IGNORECASE
        content = self.get("1.0", tk.END)
        lines   = content.split('\n')
        start_line, start_col = map(int, start.split('.'))
        # Convertit start en offset
        offset = sum(len(l) + 1 for l in lines[:start_line - 1]) + start_col
        match  = re.search(re.escape(query), content[offset:], flags)
        if match:
            abs_start = offset + match.start()
            abs_end   = offset + match.end()
            # Convertit offset en ligne.col
            def offset_to_pos(off):
                cur = 0
                for ln, l in enumerate(lines, 1):
                    if cur + len(l) >= off:
                        return f"{ln}.{off - cur}"
                    cur += len(l) + 1
                return tk.END
            return offset_to_pos(abs_start), offset_to_pos(abs_end)
        return None

# ============================================================
# 🖥️ TERMINAL EMBARQUÉ
# ============================================================
class EmbeddedTerminal:
    def __init__(self, output: scrolledtext.ScrolledText):
        self.output  = output
        self.cwd     = os.path.expanduser("~")
        self.history = deque(maxlen=100)
        self.hist_idx = -1

    def execute(self, command: str):
        self.history.appendleft(command)
        self.hist_idx = -1

        if command.strip().startswith('cd '):
            path = command.strip()[3:].strip()
            try:
                new = os.path.expanduser(path)
                if os.path.isdir(new):
                    self.cwd = new
                    self._write(f"📁 {self.cwd}\n", "success")
                else:
                    self._write(f"❌ Dossier introuvable : {path}\n", "error")
            except Exception as e:
                self._write(f"❌ Erreur : {e}\n", "error")
            return

        if command.strip() == 'clear':
            self.output.configure(state='normal')
            self.output.delete("1.0", tk.END)
            self.output.configure(state='disabled')
            return

        try:
            proc = subprocess.Popen(
                command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=self.cwd)
            stdout, stderr = proc.communicate(timeout=30)
            if stdout:
                self._write(stdout, "output")
            if stderr:
                self._write(stderr, "error")
        except subprocess.TimeoutExpired:
            self._write("⏱️ Timeout (30s)\n", "error")
        except Exception as e:
            self._write(f"❌ Erreur : {e}\n", "error")

    def _write(self, text: str, tag: str = "output"):
        self.output.configure(state='normal')
        self.output.insert(tk.END, text, tag)
        self.output.configure(state='disabled')
        self.output.see(tk.END)

# ============================================================
# ⚙️ MOTEUR DE DEBUG
# ============================================================
class PythonDebugger:
    def __init__(self):
        self.process:          subprocess.Popen | None = None
        self.output_callback:  callable | None = None
        self.error_callback:   callable | None = None
        self.finish_callback:  callable | None = None
        self.execution_history = deque(maxlen=50)
        self.profiler          = PerformanceProfiler()
        self.temp_dir          = DEBUG_ROOT / "temp" / "debug"
        self._last_autofix:    str | None = None

    def execute(self, code: str, filename: str = "<editor>",
                args: list | None = None, profile: bool = False) -> bool:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execution_history.append({
            "timestamp": ts, "filename": filename,
            "code": code, "args": args or [], "profiled": profile,
        })
        if profile:
            self.profiler.start()

        temp = self.temp_dir / f"kdb_{int(time.time()*1000)}.py"
        temp.write_text(code, encoding='utf-8')
        cmd = [sys.executable, str(temp)] + (args or [])

        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1, universal_newlines=True)

            def _read_out():
                for line in iter(self.process.stdout.readline, ''):
                    if self.output_callback:
                        self.output_callback(line, False)
                self.process.stdout.close()

            def _read_err():
                buf = []
                for line in iter(self.process.stderr.readline, ''):
                    buf.append(line)
                    if self.output_callback:
                        self.output_callback(line, True)
                self.process.stderr.close()
                if buf and self.error_callback:
                    self.error_callback(''.join(buf), code, filename)

            def _wait():
                self.process.wait()
                if profile:
                    self.profiler.stop()
                if self.finish_callback:
                    self.finish_callback(self.process.returncode, profile)
                self._cleanup_temp()

            threading.Thread(target=_read_out, daemon=True).start()
            threading.Thread(target=_read_err, daemon=True).start()
            threading.Thread(target=_wait,     daemon=True).start()
            return True
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e), code, filename)
            temp.unlink(missing_ok=True)
            return False

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def _cleanup_temp(self):
        files = sorted(
            self.temp_dir.glob("kdb_*.py"),
            key=os.path.getmtime, reverse=True)
        for f in files[10:]:
            f.unlink(missing_ok=True)

    def parse_traceback(self, error_text: str,
                        code: str, filename: str) -> dict:
        lines      = error_text.strip().split('\n')
        error_type = "UnknownError"
        error_msg  = "Erreur inconnue"
        for line in reversed(lines):
            if ':' in line and not line.strip().startswith('File'):
                parts      = line.split(':', 1)
                error_type = parts[0].strip()
                error_msg  = parts[1].strip() if len(parts) > 1 else parts[0]
                break
        line_num     = None
        file_context = None
        for line in lines:
            if 'File' in line and 'line' in line:
                m = re.search(r'line (\d+)', line)
                if m:
                    line_num = int(m.group(1))
                    idx      = lines.index(line)
                    if idx + 1 < len(lines):
                        file_context = lines[idx + 1].strip()

        suggestions = self._suggestions(error_type, error_msg)
        auto_fix    = self._auto_fix(error_type, error_msg, code, line_num)
        self._last_autofix = auto_fix

        return {
            "type":          error_type,
            "message":       error_msg,
            "line":          line_num,
            "context":       file_context,
            "full_traceback":error_text,
            "suggestions":   suggestions,
            "auto_fix":      auto_fix,
        }

    def _auto_fix(self, error_type: str, error_msg: str,
                  code: str, line_num: int | None) -> str | None:
        if not line_num:
            return None
        lines = code.split('\n')
        if line_num > len(lines):
            return None
        error_line = lines[line_num - 1]
        indent = len(error_line) - len(error_line.lstrip())
        sp = ' ' * indent

        if error_type == "NameError":
            m = re.search(r"name '(\w+)' is not defined", error_msg)
            if m:
                return f"{sp}{m.group(1)} = None  # 🤖 Auto-fix"
        elif error_type == "ZeroDivisionError" and '/' in error_line:
            divisor = error_line.split('/')[-1].strip().split()[0].rstrip(')')
            return (f"{sp}if {divisor} != 0:  # 🤖 Auto-fix\n"
                    f"{sp}    {error_line.strip()}")
        elif error_type == "AttributeError":
            return f"{sp}# 🤖 Vérifier avec hasattr() avant d'accéder à l'attribut"
        return None

    def _suggestions(self, error_type: str, error_msg: str) -> list[str]:
        s = []
        if error_type == "NameError":
            m = re.search(r"name '(\w+)'", error_msg)
            v = m.group(1) if m else "variable"
            s += [f"💡 Déclarer '{v}' avant utilisation",
                  f"💡 Vérifier l'orthographe de '{v}'"]
        elif error_type == "SyntaxError":
            s += ["💡 Vérifier parenthèses, crochets et guillemets",
                  "💡 Vérifier l'indentation (4 espaces par niveau)"]
        elif error_type == "IndentationError":
            s += ["💡 Utiliser 4 espaces (pas de tabulations)",
                  "💡 Vérifier la cohérence de l'indentation"]
        elif error_type == "AttributeError":
            s += ["💡 Objet sans cet attribut/méthode",
                  "💡 Utiliser dir(obj) pour lister les attributs"]
        elif error_type in ("ImportError", "ModuleNotFoundError"):
            m = re.search(r"No module named '(\w+)'", error_msg)
            if m:
                s += [f"💡 pip install {m.group(1)}"]
        elif error_type == "KeyError":
            s += ["💡 Utiliser .get(clé, défaut) pour éviter l'erreur",
                  "💡 Vérifier la présence de la clé avec 'in'"]
        elif error_type == "IndexError":
            s += ["💡 Vérifier len() avant accès par index"]
        elif error_type == "ZeroDivisionError":
            s += ["💡 Vérifier que le diviseur != 0 avant la division"]
        return s

# ============================================================
# 🔍 FIND / REPLACE DIALOG
# ============================================================
class FindReplaceDialog:
    """Fenêtre Find/Replace native tkinter"""

    def __init__(self, parent, editor: CodeEditor, theme: dict):
        self.editor  = editor
        self.theme   = theme
        self.win     = tk.Toplevel(parent)
        self.win.title("🔍 Rechercher / Remplacer")
        self.win.geometry("480x200")
        self.win.configure(bg=theme["bg"])
        self.win.resizable(False, False)
        self.win.transient(parent)
        self._matches: list = []
        self._cur_idx: int  = -1
        self._build()

    def _build(self):
        t = self.theme
        pad = {"padx": 10, "pady": 5}

        # Rechercher
        row1 = tk.Frame(self.win, bg=t["bg"])
        row1.pack(fill=tk.X, **pad)
        tk.Label(row1, text="Rechercher :", bg=t["bg"], fg=t["fg"],
                 font=("Consolas", 10), width=14, anchor="w").pack(side=tk.LEFT)
        self.find_var = tk.StringVar()
        self.find_entry = tk.Entry(row1, textvariable=self.find_var,
                                   font=("Consolas", 10),
                                   bg=t["editor_bg"], fg=t["accent"],
                                   insertbackground=t["accent"])
        self.find_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.find_entry.bind('<Return>', lambda e: self._find_next())

        # Remplacer
        row2 = tk.Frame(self.win, bg=t["bg"])
        row2.pack(fill=tk.X, **pad)
        tk.Label(row2, text="Remplacer par :", bg=t["bg"], fg=t["fg"],
                 font=("Consolas", 10), width=14, anchor="w").pack(side=tk.LEFT)
        self.repl_var = tk.StringVar()
        self.repl_entry = tk.Entry(row2, textvariable=self.repl_var,
                                   font=("Consolas", 10),
                                   bg=t["editor_bg"], fg=t["fg"],
                                   insertbackground=t["accent"])
        self.repl_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Options
        row3 = tk.Frame(self.win, bg=t["bg"])
        row3.pack(fill=tk.X, padx=10)
        self.case_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row3, text="Sensible à la casse",
                       variable=self.case_var,
                       bg=t["bg"], fg=t["fg"],
                       selectcolor=t["editor_bg"],
                       font=("Consolas", 9)).pack(side=tk.LEFT)
        self.count_lbl = tk.Label(row3, text="", bg=t["bg"],
                                  fg=t["accent"], font=("Consolas", 9))
        self.count_lbl.pack(side=tk.RIGHT, padx=10)

        # Boutons
        row4 = tk.Frame(self.win, bg=t["bg"])
        row4.pack(fill=tk.X, padx=10, pady=8)
        for txt, cmd in [
            ("◀ Précédent",   self._find_prev),
            ("▶ Suivant",     self._find_next),
            ("Remplacer",     self._replace_one),
            ("Tout remplacer",self._replace_all),
            ("Fermer",        self.win.destroy),
        ]:
            tk.Button(row4, text=txt, command=cmd,
                      bg=t["button_bg"], fg=t["button_fg"],
                      font=("Consolas", 9), relief=tk.FLAT,
                      padx=8, pady=4).pack(side=tk.LEFT, padx=3)

        self.find_entry.focus_set()

    def _collect_matches(self) -> list:
        query   = self.find_var.get()
        content = self.editor.get("1.0", tk.END)
        flags   = 0 if self.case_var.get() else re.IGNORECASE
        lines   = content.split('\n')

        self.editor.tag_remove("found",     "1.0", tk.END)
        self.editor.tag_remove("found_cur", "1.0", tk.END)

        if not query:
            self.count_lbl.config(text="")
            return []

        matches = []
        for m in re.finditer(re.escape(query), content, flags):
            off_s = m.start()
            off_e = m.end()
            def to_pos(off):
                cur = 0
                for ln, l in enumerate(lines, 1):
                    if cur + len(l) >= off:
                        return f"{ln}.{off - cur}"
                    cur += len(l) + 1
                return tk.END
            ps, pe = to_pos(off_s), to_pos(off_e)
            matches.append((ps, pe))
            self.editor.tag_add("found", ps, pe)

        self.count_lbl.config(
            text=f"{len(matches)} occurrence(s)" if matches else "Aucun résultat")
        return matches

    def _find_next(self):
        self._matches = self._collect_matches()
        if not self._matches:
            return
        self._cur_idx = (self._cur_idx + 1) % len(self._matches)
        self._highlight_current()

    def _find_prev(self):
        self._matches = self._collect_matches()
        if not self._matches:
            return
        self._cur_idx = (self._cur_idx - 1) % len(self._matches)
        self._highlight_current()

    def _highlight_current(self):
        self.editor.tag_remove("found_cur", "1.0", tk.END)
        if 0 <= self._cur_idx < len(self._matches):
            ps, pe = self._matches[self._cur_idx]
            self.editor.tag_add("found_cur", ps, pe)
            self.editor.see(ps)
            self.editor.mark_set(tk.INSERT, ps)

    def _replace_one(self):
        if not self._matches or self._cur_idx < 0:
            self._find_next()
            return
        if 0 <= self._cur_idx < len(self._matches):
            ps, pe = self._matches[self._cur_idx]
            self.editor.delete(ps, pe)
            self.editor.insert(ps, self.repl_var.get())
        self._matches = self._collect_matches()
        self._cur_idx = min(self._cur_idx, len(self._matches) - 1)
        self._highlight_current()

    def _replace_all(self):
        self._matches = self._collect_matches()
        count = 0
        for ps, pe in reversed(self._matches):
            self.editor.delete(ps, pe)
            self.editor.insert(ps, self.repl_var.get())
            count += 1
        self._matches = []
        self._cur_idx = -1
        self.count_lbl.config(text=f"{count} remplacement(s)")
        self.editor._highlight()

# ============================================================
# 🐺 APPLICATION PRINCIPALE
# ============================================================
class KerberosDebuggerApp:

    def __init__(self, root: tk.Tk):
        self.root              = root
        self.root.title("🐺 Kerberos Debugger v4.2 — Privacy First")
        self.root.geometry("1600x950")
        self.current_file:     str | None  = None
        self.is_executing:     bool        = False
        self.watch_active:     bool        = False
        self._theme_name:      str         = "Cyberpunk"
        self.theme:            dict        = THEMES["Cyberpunk"]
        self.bp_manager        = BreakpointManager()
        self.debugger          = PythonDebugger()
        self.analyzer          = StaticAnalyzer()
        self.gerex             = GerexAnalyzer()
        self._find_dialog:     FindReplaceDialog | None = None
        self._search_results:  list        = []

        self.root.configure(bg=self.theme["bg"])
        self._setup_style()
        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()

        # Callbacks debugger
        self.debugger.output_callback  = self._on_output
        self.debugger.error_callback   = self._on_error
        self.debugger.finish_callback  = self._on_finish

        self._log("🐺 Kerberos Debugger v4.2 démarré\n", "info")
        self._log("🔒 IA désactivée par défaut — privacy first\n", "info")
        self._log("🔍 gerex disponible — toggle dans l'onglet Traceback\n\n", "info")

    # ── Style ─────────────────────────────────────────────────────────────
    def _setup_style(self):
        t = self.theme
        s = ttk.Style()
        try:
            s.theme_use('clam')
        except Exception:
            pass
        s.configure("TFrame",         background=t["bg"])
        s.configure("TLabel",         background=t["bg"],      foreground=t["fg"],
                                      font=("Consolas", 10))
        s.configure("TButton",        background=t["button_bg"],foreground=t["button_fg"],
                                      font=("Consolas", 10,"bold"), padding=8)
        s.map("TButton",              background=[("active", t["accent"])])
        s.configure("Danger.TButton", background="#7a2020",     foreground="#ffffff")
        s.map("Danger.TButton",       background=[("active", "#a03030")])
        s.configure("TNotebook",      background=t["bg"],       borderwidth=0)
        s.configure("TNotebook.Tab",  background=t["tab_bg"],   foreground=t["tab_fg"],
                                      padding=[18, 8], font=("Consolas", 10))
        s.map("TNotebook.Tab",        background=[("selected", t["tab_sel"])],
                                      foreground=[("selected", t["accent"])])
        s.configure("TCheckbutton",   background=t["bg"],       foreground=t["accent"])
        s.configure("TScrollbar",     background=t["bg"],       troughcolor=t["editor_bg"])
        s.configure("TPanedwindow",   background=t["sash"])

    # ── Menu ──────────────────────────────────────────────────────────────
    def _build_menu(self):
        t   = self.theme
        bar = tk.Menu(self.root, bg=t["tab_bg"], fg=t["fg"],
                      activebackground=t["tab_sel"],
                      activeforeground=t["accent"])
        self.root.config(menu=bar)

        def menu(label):
            m = tk.Menu(bar, tearoff=0, bg=t["tab_bg"], fg=t["fg"],
                        activebackground=t["tab_sel"],
                        activeforeground=t["accent"])
            bar.add_cascade(label=label, menu=m)
            return m

        # Fichier
        f = menu("📁 Fichier")
        f.add_command(label="Nouveau      Ctrl+N", command=self._new_file)
        f.add_command(label="Ouvrir       Ctrl+O", command=self._open_file)
        f.add_command(label="Enregistrer  Ctrl+S", command=self._save_file)
        f.add_command(label="Enregistrer sous…",   command=self._save_as)
        f.add_separator()
        f.add_command(label="Export rapport HTML",  command=self._export_html)
        f.add_separator()
        f.add_command(label="Quitter      Ctrl+Q", command=self.root.quit)  # ✅ sans ()

        # Édition
        e = menu("✏️ Édition")
        e.add_command(label="Dupliquer ligne  Ctrl+D",   command=lambda: self.editor.event_generate('<Control-d>'))
        e.add_command(label="Commenter        Ctrl+/",   command=lambda: self.editor.event_generate('<Control-slash>'))
        e.add_separator()
        e.add_command(label="Chercher/Remplacer Ctrl+F", command=self._show_find)

        # Exécution
        r = menu("▶️ Exécution")
        r.add_command(label="Exécuter   F5",       command=self._run)
        r.add_command(label="Profiler   F7",       command=self._run_profiled)
        r.add_command(label="Analyser   F6",       command=self._analyze)
        r.add_command(label="Arrêter",             command=self._stop)
        r.add_separator()
        r.add_command(label="Effacer console",     command=self._clear_console)

        # Debug
        d = menu("🐛 Debug")
        d.add_command(label="Toggle breakpoint  F9",     command=self._toggle_bp_current)
        d.add_command(label="Effacer breakpoints",       command=self._clear_bps)
        d.add_separator()
        d.add_command(label="Appliquer auto-fix",        command=self._apply_autofix)

        # Outils
        o = menu("🔧 Outils")
        self._watch_var = tk.BooleanVar(value=False)
        o.add_checkbutton(label="👁️ Auto-Watch fichier",
                          variable=self._watch_var,
                          command=self._toggle_watch)
        o.add_separator()
        o.add_command(label="Rapport performance",       command=self._show_perf_report)
        o.add_command(label="Export performance CSV",    command=self._export_perf_csv)

        # Thèmes
        th = menu("🎨 Thème")
        for name in THEMES:
            th.add_command(label=name,
                           command=lambda n=name: self._change_theme(n))

        # Aide
        h = menu("❓ Aide")
        h.add_command(label="Raccourcis clavier", command=self._show_shortcuts)
        h.add_command(label="Documentation",      command=self._show_doc)
        h.add_separator()
        h.add_command(label="À propos",           command=self._show_about)

    # ── UI principale ─────────────────────────────────────────────────────
    def _build_ui(self):
        t = self.theme

        # Barre d'état principale
        self._statusbar = tk.Frame(self.root, bg=t["tab_bg"], height=24)
        self._statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self._status_file  = tk.Label(
            self._statusbar, text="📄 Aucun fichier",
            bg=t["tab_bg"], fg=t["accent"],
            font=("Consolas", 9), anchor="w")
        self._status_file.pack(side=tk.LEFT, padx=10)
        self._status_theme = tk.Label(
            self._statusbar, text=f"🎨 {self._theme_name}",
            bg=t["tab_bg"], fg=t["fg"],
            font=("Consolas", 9))
        self._status_theme.pack(side=tk.RIGHT, padx=10)
        self._status_cursor = tk.Label(
            self._statusbar, text="Ln 1, Col 0",
            bg=t["tab_bg"], fg=t["fg"],
            font=("Consolas", 9))
        self._status_cursor.pack(side=tk.RIGHT, padx=10)

        # Notebook principal
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 0))

        self._build_debugger_tab()
        self._build_search_tab()
        self._build_history_tab()
        self._build_terminal_tab()

    def _build_debugger_tab(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text=" 🚀 Debugger ")
        t = self.theme

        paned = tk.PanedWindow(frame, orient=tk.VERTICAL,
                               bg=t["sash"], sashwidth=5,
                               sashrelief=tk.FLAT)
        paned.pack(fill=tk.BOTH, expand=True)

        # ── ÉDITEUR ──
        editor_frame = ttk.Frame(paned)
        paned.add(editor_frame, height=520)

        # Toolbar éditeur
        tb = tk.Frame(editor_frame, bg=t["bg"])
        tb.pack(fill=tk.X, pady=(0, 4))

        self._file_lbl = tk.Label(
            tb, text="📄 Aucun fichier",
            bg=t["bg"], fg=t["accent"],
            font=("Consolas", 10, "bold"), anchor="w")
        self._file_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        for txt, cmd, style in [
            ("📂 Ouvrir",      self._open_file,    "TButton"),
            ("💾 Sauver",      self._save_file,    "TButton"),
            ("▶ Exécuter F5", self._run,           "TButton"),
            ("📊 Profiler F7", self._run_profiled, "TButton"),
            ("🔍 Analyser F6", self._analyze,      "TButton"),
            ("⏹ Stop",         self._stop,         "Danger.TButton"),
        ]:
            ttk.Button(tb, text=txt, command=cmd, style=style,
                       width=len(txt) + 2).pack(side=tk.LEFT, padx=2)

        # Args
        tk.Label(tb, text=" Args:", bg=t["bg"],
                 fg=t["fg"], font=("Consolas", 9)).pack(side=tk.LEFT)
        self._args_entry = tk.Entry(
            tb, width=18, bg=t["editor_bg"],
            fg=t["accent"], font=("Consolas", 9),
            insertbackground=t["accent"])
        self._args_entry.pack(side=tk.LEFT, padx=(0, 5))

        # Zone éditeur + canvas lignes
        ed_zone = tk.Frame(editor_frame, bg=t["bg"])
        ed_zone.pack(fill=tk.BOTH, expand=True)

        self.editor = CodeEditor(
            ed_zone, bp_manager=self.bp_manager, theme=t,
            height=20)
        self.editor.line_canvas.pack(side=tk.LEFT, fill=tk.Y)
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.editor.bind('<KeyRelease>',      self._update_cursor)
        self.editor.bind('<ButtonRelease-1>', self._update_cursor)
        self.editor.bind('<<Find>>',          lambda e: self._show_find())

        # Code d'exemple
        self.editor.insert("1.0", '''# 🐺 Kerberos Debugger v4.2
# F5 = Exécuter | F7 = Profiler | F6 = Analyser statique
# F9 = Toggle breakpoint sur la ligne courante
# Ctrl+F = Chercher/Remplacer

def saluer(nom: str) -> str:
    """Fonction de salutation"""
    return f"Bonjour {nom} ! 🐺"

nom = "Victor"
print(saluer(nom))
print("✅ Debugger v4.2 opérationnel")
''')
        self.editor._highlight()
        self.editor._update_lines()

        # ── CONSOLE + SOUS-ONGLETS ──
        bottom = ttk.Frame(paned)
        paned.add(bottom, height=330)

        bot_nb = ttk.Notebook(bottom)
        bot_nb.pack(fill=tk.BOTH, expand=True)

        # Console
        con_frame = ttk.Frame(bot_nb)
        bot_nb.add(con_frame, text=" 📟 Console ")

        con_tb = tk.Frame(con_frame, bg=t["bg"])
        con_tb.pack(fill=tk.X, pady=(0, 4))
        self._status_lbl = tk.Label(
            con_tb, text="⚪ Prêt",
            bg=t["bg"], fg=t["success"],
            font=("Consolas", 9, "bold"), anchor="w")
        self._status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(con_tb, text="🗑 Effacer",
                   command=self._clear_console, width=12).pack(side=tk.RIGHT)

        self.console = scrolledtext.ScrolledText(
            con_frame, wrap=tk.WORD, font=("Consolas", 9),
            bg=t["console_bg"], fg=t["fg"], height=15,
            relief=tk.FLAT, borderwidth=0)
        self.console.pack(fill=tk.BOTH, expand=True)
        self.console.tag_configure("output",  foreground=t["fg"])
        self.console.tag_configure("error",   foreground=t["error"])
        self.console.tag_configure("success", foreground=t["success"])
        self.console.tag_configure("info",    foreground=t["info"])

        # Analyse statique
        ana_frame = ttk.Frame(bot_nb)
        bot_nb.add(ana_frame, text=" 🔬 Analyse ")
        self._ana_text = scrolledtext.ScrolledText(
            ana_frame, wrap=tk.WORD, font=("Consolas", 9),
            bg=t["console_bg"], fg="#ffcc00", height=15,
            relief=tk.FLAT, borderwidth=0)
        self._ana_text.pack(fill=tk.BOTH, expand=True, pady=4)
        self._ana_text.tag_configure("error",   foreground=t["error"],   font=("Consolas", 9, "bold"))
        self._ana_text.tag_configure("warning", foreground=t["warning"])
        self._ana_text.tag_configure("success", foreground=t["success"])

        # Traceback + gerex + auto-fix
        tb_frame = ttk.Frame(bot_nb)
        bot_nb.add(tb_frame, text=" 🐛 Traceback ")

        gerex_bar = tk.Frame(tb_frame, bg=t["bg"])
        gerex_bar.pack(fill=tk.X, pady=(2, 4))

        self._gerex_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            gerex_bar, text="🔍 gerex  (analyse regex 100% locale)",
            variable=self._gerex_var,
            command=self._toggle_gerex,
            bg=t["bg"], fg=t["accent"],
            selectcolor=t["editor_bg"],
            font=("Consolas", 10, "bold"),
            activebackground=t["bg"],
            activeforeground=t["accent"],
        ).pack(side=tk.LEFT, padx=10)

        self._gerex_lbl = tk.Label(
            gerex_bar, text="🔴 DÉSACTIVÉ",
            bg=t["bg"], fg=t["error"],
            font=("Consolas", 9, "bold"))
        self._gerex_lbl.pack(side=tk.LEFT)

        tk.Label(gerex_bar,
                 text="  ℹ️ zéro connexion réseau",
                 bg=t["bg"], fg=t["comment"],
                 font=("Consolas", 8)).pack(side=tk.LEFT)

        fix_bar = tk.Frame(tb_frame, bg=t["bg"])
        fix_bar.pack(fill=tk.X, pady=(0, 4))
        tk.Label(fix_bar, text="🤖 Auto-fix :",
                 bg=t["bg"], fg=t["accent"],
                 font=("Consolas", 9, "bold")).pack(side=tk.LEFT, padx=8)
        ttk.Button(fix_bar, text="✨ Appliquer",
                   command=self._apply_autofix).pack(side=tk.LEFT, padx=4)
        ttk.Button(fix_bar, text="📋 Copier",
                   command=self._copy_autofix).pack(side=tk.LEFT, padx=4)

        self._tb_text = scrolledtext.ScrolledText(
            tb_frame, wrap=tk.WORD, font=("Consolas", 9),
            bg=t["console_bg"], fg=t["error"], height=15,
            relief=tk.FLAT, borderwidth=0)
        self._tb_text.pack(fill=tk.BOTH, expand=True, pady=4)
        self._tb_text.tag_configure("suggestion", foreground=t["accent"],
                                    font=("Consolas", 9, "bold"))
        self._tb_text.tag_configure("err_line",   foreground="#ffcc00",
                                    background="#3d1f1f")
        self._tb_text.tag_configure("autofix",    foreground=t["success"],
                                    font=("Consolas", 9, "bold"))
        self._tb_text.tag_configure("gerex",      foreground="#00ffcc",
                                    font=("Consolas", 9, "bold"))

        # Performance
        perf_frame = ttk.Frame(bot_nb)
        bot_nb.add(perf_frame, text=" 📊 Performance ")

        perf_tb = tk.Frame(perf_frame, bg=t["bg"])
        perf_tb.pack(fill=tk.X, pady=(2, 4))
        tk.Label(perf_tb, text="⏱️ Profiling",
                 bg=t["bg"], fg=t["info"],
                 font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=8)
        ttk.Button(perf_tb, text="💾 Export CSV",
                   command=self._export_perf_csv).pack(side=tk.RIGHT, padx=4)

        self._perf_text = scrolledtext.ScrolledText(
            perf_frame, wrap=tk.WORD, font=("Consolas", 9),
            bg=t["console_bg"], fg=t["info"], height=15,
            relief=tk.FLAT, borderwidth=0)
        self._perf_text.pack(fill=tk.BOTH, expand=True, pady=4)
        self._perf_text.tag_configure("fast",     foreground=t["success"])
        self._perf_text.tag_configure("slow",     foreground=t["warning"])
        self._perf_text.tag_configure("critical", foreground=t["error"],
                                      font=("Consolas", 9, "bold"))

        # ── BREAKPOINTS ──  ✅ FIX : rafraîchissement automatique
        bp_frame = ttk.Frame(bot_nb)
        bot_nb.add(bp_frame, text=" 🔴 Breakpoints ")

        bp_tb = tk.Frame(bp_frame, bg=t["bg"])
        bp_tb.pack(fill=tk.X, pady=(2, 4))
        tk.Label(bp_tb, text="🔴 Breakpoints actifs",
                 bg=t["bg"], fg=t["error"],
                 font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=8)
        ttk.Button(bp_tb, text="🗑 Tout effacer",
                   command=self._clear_bps).pack(side=tk.RIGHT, padx=4)
        ttk.Button(bp_tb, text="🔄 Rafraîchir",
                   command=self._refresh_bp_list).pack(side=tk.RIGHT, padx=4)

        self._bp_list = tk.Listbox(
            bp_frame, font=("Consolas", 9),
            bg=t["console_bg"], fg=t["error"],
            selectbackground=t["select_bg"],
            selectforeground="#ffffff",
            height=15, relief=tk.FLAT, borderwidth=0)
        self._bp_list.pack(fill=tk.BOTH, expand=True, pady=4)
        self._bp_list.bind('<Double-Button-1>', self._goto_bp)

        # Message initial
        self._refresh_bp_list()

    def _build_search_tab(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text=" 🔍 Recherche ")
        t = self.theme

        main = tk.Frame(frame, bg=t["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        tk.Label(main, text="🔍 RECHERCHE MULTI-FORMAT",
                 bg=t["bg"], fg=t["accent"],
                 font=("Consolas", 15, "bold")).pack(pady=(0, 12))

        # Erreur à chercher
        r1 = tk.Frame(main, bg=t["bg"])
        r1.pack(fill=tk.X, pady=4)
        tk.Label(r1, text="Terme à chercher :", bg=t["bg"],
                 fg=t["info"], font=("Consolas", 10), width=18,
                 anchor="w").pack(side=tk.LEFT)
        self._err_entry = tk.Entry(
            r1, font=("Consolas", 10), bg=t["editor_bg"],
            fg=t["accent"], insertbackground=t["accent"])
        self._err_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Dossier
        r2 = tk.Frame(main, bg=t["bg"])
        r2.pack(fill=tk.X, pady=4)
        tk.Label(r2, text="Dossier :", bg=t["bg"],
                 fg=t["fg"], font=("Consolas", 10), width=18,
                 anchor="w").pack(side=tk.LEFT)
        self._path_entry = tk.Entry(
            r2, font=("Consolas", 10), bg=t["editor_bg"],
            fg=t["accent"], insertbackground=t["accent"])
        self._path_entry.insert(0, str(Path.home()))
        self._path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(r2, text="📁", width=4,
                   command=self._browse_search).pack(side=tk.RIGHT)

        # Extensions
        ext_frame = tk.Frame(main, bg=t["bg"])
        ext_frame.pack(fill=tk.X, pady=4)
        tk.Label(ext_frame, text="Extensions :", bg=t["bg"],
                 fg=t["fg"], font=("Consolas", 10), width=18,
                 anchor="w").pack(side=tk.LEFT)
        self._ext_py   = tk.BooleanVar(value=True)
        self._ext_csv  = tk.BooleanVar(value=True)
        self._ext_json = tk.BooleanVar(value=False)
        self._ext_txt  = tk.BooleanVar(value=False)
        for var, lbl in [(self._ext_py,".py"),
                         (self._ext_csv,".csv"),
                         (self._ext_json,".json"),
                         (self._ext_txt,".txt")]:
            tk.Checkbutton(ext_frame, text=lbl, variable=var,
                           bg=t["bg"], fg=t["accent"],
                           selectcolor=t["editor_bg"],
                           font=("Consolas", 10),
                           activebackground=t["bg"],
                           activeforeground=t["accent"],
                           ).pack(side=tk.LEFT, padx=6)

        # Boutons
        btn_frame = tk.Frame(main, bg=t["bg"])
        btn_frame.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frame, text="🚀 Lancer",
                   command=self._start_search).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="💾 Rapport TXT",
                   command=self._save_search_report).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="🗑 Effacer",
                   command=lambda: self._sr.delete("1.0", tk.END)).pack(side=tk.RIGHT, padx=4)

        # Résultats
        self._sr = scrolledtext.ScrolledText(
            main, wrap=tk.WORD, font=("Consolas", 9),
            bg=t["console_bg"], fg="#ffcc00",
            relief=tk.FLAT, borderwidth=0)
        self._sr.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self._sr.tag_configure("sep",       foreground="#555555")
        self._sr.tag_configure("fichier",   foreground=t["accent"],
                               font=("Consolas", 10, "bold"))
        self._sr.tag_configure("ligne",     foreground=t["info"])
        self._sr.tag_configure("normal",    foreground="#ffcc00")
        self._sr.tag_configure("highlight", background="#ffff00",
                               foreground="#000000",
                               font=("Consolas", 9, "bold"))

    def _build_history_tab(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text=" 📚 Historique ")
        t = self.theme

        tb = tk.Frame(frame, bg=t["bg"])
        tb.pack(fill=tk.X, padx=10, pady=8)
        tk.Label(tb, text="📚 50 dernières exécutions",
                 bg=t["bg"], fg=t["accent"],
                 font=("Consolas", 12, "bold")).pack(side=tk.LEFT, padx=6)
        ttk.Button(tb, text="🗑 Effacer",
                   command=self._clear_history).pack(side=tk.RIGHT, padx=4)
        ttk.Button(tb, text="🔄 Rafraîchir",
                   command=self._refresh_history).pack(side=tk.RIGHT, padx=4)

        list_frame = tk.Frame(frame, bg=t["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._hist_list = tk.Listbox(
            list_frame, font=("Consolas", 9),
            bg=t["console_bg"], fg=t["fg"],
            selectbackground=t["select_bg"],
            selectforeground=t["select_fg"],
            yscrollcommand=sb.set,
            relief=tk.FLAT, borderwidth=0)
        self._hist_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self._hist_list.yview)
        self._hist_list.bind('<Double-Button-1>', self._load_from_history)

        tk.Label(frame, text="Détails :", bg=t["bg"],
                 fg=t["info"], font=("Consolas", 10, "bold"),
                 anchor="w").pack(fill=tk.X, padx=10, pady=(8, 2))
        self._hist_details = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, font=("Consolas", 9),
            bg=t["console_bg"], fg=t["fg"], height=8,
            relief=tk.FLAT, borderwidth=0)
        self._hist_details.pack(fill=tk.BOTH, padx=10, pady=(0, 8))

    def _build_terminal_tab(self):
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text=" 🖥️ Terminal ")
        t = self.theme

        tb = tk.Frame(frame, bg=t["bg"])
        tb.pack(fill=tk.X, padx=10, pady=(8, 4))
        tk.Label(tb, text="🖥️ TERMINAL EMBARQUÉ",
                 bg=t["bg"], fg=t["info"],
                 font=("Consolas", 12, "bold")).pack(side=tk.LEFT, padx=6)
        ttk.Button(tb, text="🗑 Effacer",
                   command=self._clear_terminal).pack(side=tk.RIGHT, padx=4)
        ttk.Button(tb, text="📁 PWD",
                   command=self._show_pwd).pack(side=tk.RIGHT, padx=4)

        self._term_out = scrolledtext.ScrolledText(
            frame, wrap=tk.WORD, font=("Consolas", 10),
            bg=t["console_bg"], fg=t["fg"],
            relief=tk.FLAT, borderwidth=0)
        self._term_out.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))
        self._term_out.tag_configure("output",  foreground=t["fg"])
        self._term_out.tag_configure("error",   foreground=t["error"])
        self._term_out.tag_configure("success", foreground=t["success"])
        self._term_out.tag_configure("prompt",  foreground=t["accent"],
                                     font=("Consolas", 10, "bold"))
        self._term_out.configure(state='disabled')

        cmd_frame = tk.Frame(frame, bg=t["bg"])
        cmd_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        tk.Label(cmd_frame, text="$", bg=t["bg"],
                 fg=t["accent"], font=("Consolas", 12, "bold")).pack(
                     side=tk.LEFT, padx=(0, 6))
        self._term_entry = tk.Entry(
            cmd_frame, font=("Consolas", 10),
            bg=t["editor_bg"], fg=t["accent"],
            insertbackground=t["accent"], relief=tk.FLAT)
        self._term_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self._term_entry.bind('<Return>', self._exec_terminal)
        ttk.Button(cmd_frame, text="▶ Exec",
                   command=lambda: self._exec_terminal(None)).pack(side=tk.RIGHT)

        self.terminal = EmbeddedTerminal(self._term_out)

        welcome = (
            "╔═══════════════════════════════════════════╗\n"
            "║  🖥️  Terminal embarqué — Kerberos v4.2   ║\n"
            "╚═══════════════════════════════════════════╝\n"
            "Tapez vos commandes ci-dessous et appuyez sur Entrée.\n\n"
        )
        self._term_out.configure(state='normal')
        self._term_out.insert(tk.END, welcome, "success")
        self._term_out.configure(state='disabled')

    # ── Raccourcis ────────────────────────────────────────────────────────
    def _bind_shortcuts(self):
        self.root.bind('<Control-n>', lambda e: self._new_file())
        self.root.bind('<Control-o>', lambda e: self._open_file())
        self.root.bind('<Control-s>', lambda e: self._save_file())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<F5>',        lambda e: self._run())
        self.root.bind('<F6>',        lambda e: self._analyze())
        self.root.bind('<F7>',        lambda e: self._run_profiled())
        self.root.bind('<F9>',        lambda e: self._toggle_bp_current())

    # ── Fichiers ──────────────────────────────────────────────────────────
    def _new_file(self):
        if messagebox.askyesno("Nouveau", "Créer un nouveau fichier vide ?"):
            self.current_file = None
            self._file_lbl.config(text="📄 Nouveau fichier")
            self._status_file.config(text="📄 Nouveau fichier")
            self.editor.delete("1.0", tk.END)
            self._clear_console()

    def _open_file(self):
        fn = filedialog.askopenfilename(
            title="Ouvrir un fichier Python",
            filetypes=[("Python", "*.py"), ("Tous", "*.*")])
        if fn:
            try:
                content = Path(fn).read_text(encoding='utf-8')
                self.editor.delete("1.0", tk.END)
                self.editor.insert("1.0", content)
                self.editor._highlight()
                self.editor._update_lines()
                self.current_file = fn
                name = Path(fn).name
                self._file_lbl.config(text=f"📄 {name}")
                self._status_file.config(text=f"📄 {name}")
                self._log(f"✅ Fichier ouvert : {fn}\n", "success")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'ouvrir :\n{e}")

    def _save_file(self):
        if self.current_file:
            try:
                Path(self.current_file).write_text(
                    self.editor.get("1.0", tk.END), encoding='utf-8')
                self._log(f"✅ Sauvegardé : {self.current_file}\n", "success")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder :\n{e}")
        else:
            self._save_as()

    def _save_as(self):
        fn = filedialog.asksaveasfilename(
            title="Enregistrer sous",
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("Tous", "*.*")])
        if fn:
            try:
                Path(fn).write_text(
                    self.editor.get("1.0", tk.END), encoding='utf-8')
                self.current_file = fn
                name = Path(fn).name
                self._file_lbl.config(text=f"📄 {name}")
                self._status_file.config(text=f"📄 {name}")
                self._log(f"✅ Sauvegardé : {fn}\n", "success")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder :\n{e}")

    # ── Exécution ─────────────────────────────────────────────────────────
    def _run(self, profiled: bool = False):
        if self.is_executing:
            messagebox.showwarning("Attention", "Exécution déjà en cours !")
            return
        code = self.editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Attention", "Éditeur vide !")
            return

        self._clear_console()
        self._tb_text.delete("1.0", tk.END)
        self.is_executing = True
        self._status_lbl.config(
            text="📊 Profilage…" if profiled else "🟢 Exécution…",
            fg=self.theme["info"] if profiled else self.theme["success"])

        # ✅ FIX : rafraîchit la liste breakpoints avant exécution
        self._refresh_bp_list()

        args = self._args_entry.get().strip().split() or None
        fn   = self.current_file or "<éditeur>"

        self._log(f"{'═'*55}\n", "info")
        self._log(f"{'📊' if profiled else '▶️'}  {Path(fn).name}\n", "info")
        self._log(f"{'═'*55}\n", "info")

        self.debugger.execute(code, fn, args, profile=profiled)

    def _run_profiled(self):
        self._run(profiled=True)

    def _stop(self):
        if self.is_executing:
            self.debugger.stop()
            self._log("\n⏹ Arrêté par l'utilisateur\n", "error")
            self._status_lbl.config(text="🔴 Arrêté", fg=self.theme["error"])
            self.is_executing = False

    def _analyze(self):
        code = self.editor.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Attention", "Éditeur vide !")
            return
        self._ana_text.delete("1.0", tk.END)
        ok     = self.analyzer.analyze(code, self.current_file or "<éditeur>")
        report = self.analyzer.get_report()
        for line in report.split('\n'):
            if '🔴' in line:
                self._ana_text.insert(tk.END, line + '\n', "error")
            elif '⚠️' in line or '🔸' in line:
                self._ana_text.insert(tk.END, line + '\n', "warning")
            else:
                tag = "success" if ok and not self.analyzer.warnings else ""
                self._ana_text.insert(tk.END, line + '\n', tag)

    # ── Callbacks debugger ────────────────────────────────────────────────
    def _on_output(self, line: str, is_error: bool):
        self._log(line, "error" if is_error else "output")

    def _on_error(self, error_text: str, code: str, filename: str):
        info = self.debugger.parse_traceback(error_text, code, filename)

        self._tb_text.delete("1.0", tk.END)
        self._tb_text.insert(tk.END, "🐛 TRACEBACK DÉTAILLÉ\n")
        self._tb_text.insert(tk.END, "═"*50 + "\n")
        self._tb_text.insert(tk.END, info["full_traceback"] + "\n")
        self._tb_text.insert(tk.END, f"❌ Type    : {info['type']}\n")
        self._tb_text.insert(tk.END, f"💬 Message : {info['message']}\n")

        if info['line']:
            self._tb_text.insert(tk.END,
                f"📍 Ligne {info['line']}\n", "err_line")
            self.editor.highlight_error_line(info['line'])

        # Gerex
        if self._gerex_var.get():
            gr = self.gerex.analyze(error_text)
            if gr:
                self._tb_text.insert(tk.END, "\n" + "═"*50 + "\n", "gerex")
                self._tb_text.insert(tk.END,
                    f"{gr['emoji']} gerex — {gr['cause']}\n", "gerex")
                self._tb_text.insert(tk.END,
                    f"   Fix : {gr['fix']}\n", "gerex")
                self._tb_text.insert(tk.END,
                    f"   Confiance : {int(gr['confidence']*100)}%\n", "gerex")

        # Suggestions
        if info['suggestions']:
            self._tb_text.insert(tk.END,
                "\n💡 SUGGESTIONS\n" + "═"*50 + "\n", "suggestion")
            for s in info['suggestions']:
                self._tb_text.insert(tk.END, f"{s}\n", "suggestion")

        # Auto-fix
        if info['auto_fix']:
            self._tb_text.insert(tk.END,
                "\n🤖 AUTO-FIX\n" + "═"*50 + "\n", "autofix")
            self._tb_text.insert(tk.END,
                info['auto_fix'] + "\n", "autofix")

    def _on_finish(self, return_code: int, profiled: bool):
        self.is_executing = False
        if return_code == 0:
            self._log(f"\n{'═'*55}\n✅ Succès (code 0)\n{'═'*55}\n",
                      "success")
            self._status_lbl.config(text="✅ Succès",
                                    fg=self.theme["success"])
        else:
            self._log(f"\n{'═'*55}\n❌ Erreur (code {return_code})\n{'═'*55}\n",
                      "error")
            self._status_lbl.config(text=f"❌ Erreur ({return_code})",
                                    fg=self.theme["error"])
        if profiled:
            self._show_profiling()

    # ── Console ───────────────────────────────────────────────────────────
    def _log(self, msg: str, tag: str = "output"):
        self.console.insert(tk.END, msg, tag)
        self.console.see(tk.END)

    def _clear_console(self):
        self.console.delete("1.0", tk.END)

    # ── Find/Replace ──────────────────────────────────────────────────────
    def _show_find(self):
        if self._find_dialog and self._find_dialog.win.winfo_exists():
            self._find_dialog.win.lift()
            return
        self._find_dialog = FindReplaceDialog(
            self.root, self.editor, self.theme)

    # ── Breakpoints ───────────────────────────────────────────────────────
    def _toggle_bp_current(self):
        try:
            line = int(self.editor.index(tk.INSERT).split('.')[0])
            added = self.bp_manager.toggle(line)
            self.editor._update_lines()
            self._refresh_bp_list()
            self._log(
                f"{'🔴 Breakpoint ajouté' if added else '⚪ Breakpoint retiré'}"
                f" — ligne {line}\n", "info")
        except Exception:
            pass

    def _clear_bps(self):
        if messagebox.askyesno("Confirmation",
                               "Supprimer tous les breakpoints ?"):
            self.bp_manager.clear()
            self.editor._update_lines()
            self._refresh_bp_list()
            self._log("🗑 Tous les breakpoints supprimés\n", "info")

    def _refresh_bp_list(self):
        """✅ FIX : affiche un message utile et se met à jour automatiquement"""
        try:
            self._bp_list.delete(0, tk.END)
            bps = self.bp_manager.all()

            if not bps:
                self._bp_list.config(fg=self.theme["comment"])
                self._bp_list.insert(tk.END, "⚪ Aucun breakpoint actif")
                self._bp_list.insert(tk.END, "")
                self._bp_list.insert(tk.END,
                    "💡 Clic sur numéro de ligne ou F9")
                return

            self._bp_list.config(fg=self.theme["error"])
            self._bp_list.insert(tk.END,
                f"🔴 {len(bps)} breakpoint(s) actif(s)")
            self._bp_list.insert(tk.END, "─" * 38)

            for bp in bps:
                try:
                    content = self.editor.get(
                        f"{bp}.0", f"{bp}.end").strip()
                    if len(content) > 46:
                        content = content[:43] + "..."
                    self._bp_list.insert(
                        tk.END, f"🔴 Ligne {bp:3d}  │  {content}")
                except Exception:
                    self._bp_list.insert(tk.END, f"🔴 Ligne {bp}")
        except Exception:
            pass

    def _goto_bp(self, event=None):
        sel = self._bp_list.curselection()
        if not sel:
            return
        text = self._bp_list.get(sel[0])
        m = re.search(r'Ligne\s+(\d+)', text)
        if m:
            ln = int(m.group(1))
            self.editor.see(f"{ln}.0")
            self.editor.mark_set(tk.INSERT, f"{ln}.0")
            self.editor.highlight_current_line(ln)
            self.nb.select(0)

    # ── Auto-fix ─────────────────────────────────────────────────────────
    def _apply_autofix(self):
        fix = self.debugger._last_autofix
        if not fix:
            messagebox.showinfo("Info",
                "Aucun auto-fix disponible.\n"
                "Exécute un code avec erreur d'abord (F5).")
            return
        if messagebox.askyesno("Auto-Fix",
                               f"Appliquer :\n{fix}\n\nAu début du fichier ?"):
            self.editor.insert("1.0", fix + "\n")
            self.editor._highlight()
            self._log("🤖 Auto-fix appliqué\n", "success")

    def _copy_autofix(self):
        fix = self.debugger._last_autofix
        if not fix:
            messagebox.showinfo("Info", "Aucun auto-fix disponible.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(fix)
        self._log("📋 Auto-fix copié dans le presse-papier\n", "success")

    # ── Gerex ─────────────────────────────────────────────────────────────
    def _toggle_gerex(self):
        state  = self._gerex_var.get()
        status = self.gerex.toggle(state)
        color  = self.theme["success"] if state else self.theme["error"]
        self._gerex_lbl.config(text=status, fg=color)
        self._log(f"🔍 gerex → {status}\n", "info")

    # ── Profiling ────────────────────────────────────────────────────────
    def _show_profiling(self):
        self._perf_text.delete("1.0", tk.END)
        self._perf_text.insert(tk.END,
            "⏱️  RAPPORT PERFORMANCE\n" + "═"*50 + "\n", "fast")
        self._perf_text.insert(tk.END,
            self.debugger.profiler.get_stats() + "\n")
        self._perf_text.insert(tk.END,
            "🎯 TOP 10 FONCTIONS LES PLUS LENTES\n" + "═"*50 + "\n", "slow")
        for fn in self.debugger.profiler.get_top_functions(10):
            ms  = fn['cumulative_time'] * 1000
            tag = "critical" if ms > 100 else "slow" if ms > 10 else "fast"
            ico = "🔴" if ms > 100 else "⚠️" if ms > 10 else "✅"
            self._perf_text.insert(tk.END,
                f"{ico} {fn['function']}()  "
                f"{ms:.2f} ms  |  {fn['calls']} appels\n", tag)

    def _show_perf_report(self):
        if not self.debugger.profiler.profiler:
            messagebox.showinfo("Info",
                "Aucun profilage effectué.\nAppuie sur F7.")
            return
        win = tk.Toplevel(self.root)
        win.title("📊 Rapport Performance")
        win.geometry("800x600")
        win.configure(bg=self.theme["bg"])
        t = scrolledtext.ScrolledText(
            win, wrap=tk.WORD, font=("Consolas", 9),
            bg=self.theme["console_bg"], fg=self.theme["fg"],
            relief=tk.FLAT, borderwidth=0)
        t.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        t.insert("1.0", self.debugger.profiler.get_stats())
        t.configure(state='disabled')
        ttk.Button(win, text="Fermer",
                   command=win.destroy).pack(pady=8)

    def _export_perf_csv(self):
        if not self.debugger.profiler.profiler:
            messagebox.showinfo("Info",
                "Aucun profilage effectué.\nAppuie sur F7.")
            return
        fn = filedialog.asksaveasfilename(
            title="Export CSV Performance",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")])
        if fn:
            try:
                with open(fn, 'w', newline='', encoding='utf-8') as f:
                    w = csv.writer(f)
                    w.writerow(['Fonction', 'Fichier', 'Ligne',
                                'Appels', 'Temps total (s)',
                                'Temps cumulé (s)'])
                    for r in self.debugger.profiler.get_top_functions(50):
                        w.writerow([
                            r['function'], r['file'], r['line'],
                            r['calls'],
                            f"{r['total_time']:.6f}",
                            f"{r['cumulative_time']:.6f}",
                        ])
                messagebox.showinfo("Succès", f"Export CSV :\n{fn}")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    # ── Terminal ──────────────────────────────────────────────────────────
    def _exec_terminal(self, event):
        cmd = self._term_entry.get().strip()
        if not cmd:
            return
        self._term_out.configure(state='normal')
        self._term_out.insert(tk.END, f"\n$ {cmd}\n", "prompt")
        self._term_out.configure(state='disabled')
        self.terminal.execute(cmd)
        self._term_entry.delete(0, tk.END)

    def _clear_terminal(self):
        self._term_out.configure(state='normal')
        self._term_out.delete("1.0", tk.END)
        self._term_out.configure(state='disabled')

    def _show_pwd(self):
        self._term_out.configure(state='normal')
        self._term_out.insert(tk.END,
            f"\n📁 {self.terminal.cwd}\n", "success")
        self._term_out.configure(state='disabled')

    # ── Recherche ─────────────────────────────────────────────────────────
    def _browse_search(self):
        d = filedialog.askdirectory(title="Sélectionner un dossier")
        if d:
            self._path_entry.delete(0, tk.END)
            self._path_entry.insert(0, d)

    def _start_search(self):
        self._sr.delete("1.0", tk.END)
        dossier = self._path_entry.get().strip()
        motif   = self._err_entry.get().strip()
        if not motif:
            messagebox.showwarning("Attention", "Entrez un terme à chercher")
            return
        if not os.path.isdir(dossier):
            messagebox.showerror("Erreur", f"Dossier introuvable :\n{dossier}")
            return

        exts = []
        if self._ext_py.get():   exts.append(".py")
        if self._ext_csv.get():  exts.append(".csv")
        if self._ext_json.get(): exts.append(".json")
        if self._ext_txt.get():  exts.append(".txt")
        if not exts:
            messagebox.showwarning("Attention",
                                   "Cochez au moins une extension")
            return

        def _search():
            results = []
            for ext in exts:
                for path in Path(dossier).rglob(f"*{ext}"):
                    try:
                        try:
                            lines = path.read_text(
                                encoding="utf-8").splitlines()
                        except UnicodeDecodeError:
                            lines = path.read_text(
                                encoding="latin-1").splitlines()
                        for i, line in enumerate(lines, 1):
                            if motif in line:
                                ctx_start = max(0, i - 2)
                                ctx_end   = min(len(lines), i + 2)
                                ctx = []
                                for j in range(ctx_start, ctx_end):
                                    pref = " >> " if j + 1 == i else "    "
                                    ctx.append(
                                        f"{pref}{j+1:4d} | {lines[j]}")
                                results.append({
                                    "file":    path.relative_to(dossier),
                                    "line":    i,
                                    "context": "\n".join(ctx),
                                })
                    except Exception:
                        pass

            def _display():
                if not results:
                    self._sr.insert(tk.END, "✅ Aucune occurrence trouvée\n")
                    return
                self._sr.insert(tk.END,
                    f"🔍 '{motif}' — {len(results)} occurrence(s)\n",
                    "fichier")
                self._sr.insert(tk.END, "═"*60 + "\n", "sep")
                for r in results:
                    self._sr.insert(tk.END,
                        f"\n📍 {r['file']}\n", "fichier")
                    self._sr.insert(tk.END,
                        f"   Ligne {r['line']}\n", "ligne")
                    for ln in r['context'].split('\n'):
                        if motif in ln:
                            parts = ln.split(motif, 1)
                            self._sr.insert(tk.END, parts[0], "normal")
                            self._sr.insert(tk.END, motif, "highlight")
                            self._sr.insert(tk.END,
                                parts[1] + "\n", "normal")
                        else:
                            self._sr.insert(tk.END,
                                ln + "\n", "normal")
                self._sr.insert(tk.END,
                    f"\n{'═'*60}\n✅ Total : {len(results)} résultat(s)\n")
                self._sr.see(tk.END)

            self.root.after(0, _display)

        threading.Thread(target=_search, daemon=True).start()

    def _save_search_report(self):
        content = self._sr.get("1.0", tk.END)
        if not content.strip():
            messagebox.showwarning("Attention", "Aucun résultat à sauvegarder")
            return
        fn = filedialog.asksaveasfilename(
            title="Sauvegarder le rapport",
            defaultextension=".txt",
            filetypes=[("Texte", "*.txt")])
        if fn:
            try:
                Path(fn).write_text(content, encoding='utf-8')
                messagebox.showinfo("Succès", f"Rapport sauvegardé :\n{fn}")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    # ── Historique ────────────────────────────────────────────────────────
    def _refresh_history(self):
        self._hist_list.delete(0, tk.END)
        for i, e in enumerate(reversed(
                self.debugger.execution_history)):
            name = (Path(e['filename']).name
                    if e['filename'] != "<éditeur>" else "Éditeur")
            self._hist_list.insert(
                tk.END, f"{i+1}. [{e['timestamp']}] {name}")

    def _load_from_history(self, event=None):
        sel = self._hist_list.curselection()
        if not sel:
            return
        idx = len(self.debugger.execution_history) - 1 - sel[0]
        entry = list(self.debugger.execution_history)[idx]
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", entry['code'])
        self.editor._highlight()
        self._hist_details.delete("1.0", tk.END)
        self._hist_details.insert(tk.END,
            f"Date    : {entry['timestamp']}\n"
            f"Fichier : {entry['filename']}\n"
            f"Args    : {' '.join(entry['args']) or 'aucun'}\n"
            f"{'─'*50}\n{entry['code']}")
        self.nb.select(0)
        messagebox.showinfo("Historique", "Code chargé depuis l'historique !")

    def _clear_history(self):
        if messagebox.askyesno("Confirmation",
                               "Effacer tout l'historique ?"):
            self.debugger.execution_history.clear()
            self._refresh_history()
            self._hist_details.delete("1.0", tk.END)

    # ── Auto-Watch ────────────────────────────────────────────────────────
    def _toggle_watch(self):
        if self._watch_var.get():
            if not self.current_file:
                messagebox.showwarning("Attention",
                    "Ouvre un fichier d'abord pour activer le watch !")
                self._watch_var.set(False)
                return
            self._start_watch()
        else:
            self.watch_active = False

    def _start_watch(self):
        self.watch_active = True
        self._log(f"👁️ Watch activé : {self.current_file}\n", "info")
        def _loop():
            last = os.path.getmtime(self.current_file)
            while self.watch_active:
                time.sleep(1)
                try:
                    cur = os.path.getmtime(self.current_file)
                    if cur > last:
                        last = cur
                        content = Path(
                            self.current_file).read_text(encoding='utf-8')
                        self.editor.delete("1.0", tk.END)
                        self.editor.insert("1.0", content)
                        self.editor._highlight()
                        self._log("\n🔄 Fichier modifié → rechargement\n",
                                  "info")
                        self.root.after(0, self._run)
                except Exception:
                    pass
        threading.Thread(target=_loop, daemon=True).start()

    # ── Thème ─────────────────────────────────────────────────────────────
    def _change_theme(self, name: str):
        if name not in THEMES:
            return
        self._theme_name = name
        self.theme       = THEMES[name]
        t                = self.theme

        self.root.configure(bg=t["bg"])
        self._setup_style()

        # Widgets
        for w in [self._file_lbl, self._status_lbl]:
            try:
                w.config(bg=t["bg"])
            except Exception:
                pass

        self._status_file.config(bg=t["tab_bg"], fg=t["accent"])
        self._status_theme.config(
            bg=t["tab_bg"], fg=t["fg"],
            text=f"🎨 {name}")
        self._status_cursor.config(bg=t["tab_bg"], fg=t["fg"])

        self.console.config(bg=t["console_bg"], fg=t["fg"])
        self.console.tag_configure("error",   foreground=t["error"])
        self.console.tag_configure("success", foreground=t["success"])
        self.console.tag_configure("info",    foreground=t["info"])

        self._ana_text.config(bg=t["console_bg"])
        self._tb_text.config(bg=t["console_bg"], fg=t["error"])
        self._perf_text.config(bg=t["console_bg"], fg=t["info"])
        self._bp_list.config(bg=t["console_bg"], fg=t["error"])
        self._sr.config(bg=t["console_bg"])
        self._hist_list.config(bg=t["console_bg"], fg=t["fg"])
        self._hist_details.config(bg=t["console_bg"], fg=t["fg"])
        self._term_out.config(bg=t["console_bg"], fg=t["fg"])

        self.editor.apply_theme(t)
        self.editor.line_canvas.config(bg="#111111")

        self._log(f"🎨 Thème changé : {name}\n", "info")

    # ── Export HTML ──────────────────────────────────────────────────────
    def _export_html(self):
        con = self.console.get("1.0", tk.END)
        tb  = self._tb_text.get("1.0", tk.END)
        ana = self._ana_text.get("1.0", tk.END)
        if not any(x.strip() for x in [con, tb, ana]):
            messagebox.showinfo("Info",
                "Rien à exporter.\nExécute du code d'abord.")
            return
        fn = filedialog.asksaveasfilename(
            title="Export HTML",
            defaultextension=".html",
            filetypes=[("HTML", "*.html")])
        if fn:
            html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8">
<title>Kerberos Debugger v4.2 — Rapport</title>
<style>
body{{font-family:Consolas,monospace;background:#1a1a1a;
     color:#e0e0e0;padding:24px;line-height:1.5}}
h1{{color:#00ffcc;border-bottom:2px solid #00ffcc;padding-bottom:8px}}
h2{{color:#bb86fc;margin-top:28px}}
.box{{background:#0d0d0d;padding:16px;border-radius:6px;
      margin:16px 0;border-left:4px solid #00ffcc}}
pre{{white-space:pre-wrap;word-break:break-all}}
.err{{color:#ff5252}}.ok{{color:#4CAF50}}.warn{{color:#ff9800}}
footer{{text-align:center;color:#555;margin-top:40px;font-size:.85em}}
</style></head><body>
<h1>🐺 Kerberos Debugger v4.2 — Rapport</h1>
<p><b>Généré :</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
<p><b>Fichier :</b> {self.current_file or 'Éditeur'}</p>
<div class="box"><h2>📟 Console</h2><pre>{con}</pre></div>
<div class="box"><h2>🔬 Analyse statique</h2><pre>{ana}</pre></div>
<div class="box"><h2>🐛 Traceback</h2>
<pre class="err">{tb}</pre></div>
<footer>Kerberos Debugger v4.2 — Victor Pozen 🐺 — GPLv3</footer>
</body></html>"""
            try:
                Path(fn).write_text(html, encoding='utf-8')
                messagebox.showinfo("Succès", f"HTML exporté :\n{fn}")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    # ── Curseur ───────────────────────────────────────────────────────────
    def _update_cursor(self, event=None):
        try:
            pos  = self.editor.index(tk.INSERT)
            ln, col = pos.split('.')
            self._status_cursor.config(text=f"Ln {ln}, Col {col}")
        except Exception:
            pass

    # ── Aide ─────────────────────────────────────────────────────────────
    def _show_shortcuts(self):
        messagebox.showinfo("Raccourcis clavier", """
🎹 RACCOURCIS CLAVIER — Kerberos Debugger v4.2
═══════════════════════════════════════════════
📁 Fichiers
  Ctrl+N   Nouveau fichier
  Ctrl+O   Ouvrir
  Ctrl+S   Sauvegarder
  Ctrl+Q   Quitter

▶️ Exécution
  F5       Exécuter
  F6       Analyse statique
  F7       Exécuter avec profilage

✏️ Édition
  Ctrl+D   Dupliquer la ligne
  Ctrl+/   Commenter/Décommenter
  Ctrl+F   Chercher / Remplacer
  Tab      Insérer 4 espaces

🔴 Breakpoints
  F9             Toggle breakpoint ligne courante
  Double-clic    Aller à un breakpoint (liste)
═══════════════════════════════════════════════
""")

    def _show_doc(self):
        messagebox.showinfo("Documentation", """
🐺 KERBEROS DEBUGGER v4.2 — Documentation
══════════════════════════════════════════
NOUVEAUTÉS v4.2 :
  ✅ Bug menu Quit corrigé
  ✅ Onglet Breakpoints rafraîchi automatiquement
  ✅ Find/Replace natif (Ctrl+F)
  ✅ Coloration syntaxique optimisée (zone visible)
  ✅ Thème appliqué à tous les widgets

GEREX :
  Toggle dans l'onglet Traceback.
  Analyse 100% locale — zéro réseau.

AUTO-FIX :
  Suggestions automatiques après erreur.
  "Appliquer" insère le fix dans l'éditeur.

PROFILAGE :
  F7 au lieu de F5 pour profiler.
  Export CSV disponible.

PRIVACY FIRST :
  Aucune IA activée par défaut.
  Aucun appel réseau silencieux.
  Tout reste sur votre machine.
══════════════════════════════════════════
""")

    def _show_about(self):
        messagebox.showinfo("À propos", """
🐺 KERBEROS DEBUGGER v4.2
══════════════════════════════════════
Débogueur Python modulaire — Privacy First

Auteur  : Victor Pozen 🐺
Licence : GPLv3
Version : 4.2
Date    : Février 2026

Historique depuis v4.1 :
  • Correction bug quit()
  • Breakpoints auto-rafraîchis
  • Find/Replace natif
  • Highlight optimisé
  • Gerex étendu (RecursionError, MemoryError)
══════════════════════════════════════
""")


# ============================================================
# POINT D'ENTRÉE
# ============================================================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app  = KerberosDebuggerApp(root)
        root.mainloop()
    except Exception as e:
        print(f"ERREUR FATALE : {e}")
        tb_module.print_exc()
        input("\nAppuyez sur Entrée pour quitter…")
