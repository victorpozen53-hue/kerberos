#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌾 ARGOS CROP CIRCLE v1.0 — organe PRIVÉ (cercles de cultures)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — usage LOCAL, ne jamais partager
Signature d'un crop circle :
- cercle quasi parfait (circularité >= 0.72, ratio ~1)
- posé DANS un champ (teintes végétation/cultures autour)
- champ CALME : faible densité d'arêtes autour (pas une ville)
- 2+ cercles proches = FORMATION (motif classique)
🕊️ Respect du sanctuaire : détection protégée = jamais divulguée.
Usage : bouton organe dans ARGOS v3.0, ou python argos_cropcircle.py
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
UI_TOP, UI_LEFT, UI_BOTTOM = 210, 310, 45

LABELS = {"CROP CIRCLE": (0, 165, 255), "FORMATION": (255, 255, 255)}


def detect_cropcircle(frame):
    """Cercle parfait + champ calme = crop circle ; plusieurs proches = formation."""
    hits = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    field = ((h >= 15) & (h <= 90) & (s >= 20) & (v >= 40)).astype(np.uint8) * 255
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 40, 120)
    edges[:UI_TOP, :] = 0
    edges[:, :UI_LEFT] = 0
    if UI_BOTTOM:
        edges[-UI_BOTTOM:, :] = 0
    edges[:300, -170:] = 0
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    circles = []
    H, W = frame.shape[:2]
    for c in cnts:
        area = cv2.contourArea(c)
        if not (200 < area < 200000):
            continue
        per = cv2.arcLength(c, True)
        if per == 0:
            continue
        circ = 4 * math.pi * area / (per * per)
        if circ < 0.72:
            continue
        x, y, w, hh = cv2.boundingRect(c)
        ar = float(w) / max(1, hh)
        if not (0.6 <= ar <= 1.6):
            continue
        X0, Y0 = max(0, x - w), max(0, y - hh)
        X1, Y1 = min(W, x + 2 * w), min(H, y + 2 * hh)
        roi_f = field[Y0:Y1, X0:X1]
        roi_e = edges[Y0:Y1, X0:X1]
        ff = float((roi_f > 0).mean()) if roi_f.size else 0.0
        ed = float((roi_e > 0).mean()) if roi_e.size else 1.0
        if ff < 0.4:
            continue          # pas un champ
        if ed > 0.12:
            continue          # trop d'arêtes = ville/texturé, pas un champ calme
        circles.append((x, y, w, hh))
    for (x, y, w, hh) in circles:
        cx, cy = x + w / 2.0, y + hh / 2.0
        near = sum(1 for (x2, y2, w2, h2) in circles
                   if math.hypot(x2 + w2 / 2.0 - cx, y2 + h2 / 2.0 - cy) < 3 * max(w, hh))
        label = "FORMATION" if near >= 2 else "CROP CIRCLE"
        hits.append((label, (x, y, w, hh)))
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


class CropApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌾 ARGOS CROP CIRCLE v1.0 — PRIVÉ")
        self.root.geometry("980x780")
        self.root.configure(bg=self.BG)
        self.stop_flag = False
        self.latest = None
        self.photo = None
        self._build()
        self._refresh()
        self._log("🌾 ARGOS CROP CIRCLE — cercle parfait + champ calme")
        self._log("🕊️ les zones sanctuaire sont détectées en silence, jamais divulguées")
        self.root.mainloop()

    def _build(self):
        vf = tk.Frame(self.root, bg=self.BG)
        vf.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(vf, text="🖼️ Source:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.src_var = tk.StringVar()
        tk.Entry(vf, textvariable=self.src_var, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(vf, text="📂", bg=self.BTN, fg=self.WH, command=self._browse).pack(side=tk.LEFT)
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
        if not self.src_var.get().strip():
            messagebox.showerror("Erreur", "Choisis d'abord un dossier (📂)")
            return
        src = Path(self.src_var.get())
        if not src.exists():
            messagebox.showerror("Erreur", "Dossier introuvable")
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
            if not files:
                self.root.after(0, lambda: self._log("🌾 Aucun JPEG dans ce dossier"))
                return
            found, protected = 0, 0
            for i, p in enumerate(files):
                if self.stop_flag:
                    break
                frame = cv2.imread(str(p))
                if frame is None:
                    continue
                keep = []
                for label, (x, y, w, hh) in detect_cropcircle(frame):
                    if in_sanctuaire(p.stem, x + w // 2, y + hh // 2):
                        protected += 1
                        self.root.after(0, lambda p=p, l=label: self._log(
                            f"🕊️ {p.name}: {l} en sanctuaire — NON divulguée"))
                    else:
                        keep.append((label, (x, y, w, hh)))
                for label, (x, y, w, hh) in keep:
                    color = LABELS[label]
                    cv2.rectangle(frame, (x, y), (x + w, y + hh), color, 2)
                    cxm, cym = x + w // 2, y + hh // 2
                    cv2.line(frame, (cxm - 14, cym), (cxm + 14, cym), color, 2)
                    cv2.line(frame, (cxm, cym - 14), (cxm, cym + 14), color, 2)
                    cv2.putText(frame, label, (x, max(12, y - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                if keep:
                    found += len(keep)
                    cv2.imwrite(str(CIBLES / f"crop_{p.stem}.jpg"), frame,
                                [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                    self.root.after(0, lambda p=p, ks=keep: self._log(
                        f"🌾 {p.name}: " + ", ".join(l for l, _ in ks)))
                self.latest = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.root.after(0, lambda i=i, t=len(files), p=p:
                                self.status_config(f"🌾 {i + 1}/{t} — {p.name}"))
            self.root.after(0, lambda: self._log(f"✅ Fin: {found} signature(s), {protected} protégée(s) 🕊️"))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ " + str(e)))
        finally:
            self.root.after(0, lambda: self.btn_go.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))

    def status_config(self, txt):
        pass  # statut géré par l'engine si intégré ; silencieux en standalone

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
    CropApp()
    return "✅ ARGOS CROP CIRCLE fermé"


def main():
    try:
        CropApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()