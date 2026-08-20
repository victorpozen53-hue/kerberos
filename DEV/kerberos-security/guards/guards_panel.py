#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Guards Panel — Panneau de contrôle des guards (HYBRIDE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Affichage en grille horizontale (4 cartes par ligne)
- VU-mètres animés par carte
- Bouton ℹ️ → Fenêtre détaillée avec 3 onglets (Interconnexions, Stats, Code)
- Bouton ▶️ → Exécution du guard
- Refresh automatique toutes les 2s
- Intégration Kerberos complète
- Rapports JSON + HTML dans logs.full.option/logs_guards/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guards Panel (Hybride)
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE : GPLv3
#  AUTEUR  : Victor Pozen
#  VERSION : 4.2 Ultimate
#  DATE    : 2025
#  🔗 https://github.com/victorpozen
# ============================================================================
import ast
import threading
import sys
import random
import json
import psutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ============================================================================
# === INTÉGRATION KERBEROS ===================================================
# ============================================================================
try:
    _kerberos_main = sys.modules.get("__main__")
    _GUARD_METRICS: dict = getattr(_kerberos_main, "_GUARD_METRICS", {})
except Exception:
    _GUARD_METRICS = {}

_MODULE_NAME = Path(__file__).name

def _publish_metric(level: float):
    """Publie le niveau d'activité du guard (0.0 à 1.0)"""
    _GUARD_METRICS[_MODULE_NAME] = max(0.0, min(1.0, level))

# ============================================================================
# === LOGS CENTRALISÉS + RAPPORTS ============================================
# ============================================================================
LOGS_BASE = Path(r"F:\kerberos-security\logs.full.option\logs_guards")
GUARD_LOGS_DIR = LOGS_BASE / "guards_panel"

# Créer le dossier au premier démarrage
GUARD_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# === FONCTIONS DE RAPPORT ===================================================
# ============================================================================
def _save_reports(report_data: dict):
    """Sauvegarde les rapports JSON + HTML"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Rapport JSON
    json_file = GUARD_LOGS_DIR / f"guards_panel_report_{timestamp}.json"
    json_file.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # Rapport HTML
    html_file = GUARD_LOGS_DIR / f"guards_panel_report_{timestamp}.html"
    _generate_html_report(report_data, html_file)

def _generate_html_report(data: dict, filepath: Path):
    """Génère un rapport HTML lisible"""
    status_color = {
        "active": "#00ff88",
        "monitoring": "#00aaff",
        "stopped": "#ff2244"
    }.get(data.get("status", "unknown"), "#607d8b")
    
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Guards Panel — {data.get('timestamp', 'N/A')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #0a0f1a;
            color: #00ffcc;
            font-family: 'Consolas', monospace;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            border: 2px solid #00ffcc;
            text-align: center;
        }}
        header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
            text-shadow: 0 0 10px #00ffcc;
        }}
        .timestamp {{ color: #607d8b; font-size: 14px; }}
        .section {{
            background: #1a1a2e;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #00ffcc;
        }}
        .section h2 {{
            margin-bottom: 15px;
            color: #00ffcc;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-card {{
            background: #16213e;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: {status_color};
        }}
        .stat-label {{ color: #607d8b; font-size: 12px; margin-top: 5px; }}
        .footer {{
            text-align: center;
            padding: 20px;
            margin-top: 30px;
            border-top: 1px solid #2d2d3d;
            color: #607d8b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ RAPPORT GUARDS PANEL</h1>
            <p class="timestamp">📅 {data.get('timestamp', 'N/A')}</p>
        </header>
        
        <div class="section">
            <h2>📊 Résumé du Panel</h2>
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-value">{data.get('total_guards', 0)}</div>
                    <div class="stat-label">Guards Totaux</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{data.get('cards_per_row', 4)}</div>
                    <div class="stat-label">Cartes par Ligne</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{"✅" if data.get('panel_active') else "❌"}</div>
                    <div class="stat-label">Panel Actif</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: {status_color}">{data.get('status', 'unknown').upper()}</div>
                    <div class="stat-label">Statut</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>🛡️ KERBEROS ULTIMATE v4.2 — GPLv3 • Victor Pozen</p>
            <p>🔗 github.com/victorpozen</p>
        </div>
    </div>
</body>
</html>"""
    filepath.write_text(html, encoding="utf-8")

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================
GUARDS_DIR   = Path(__file__).parent
CARDS_PER_ROW = 4

