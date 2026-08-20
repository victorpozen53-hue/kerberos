#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛸 ARGOS UFO v1.2 — organe PRIVÉ soucoupes & tic-tacs (version stricte)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — usage LOCAL, ne jamais partager
v1.2 : 4 verrous anti faux positifs :
1. 🎨 couleur RARE : gris métallisé / noir profond / fort contraste
   (rejet auto du vert végétal et de l'écume blanche)
2. 🧘 contexte CALME : peu d'arêtes autour (pas un relief texturé)
3. 🕊️ SOLITUDE : un objet entouré de voisins = motif naturel -> rejeté
4. 🚫 disjoncteur : >30 signatures sur une image = texture -> ignorée
Signatures : SOUCOUPE = 2 ronds emboîtés • TICTAC = capsule métallique
🕊️ Respect du sanctuaire : détection protégée = jamais divulguée.
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
MAX_PER_IMAGE = 30
LABELS = {"SOUCOUPE": (255, 0, 255), "TICTAC": (255, 255, 0)}


def detect_ufo(frame):
    """v1.2 : géométrie + gris métallisé + contexte calme + solitude."""
    hits = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    closed = cv2.morphologyEx(cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 50, 130),
                              cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    closed[:UI_TOP, :] = 0
    closed[:, :UI_LEFT] = 0
    if UI_BOTTOM:
        closed[-UI_BOTTOM:, :] = 0
    closed[:300, -170:] = 0
    cnts, hier = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:
        return hits
    hier = hier[0]
    H, W = gray.shape
    cands = []
    for i, c in enumerate(cnts):
        area = cv2.contourArea(c)
        if not (30 < area < 4000):
            continue
        per = cv2.arcLength(c, True)
        if per == 0:
            continue
        circ = 4 * math.pi * area / (per * per)
        x, y, w, hh = cv2.boundingRect(c)
        rect = cv2.minAreaRect(c)
        rw, rh = rect[1]
        aspect = (max(rw, rh) / min(rw, rh)) if min(rw, rh) > 0 else 99
        extent = area / (rw * rh) if rw * rh > 0 else 0
        hull = cv2.convexHull(c)
        ha = cv2.contourArea(hull)
        sol = area / ha if ha else 0

        # couleurs du cœur et de l'anneau
        m = np.zeros(gray.shape, np.uint8)
        cv2.drawContours(m, [c], -1, 255, -1)
        mv, ms, mh = v[m > 0], s[m > 0], h[m > 0]
        if mv.size == 0:
            continue
        core_v, core_s, core_h = float(mv.mean()), float(ms.mean()), float(mh.mean())
        ring = cv2.dilate(m, np.ones((9, 9), np.uint8))
        ringm = (ring > 0) & (m == 0)
        ring_v = float(v[ringm].mean()) if ringm.any() else core_v

        # 🎨 verrou 1 : couleur rare dans la nature
        metallic = (core_s < 60) and (110 <= core_v <= 230)
        blackobj = (core_s < 60) and (core_v < 70)
        contrast = abs(core_v - ring_v) > 25
        veget = (25 <= core_h <= 90) and (core_s > 50)
        foam = (core_v > 235) and (core_s < 35)
        if veget or foam or not (metallic or blackobj or contrast):
            continue

        # 🧘 verrou 2 : contexte calme (pas une crête de relief)
        X0, Y0 = max(0, x - w), max(0, y - hh)
        X1, Y1 = min(W, x + 2 * w), min(H, y + 2 * hh)
        roi_e = closed[Y0:Y1, X0:X1]
        ed = float((roi_e > 0).mean()) if roi_e.size else 1.0
        if ed > 0.08:
            continue

        kind = None
        # 🛸 SOUCOUPE : deux ronds emboîtés
        if circ >= 0.70 and 0.7 <= (w / max(1, hh)) <= 1.4:
            child = hier[i][2]
            if child != -1:
                cc = cnts[child]
                ca, cp = cv2.contourArea(cc), cv2.arcLength(cc, True)
                if cp > 0 and ca > 0:
                    ccirc = 4 * math.pi * ca / (cp * cp)
                    if ccirc >= 0.5 and 0.15 < ca / area < 0.85:
                        kind = "SOUCOUPE"
        # 🛸 TICTAC : capsule convexe, allongée, sans coins
        if kind is None and 1.8 <= aspect <= 5.5 and sol >= 0.93 and 0.84 <= extent <= 0.965:
            kind = "TICTAC"
        if kind:
            cands.append((kind, (x, y, w, hh), (x + w / 2.0, y + hh / 2.0)))

    # 🕊️ verrou 3 : solitude (la nature va en groupes, un objet est SEUL)
    for kind, box, (cx, cy) in cands:
        near = sum(1 for _, _, (ox, oy) in cands if math.hypot(ox - cx, oy - cy) < 80)
        if near <= 2:
            hits.append((kind, box))
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


class UfoApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛸 ARGOS UFO v1.2 — PRIVÉ (soucoupes & tic-tacs)")
        self.root.geometry("980x780")
        self.root.configure(bg=self.BG)
        self.stop_flag = False
        self.latest = None
        self.photo = None
        self._build()
        self._refresh()
        self._log("🛸 ARGOS UFO v1.2 — métallisé + calme + solitude + disjoncteur")
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
                self.root.after(0, lambda: self._log("🛸 Aucun JPEG dans ce dossier"))
                return
            found, protected = 0, 0
            for i, p in enumerate(files):
                if self.stop_flag:
                    break
                frame = cv2.imread(str(p))
                if frame is None:
                    continue
                keep = []
                for label, (x, y, w, h) in detect_ufo(frame):
                    if in_sanctuaire(p.stem, x + w // 2, y + h // 2):
                        protected += 1
                        self.root.after(0, lambda p=p, l=label: self._log(
                            f"🕊️ {p.name}: {l} en sanctuaire — NON divulguée"))
                    else:
                        keep.append((label, (x, y, w, h)))
                # 🚫 verrou 4 : disjoncteur anti-texture
                if len(keep) > MAX_PER_IMAGE:
                    self.root.after(0, lambda p=p, n=len(keep): self._log(
                        f"⚠️ {p.name}: {n} signatures — texture naturelle, image ignorée"))
                    keep = []
                for label, (x, y, w, h) in keep:
                    color = LABELS[label]
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    cxm, cym = x + w // 2, y + h // 2
                    cv2.line(frame, (cxm - 14, cym), (cxm + 14, cym), color, 2)
                    cv2.line(frame, (cxm, cym - 14), (cxm, cym + 14), color, 2)
                    cv2.putText(frame, label, (x, max(12, y - 6)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                if keep:
                    found += len(keep)
                    cv2.imwrite(str(CIBLES / f"ufo_{p.stem}.jpg"), frame,
                                [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                    self.root.after(0, lambda p=p, ks=keep: self._log(
                        f"🛸 {p.name}: " + ", ".join(l for l, _ in ks)))
                self.latest = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.root.after(0, lambda: self._log(f"✅ Fin: {found} signature(s), {protected} protégée(s) 🕊️"))
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
    UfoApp()
    return "✅ ARGOS UFO fermé"


def main():
    try:
        UfoApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()