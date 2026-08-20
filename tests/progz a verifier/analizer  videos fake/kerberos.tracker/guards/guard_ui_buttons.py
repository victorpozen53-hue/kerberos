#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔘 GUARD UI BUTTONS — Extension dynamique de l'interface"""
import tkinter as tk
from tkinter import messagebox, simpledialog
import logging
from typing import Dict, Any
from guards.guard_interface import GuardInterface
logger = logging.getLogger(__name__)

class UIButtonsGuard(GuardInterface):
    def __init__(self, kerberos_app=None):
        super().__init__("ui_buttons")
        self.kerberos, self.is_running, self.injected_buttons = kerberos_app, False, []
        self.buttons_config = [
            {"text": "📊 Fractionner Rapports", "bg": "#6b2d7b", "command": self._on_split, "side": tk.RIGHT},
            {"text": "🧹 Nettoyer Frames", "bg": "#7b5a2d", "command": self._on_clean, "side": tk.RIGHT},
            {"text": "📈 Stats Avancées", "bg": "#2d7b7b", "command": self._on_stats, "side": tk.LEFT},
        ]

    def inject_buttons(self) -> int:
        if not self.kerberos: return 0
        btn_frame = getattr(self.kerberos, 'btn_frame', None)
        if not btn_frame: return 0
        
        count = 0
        for cfg in self.buttons_config:
            try:
                btn = tk.Button(btn_frame, text=cfg["text"], bg=cfg["bg"], fg='white', font=("Consolas", 10), command=cfg["command"])
                btn.pack(side=cfg.get("side", tk.RIGHT), padx=5)
                self.injected_buttons.append(btn)
                count += 1
            except Exception as e: logger.error(f"❌ Erreur injection: {e}")
        btn_frame.update_idletasks()
        return count

    def _on_split(self):
        try:
            splitter = self.kerberos.guard_manager.get_guard("report_splitter")
            videos = self.kerberos._video_analyzer_engine.get_analyzed_videos() if self.kerberos._video_analyzer_engine else []
            if not videos: return messagebox.showinfo("Info", "Aucune vidéo.")
            size = simpledialog.askinteger("Chunk", f"Vidéos par rapport (50-500) :\n(Total: {len(videos)})", parent=self.kerberos.root, minvalue=50, maxvalue=500, initialvalue=50)
            if size:
                reports = splitter.generate_split_reports(videos, chunk_size=size)
                if reports: messagebox.showinfo("Succès", f"{len(reports)} rapport(s) généré(s) !")
        except Exception as e: messagebox.showerror("Erreur", str(e))

    def _on_clean(self):
        try:
            from pathlib import Path
            frames = list(Path("reports/frames").glob("frame_*.png"))
            if not frames: return
            if messagebox.askyesno("Confirmation", f"Supprimer {len(frames)} frames ?"):
                for f in frames: f.unlink()
                messagebox.showinfo("Succès", f"{len(frames)} frames supprimées !")
        except Exception as e: messagebox.showerror("Erreur", str(e))

    def _on_stats(self):
        try:
            win = tk.Toplevel(self.kerberos.root)
            win.title("📈 Stats"); win.geometry("600x400"); win.configure(bg='#1e1e2e')
            text = tk.scrolledtext.ScrolledText(win, bg='#0a0a0a', fg='#00ff00', font=("Consolas", 10))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            for name, stats in self.kerberos.guard_manager.get_all_stats().items():
                text.insert(tk.END, f"\n{'='*40}\n🛡️ {name}\n{'='*40}\n")
                for k, v in stats.items(): text.insert(tk.END, f"  {k}: {v}\n")
            text.configure(state='disabled')
        except Exception as e: messagebox.showerror("Erreur", str(e))

    def start(self):
        self.is_running = True
        logger.info(f"🔘 UIButtonsGuard démarré ({self.inject_buttons()} boutons)")
    def stop(self):
        self.is_running = False
        for btn in self.injected_buttons:
            try: btn.destroy()
            except: pass
        self.injected_buttons.clear()
    def get_stats(self) -> Dict[str, Any]: return {"buttons_injected": len(self.injected_buttons)}

_guard_instance = None
def start_guard(kerberos_app=None):
    global _guard_instance; _guard_instance = UIButtonsGuard(kerberos_app); return _guard_instance
def stop_guard():
    global _guard_instance
    if _guard_instance: _guard_instance.stop()
def get_stats():
    global _guard_instance; return _guard_instance.get_stats() if _guard_instance else {}