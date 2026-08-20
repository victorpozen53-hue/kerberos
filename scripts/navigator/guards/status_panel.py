# -*- coding: utf-8 -*-
# ==============================================================
# guard_status_panel.py — v1.1 — (-;
# Panneau retractable d’état des guards Kerberos
# White hat only. GPLv3.
# ==============================================================

import os
import tkinter as tk

GUARD_DIR = r"H:\navigator\guards"

GUARD_FILES = [
    "guard_bubble.py",
    "guard_no_shodan.py",
    "guard_no_tracker.py",
    "guard_no_pub.py",
    "guard_no_spamm.py",
    "guard_pe_arch.py"
]

class GuardStatusPanel:
    def __init__(self, parent):
        self.is_expanded = True
        self.frame = tk.Frame(parent, bg="#0d1117")
        self.frame.pack(fill="x", padx=10, pady=(0,5))

        # Titre cliquable (retractable)
        self.title_frame = tk.Frame(self.frame, bg="#161b22")
        self.title_frame.pack(fill="x")
        self.title_label = tk.Label(
            self.title_frame, text=" 🛡️ Guards — État — (-; ▼",
            bg="#161b22", fg="#58a6ff", font=("Consolas", 10, "bold"), cursor="hand2"
        )
        self.title_label.pack(fill="x", padx=8, pady=4)
        self.title_label.bind("<Button-1>", self.toggle)

        # Contenu (retractable)
        self.content_frame = tk.Frame(self.frame, bg="#161b22")
        self.content_frame.pack(fill="x", padx=1, pady=(0,1))

        self.guards_frame = tk.Frame(self.content_frame, bg="#161b22")
        self.guards_frame.pack(fill="x", padx=5, pady=5)

        self.labels = {}
        for guard in GUARD_FILES:
            name = guard.replace(".py", "")
            row = tk.Frame(self.guards_frame, bg="#161b22")
            row.pack(fill="x", pady=1)
            
            status = tk.Label(row, text="⏳", bg="#161b22", fg="#d29922", font=("Consolas", 10))
            status.pack(side="left", padx=(0,6))
            
            tk.Label(row, text=name, bg="#161b22", fg="#c9d1d9", font=("Consolas", 10)).pack(side="left")
            
            self.labels[guard] = status

        self.update_status()
        self.content_frame.after(5000, self.update_status)

    def toggle(self, _=None):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.content_frame.pack(fill="x", padx=1, pady=(0,1))
            self.title_label.config(text=" 🛡️ Guards — État — (-; ▼")
        else:
            self.content_frame.pack_forget()
            self.title_label.config(text=" 🛡️ Guards — (-; ▶")

    def update_status(self):
        for guard, label in self.labels.items():
            path = os.path.join(GUARD_DIR, guard)
            if not os.path.isfile(path):
                label.config(text="❌", fg="#f85149")
            else:
                label.config(text="✅", fg="#2ea043")
        if self.is_expanded:
            self.content_frame.after(5000, self.update_status)