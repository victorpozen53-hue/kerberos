#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛸 ARGOS OVNI v1.0 — module PRIVÉ (signature disques / halo plasma)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — usage LOCAL, ne jamais partager
Signature : circularité haute + ratio ~1 + contraste cœur/anneau
(cœur brillant sur anneau sombre, OU anneau lumineux autour d'un cœur sombre)
🕊️ Respect du SANCTUAIRE : une détection dans un masque privé est
comptée mais JAMAIS sauvegardée ni divulguée.
"""
import sys
import math
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

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

_p = Path(__file__).resolve().parent
ARGOS_ROOT = _p.parent if (_p.parent / "img").exists() or _p.name == "modules" else _p
CIBLES = ARGOS_ROOT / "img" / "cibles"
SANCT = ARGOS_ROOT / "sanctuaire"
CIBLES.mkdir(parents=True, exist_ok=True)
EXTS = (".jpg", ".jpeg", ".png")


def detect_disc(frame):
    hits = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    v = hsv[:, :, 2]
    edges = cv2.Canny(gray, 60, 140)
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        area = cv2.contourArea(c)
        if not (20 < area < 2500):
            continue
        per = cv2.arcLength(c, True)
        if per == 0:
            continue
        circ = 4 * math.pi * area / (per * per)
        x, y, w, h = cv2.boundingRect(c)
        ar = float(w) / max(1, h)
        if circ < 0.78 or not (0.6 <= ar <= 1.6):
            continue
        m = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(m, [c], -1, 255, -1)
        core_v = float(v[m > 0].mean()) if (m > 0).any() else 0.0
        ring = cv2.dilate(m, np.ones((9, 9), np.uint8))
        ringm = (ring > 0) & (m == 0)
        ring_v = float(v[ringm].mean()) if ringm.any() else core_v
        plasma = (ring_v > core_v + 20) or (core_v > 190 and ring_v < core_v - 25)
        if plasma or circ >= 0.9:
            hits.append((x, y, w, h))
    return hits


def in_sanctuaire(stem, x, y):
    mp = SANCT / f"{stem}.png"
    if not mp.exists():
        return False
    mask = cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return False
    H, W = mask.shape
    return bool(mask[min(y, H - 1), min(x, W - 1)] > 0)


class OvniApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛸 ARGOS OVNI v1.0 — PRIVÉ")
        self.root.geometry("980x780")
        self.root.configure(bg=self.BG)
        self.stop_flag = False
        self.latest = None
        self.photo = None
        self._build()
        self._refresh()
        self._log("🛸 ARGOS OVNI — signature disques/plasma, usage LOCAL")
        self._log("🕊️ Les zones sanctuaire sont détectées en silence, jamais divulguées")
        self.root.mainloop()

    def _build(self):
        vf = tk.Frame(self.root, bg=self.BG)
        vf.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(vf, text="🖼️ Source:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.src_var = tk.StringVar()
        tk.Entry(vf, textvariable=self.src_var, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(vf, text="📂", bg=self.BTN, fg=self.WH,
                  command=self._browse).pack(side=tk.LEFT)
        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=5)
        self.btn_go = tk.Button(bf, text="▶️ Chercher", bg='#4CAF50', fg=self.WH,
                                font=("Consolas", 12, "bold"), command=self._start)
        self.btn_go.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.btn_stop = tk.Button(bf, text="⏹️ Stop", bg='#ff5252', fg=self.WH,
                                  font=("Consolas", 12, "bold"), command=self._stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.preview = tk.Label(self.root, bg=self.BG, text="⏳ …", fg=self.CY, font=("Consolas", 12))
        self.preview.pack(padx=10, pady=5)
        self.log = tk.Text(self.root, height=9, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _browse(self):
        p = filedialog.askdirectory(title="Dossier de JPEG")
        if p:
            self.src_var.set(p)

    def _log(self, msg):
        try:
            self.log.configure(state='normal')
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state='disabled')
        except Exception:
            pass

    def _start(self):
        src = Path(self.src_var.get())
        if not src.exists():
            messagebox.showerror("Erreur", "Choisis un dossier")
            return
        self.stop_flag = False
        self.btn_go.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        threading.Thread(target=self._scan, args=(src,), daemon=True).start()

    def _stop(self):
        self.stop_flag = True

    def _scan(self, src):
        try:
            files = sorted([p for p in src.glob("*.*") if p.suffix.lower() in EXTS])
            found, protected = 0, 0
            for i, p in enumerate(files):
                if self.stop_flag:
                    break
                frame = cv2.imread(str(p))
                if frame is None:
                    continue
                hits = detect_disc(frame)
                keep = []
                for (x, y, w, h) in hits:
                    cx, cy = x + w // 2, y + h // 2
                    if in_sanctuaire(p.stem, cx, cy):
                        protected += 1
                        self.root.after(0, lambda p=p: self._log(f"🕊️ {p.name}: signature en sanctuaire — NON divulguée"))
                    else:
                        keep.append((x, y, w, h))
                for (x, y, w, h) in keep:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
                    cv2.putText(frame, "OVNI", (x, max(12, y - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
                if keep:
                    found += len(keep)
                    cv2.imwrite(str(CIBLES / f"ovni_{p.stem}.jpg"), frame)
                self.latest = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.root.after(0, lambda i=i, t=len(files), p=p:
                                self.log.configure(state='normal') or None)
            self.root.after(0, lambda: self._log(f"✅ Fin: {found} signature(s) publique(s), {protected} protégée(s) 🕊️"))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ " + str(e)))
        finally:
            self.root.after(0, lambda: self.btn_go.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))

    def _refresh(self):
        try:
            if self.latest is not None and Image is not None:
                img = Image.fromarray(self.latest)
                img.thumbnail((940, 520))
                self.photo = ImageTk.PhotoImage(img)
                self.preview.config(image=self.photo, text="")
        except Exception:
            pass
        self.root.after(33, self._refresh)


def run():
    OvniApp()
    return "✅ ARGOS OVNI fermé"


def main():
    try:
        OvniApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()