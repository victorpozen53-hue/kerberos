#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕊️ ARGOS SANCTUAIRE v1.0 — module PRIVÉ de protection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — NE JAMAIS PARTAGER (ni ce module, ni sanctuaire/)
Ce module ne détecte rien : il PROTÈGE.
1. 🎯 tu dessines un cercle sur une image -> masque LOCAL privé
2. 🕊️ "Voiler" : flou + noir sur toutes les cibles/exports qui recoupent
   un sanctuaire -> aucune trace ne fuit hors de cette machine.
"""
import sys
import threading
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


def _excepthook(t, v, tb):
    print("❌ ERREUR CRITIQUE:\n" + "".join(traceback.format_exception(t, v, tb)))
    input("Appuyez sur Entrée pour fermer...")


sys.excepthook = _excepthook

try:
    import cv2
    import numpy as np
except ImportError as e:
    print("❌ OpenCV/numpy manquant:", e)
    input("Appuyez sur Entrée...")
    sys.exit(1)

_p = Path(__file__).resolve().parent
ARGOS_ROOT = _p.parent if (_p.parent / "img").exists() or _p.name == "modules" else _p
SANCT = ARGOS_ROOT / "sanctuaire"
SANCT.mkdir(parents=True, exist_ok=True)
_rd = SANCT / "README.txt"
if not _rd.exists():
    _rd.write_text("PRIVÉ — NE JAMAIS PARTAGER.\nMasques de sanctuaire : coordonnées locales uniquement.\n", encoding="utf-8")
CIBLES = ARGOS_ROOT / "img" / "cibles"
EXPORTS = ARGOS_ROOT / "exports"


class SanctuaireApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🕊️ ARGOS SANCTUAIRE v1.0 — PRIVÉ")
        self.root.geometry("760x420")
        self.root.configure(bg=self.BG)
        self.src = None
        self._build()
        self._log("🕊️ Sanctuaire prêt — les masques restent sur CETTE machine")
        self.root.mainloop()

    def _build(self):
        vf = tk.Frame(self.root, bg=self.BG)
        vf.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(vf, text="🖼️ Image:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.src_var = tk.StringVar()
        tk.Entry(vf, textvariable=self.src_var, width=55, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(vf, text="📂", bg=self.BTN, fg=self.WH, command=self._browse).pack(side=tk.LEFT)
        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(bf, text="🎯 Dessiner une zone", bg='#4CAF50', fg=self.WH,
                  font=("Consolas", 11, "bold"), command=self._draw).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        tk.Button(bf, text="🕊️ Voiler les exports", bg=self.BTN, fg=self.WH,
                  font=("Consolas", 11, "bold"), command=self._veil).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        self.log = tk.Text(self.root, height=10, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _browse(self):
        p = filedialog.askopenfilename(title="Image de référence",
                                       filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if p:
            self.src = Path(p)
            self.src_var.set(p)

    def _log(self, msg):
        try:
            self.log.configure(state='normal')
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state='disabled')
        except Exception:
            pass

    def _draw(self):
        if self.src is None or not self.src.exists():
            messagebox.showerror("Erreur", "Choisis d'abord une image")
            return
        threading.Thread(target=self._draw_worker, daemon=True).start()

    def _draw_worker(self):
        img = cv2.imread(str(self.src))
        if img is None:
            self.root.after(0, lambda: messagebox.showerror("Erreur", "Image illisible"))
            return
        mask = np.zeros(img.shape[:2], np.uint8)
        state = {"c": None, "r": 0}
        win = "SANCTUAIRE — clique-glisse pour le cercle, ENTREE pour valider"

        def on_mouse(ev, x, y, fl, _):
            if ev == cv2.EVENT_LBUTTONDOWN:
                state["c"] = (x, y)
            elif ev == cv2.EVENT_MOUSEMOVE and state["c"]:
                state["r"] = int(((x - state["c"][0]) ** 2 + (y - state["c"][1]) ** 2) ** 0.5)

        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(win, on_mouse)
        while True:
            show = img.copy()
            if state["c"]:
                cv2.circle(show, state["c"], state["r"], (0, 255, 0), 2)
            cv2.imshow(win, show)
            k = cv2.waitKey(30) & 0xFF
            if k == 13 and state["c"] and state["r"] > 3:   # ENTREE
                cv2.circle(mask, state["c"], state["r"], 255, -1)
                out = SANCT / f"{self.src.stem}.png"
                cv2.imwrite(str(out), mask)
                self.root.after(0, lambda: self._log(f"🎯 Sanctuaire enregistré (LOCAL): {out.name}"))
                break
            if k == 27:                                      # ESC
                break
        cv2.destroyAllWindows()

    def _veil(self):
        threading.Thread(target=self._veil_worker, daemon=True).start()

    def _veil_worker(self):
        n = 0
        for mp in sorted(SANCT.glob("*.png")):
            mask = cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE)
            if mask is None:
                continue
            for folder in (CIBLES, EXPORTS):
                if not folder.exists():
                    continue
                for imgp in folder.glob(f"{mp.stem}*.*"):
                    if imgp.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                        continue
                    img = cv2.imread(str(imgp))
                    if img is None:
                        continue
                    H, W = img.shape[:2]
                    m = cv2.resize(mask, (W, H), interpolation=cv2.INTER_NEAREST) > 0
                    if not m.any():
                        continue
                    blur = cv2.GaussianBlur(img, (99, 99), 0)
                    img[m] = blur[m]
                    img[m] = (img[m].astype(np.float32) * 0.25).astype(np.uint8)
                    cv2.imwrite(str(imgp), img)
                    n += 1
                    self.root.after(0, lambda p=imgp: self._log(f"🕊️ Voilé: {p.name}"))
        self.root.after(0, lambda: self._log(f"✅ {n} export(s) voilé(s) — rien n'a fui"))


def run():
    SanctuaireApp()
    return "✅ Sanctuaire fermé"


def main():
    try:
        SanctuaireApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()