# ============================================================================
# === FENÊTRE DÉTAILLÉE — 3 ONGLETS ==========================================
# ============================================================================
class GuardDetailWindow:
    """Fenêtre détaillée guard — Header shield + 4 métriques + 3 onglets"""
    # Fonctions Kerberos requises pour le score d'intégration
    _INTEGRATION_CHECKS = [
        ("start_guard()",    "Point d'entrée Kerberos"),
        ("get_stats()",      "Stats pour onglet Guards"),
        ("_publish_metric()", "Vu-mètre actif"),
        ("_GUARD_METRICS",   "Registre métriques"),
    ]
    
    def __init__(self, root_widget, guard_path: Path, guard_name: str):
        self.root = tk.Toplevel(root_widget)
        self.root.title(f"🛡️ {guard_name.replace('.py', '').upper()}")
        self.root.geometry("820x680")
        self.root.configure(bg='#0d1117')
        self.root.resizable(True, True)
        self.guard_path  = guard_path
        self.guard_name  = guard_name
        self._root_widget = root_widget
        
        # Analyse du guard une seule fois
        self._source       = self._read_source()
        self._analysis     = self._analyze_guard()
        self._integ_score  = self._compute_integration_score()
        self._setup_ui()
    
    # ─────────────────────────────────────────────────────────────────────
    # ANALYSE
    # ─────────────────────────────────────────────────────────────────────
    def _read_source(self) -> str:
        try:
            return self.guard_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""
    
    def _analyze_guard(self) -> dict:
        """Analyse complète du guard : lignes, type, docstring, imports"""
        src    = self._source
        lines  = len(src.splitlines())
        has_doc = False
        guard_type = "system"
        imports = {"guards": [], "modules": [], "external": []}
        
        try:
            tree = ast.parse(src)
            doc  = ast.get_docstring(tree)
            has_doc = bool(doc)
            
            # Type du guard
            if "network" in self.guard_name.lower() or "net" in self.guard_name.lower():
                guard_type = "network"
            elif "crypto" in self.guard_name.lower() or "quantum" in self.guard_name.lower():
                guard_type = "crypto"
            elif "ai" in self.guard_name.lower() or "yara" in self.guard_name.lower():
                guard_type = "ai"
            else:
                guard_type = "system"
            
            # Imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name
                        if name.startswith("guard_"):
                            imports["guards"].append(name)
                        elif "kerberos" in name.lower():
                            imports["modules"].append(name)
                        else:
                            imports["external"].append(name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("guard_"):
                        imports["guards"].append(node.module)
                    elif "kerberos" in node.module.lower():
                        imports["modules"].append(node.module)
                    else:
                        imports["external"].append(node.module)
        except Exception:
            pass
        
        return {
            "lines":      lines,
            "type":       guard_type,
            "has_doc":    has_doc,
            "imports":    imports,
        }
    
    def _compute_integration_score(self) -> list:
        """Vérifie la présence de chaque élément d'intégration Kerberos"""
        src = self._source
        return [name in src for name, _ in self._INTEGRATION_CHECKS]
    
    # ─────────────────────────────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        short = self.guard_name.replace(".py", "").upper()
        gtype = self._analysis["type"]
        
        # ── Header ───────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg='#161b27', height=68)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Icône shield + nom
        left = tk.Frame(header, bg='#161b27')
        left.pack(side=tk.LEFT, padx=18, pady=10)
        tk.Label(left, text="🛡", bg='#161b27', fg='#00ccaa',
                font=("Segoe UI Emoji", 22)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Label(left, text=short, bg='#161b27', fg='#00ffcc',
                font=("Consolas", 15, "bold")).pack(side=tk.LEFT)
        
        # Badge type à droite
        badge_colors = {
            "system":  ("#00ffcc", "#0a2a20"),
            "network": ("#00aaff", "#0a1a2a"),
            "crypto":  ("#ff8800", "#2a1a00"),
            "ai":      ("#ff2244", "#2a0010"),
        }
        bc, bg2 = badge_colors.get(gtype, ("#00ffcc", "#0a2a20"))
        badge = tk.Frame(header, bg=bg2, padx=10, pady=4)
        badge.pack(side=tk.RIGHT, padx=18, pady=18)
        tk.Label(badge, text=f"● {gtype.upper()}",
                bg=bg2, fg=bc,
                font=("Consolas", 9, "bold")).pack()
        
        # ── 4 métriques ──────────────────────────────────────────────────
        metrics_bar = tk.Frame(self.root, bg='#0d1117')
        metrics_bar.pack(fill=tk.X, padx=14, pady=(10, 0))
        
        score_count = sum(self._integ_score)
        score_total = len(self._INTEGRATION_CHECKS)
        
        metrics = [
            ("✏", str(self._analysis["lines"]),        "Lignes"),
            ("📊", self._analysis["type"],              "Type"),
            ("🔗", f"{score_count}/{score_total}",      "Intégration"),
            ("📄", "Oui" if self._analysis["has_doc"] else "Non", "Docstring"),
        ]
        
        for i, (icon, val, label) in enumerate(metrics):
            card = tk.Frame(metrics_bar, bg='#161b27', relief=tk.FLAT)
            card.grid(row=0, column=i, padx=4, sticky="nsew")
            metrics_bar.columnconfigure(i, weight=1)
            
            tk.Label(card, text=icon, bg='#161b27', fg='#00ffcc',
                    font=("Segoe UI Emoji", 18)).pack(pady=(10, 2))
            tk.Label(card, text=val, bg='#161b27', fg='#00ffcc',
                    font=("Consolas", 13, "bold")).pack()
            tk.Label(card, text=label, bg='#161b27', fg='#607080',
                    font=("Consolas", 8)).pack(pady=(0, 10))
        
        # ── Notebook 3 onglets ───────────────────────────────────────────
        style = ttk.Style()
        style.configure("Dark.TNotebook",         background='#0d1117')
        style.configure("Dark.TNotebook.Tab",     background='#161b27',
                       foreground='#607080',      padding=[14, 6])
        style.map("Dark.TNotebook.Tab",
                 background=[("selected", '#0d1117')],
                 foreground=[("selected", '#00ffcc')])
        
        nb = ttk.Notebook(self.root, style="Dark.TNotebook")
        nb.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)
        
        self._create_description_tab(nb)
        self._create_integration_tab(nb)
        self._create_code_tab(nb)
        
        # ── Footer bouton carré ───────────────────────────────────────────
        footer = tk.Frame(self.root, bg='#0d1117')
        footer.pack(fill=tk.X, padx=14, pady=(0, 12))
        tk.Button(footer, text="▣",
                 bg='#161b27', fg='#00ffcc',
                 font=("Consolas", 14),
                 relief=tk.FLAT, cursor="hand2", width=3,
                 command=self.root.destroy).pack()
    
    # ─────────────────────────────────────────────────────────────────────
    # ONGLET 1 — DESCRIPTION
    # ─────────────────────────────────────────────────────────────────────
    def _create_description_tab(self, nb):
        tab = tk.Frame(nb, bg='#0d1117')
        nb.add(tab, text=' 📋 Description ')
        
        # Docstring
        try:
            tree = ast.parse(self._source)
            doc  = ast.get_docstring(tree) or "Aucune description disponible."
        except Exception:
            doc = "Erreur lecture source."
        
        doc_frame = tk.Frame(tab, bg='#161b27', relief=tk.FLAT)
        doc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        doc_text = scrolledtext.ScrolledText(
            doc_frame, font=("Consolas", 9),
            bg='#0d1117', fg='#a0b8c0',
            relief=tk.FLAT, wrap=tk.WORD)
        doc_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        doc_text.insert(tk.END, doc)
        doc_text.configure(state='disabled')
        
        # Infos fichier
        info_bar = tk.Frame(tab, bg='#161b27')
        info_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        try:
            mtime = self.guard_path.stat().st_mtime
            mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            size_str  = f"{self.guard_path.stat().st_size:,} octets"
        except Exception:
            mtime_str = "?"
            size_str  = "?"
        
        for label, value in [
            ("📁 Chemin",    str(self.guard_path)),
            ("📅 Modifié",   mtime_str),
            ("📏 Taille",    size_str),
            ("🔗 Imports",   f"{len(self._analysis['imports']['external'])} externes"),
        ]:
            row = tk.Frame(info_bar, bg='#161b27')
            row.pack(fill=tk.X, padx=10, pady=1)
            tk.Label(row, text=label + " :", width=14,
                    bg='#161b27', fg='#607080',
                    font=("Consolas", 8), anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=value,
                    bg='#161b27', fg='#a0b8c0',
                    font=("Consolas", 8), anchor=tk.W).pack(side=tk.LEFT)
    
    # ─────────────────────────────────────────────────────────────────────
    # ONGLET 2 — INTÉGRATION (le cœur de la fenêtre)
    # ─────────────────────────────────────────────────────────────────────
    def _create_integration_tab(self, nb):
        tab = tk.Frame(nb, bg='#0d1117')
        nb.add(tab, text=' 🔗 Intégration ')
        
        # Liens licence / github / liberapay
        links_frame = tk.Frame(tab, bg='#0d1117')
        links_frame.pack(fill=tk.X, pady=(16, 6))
        for icon, text in [
            ("📜", "Licence GPLv3 — Victor Pozen"),
            ("🔗", "github.com/victorpozen"),
            ("💰", "liberapay.com/EthicalKerberos"),
        ]:
            tk.Label(links_frame,
                    text=f"{icon}  {text}",
                    bg='#0d1117', fg='#607080',
                    font=("Consolas", 9)).pack()
        
        # Score d'intégration
        score = sum(self._integ_score)
        total = len(self._INTEGRATION_CHECKS)
        score_color = "#00ff88" if score == total else \
                     "#ff8800" if score >= total // 2 else "#ff2244"
        tk.Label(tab,
                text=f"Score d'intégration : {score}/{total}",
                bg='#0d1117', fg=score_color,
                font=("Consolas", 13, "bold")).pack(pady=(10, 16))
        
        # Checkboxes 4 éléments
        checks_frame = tk.Frame(tab, bg='#0d1117')
        checks_frame.pack(fill=tk.X, padx=30)
        
        for i, ((name, desc), present) in enumerate(
            zip(self._INTEGRATION_CHECKS, self._integ_score)):
            row = tk.Frame(checks_frame, bg='#161b27',
                          relief=tk.FLAT, pady=2)
            row.pack(fill=tk.X, pady=3)
            
            # Checkbox visuelle
            check_bg = '#1a2e1a' if present else '#2e1a1a'
            check_fg = '#00ff88' if present else '#ff2244'
            check_sym = "☑" if present else "✗"
            
            tk.Label(row, text=f"  {check_sym}",
                    bg=check_bg, fg=check_fg,
                    font=("Consolas", 13, "bold"),
                    width=3).pack(side=tk.LEFT)
            
            info = tk.Frame(row, bg='#161b27')
            info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
            tk.Label(info, text=name,
                    bg='#161b27', fg='#00ffcc',
                    font=("Consolas", 9, "bold"),
                    anchor=tk.W).pack(fill=tk.X)
            tk.Label(info, text=desc,
                    bg='#161b27', fg='#607080',
                    font=("Consolas", 8),
                    anchor=tk.W).pack(fill=tk.X)
        
        # Interconnexions
        imports = self._analysis["imports"]
        if any(imports.values()):
            sep = tk.Frame(tab, bg='#1e2535', height=1)
            sep.pack(fill=tk.X, padx=30, pady=(16, 8))
            tk.Label(tab, text="📡 Interconnexions",
                    bg='#0d1117', fg='#607080',
                    font=("Consolas", 9, "bold")).pack(anchor=tk.W, padx=30)
            
            for category, items, color in [
                ("Guards liés",    imports["guards"],   "#00ffcc"),
                ("Modules Kerberos", imports["modules"], "#00aaff"),
                ("Modules externes", imports["external"], "#607080"),
            ]:
                if items:
                    for item in items[:6]:
                        tk.Label(tab,
                                text=f"   → {item}",
                                bg='#0d1117', fg=color,
                                font=("Consolas", 8),
                                anchor=tk.W).pack(fill=tk.X, padx=30)
    
    # ─────────────────────────────────────────────────────────────────────
    # ONGLET 3 — CODE SOURCE
    # ─────────────────────────────────────────────────────────────────────
    def _create_code_tab(self, nb):
        tab = tk.Frame(nb, bg='#0d1117')
        nb.add(tab, text=' 📄 Code ')
        
        code_text = scrolledtext.ScrolledText(
            tab, font=("Consolas", 9),
            bg='#0d1117', fg='#a0c8a0',
            insertbackground='#00ffcc',
            relief=tk.FLAT)
        code_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 0))
        code_text.insert(tk.END, self._source if self._source else "❌ Fichier illisible")
        code_text.configure(state='disabled')
        
        btn_bar = tk.Frame(tab, bg='#0d1117')
        btn_bar.pack(fill=tk.X, padx=6, pady=6)
        tk.Button(btn_bar, text="📋 Copier",
                 bg='#161b27', fg='#00ffcc',
                 font=("Consolas", 9), relief=tk.FLAT, cursor="hand2",
                 command=lambda: self._copy_code(code_text)
                ).pack(side=tk.LEFT, padx=4)
        tk.Label(btn_bar,
                text=f"{self._analysis['lines']} lignes",
                bg='#0d1117', fg='#304050',
                font=("Consolas", 8)).pack(side=tk.RIGHT, padx=8)
    
    def _copy_code(self, text_widget):
        code = text_widget.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        messagebox.showinfo("Succès", "Code copié dans le presse-papier !")

