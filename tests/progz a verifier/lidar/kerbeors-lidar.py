#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛰️ KERBEROS LIDAR GUI — v3.1 (le scintillement est de retour, en 2×2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3
- Interface Tkinter qui NE DISPARAÎT JAMAIS (scan dans un thread)
- Lit UNIQUEMENT des images (PNG/TIFF/BMP/JPG) : dossier ou image seule
- ☁️ Nuage de points cyan 2×2 (le scintillement "classe")
- Option ½ PIXEL, filtre anti-UI, masque UI Google Earth, SMART JPEG
- Sorties : lidar_<nom>.mp4 + lidar_<nom>_frames/
"""
import threading
import math
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
import numpy as np
from PIL import Image, ImageTk

# --- PARAMÈTRES ---
VEG_H_RANGE = (30, 90)
VEG_S_MIN, VEG_V_MIN = 40, 40
MIN_AREA, MAX_AREA = 150, 30000
LINE_MIN_LEN = 80
CONFIRM_FRAMES = 3

UI_TOP, UI_LEFT, UI_BOTTOM = 210, 310, 45
OUT_FPS = 10.0
JPEG_QUALITY = 90
EXTS = ("*.png", "*.tif", "*.tiff", "*.bmp", "*.jpg", "*.jpeg")
SUFFIXES = (".png", ".tif", ".tiff", ".bmp", ".jpg", ".jpeg")
VIDEO_SUFFIXES = (".mp4", ".avi", ".mkv")


class LidarCore:
    """Moteur de scan image, avec option ½ pixel (×2)."""

    def __init__(self, circ_min=0.72, max_points=1800, subpixel=False):
        self.circ_min = circ_min
        self.max_points = max_points
        self.subpixel = subpixel
        self.echo_history = {}
        self.confirmed = []
        self.sweep = 0.0

    @staticmethod
    def _is_ui(hsv, x, y, w, h):
        """Rejette les échos posés sur l'interface (fenêtres, pins, labels)."""
        if w < 1 or h < 1:
            return False
        roi = hsv[y:y + h, x:x + w]
        if roi.size == 0:
            return False
        m_h = float(roi[:, :, 0].mean())
        m_s = float(roi[:, :, 1].mean())
        m_v = float(roi[:, :, 2].mean())
        if m_s < 25 and m_v > 140:                        # blanc/gris = fenêtres
            return True
        if 15 <= m_h <= 35 and m_s > 120 and m_v > 180:   # jaune = pins/labels
            return True
        if (m_h <= 10 or m_h >= 170) and m_s > 120 and m_v > 150:  # rouge = pins
            return True
        return False

    def process(self, frame):
        sc = 2.0 if self.subpixel else 1.0
        if sc > 1:
            work = cv2.resize(frame, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC)
        else:
            work = frame
        gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(work, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        veg = ((h >= VEG_H_RANGE[0]) & (h <= VEG_H_RANGE[1]) &
               (s >= VEG_S_MIN) & (v >= VEG_V_MIN)).astype(np.uint8) * 255
        veg = cv2.dilate(veg, np.ones((3, 3), np.uint8))
        structure = cv2.bitwise_and(cv2.Canny(gray, 60, 140), cv2.bitwise_not(veg))

        # Masque UI (mis à l'échelle)
        ut, ul, ub = int(UI_TOP * sc), int(UI_LEFT * sc), int(UI_BOTTOM * sc)
        structure[:ut, :] = 0
        structure[:, :ul] = 0
        if ub:
            structure[-ub:, :] = 0

        # ☁️ Nuage de points cyan ramené à la taille d'origine, EN 2×2
        if sc > 1:
            disp = cv2.resize(structure, (frame.shape[1], frame.shape[0]),
                              interpolation=cv2.INTER_NEAREST)
        else:
            disp = structure
        ys, xs = np.nonzero(disp)
        n = len(xs)
        if n > self.max_points:
            idx = np.random.choice(n, self.max_points, replace=False)
            xs, ys = xs[idx], ys[idx]
            n = self.max_points
        if n:
            frame[ys, xs] = (0, 255, 204)
            y2 = np.minimum(ys + 1, frame.shape[0] - 1)
            x2 = np.minimum(xs + 1, frame.shape[1] - 1)
            frame[y2, xs] = (0, 255, 204)
            frame[ys, x2] = (0, 255, 204)

        # Échos calculés en ×2 si ½ pixel, puis ramenés à l'échelle d'origine
        echoes = []
        a_min, a_max = MIN_AREA * sc * sc, MAX_AREA * sc * sc
        l_min = int(LINE_MIN_LEN * sc)
        closed = cv2.morphologyEx(structure, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            area = cv2.contourArea(c)
            if not (a_min < area < a_max):
                continue
            per = cv2.arcLength(c, True)
            if per and 4 * math.pi * area / (per * per) >= self.circ_min:
                xw, yw, ww, hw = cv2.boundingRect(c)
                if not self._is_ui(hsv, xw, yw, ww, hw):
                    echoes.append(("CIRCULAIRE", (int(xw / sc), int(yw / sc),
                                                  int(ww / sc), int(hw / sc))))
        lines = cv2.HoughLinesP(structure, 1, np.pi / 180, 60,
                                minLineLength=l_min, maxLineGap=6)
        if lines is not None:
            for l in lines[:6]:
                x1, y1, x2, y2 = map(int, np.asarray(l).ravel())
                xw, yw = min(x1, x2), min(y1, y2)
                ww, hw = abs(x2 - x1), abs(y2 - y1)
                if not self._is_ui(hsv, xw, yw, ww, hw):
                    echoes.append(("LINEAIRE", (int(xw / sc), int(yw / sc),
                                                int(ww / sc), int(hw / sc))))

        self.confirmed = []
        for kind, box in echoes:
            key = (kind, round(box[0] / 40), round(box[1] / 40))
            self.echo_history[key] = self.echo_history.get(key, 0) + 1
            if self.echo_history[key] >= CONFIRM_FRAMES:
                self.confirmed.append((kind, box))
        for k in list(self.echo_history):
            self.echo_history[k] = max(0.0, self.echo_history[k] - 0.4)

        for kind, (x, y, w, h) in self.confirmed:
            color = (0, 165, 255) if kind == "CIRCULAIRE" else (80, 80, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cxm, cym = x + w // 2, y + h // 2
            cv2.line(frame, (cxm - 14, cym), (cxm + 14, cym), color, 2)
            cv2.line(frame, (cxm, cym - 14), (cxm, cym + 14), color, 2)
            cv2.putText(frame, kind, (x, max(12, y - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        self.sweep = (self.sweep + 0.07) % (2 * math.pi)
        H, W = frame.shape[:2]
        r, cx, cy = 60, W - 80, H - 80
        cv2.circle(frame, (cx, cy), r, (0, 255, 204), 1)
        cv2.line(frame, (cx, cy),
                 (int(cx + math.cos(self.sweep) * r), int(cy + math.sin(self.sweep) * r)),
                 (0, 255, 204), 2)
        cv2.putText(frame, f"points:{n} echos:{len(self.confirmed)}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 204), 1)
        return frame, n, len(self.confirmed)


class LidarApp:
    BG_DARK = '#1e1e1e'; BG_MEDIUM = '#2d2d2d'; FG_CYAN = '#00ffcc'
    FG_GREEN = '#4CAF50'; FG_RED = '#ff5252'; FG_ORANGE = '#ff9800'
    FG_WHITE = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛰️ KERBEROS LIDAR v3.1")
        self.root.geometry("1000x820")
        self.root.configure(bg=self.BG_DARK)
        self.source = None
        self.core = None
        self.thread = None
        self.stop_flag = False
        self.latest = None
        self.photo = None
        self._build()
        self._refresh()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self.root.mainloop()

    def _build(self):
        tk.Label(self.root, text="🛰️ KERBEROS LIDAR v3.1", bg=self.BG_MEDIUM,
                 fg=self.FG_CYAN, font=("Consolas", 16, "bold")).pack(fill=tk.X, pady=8)

        cfg = tk.Frame(self.root, bg=self.BG_DARK)
        cfg.pack(fill=tk.X, padx=10, pady=5)

        vf = tk.Frame(cfg, bg=self.BG_DARK)
        vf.pack(fill=tk.X, pady=3)
        tk.Label(vf, text="🖼️ Source:", bg=self.BG_DARK, fg=self.FG_CYAN).pack(side=tk.LEFT)
        self.src_var = tk.StringVar()
        tk.Entry(vf, textvariable=self.src_var, width=55,
                 bg=self.BG_MEDIUM, fg=self.FG_WHITE).pack(side=tk.LEFT, padx=5)
        tk.Button(vf, text="📂 Dossier", bg=self.BTN, fg=self.FG_WHITE,
                  command=self._browse_dir).pack(side=tk.LEFT, padx=2)
        tk.Button(vf, text="🖼️ Image", bg=self.BTN, fg=self.FG_WHITE,
                  command=self._browse_img).pack(side=tk.LEFT, padx=2)

        sf = tk.Frame(cfg, bg=self.BG_DARK)
        sf.pack(fill=tk.X, pady=3)
        tk.Label(sf, text="⭕ Circularité:", bg=self.BG_DARK, fg=self.FG_CYAN).pack(side=tk.LEFT)
        self.circ_var = tk.IntVar(value=72)
        tk.Scale(sf, from_=50, to=95, orient=tk.HORIZONTAL, variable=self.circ_var,
                 bg=self.BG_MEDIUM, fg=self.FG_CYAN, highlightthickness=0,
                 length=220, showvalue=1, command=self._live).pack(side=tk.LEFT, padx=5)
        tk.Label(sf, text="☁️ Points:", bg=self.BG_DARK, fg=self.FG_CYAN).pack(side=tk.LEFT, padx=(15, 0))
        self.points_var = tk.IntVar(value=1800)
        tk.Scale(sf, from_=500, to=4000, resolution=100, orient=tk.HORIZONTAL,
                 variable=self.points_var, bg=self.BG_MEDIUM, fg=self.FG_CYAN,
                 highlightthickness=0, length=220, command=self._live).pack(side=tk.LEFT, padx=5)

        of = tk.Frame(cfg, bg=self.BG_DARK)
        of.pack(fill=tk.X, pady=3)
        self.subpixel_var = tk.BooleanVar(value=False)
        tk.Checkbutton(of, text="½ PIXEL (précision ×2)", variable=self.subpixel_var,
                       bg=self.BG_DARK, fg=self.FG_CYAN, selectcolor=self.BG_MEDIUM,
                       activebackground=self.BG_DARK,
                       activeforeground=self.FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.smart_var = tk.BooleanVar(value=True)
        tk.Checkbutton(of, text="📷 SMART JPEG (anomalies seulement)", variable=self.smart_var,
                       bg=self.BG_DARK, fg=self.FG_CYAN, selectcolor=self.BG_MEDIUM,
                       activebackground=self.BG_DARK,
                       activeforeground=self.FG_CYAN).pack(side=tk.LEFT, padx=20)

        self.preview = tk.Label(self.root, bg=self.BG_DARK, text="⏳ Choisis un dossier d'images…",
                                fg=self.FG_CYAN, font=("Consolas", 12))
        self.preview.pack(padx=10, pady=5)

        bf = tk.Frame(self.root, bg=self.BG_DARK)
        bf.pack(fill=tk.X, padx=10, pady=5)
        self.btn_start = tk.Button(bf, text="▶️ Scanner", bg=self.FG_GREEN, fg=self.FG_WHITE,
                                   font=("Consolas", 12, "bold"), command=self._start)
        self.btn_start.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.btn_stop = tk.Button(bf, text="⏹️ Stop", bg=self.FG_RED, fg=self.FG_WHITE,
                                  font=("Consolas", 12, "bold"), command=self._stop,
                                  state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.status_label = tk.Label(self.root, text="⏳ Prêt", bg=self.BG_DARK,
                                     fg=self.FG_ORANGE, font=("Consolas", 10))
        self.status_label.pack(pady=2)

        self.log = tk.Text(self.root, height=8, bg=self.BG_MEDIUM, fg=self.FG_GREEN,
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _browse_dir(self):
        p = filedialog.askdirectory(title="Choisis le dossier d'images")
        if p:
            self.source = Path(p)
            self.src_var.set(p)

    def _browse_img(self):
        p = filedialog.askopenfilename(
            title="Choisis une image",
            filetypes=[("Images", "*.png *.tif *.tiff *.bmp *.jpg *.jpeg"), ("Tous", "*.*")])
        if p:
            self.source = Path(p)
            self.src_var.set(p)

    def _live(self, *_):
        if self.core:
            self.core.circ_min = self.circ_var.get() / 100.0
            self.core.max_points = self.points_var.get()

    def _log(self, msg):
        self.log.configure(state='normal')
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.configure(state='disabled')

    def _status(self, fi, tot, e, name):
        self.status_label.config(text=f"🖼️ {fi}/{tot} — {name} — 🎯 {e}")
        if e:
            self._log(f"🎯 image {fi}: {e} écho(s) confirmé(s)")

    def _start(self):
        src = self.source
        if src is None or not src.exists():
            messagebox.showerror("Erreur", "Choisis d'abord un dossier ou une image")
            return
        if src.is_file() and src.suffix.lower() in VIDEO_SUFFIXES:
            messagebox.showerror("Erreur",
                                 "Le LiDAR v3 ne lit QUE les images.\n"
                                 "Convertis la vidéo avec le recorder (🎞️➡️📷).")
            return
        self.stop_flag = False
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.thread = threading.Thread(target=self._scan, args=(src,), daemon=True)
        self.thread.start()

    def _stop(self):
        self.stop_flag = True

    def _scan(self, src):
        if src.is_dir():
            files = sorted([p for ext in EXTS for p in src.glob(ext)], key=lambda p: p.name)
        else:
            files = [src]
        if not files:
            self.root.after(0, lambda: messagebox.showerror("Erreur", "Aucune image trouvée"))
            self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))
            return
        first = cv2.imread(str(files[0]))
        h0, w0 = first.shape[:2]
        stem = src.stem if src.is_file() else src.name
        out = src.parent / f"lidar_{stem}.mp4"
        writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*'mp4v'), OUT_FPS, (w0, h0))
        jpg_dir = out.with_name(out.stem + "_frames")
        jpg_dir.mkdir(parents=True, exist_ok=True)

        sub = self.subpixel_var.get()
        self.core = LidarCore(self.circ_var.get() / 100.0, self.points_var.get(), sub)
        smart = self.smart_var.get()
        ring, saved, jpg_count = [], set(), 0
        self.root.after(0, lambda: self._log(
            f"▶️ Scan de {len(files)} image(s) — mode {'½ pixel' if sub else 'pixel'} — nuage cyan ACTIF"))

        fi = 0
        for path in files:
            if self.stop_flag:
                break
            frame = cv2.imread(str(path))
            if frame is None:
                continue
            if frame.shape[1] != w0 or frame.shape[0] != h0:
                frame = cv2.resize(frame, (w0, h0))
            fi += 1
            frame, n, e = self.core.process(frame)
            writer.write(frame)

            if smart:
                if self.core.confirmed:
                    for idx, buf in ring:
                        if idx not in saved:
                            cv2.imwrite(str(jpg_dir / f"ctx_{idx:04d}.jpg"), buf,
                                        [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                            saved.add(idx)
                            jpg_count += 1
                    ring.clear()
                    if fi not in saved:
                        k0 = self.core.confirmed[0][0]
                        cv2.imwrite(str(jpg_dir / f"anomalie_{fi:04d}_{k0}.jpg"), frame,
                                    [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                        saved.add(fi)
                        jpg_count += 1
                else:
                    ring.append((fi, frame.copy()))
                    if len(ring) > 5:
                        ring.pop(0)
            else:
                cv2.imwrite(str(jpg_dir / f"img_{fi:04d}.jpg"), frame,
                            [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                jpg_count += 1

            self.latest = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.root.after(0, lambda fi=fi, tot=len(files), e=e, p=path.name:
                            self._status(fi, tot, e, p))

        writer.release()
        self.root.after(0, lambda: self._log(f"✅ Terminé: {out}"))
        self.root.after(0, lambda: self._log(f"📷 {jpg_count} JPEG dans {jpg_dir}"))
        self.root.after(0, lambda: self.status_label.config(text="✅ Scan terminé — interface prête"))
        self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))

    def _refresh(self):
        if self.latest is not None:
            img = Image.fromarray(self.latest)
            img.thumbnail((960, 540))
            self.photo = ImageTk.PhotoImage(img)
            self.preview.config(image=self.photo, text="")
        self.root.after(33, self._refresh)

    def _on_close(self):
        self.stop_flag = True
        self.root.destroy()


def main():
    try:
        LidarApp()
    except Exception as e:
        import traceback
        print(f"❌ Erreur critique: {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()