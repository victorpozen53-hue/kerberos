#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 ARGOS DASHBOARD v1.0 — salle de contrôle (adapté de guard_ui_manager.py)
- VU-mètres par organe : statut + compteurs
- Totaux : Σ cibles/signatures + Σ 🕊️ protégées
- Lecture via la lymphe (lymph_argos/stats/*.json), refresh 2,5 s
Usage : bouton organe dans ARGOS, ou python argos_dashboard.py
"""
import sys
import traceback
from pathlib import Path
import tkinter as tk

_p = Path(__file__).resolve().parent
sys.path.insert(0, str(_p))
try:
    import argos_manager as am
except ImportError:
    print("❌ argos_manager.py introuvable (même dossier)")
    input("Appuyez sur Entrée...")
    sys.exit(1)

TOT_KEYS = ("cibles", "signatures", "formations", "captures", "trouvees")
PROT_KEYS = ("protegees", "protegee", "protected")


class DashboardApp:
    BG = '#101418'; BG2 = '#161a2e'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📊 ARGOS DASHBOARD v1.0 — salle de contrôle")
        self.root.geometry("760x520")
        self.root.configure(bg=self.BG)
        tk.Label(self.root, text="📊 SALLE DE CONTRÔLE ARGOS", bg=self.BG2, fg=self.CY,
                 font=("Consolas", 14, "bold")).pack(fill=tk.X, pady=8)
        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=3)
        tk.Button(bf, text="🔄 Refresh", bg=self.BTN, fg=self.WH,
                  command=self._refresh).pack(side=tk.LEFT, padx=3)
        tk.Button(bf, text="🧹 Reset stats", bg='#7b2d2d', fg=self.WH,
                  command=self._reset).pack(side=tk.LEFT, padx=3)
        self.totals = tk.Label(self.root, text="⏳ …", bg=self.BG, fg=self.OR,
                               font=("Consolas", 12, "bold"))
        self.totals.pack(pady=5)
        self.canvas = tk.Canvas(self.root, bg=self.BG, highlightthickness=0)
        sb = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, bg=self.BG)
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._refresh()
        self.root.mainloop()

    def _reset(self):
        am.reset_stats()
        self._refresh()

    def _refresh(self):
        for w in self.body.winfo_children():
            w.destroy()
        data = am.read_all_stats()
        tot, prot = 0, 0
        if not data:
            tk.Label(self.body, text="aucun organe n'a publié de stats\n(lance un scan : ufo, cropcircle, vision…)",
                     bg=self.BG, fg='#a0a0c0', font=("Consolas", 10)).pack(pady=20)
        for name, d in data.items():
            st = d.get("stats", {})
            run = "● en cours" if d.get("running") else "○ veille"
            box = tk.Frame(self.body, bg=self.BG2, relief=tk.RIDGE, bd=1)
            box.pack(fill=tk.X, pady=3, padx=5)
            tk.Label(box, text=f"👁️ {name}", bg=self.BG2, fg=self.CY,
                     font=("Consolas", 11, "bold"), anchor="w").pack(side=tk.LEFT, padx=8)
            tk.Label(box, text=run, bg=self.BG2,
                     fg='#4CAF50' if d.get("running") else '#a0a0c0',
                     font=("Consolas", 9)).pack(side=tk.LEFT, padx=8)
            lines = "  ".join(f"{k}:{v}" for k, v in st.items())
            tk.Label(box, text=lines or "—", bg=self.BG2, fg=self.WH,
                     font=("Consolas", 10), anchor="w").pack(side=tk.LEFT, padx=8)
            for k, v in st.items():
                if isinstance(v, int):
                    if k in PROT_KEYS:
                        prot += v
                    elif k in TOT_KEYS:
                        tot += v
        self.totals.config(text=f"🎯 Σ cibles/signatures : {tot}   •   🕊️ Σ protégées : {prot}")
        self.root.after(2500, self._refresh)


def run():
    DashboardApp()
    return "✅ DASHBOARD fermé"


def main():
    try:
        DashboardApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()