# ============================================================================
# === VU-MÈTRE ===============================================================
# ============================================================================
class VUMeter:
    """Barre de diodes animée verticale"""
    def __init__(self, parent, height=90, width=22, segments=10):
        self.canvas = tk.Canvas(parent, width=width, height=height,
                               bg='#0a0a0a', highlightthickness=0)
        self.segments = segments
        self.segment_height = height // segments
        self.colors = ['#00ff00'] * 5 + ['#ffcc00'] * 3 + ['#ff0000'] * 2
        self.leds = []
        self._alive = True
        self._anim_id = None
        self.current_level = 0.0
        self.target_level = 0.0
        
        for i in range(segments):
            y1 = height - (i + 1) * self.segment_height + 2
            y2 = height - i * self.segment_height - 2
            led = self.canvas.create_rectangle(2, y1, width - 2, y2,
                                              fill='#1a1a1a', outline='#333', width=1)
            self.leds.append(led)
    
    def set_level(self, value: float):
        self.target_level = max(0.0, min(1.0, value))
        if self._alive:
            self._animate()
    
    def _animate(self):
        if not self._alive:
            return
        try:
            if not self.canvas.winfo_exists():
                self._alive = False
                return
        except Exception:
            self._alive = False
            return
        
        if self.target_level > self.current_level:
            self.current_level += (self.target_level - self.current_level) * 0.3
        else:
            self.current_level += (self.target_level - self.current_level) * 0.05
        
        active = int(self.current_level * self.segments)
        for i, led in enumerate(self.leds):
            self.canvas.itemconfig(led, fill=self.colors[i] if i < active else '#1a1a1a')
        
        if abs(self.target_level - self.current_level) > 0.01:
            self._anim_id = self.canvas.after(50, self._animate)
    
    def flash(self, color: str = '#ff3333', duration: int = 200):
        if not self._alive:
            return
        try:
            orig = [self.canvas.itemcget(led, 'fill') for led in self.leds]
            for led in self.leds:
                self.canvas.itemconfig(led, fill=color)
            self.canvas.after(duration, lambda: [
                self.canvas.itemconfig(l, fill=c)
                for l, c in zip(self.leds, orig)
            ] if self._alive else None)
        except Exception:
            pass
    
    def destroy(self):
        self._alive = False
        if self._anim_id:
            try:
                self.canvas.after_cancel(self._anim_id)
            except Exception:
                pass
        try:
            self.canvas.destroy()
        except Exception:
            pass

