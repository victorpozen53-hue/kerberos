#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard UI Manager — Gestionnaire interface"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Any, Dict
import logging
logger = logging.getLogger(__name__)

class UIManager:
    def __init__(self, root: tk.Tk, guard_manager: Any) -> None:
        self.root = root; self.guard_manager = guard_manager; self.chat_widget = None; self.stats_vars: Dict[str, tk.StringVar] = {}
        self._setup_ui(); logger.info("UIManager initialisé")
    
    def _setup_ui(self) -> None:
        style = ttk.Style(); style.theme_use('clam'); style.configure('TFrame', background='#1e1e1e'); style.configure('TLabel', background='#1e1e1e', foreground='#00ffcc', font=('Consolas', 10))
        main_frame = tk.Frame(self.root, bg='#1e1e1e'); main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        header = tk.Label(main_frame, text="️ KERBEROS VIDEO ANALYZER", bg='#1e1e1e', fg='#00ffcc', font=("Consolas", 18, "bold")); header.pack(pady=10)
        self._create_stats_panel(main_frame)
        self.chat_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=('Consolas', 11), bg='#2d2d2d', fg='#ffffff'); self.chat_widget.pack(fill=tk.BOTH, expand=True, padx=8, pady=8); self.chat_widget.insert(tk.END, "✅ Kerberos Video Analyzer v7.2 prêt\n"); self.chat_widget.configure(state='disabled')
        self._create_control_buttons(main_frame)
        self.status_label = ttk.Label(self.root, text='✅ Prêt', relief=tk.SUNKEN, anchor=tk.W); self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_stats_panel(self, parent: tk.Widget) -> None:
        stats_frame = tk.Frame(parent, bg='#161a2e'); stats_frame.pack(fill=tk.X, pady=10)
        for key, label, color in [("total", "Total", "#00ffcc"), ("real", "Réelles", "#4CAF50"), ("suspicious", "Suspectes", "#ff5252"), ("uncertain", "Incertaines", "#ff9800")]:
            box = tk.Frame(stats_frame, bg='#1e1e2e', relief=tk.RIDGE, bd=1); box.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=5)
            tk.Label(box, text=label, bg='#1e1e2e', fg='#a0a0c0', font=("Consolas", 9)).pack(pady=5)
            var = tk.StringVar(value="0"); tk.Label(box, textvariable=var, bg='#1e1e2e', fg=color, font=("Consolas", 16, "bold")).pack(); self.stats_vars[key] = var
    
    def _create_control_buttons(self, parent: tk.Widget) -> None:
        btn_frame = tk.Frame(parent, bg='#1e1e1e'); btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="▶️ Démarrer", bg='#2d7b5a', fg='white', font=("Consolas", 11), command=self._start_analysis).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="️ Arrêter", bg='#7b2d2d', fg='white', font=("Consolas", 11), command=self._stop_analysis).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📊 Rapport", bg='#2d5a7b', fg='white', font=("Consolas", 11), command=self._generate_report).pack(side=tk.RIGHT, padx=5)
    
    def _start_analysis(self) -> None:
        if self.guard_manager.start_guard("video_analyzer"): self.append_to_chat("✅ Analyse démarrée\n"); self.status_label.config(text="🔍 Analyse en cours...")
        else: messagebox.showerror("Erreur", "Impossible de démarrer l'analyse")
    
    def _stop_analysis(self) -> None:
        if self.guard_manager.stop_guard("video_analyzer"): self.append_to_chat("⏹️ Analyse arrêtée\n"); self.status_label.config(text="⏸️ Arrêté")
    
    def _generate_report(self) -> None:
        try:
            from guards import guard_report_generator; guard_report_generator.generate_report(self.guard_manager.get_all_stats())
        except ImportError: messagebox.showwarning("Attention", "Report Generator non disponible")
        except Exception as e: logger.error(f"Erreur génération rapport: {e}"); messagebox.showerror("Erreur", f"Impossible de générer le rapport:\n{e}")
    
    def append_to_chat(self, text: str) -> None:
        if self.chat_widget:
            try:
                self.chat_widget.configure(state='normal'); self.chat_widget.insert(tk.END, text)
                lines = int(self.chat_widget.index('end-1c').split('.')[0])
                if lines > 100: self.chat_widget.delete('1.0', f'{lines-100}.0')
                self.chat_widget.configure(state='disabled'); self.chat_widget.see(tk.END)
            except Exception as e: logger.error(f"Erreur écriture chat: {e}")
    
    def update_stats(self, stats: Dict[str, int]) -> None:
        for key, value in stats.items():
            if key in self.stats_vars: self.stats_vars[key].set(str(value))
    
    def start(self) -> None: self._refresh_stats(); logger.info("UI démarrée")
    
    def _refresh_stats(self) -> None:
        try:
            stats = self.guard_manager.get_all_stats(); video_stats = stats.get('video_analyzer', {}); self.update_stats(video_stats)
        except: pass
        self.root.after(3000, self._refresh_stats)