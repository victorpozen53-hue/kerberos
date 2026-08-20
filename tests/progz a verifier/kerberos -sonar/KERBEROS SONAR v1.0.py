#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌊 KERBEROS SONAR v1.0 — "vidage virtuel de la flotte"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3
Simulateur d'échogramme sonar pour les retenues (Chira / Las Niñas / Soria) :
- colonne d'eau + écho du fond + couche de sédiment
- objet enfoui = signature HYPERBOLIQUE orange (la sphère)
- bouton 🌊 VIDER LA FLOTTE : vue synthétique sans eau, cible exposée
- export JPEG pour la vidéo
(Saison 2 : brancher un JSN-SR04T + Arduino pour de vraies mesures.)
"""
import threading
import math
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from PIL import Image, ImageTk

PRESETS = {
    "CHIRA (niveau stable)": {"depth": 45, "sed": 6},
    "LAS NIÑAS (niveau stable)": {"depth": 35, "sed": 5},
    "SORIA (niveau aléatoire)": {"depth": 25, "sed": 3},
}


class SonarApp:
    BG = '#0a0a12'; BG2 = '#141420'; CY = '#00ffcc'; OR = '#ff9800'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌊 KERBEROS SONAR v1.0")
        self.root.geometry("1000x760")
        self.root.configure(bg=self.BG)
        self.W, self.H = 960, 480
        self.view = np.zeros((self.H, self.W, 3), np.uint8)
        self.scanning = False
        self.x0 = int(self.W * 0.62)
        self.photo = None
        self._build()
        self._show()
        self.root.mainloop()

    def _build(self):
        tk.Label(self.root, text="🌊 KERBEROS SONAR — vidage virtuel de la flotte",
                 bg=self.BG2, fg=self.CY, font=("Consolas", 15, "bold")).pack(fill=tk.X, pady=8)

        cf = tk.Frame(self.root, bg=self.BG)
        cf.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(cf, text="️ Retenue:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.preset_var = tk.StringVar(value=list(PRESETS)[0])
        ttk.Combobox(cf, textvariable=self.preset_var, values=list(PRESETS),
                     width=24, state='readonly',
                     ).pack(side=tk.LEFT, padx=5)
        tk.Button(cf, text="Appliquer", bg='#2d5a7b', fg='white',
                  command=self._apply_preset).pack(side=tk.LEFT, padx=5)

        sf = tk.Frame(self.root, bg=self.BG)
        sf.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(sf, text="Profondeur:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.depth_var = tk.IntVar(value=45)
        tk.Scale(sf, from_=10, to=80, orient=tk.HORIZONTAL, variable=self.depth_var,
                 bg=self.BG2, fg=self.CY, highlightthickness=0, length=180).pack(side=tk.LEFT, padx=5)
        tk.Label(sf, text="Sédiment:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT, padx=(15, 0))
        self.sed_var = tk.IntVar(value=6)
        tk.Scale(sf, from_=0, to=15, orient=tk.HORIZONTAL, variable=self.sed_var,
                 bg=self.BG2, fg=self.CY, highlightthickness=0, length=140).pack(side=tk.LEFT, padx=5)
        tk.Label(sf, text="Ø objet:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT, padx=(15, 0))
        self.obj_size_var = tk.IntVar(value=3)
        tk.Scale(sf, from_=1, to=6, orient=tk.HORIZONTAL, variable=self.obj_size_var,
                 bg=self.BG2, fg=self.OR, highlightthickness=0, length=110).pack(side=tk.LEFT, padx=5)
        self.obj_var = tk.BooleanVar(value=True)
        tk.Checkbutton(sf, text="🎯 Objet enfoui", variable=self.obj_var,
                       bg=self.BG, fg=self.OR, selectcolor=self.BG2,
                       activebackground=self.BG, activeforeground=self.OR).pack(side=tk.LEFT, padx=10)

        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(bf, text="▶️ SCAN SONAR", bg='#4CAF50', fg='white',
                  font=("Consolas", 11, "bold"), command=self._start).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        tk.Button(bf, text="⏹️ Stop", bg='#ff5252', fg='white',
                  font=("Consolas", 11, "bold"), command=self._stop).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        tk.Button(bf, text="🌊 VIDER LA FLOTTE", bg='#2d5a7b', fg='white',
                  font=("Consolas", 11, "bold"), command=self._drain).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        tk.Button(bf, text="📷 JPEG", bg='#2d5a7b', fg='white',
                  font=("Consolas", 11, "bold"), command=self._save).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

        self.canvas_lbl = tk.Label(self.root, bg=self.BG)
        self.canvas_lbl.pack(padx=10, pady=8)

        self.log = tk.Text(self.root, height=6, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._log("🌊 KERBEROS SONAR prêt. Choisis la retenue, ▶️ SCAN, puis 🌊 VIDER LA FLOTTE.")

    def _apply_preset(self):
        p = PRESETS[self.preset_var.get()]
        self.depth_var.set(p["depth"])
        self.sed_var.set(p["sed"])
        self._log(f"🏞️ Preset {self.preset_var.get()}: profondeur {p['depth']} m, sédiment {p['sed']} m")

    def _log(self, msg):
        self.log.configure(state='normal')
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.configure(state='disabled')

    def _bottom(self, x):
        return (self.depth_var.get() + 4 * math.sin(x / 90.0)
                + 2 * math.sin(x / 23.0) + random.uniform(-0.25, 0.25))

    def _ping_column(self, x):
        H = self.H
        dmax = self.depth_var.get() + self.sed_var.get() + 20
        sc = H / dmax
        zb = self._bottom(x)
        rb = min(H - 4, int(zb * sc))
        c = np.zeros((H, 3), np.int16)
        c[:rb] = (5, 12, 24)                                   # colonne d'eau
        n = np.random.randint(0, 14, rb)                       # speckle
        c[:rb, 0] += n // 2; c[:rb, 1] += n // 2; c[:rb, 2] += n
        c[rb:rb + 3] = (0, 255, 204)                           # écho du fond
        rs = min(H, rb + 3 + int(self.sed_var.get() * sc))     # sédiment
        for r in range(rb + 3, rs):
            t = (r - rb - 3) / max(1, (rs - rb - 3))
            c[r] = (int(60 * (1 - t)) + 12, int(42 * (1 - t)) + 8, int(25 * (1 - t)) + 6)
        if self.obj_var.get():                                 # hyperbole de la cible
            dx = 0.35
            dobj = zb + self.sed_var.get() * 0.6
            ro = int(math.sqrt(dobj * dobj + ((x - self.x0) * dx) ** 2) * sc)
            if rb + 2 < ro < H - 2:
                c[ro:ro + 2] = (255, 140, 0)
        return np.clip(c, 0, 255).astype(np.uint8)

    def _start(self):
        if self.scanning:
            return
        self.scanning = True
        self.x0 = int(self.W * random.uniform(0.55, 0.7))
        self.view = np.zeros((self.H, self.W, 3), np.uint8)
        self._log(f"▶️ SCAN: {self.preset_var.get()} — profondeur {self.depth_var.get()} m")
        threading.Thread(target=self._loop, daemon=True).start()

    def _stop(self):
        self.scanning = False

    def _loop(self):
        for x in range(self.W):
            if not self.scanning:
                break
            self.view[:, x] = self._ping_column(x)
            if x % 3 == 0:
                self.root.after(0, self._show)
        self.scanning = False
        self.root.after(0, self._show)
        self.root.after(0, lambda: self._log(
            "✅ Passe terminée. L'hyperbole orange = signature d'un objet enfoui."))

    def _drain(self):
        """Vue synthétique 'flotte vidée' : fond exposé + cible à nu."""
        H, W = self.H, self.W
        dmax = self.depth_var.get() + self.sed_var.get() + 20
        sc = H / dmax
        img = np.zeros((H, W, 3), np.uint8)
        img[:] = (12, 12, 20)
        prof = [self._bottom(x) for x in range(W)]
        for x in range(W):
            rb = min(H - 4, int(prof[x] * sc))
            img[rb:rb + 2, x] = (0, 255, 204)                  # fond exposé
            rs = min(H, rb + 2 + int(self.sed_var.get() * sc))
            img[rb + 2:rs, x] = (45, 32, 20)                   # sédiment
        if self.obj_var.get():
            zb = prof[self.x0]
            cy = int((zb + self.sed_var.get() * 0.6) * sc)
            r = max(3, int(self.obj_size_var.get() / 2 * sc))
            yy, xx = np.ogrid[:H, :W]
            ring = ((xx - self.x0) ** 2 + (yy - cy) ** 2 <= r ** 2) & \
                   ((xx - self.x0) ** 2 + (yy - cy) ** 2 >= (r - 2) ** 2)
            img[ring] = (255, 140, 0)
            img[max(0, cy - 1):cy + 1, self.x0 - r - 6:self.x0 + r + 6] = (255, 140, 0)
            img[max(0, cy - r - 6):cy + r + 6, self.x0 - 1:self.x0 + 1] = (255, 140, 0)
        self.view = img
        self._show()
        self._log(f"🌊 FLOTTE VIDÉE: {self.preset_var.get()} — cible Ø {self.obj_size_var.get()} m exposée à "
                  f"~{int(prof[self.x0] + self.sed_var.get() * 0.6)} m")

    def _show(self):
        img = Image.fromarray(self.view)
        self.photo = ImageTk.PhotoImage(img)
        self.canvas_lbl.config(image=self.photo)

    def _save(self):
        p = filedialog.asksaveasfilename(defaultextension=".jpg",
                                         filetypes=[("JPEG", "*.jpg")])
        if p:
            Image.fromarray(self.view).save(p, quality=92)
            self._log(f"📷 Vue exportée: {p}")


def main():
    try:
        SonarApp()
    except Exception as e:
        import traceback
        print(f"❌ Erreur critique: {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()