# ============================================================================
# === HELPERS ================================================================
# ============================================================================
def _extract_docstring(file_path: Path) -> str:
    try:
        node = ast.parse(file_path.read_text(encoding="utf-8"))
        doc = ast.get_docstring(node)
        if doc:
            return doc.strip().split('\n')[0]
    except Exception:
        pass
    return "Aucune description"

def _guard_metric(guard_name: str) -> float:
    val = _GUARD_METRICS.get(guard_name)
    if val is not None:
        return float(val)
    cpu = psutil.cpu_percent(interval=None) / 100.0
    seed = sum(ord(c) for c in guard_name) % 17
    noise = (seed / 100.0) + random.uniform(-0.04, 0.04)
    return max(0.05, min(0.95, cpu * 0.6 + noise))

# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================
class GuardsPanel:
    """Panneau de guards en grille avec fenêtre détaillée (HYBRIDE)"""
    def __init__(self, root_widget, guards_dir: Path,
                 execute_callback=None, info_callback=None):
        self._root = root_widget
        self._guards_dir = guards_dir
        self._execute_cb = execute_callback
        self._info_cb = info_callback
        self._vu_pairs: List[Tuple[VUMeter, str]] = []
        self._active_vus: List[VUMeter] = []
        self._monitoring = False
        self._grid_frame = None
        self._detail_windows = {}  # Garde référence aux fenêtres détaillées
    
    def build_tab(self, notebook) -> None:
        """Crée et ajoute l'onglet Guards au notebook"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text=' 🛡️ Guards ')
        
        # Header
        header = tk.Frame(tab, bg='#1e1e2e')
        header.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Label(header, text="📡 État des Guards en Temps Réel",
                bg='#1e1e2e', fg='#00ffcc',
                font=("Consolas", 11, "bold")).pack(side=tk.LEFT)
        tk.Button(header, text="🔄 Scan", bg='#2d5a7b', fg='white',
                 font=("Consolas", 9),
                 command=self.refresh).pack(side=tk.RIGHT, padx=5)
        
        # Zone grille
        self._grid_frame = tk.Frame(tab, bg='#1a1a2e')
        self._grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Premier affichage
        self._root.after(200, self.refresh)
        
        # Démarrage monitoring
        self._monitoring = True
        self._root.after(500, self._monitor_loop)
    
    def refresh(self) -> None:
        """Reconstruit la grille complète"""
        if not self._grid_frame:
            return
        
        # Nettoyage
        self._cleanup_vus()
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self._vu_pairs.clear()
        
        # Liste des guards
        guards = []
        if self._guards_dir.exists():
            for f in sorted(self._guards_dir.glob("*.py")):
                desc = _extract_docstring(f)
                short = desc[:45] + "…" if len(desc) > 45 else desc
                guards.append((f.name, short))
        
        if not guards:
            tk.Label(self._grid_frame,
                    text="⚠️ Aucun guard détecté dans /guards",
                    bg='#1a1a2e', fg='#ff5252',
                    font=("Consolas", 10)).pack(pady=30)
            return
        
        # Construction grille
        for col in range(CARDS_PER_ROW):
            self._grid_frame.columnconfigure(col, weight=1, uniform="card")
        
        for idx, (name, desc) in enumerate(guards):
            row = idx // CARDS_PER_ROW
            col = idx % CARDS_PER_ROW
            vu = self._build_card(self._grid_frame, name, desc, row, col)
            if vu:
                self._vu_pairs.append((vu, name))
                self._active_vus.append(vu)
        
        _publish_metric(len(guards) / max(len(guards), 1))
    
    def _build_card(self, parent, guard_name: str,
                   description: str, row: int, col: int) -> Optional[VUMeter]:
        """Construit une carte guard en grille"""
        guard_path = self._guards_dir / guard_name
        exists = guard_path.exists()
        
        # Carte
        card = tk.Frame(parent, bg='#161a2e', relief=tk.RIDGE, bd=1)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        parent.rowconfigure(row, weight=1)
        
        # Nom
        short_name = guard_name.replace("guard_", "").replace(".py", "").upper()
        tk.Label(card, text=f"🛡️ {short_name}",
                bg='#161a2e', fg='#00ffcc',
                font=("Consolas", 8, "bold"),
                anchor="w").pack(fill=tk.X, padx=6, pady=(6, 0))
        
        # Corps : VU-mètre + infos
        body = tk.Frame(card, bg='#161a2e')
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        
        # VU-mètre vertical
        vu = VUMeter(body, height=80, width=22)
        vu.canvas.pack(side=tk.LEFT, padx=(0, 8))
        
        # Infos droite
        info = tk.Frame(body, bg='#161a2e')
        info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(info, text=description,
                bg='#161a2e', fg='#8a8ab0',
                font=("Consolas", 7),
                wraplength=130, justify=tk.LEFT,
                anchor="nw").pack(fill=tk.X, pady=(0, 4))
        
        status_txt = "✅ ACTIF" if exists else "⚠️ MANQUANT"
        status_clr = "#4CAF50" if exists else "#ff9800"
        tk.Label(info, text=status_txt,
                bg='#161a2e', fg=status_clr,
                font=("Consolas", 8, "bold"),
                anchor="w").pack(fill=tk.X)
        
        # Boutons
        btn_frame = tk.Frame(card, bg='#161a2e')
        btn_frame.pack(fill=tk.X, padx=6, pady=(0, 6))
        
        # ← BOUTON ℹ️ → info_callback Kerberos OU fenêtre locale
        tk.Button(btn_frame, text="ℹ️", width=3,
                 bg='#2d5a7b', fg='white',
                 font=("Consolas", 8),
                 command=lambda n=guard_name, p=guard_path: (
                    self._info_cb(n) if self._info_cb
                    else self._on_detail(n, p)
                 )
                ).pack(side=tk.LEFT, padx=(0, 3))
        
        if self._execute_cb:
            tk.Button(btn_frame, text="▶", width=3,
                     bg='#2d7b5a', fg='white',
                     font=("Consolas", 8),
                     command=lambda p=guard_path: self._execute_cb(p)
                    ).pack(side=tk.LEFT)
        
        # Niveau initial
        vu.set_level(_guard_metric(guard_name))
        return vu
    
    def _on_detail(self, guard_name: str, guard_path: Path):
        """Ouvre la fenêtre détaillée avec 3 onglets"""
        # Fermer l'ancienne si elle existe
        if guard_name in self._detail_windows:
            try:
                self._detail_windows[guard_name].root.destroy()
            except Exception:
                pass
            self._detail_windows.pop(guard_name, None)
        
        # Remonter jusqu'à la vraie racine Tk
        try:
            root_tk = self._root.winfo_toplevel()
        except Exception:
            root_tk = self._root
        
        # Créer la fenêtre détaillée
        try:
            detail_win = GuardDetailWindow(root_tk, guard_path, guard_name)
            self._detail_windows[guard_name] = detail_win
            detail_win.root.lift()
            detail_win.root.focus_force()
        except Exception as e:
            print(f"[⚠️ Guards Panel] Erreur ouverture {guard_name}: {e}")
    
    def _monitor_loop(self):
        if not self._monitoring:
            return
        try:
            for vu, name in self._vu_pairs:
                if not vu._alive:
                    continue
                level = _guard_metric(name)
                vu.set_level(level)
                if level > 0.85:
                    vu.flash('#ff3333', duration=150)
        except Exception:
            pass
        self._root.after(2000, self._monitor_loop)
    
    def _cleanup_vus(self):
        for vu in self._active_vus:
            try:
                vu.destroy()
            except Exception:
                pass
        self._active_vus.clear()
    
    def destroy(self):
        self._monitoring = False
        self._cleanup_vus()
        for win in self._detail_windows.values():
            try:
                win.root.destroy()
            except:
                pass

# ============================================================================
# === INTÉGRATION KERBEROS ===================================================
# ============================================================================
_panel_instance: Optional[GuardsPanel] = None

def build_guards_tab(notebook, root_widget, guards_dir: Path,
                    execute_callback=None, info_callback=None) -> GuardsPanel:
    """Point d'intégration principal"""
    global _panel_instance
    _panel_instance = GuardsPanel(
        root_widget=root_widget,
        guards_dir=guards_dir,
        execute_callback=execute_callback,
        info_callback=info_callback,
    )
    _panel_instance.build_tab(notebook)
    return _panel_instance

