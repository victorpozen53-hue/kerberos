#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 Guard Explainer — Analyse et explique automatiquement les guards
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Analyse statique du code Python (AST)
- Détecte les imports, fonctions, patterns
- Génère une description automatique si docstring absente
- Identifie le type de guard (réseau, système, sécurité, etc.)
- Vérifie l'intégration Kerberos (_GUARD_METRICS, start_guard, get_stats)
- Affiche fenêtre détaillée avec onglets (Description, Intégration, Code)
- Copier-coller libre dans les 3 onglets (licence affichée dans l'UI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guard Explainer
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE : GPLv3 (GNU General Public License v3.0)
#  AUTEUR  : Victor Pozen
#  VERSION : 4.2 Ultimate
#  DATE    : 2025
#  🔗 https://github.com/victorpozen
#  💰 https://liberapay.com/EthicalKerberos/
# ============================================================================

import ast
import threading
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# ============================================================================
# === PATTERNS DE DÉTECTION ==================================================
# ============================================================================

GUARD_PATTERNS = {
    "network": {
        "imports": ["socket", "requests", "urllib", "http", "psutil"],
        "keywords": ["connect", "send", "recv", "IP", "port", "firewall", "block", "netshield"],
        "description": "Guard réseau — Gère les connexions, le filtrage IP ou le monitoring réseau",
        "color": "#ff5252"
    },
    "system": {
        "imports": ["psutil", "os", "sys", "platform", "subprocess", "ctypes"],
        "keywords": ["process", "cpu", "memory", "disk", "system", "resource", "thread"],
        "description": "Guard système — Surveille les ressources système (CPU, RAM, processus)",
        "color": "#00ffcc"
    },
    "security": {
        "imports": ["hashlib", "cryptography", "ssl", "secrets", "json"],
        "keywords": ["encrypt", "decrypt", "hash", "password", "auth", "token", "key", "shield", "protect"],
        "description": "Guard sécurité — Gère le chiffrement, l'authentification ou la protection des données",
        "color": "#ff9800"
    },
    "file": {
        "imports": ["shutil", "pathlib", "io", "zipfile"],
        "keywords": ["file", "read", "write", "copy", "delete", "backup", "quarantine", "folder"],
        "description": "Guard fichiers — Gère la manipulation, la protection ou la quarantaine de fichiers",
        "color": "#4CAF50"
    },
    "monitoring": {
        "imports": ["logging", "datetime", "time", "threading"],
        "keywords": ["log", "monitor", "watch", "alert", "track", "event", "scan", "detect"],
        "description": "Guard monitoring — Surveille et logge les événements système",
        "color": "#bb86fc"
    },
    "gui": {
        "imports": ["tkinter", "tkinter.ttk", "PIL", "pystray", "webbrowser"],
        "keywords": ["window", "button", "menu", "tray", "interface", "UI", "canvas", "label"],
        "description": "Guard interface — Gère l'interface graphique ou la tray icon",
        "color": "#ffeb3b"
    },
    "guard_management": {
        "imports": ["importlib", "threading", "ast", "weakref"],
        "keywords": ["guard", "load", "unload", "start", "stop", "manager", "cortex", "registry"],
        "description": "Guard management — Gère le chargement et l'orchestration des autres guards",
        "color": "#00bcd4"
    }
}

# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================

class GuardExplainer:
    """Analyse et explique automatiquement un guard"""

    def __init__(self, guard_path: Path):
        self.guard_path = guard_path
        self.guard_name = guard_path.stem
        self.source_code = ""
        self.tree = None
        self.imports = []
        self.functions = []
        self.classes = []
        self.keywords_found = []

    def analyze(self) -> Dict:
        """Analyse complète du guard"""
        try:
            self.source_code = self.guard_path.read_text(encoding="utf-8")
            self.tree = ast.parse(self.source_code)

            self._extract_imports()
            self._extract_functions()
            self._extract_classes()
            self._find_keywords()

            guard_type  = self._detect_guard_type()
            integration = self._detect_kerberos_integration()
            description = self._generate_description(guard_type)

            return {
                "guard_name":          self.guard_name,
                "file":                str(self.guard_path),
                "type":                guard_type,
                "type_color":          GUARD_PATTERNS.get(guard_type, {}).get("color", "#888888"),
                "description":         description,
                "imports":             self.imports,
                "functions":           self.functions,
                "classes":             self.classes,
                "has_docstring":       bool(ast.get_docstring(self.tree)),
                "lines":               len(self.source_code.splitlines()),
                "kerberos_integration": integration,
                "integration_score":   sum(integration.values()),
            }

        except Exception as e:
            return {
                "guard_name":          self.guard_name,
                "error":               str(e),
                "description":         f"⚠️ Erreur d'analyse : {e}",
                "kerberos_integration": {},
                "integration_score":   0,
                "type":                "unknown",
                "type_color":          "#888888",
            }

    def _extract_imports(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.imports.append(node.module.split('.')[0])

    def _extract_functions(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):
                    self.functions.append(node.name)

    def _extract_classes(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                self.classes.append(node.name)

    def _find_keywords(self):
        code_lower = self.source_code.lower()
        for pattern_type, pattern_info in GUARD_PATTERNS.items():
            for keyword in pattern_info["keywords"]:
                if keyword.lower() in code_lower:
                    self.keywords_found.append((keyword, pattern_type))

    def _detect_guard_type(self) -> str:
        type_scores = {}
        for pattern_type, pattern_info in GUARD_PATTERNS.items():
            score = 0
            for imp in self.imports:
                if imp in pattern_info["imports"]:
                    score += 2
            for keyword, _ in self.keywords_found:
                if keyword in pattern_info["keywords"]:
                    score += 1
            if score > 0:
                type_scores[pattern_type] = score
        if type_scores:
            return max(type_scores, key=type_scores.get)
        return "unknown"

    def _detect_kerberos_integration(self) -> dict:
        return {
            "has_publish_metric": "_publish_metric" in self.source_code,
            "has_get_stats":      "get_stats"        in self.source_code,
            "has_start_guard":    "start_guard"      in self.source_code,
            "has_guard_metrics":  "_GUARD_METRICS"   in self.source_code,
        }

    def _generate_description(self, guard_type: str) -> str:
        docstring = ast.get_docstring(self.tree)
        if docstring:
            return docstring.split('\n')[0]
        base_desc = GUARD_PATTERNS.get(guard_type, {}).get(
            "description", "Guard personnalisé — Fonctionnalité spécifique"
        )
        details = []
        if "start_guard" in self.functions or "run" in self.functions:
            details.append("démarrable")
        if "monitor" in self.functions or "scan" in self.functions:
            details.append("surveillance active")
        if "block" in self.functions or "protect" in self.functions:
            details.append("protection")
        if details:
            base_desc += f" ({', '.join(details)})"
        return base_desc

# ============================================================================
# === FONCTIONS UTILITAIRES ==================================================
# ============================================================================

def analyze_guard(guard_path: Path) -> Dict:
    explainer = GuardExplainer(guard_path)
    return explainer.analyze()

def get_stats() -> dict:
    guards_dir  = Path(__file__).parent
    all_guards  = list(guards_dir.glob("guard_*.py"))
    analyzed    = 0
    for g in all_guards:
        try:
            analyze_guard(g)
            analyzed += 1
        except:
            pass
    return {
        "guard_name":            "Guard Explainer",
        "total_guards_analyzed": analyzed,
        "total_guards":          len(all_guards),
        "last_analysis":         datetime.now().isoformat()
    }

# ============================================================================
# === INTÉGRATION UI — FENÊTRE DÉTAILLÉE =====================================
# ============================================================================

def show_guard_info_window(guard_path: Path, root_widget, execute_callback=None):
    """
    Affiche une fenêtre détaillée avec onglets pour un guard.
    ✅ COPIER-COLLER LIBRE dans les 3 onglets — Licence affichée dans l'UI
    """
    import tkinter as tk
    from tkinter import ttk, scrolledtext

    # ── Fenêtre Toplevel 650x600 ──────────────────────────────────
    win = tk.Toplevel(root_widget)
    win.title(f"🛡️ {guard_path.stem}")
    win.geometry("650x600")
    win.configure(bg='#1a1a2e')
    win.resizable(True, True)

    # ── Header avec badge de type ─────────────────────────────────
    header = tk.Frame(win, bg='#16213e', height=70)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    tk.Label(header, text=f"🛡️ {guard_path.stem.upper()}",
             bg='#16213e', fg='#00ffcc',
             font=("Consolas", 14, "bold")).pack(side=tk.LEFT, padx=20, pady=20)

    badge_label = tk.Label(header, text="🔍 Analyse...",
                           bg='#2d5a7b', fg='white',
                           font=("Consolas", 9, "bold"),
                           padx=8, pady=4)
    badge_label.pack(side=tk.RIGHT, padx=20, pady=20)

    # ── Barre métriques rapides ───────────────────────────────────
    metrics_frame = tk.Frame(win, bg='#1a1a2e')
    metrics_frame.pack(fill=tk.X, padx=15, pady=(10, 0))

    metric_boxes = {}
    for key, icon, label in [
        ("lines",  "📏", "Lignes"),
        ("type",   "📊", "Type"),
        ("score",  "🔗", "Intégration"),
        ("docstr", "📝", "Docstring"),
    ]:
        box = tk.Frame(metrics_frame, bg='#161a2e', relief=tk.RIDGE, bd=1)
        box.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=4)
        tk.Label(box, text=icon, bg='#161a2e', fg='#00ffcc',
                 font=("Consolas", 18)).pack(pady=(8, 0))
        val = tk.Label(box, text="...", bg='#161a2e', fg='white',
                       font=("Consolas", 11, "bold"))
        val.pack()
        tk.Label(box, text=label, bg='#161a2e', fg='#a0a0c0',
                 font=("Consolas", 8)).pack(pady=(0, 8))
        metric_boxes[key] = val

    # ── Notebook avec onglets ─────────────────────────────────────
    nb = ttk.Notebook(win)
    nb.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

    # ── Onglet Description ────────────────────────────────────────
    tab_desc = ttk.Frame(nb)
    nb.add(tab_desc, text=' 📝 Description ')
    desc_text = scrolledtext.ScrolledText(
        tab_desc, font=("Consolas", 10),
        bg='#0a0a0a', fg='#e0e0e0', wrap=tk.WORD,
        state='normal')  # ← Libre pour copier-coller
    desc_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    desc_text.insert(tk.END, "🔍 Analyse en cours...\n")

    # ── Onglet Intégration Kerberos — ScrolledText copiable ───────
    tab_integ = ttk.Frame(nb)
    nb.add(tab_integ, text=' 🔗 Intégration ')
    integ_text = scrolledtext.ScrolledText(
        tab_integ, font=("Consolas", 10),
        bg='#1e1e2e', fg='#e0e0e0', wrap=tk.WORD,
        state='normal')  # ← Libre pour copier-coller ✅
    integ_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    integ_text.insert(tk.END, "🔍 Analyse en cours...\n")

    # ── Onglet Code (aperçu 80 lignes) ────────────────────────────
    tab_code = ttk.Frame(nb)
    nb.add(tab_code, text=' 💻 Code ')
    code_text = scrolledtext.ScrolledText(
        tab_code, font=("Consolas", 9),
        bg='#0a0a0a', fg='#00ff00', wrap=tk.NONE,
        state='normal')  # ← Libre pour copier-coller
    code_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    try:
        preview = guard_path.read_text(encoding="utf-8").splitlines()[:80]
        code_text.insert(tk.END, "\n".join(preview) + "\n\n[... aperçu limité à 80 lignes]")
    except Exception:
        code_text.insert(tk.END, "⚠️ Lecture impossible")

    # ── Footer avec boutons ───────────────────────────────────────
    footer = tk.Frame(win, bg='#16213e', height=45)
    footer.pack(fill=tk.X, side=tk.BOTTOM)
    footer.pack_propagate(False)

    def copy_to_clipboard():
        try:
            current_tab = nb.index(nb.select())
            if current_tab == 0:
                content = desc_text.get("1.0", tk.END)
            elif current_tab == 1:
                content = integ_text.get("1.0", tk.END)  # ✅ Intégration copiable
            else:
                content = code_text.get("1.0", tk.END)
            root_widget.clipboard_clear()
            root_widget.clipboard_append(content)
        except Exception:
            pass

    tk.Button(footer, text="📋 Copier", bg='#2d5a7b',
              fg='white', font=("Consolas", 10),
              command=copy_to_clipboard
              ).pack(side=tk.LEFT, padx=10, pady=8)

    if execute_callback:
        tk.Button(footer, text="▶️ Exécuter", bg='#2d7b5a',
                  fg='white', font=("Consolas", 10),
                  command=execute_callback
                  ).pack(side=tk.LEFT, padx=10, pady=8)

    tk.Button(footer, text="Fermer", bg='#2d5a7b',
              fg='white', font=("Consolas", 10),
              command=win.destroy
              ).pack(side=tk.RIGHT, padx=10, pady=8)

    # ── Analyse en thread ─────────────────────────────────────────
    def do_analysis():
        result = analyze_guard(guard_path)

        def update_ui():
            if not win.winfo_exists():
                return

            # Métriques
            metric_boxes["lines"].config(text=str(result.get("lines", "?")))
            metric_boxes["type"].config(text=result.get("type", "?"))
            metric_boxes["score"].config(text=f"{result.get('integration_score', 0)}/4")
            metric_boxes["docstr"].config(
                text="✅ Oui" if result.get("has_docstring") else "❌ Non",
                fg='#4CAF50' if result.get("has_docstring") else '#ff5252')

            # Badge type
            type_color = result.get("type_color", "#888888")
            badge_label.config(text=f"● {result.get('type', '?').upper()}",
                               bg=type_color, fg='#000000')

            # ── Onglet Description ────────────────────────────────
            desc_text.delete("1.0", tk.END)
            desc_text.insert(tk.END, f"📝 {result.get('description', 'Aucune')}\n")
            desc_text.insert(tk.END, f"\n📏 Lignes: {result.get('lines', '?')}\n")
            if result.get('imports'):
                desc_text.insert(tk.END, "\n📦 IMPORTS :\n")
                for imp in result['imports'][:8]:
                    desc_text.insert(tk.END, f"   • {imp}\n")
            if result.get('functions'):
                desc_text.insert(tk.END, "\n⚙️ FONCTIONS PUBLIQUES :\n")
                for fn in result['functions'][:8]:
                    desc_text.insert(tk.END, f"   • {fn}()\n")
            if result.get('classes'):
                desc_text.insert(tk.END, "\n🏗️ CLASSES :\n")
                for cl in result['classes']:
                    desc_text.insert(tk.END, f"   • {cl}\n")

            # ── Onglet Intégration — ScrolledText copiable ✅ ─────
            integration = result.get("kerberos_integration", {})
            score       = result.get("integration_score", 0)

            integ_text.delete("1.0", tk.END)
            integ_text.insert(tk.END, "📜 Licence GPLv3 — Victor Pozen\n")
            integ_text.insert(tk.END, "🔗 github.com/victorpozen\n")
            integ_text.insert(tk.END, "💰 liberapay.com/EthicalKerberos\n")
            integ_text.insert(tk.END, "─" * 40 + "\n\n")

            score_color = "✅" if score >= 3 else "🟠" if score >= 1 else "🔴"
            integ_text.insert(tk.END, f"{score_color}  Score d'intégration : {score}/4\n\n")
            integ_text.insert(tk.END, "─" * 40 + "\n\n")

            checks = {
                "has_start_guard":    ("start_guard()",     "Point d'entrée Kerberos"),
                "has_get_stats":      ("get_stats()",        "Stats pour onglet Guards"),
                "has_publish_metric": ("_publish_metric()", "VU-mètre actif"),
                "has_guard_metrics":  ("_GUARD_METRICS",    "Registre métriques"),
            }
            for key, (label, detail) in checks.items():
                ok   = integration.get(key, False)
                icon = "✅" if ok else "❌"
                integ_text.insert(tk.END, f"{icon}  {label}\n")
                integ_text.insert(tk.END, f"     → {detail}\n\n")

        root_widget.after(0, update_ui)

    threading.Thread(target=do_analysis, daemon=True).start()

# ============================================================================
# === POINTS D'ENTRÉE ========================================================
# ============================================================================

def start_guard():
    print("🧠 [Guard Explainer] Module chargé — Prêt à analyser les guards...")
    return GuardExplainer

def run():
    print("""
╔════════════════════════════════════════════════════════════╗
║  🧠 KERBEROS GUARD EXPLAINER — Analyse de guards          ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
║  🔗 github.com/victorpozen                                ║
║  💰 liberapay.com/EthicalKerberos                         ║
╚════════════════════════════════════════════════════════════╝
    """)
    guards_dir = Path(__file__).parent
    for guard_file in sorted(guards_dir.glob("guard_*.py")):
        result = analyze_guard(guard_file)
        print(f"\n🛡️ {result['guard_name']}")
        print(f"   Type        : {result['type']}")
        print(f"   Intégration : {result['integration_score']}/4")
        print(f"   {result['description']}")

if __name__ == "__main__":
    run()
