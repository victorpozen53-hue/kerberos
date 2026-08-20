#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Guard Guards Panel — Panneau de contrôle des guards en grille
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Affichage en grille horizontale (4 cartes par ligne, sans scroll)
- VU-mètres animés par carte
- Bouton ℹ️ → Guard Explainer
- Bouton ▶️ → Exécution du guard
- Refresh automatique toutes les 2s
- Intégration Kerberos complète (4/4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
import ast
import threading
import importlib.util
import sys
import random
import psutil
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

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
    _GUARD_METRICS[_MODULE_NAME] = max(0.0, min(1.0, level))

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================

GUARDS_DIR   = Path(__file__).parent
CARDS_PER_ROW = 4   # Nombre de cartes par ligne

# ============================================================================
# === VU-MÈTRE ===============================================================
# ============================================================================

class VUMeter:
    """Barre de diodes animée verticale"""

    def __init__(self, parent, height=90, width=22, segments=10):
        import tkinter as tk
        self.canvas         = tk.Canvas(parent, width=width, height=height,
                                        bg='#0a0a0a', highlightthickness=0)
        self.segments       = segments
        self.segment_height = height // segments
        self.colors         = ['#00ff00'] * 5 + ['#ffcc00'] * 3 + ['#ff0000'] * 2
        self.leds           = []
        self._alive         = True
        self._anim_id       = None
        self.current_level  = 0.0
        self.target_level   = 0.0

        for i in range(segments):
            y1  = height - (i + 1) * self.segment_height + 2
            y2  = height - i * self.segment_height - 2
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
        doc  = ast.get_docstring(node)
        if doc:
            return doc.strip().split('\n')[0]
    except Exception:
        pass
    return "Aucune description"

def _guard_metric(guard_name: str) -> float:
    """Retourne la métrique réelle ou une simulation CPU"""
    val = _GUARD_METRICS.get(guard_name)
    if val is not None:
        return float(val)
    # Simulation basée sur CPU + seed déterministe par guard
    cpu   = psutil.cpu_percent(interval=None) / 100.0
    seed  = sum(ord(c) for c in guard_name) % 17
    noise = (seed / 100.0) + random.uniform(-0.04, 0.04)
    return max(0.05, min(0.95, cpu * 0.6 + noise))


# ============================================================================
# === CLASSE PRINCIPALE ======================================================
# ============================================================================

class GuardsPanel:
    """
    Panneau de guards en grille horizontale.
    S'intègre dans un onglet ttk.Notebook existant.
    """

    def __init__(self, root_widget, guards_dir: Path,
                 execute_callback=None, info_callback=None):
        self._root          = root_widget
        self._guards_dir    = guards_dir
        self._execute_cb    = execute_callback   # fn(Path)
        self._info_cb       = info_callback      # fn(str guard_name)
        self._vu_pairs:     List[Tuple[VUMeter, str]] = []
        self._active_vus:   List[VUMeter] = []
        self._monitoring    = False
        self._grid_frame    = None               # Frame grille (réf pour refresh)

    # ── Construction de l'onglet ─────────────────────────────────────────
    def build_tab(self, notebook) -> None:
        """Crée et ajoute l'onglet Guards au notebook"""
        import tkinter as tk
        from tkinter import ttk

        tab = ttk.Frame(notebook)
        notebook.add(tab, text=' 🛡️ Guards ')

        # ── Header ────────────────────────────────────────────────────────
        header = tk.Frame(tab, bg='#1e1e2e')
        header.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Label(header, text="📡 État des Guards en Temps Réel",
                 bg='#1e1e2e', fg='#00ffcc',
                 font=("Consolas", 11, "bold")).pack(side=tk.LEFT)
        tk.Button(header, text="🔄 Scan", bg='#2d5a7b', fg='white',
                  font=("Consolas", 9),
                  command=self.refresh).pack(side=tk.RIGHT, padx=5)

        # ── Zone grille (pas de scrollbar — grille responsive) ────────────
        self._grid_frame = tk.Frame(tab, bg='#1a1a2e')
        self._grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Premier affichage
        self._root.after(200, self.refresh)

        # Démarrage monitoring
        self._monitoring = True
        self._root.after(500, self._monitor_loop)

    # ── Grille de cartes ─────────────────────────────────────────────────
    def refresh(self) -> None:
        """Reconstruit la grille complète"""
        import tkinter as tk

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
                desc  = _extract_docstring(f)
                short = desc[:45] + "…" if len(desc) > 45 else desc
                guards.append((f.name, short))

        if not guards:
            tk.Label(self._grid_frame,
                     text="⚠️ Aucun guard détecté dans /guards",
                     bg='#1a1a2e', fg='#ff5252',
                     font=("Consolas", 10)).pack(pady=30)
            return

        # Construction grille — CARDS_PER_ROW cartes par ligne
        for col in range(CARDS_PER_ROW):
            self._grid_frame.columnconfigure(col, weight=1, uniform="card")

        for idx, (name, desc) in enumerate(guards):
            row = idx // CARDS_PER_ROW
            col = idx % CARDS_PER_ROW
            vu  = self._build_card(self._grid_frame, name, desc, row, col)
            if vu:
                self._vu_pairs.append((vu, name))
                self._active_vus.append(vu)

        _publish_metric(len(guards) / max(len(guards), 1))

    def _build_card(self, parent, guard_name: str,
                    description: str, row: int, col: int) -> Optional[VUMeter]:
        """Construit une carte guard en grille"""
        import tkinter as tk

        guard_path = self._guards_dir / guard_name
        exists     = guard_path.exists()

        # ── Carte ─────────────────────────────────────────────────────────
        card = tk.Frame(parent, bg='#161a2e', relief=tk.RIDGE, bd=1)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        parent.rowconfigure(row, weight=1)

        # ── Nom ───────────────────────────────────────────────────────────
        short_name = guard_name.replace("guard_", "").replace(".py", "").upper()
        tk.Label(card, text=f"🛡️ {short_name}",
                 bg='#161a2e', fg='#00ffcc',
                 font=("Consolas", 8, "bold"),
                 anchor="w").pack(fill=tk.X, padx=6, pady=(6, 0))

        # ── Corps : VU-mètre + infos ──────────────────────────────────────
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

        # ── Boutons ────────────────────────────────────────────────────────
        btn_frame = tk.Frame(card, bg='#161a2e')
        btn_frame.pack(fill=tk.X, padx=6, pady=(0, 6))

        tk.Button(btn_frame, text="ℹ️", width=3,
                  bg='#2d5a7b', fg='white',
                  font=("Consolas", 8),
                  command=lambda n=guard_name: self._on_info(n)
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

    # ── Info guard ────────────────────────────────────────────────────────
    def _on_info(self, guard_name: str):
        if self._info_cb:
            self._info_cb(guard_name)

    # ── Boucle monitoring ─────────────────────────────────────────────────
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

    # ── Nettoyage ─────────────────────────────────────────────────────────
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


# ============================================================================
# === INTÉGRATION KERBEROS ===================================================
# ============================================================================

_panel_instance: Optional[GuardsPanel] = None

def build_guards_tab(notebook, root_widget, guards_dir: Path,
                     execute_callback=None, info_callback=None) -> GuardsPanel:
    """
    Point d'intégration principal — appelé depuis kerberos.py.

    Usage dans KerberosApp.show_gestion() :
        from guards.guard_guards_panel import build_guards_tab
        build_guards_tab(nb, self.root, GUARDS_DIR,
                         execute_callback=self.execute_module,
                         info_callback=self._show_guard_info)
    """
    global _panel_instance
    _panel_instance = GuardsPanel(
        root_widget   = root_widget,
        guards_dir    = guards_dir,
        execute_callback = execute_callback,
        info_callback    = info_callback,
    )
    _panel_instance.build_tab(notebook)
    return _panel_instance

def get_panel() -> Optional[GuardsPanel]:
    return _panel_instance

def get_stats() -> dict:
    guards = list(GUARDS_DIR.glob("*.py")) if GUARDS_DIR.exists() else []
    return {
        "guard_name":    _MODULE_NAME,
        "total_guards":  len(guards),
        "cards_per_row": CARDS_PER_ROW,
        "panel_active":  _panel_instance is not None,
        "last_refresh":  datetime.now().isoformat(),
    }

def start_guard():
    print("🛡️ [Guards Panel] Module chargé — prêt pour intégration")
    _publish_metric(0.1)
    return None

def run():
    print("""
╔════════════════════════════════════════════════════════════════╗
║  🛡️ KERBEROS GUARDS PANEL — Grille horizontale               ║
║                                                                ║
║  • Grille responsive (4 cartes par ligne)                     ║
║  • VU-mètres animés                                           ║
║  • Boutons ℹ️ Guard Explainer + ▶ Exécution                  ║
║  • Refresh automatique toutes les 2s                          ║
║  • Intégration Kerberos 4/4                                   ║
║                                                                ║
║  Licence : GPLv3 — Victor Pozen                               ║
╚════════════════════════════════════════════════════════════════╝
    """)
    guards = list(GUARDS_DIR.glob("*.py")) if GUARDS_DIR.exists() else []
    print(f"📂 Guards détectés : {len(guards)}")
    for g in sorted(guards):
        print(f"   🛡️ {g.name}")

if __name__ == "__main__":
    run()