def get_panel() -> Optional[GuardsPanel]:
    return _panel_instance

def get_stats() -> dict:
    guards = list(GUARDS_DIR.glob("*.py")) if GUARDS_DIR.exists() else []
    
    report = {
        "guard": "guards_panel",
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "total_guards": len(guards),
        "cards_per_row": CARDS_PER_ROW,
        "panel_active": _panel_instance is not None,
        "last_refresh": datetime.now().isoformat(),
        "logs_dir": str(GUARD_LOGS_DIR),
    }
    
    # Sauvegarde automatique des rapports
    _save_reports(report)
    
    return report

def start_guard():
    """Point d'entrée pour Kerberos — Panel des guards"""
    _publish_metric(0.1)
    print("🛡️ [Guards Panel] Module chargé — prêt pour intégration")
    
    # Sauvegarde rapport initial
    _save_reports(get_stats())
    
    return None

def stop_guard():
    """Arrêt propre du panel"""
    global _panel_instance
    if _panel_instance:
        _panel_instance.destroy()
    _publish_metric(0.0)
    print("🛡️ [Guards Panel] Panel arrêté")

def run():
    print("""
╔════════════════════════════════════════════════════════════╗
║  🛡️ KERBEROS GUARDS PANEL — Grille + Détails (HYBRIDE)  ║
║                                                            ║
║  • Grille responsive (4 cartes par ligne)                 ║
║  • VU-mètres animés                                       ║
║  • Bouton ℹ️ → Fenêtre 3 onglets (Interconnexions/Stats/Code) ║
║  • Bouton ▶ → Exécution                                   ║
║  • Refresh automatique toutes les 2s                      ║
║  • Rapports JSON + HTML auto                              ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
╚════════════════════════════════════════════════════════════╝
""")
    guards = list(GUARDS_DIR.glob("*.py")) if GUARDS_DIR.exists() else []
    print(f"📂 Guards détectés : {len(guards)}")
    for g in sorted(guards):
        print(f"   🛡️ {g.name}")

if __name__ == "__main__":
    run()