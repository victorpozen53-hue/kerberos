#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👁️ ARGOS VISION v1.0 — module de scan JPEG de la flotte ARGOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3
Décortique des JPEG et cherche : AVION, BATEAU, VOITURE, CAMION, OVNI
Trois cerveaux :
1. YOLO (si ultralytics installé) -> avion/voiture/camion/bateau
2. Grammaire géométrique : croix=avion, rectangles=voiture/camion,
   allongé-sur-l'eau=bateau
3. Détecteur OVNI : disque rond (circularité >= 0.85) + brillance
   métallique -> OVNI (l'humain reste le juge final)
Héritage du LiDAR d'origine : nuage de points cyan "classe".
Cibles sauvegardées dans ../img/cibles/ (la maison ARGOS).
Usage : python argos_scanner.py   OU   bouton module dans ARGOS (run())
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
except ImportError as e:
    print("❌ Pillow manquant:", e)
    input("Appuyez sur Entrée...")
    sys.exit(1)

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except Exception:
    HAS_YOLO = False

# --- Maison ARGOS (le module vit dans modules/, la maison est au-dessus) ---
ARGOS_ROOT = Path(__file__).resolve().parent.parent
CIBLES_DIR = ARGOS_ROOT / "img" / "cibles"
CIBLES_DIR.mkdir(parents=True, exist_ok=True)

EXTS = (".jpg", ".jpeg", ".png")
JPEG_QUALITY = 90
MAX_POINTS = 1500

LABELS = {
    "AVION": (255, 255, 255),
    "BATEAU": (255, 255, 0),
    "VOITURE": (0, 255, 255),
    "CAMION": (0, 165, 255),
    "OVNI": (255, 0, 255),
}
YOLO_MAP = {2: "VOITURE", 4: "AVION", 5: "CAMION", 7: "CAMION", 8: "BATEAU"}


class VisionCore:
    """Le cerveau : eau, géométrie, OVNI, YOLO, nuage cyan."""

    def __init__(self):
        self.yolo = None
        if HAS_YOLO:
            try:
                self.yolo = YOLO("yolov8n.pt")
            except Exception:
                self.yolo = None

    @staticmethod
    def _water_mask(hsv):
        h, s, v = cv2.split(hsv)
        return ((h >= 90) & (h <= 130) & (s >= 40) & (v >= 40)).astype(np.uint8) * 255

    @staticmethod
    def _veg_mask(hsv):
        h, s, v = cv2.split(hsv)
        m = ((h >= 30) & (h <= 90) & (s >= 40) & (v >= 40)).astype(np.uint8) * 255
        return cv2.dilate(m, np.ones((3, 3), np.uint8))

    def classify_geo(self, cnt, water, gray):
        area = cv2.contourArea(cnt)
        if not (40 < area < 6000):
            return None
        per = cv2.arcLength(cnt, True)
        if per == 0:
            return None
        circ = 4 * math.pi * area / (per * per)
        x, y, w, h = cv2.boundingRect(cnt)
        ar = float(w) / max(1, h)
        hull = cv2.convexHull(cnt)
        ha = cv2.contourArea(hull)
        sol = area / ha if ha else 0
        roi_w = water[y:y + h, x:x + w]
        wf = float((roi_w > 0).mean()) if roi_w.size else 0.0

        if wf > 0.5 and (ar >= 2.0 or (sol > 0.5 and area > 200)):
            return "BATEAU"
        if circ >= 0.85 and 0.7 <= ar <= 1.3:
            m_v = float(gray[y:y + h, x:x + w].mean())
            if m_v > 170:
                return "OVNI"
            return None
        if sol < 0.6 and wf < 0.5:
            return "AVION"
        approx = cv2.approxPolyDP(cnt, 0.04 * per, True)
        if len(approx) == 4 or sol > 0.8:
            if 1.2 < ar <= 2.5:
                return "VOITURE"
            if 2.5 < ar <= 7.0:
                return "CAMION"
        return None

    def process(self, frame):
        hits = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        water = self._water_mask(hsv)
        veg = self._veg_mask(hsv)
        structure = cv2.bitwise_and(cv2.Canny(gray, 60, 140), cv2.bitwise_not(veg))

        # nuage cyan hérité du LiDAR d'origine
        ys, xs = np.nonzero(structure)
        n = len(xs)
        if n > MAX_POINTS:
            idx = np.random.choice(n, MAX_POINTS, replace=False)
            xs, ys = xs[idx], ys[idx]
            n = MAX_POINTS
        if n:
            frame[ys, xs] = (0, 255, 204)

        # cerveau 2 : géométrie + eau + OVNI
        closed = cv2.morphologyEx(structure, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            label = self.classify_geo(c, water, gray)
            if label:
                hits.append((label, cv2.boundingRect(c)))

        # cerveau 1 : YOLO
        if self.yolo is not None:
            try:
                for r in self.yolo.predict(frame, verbose=False, conf=0.35):
                    for b in r.boxes:
                        c = int(b.cls[0])
                        if c in YOLO_MAP:
                            x1, y1, x2, y2 = map(int, b.xyxy[0])
                            hits.append((YOLO_MAP[c], (x1, y1, x2 - x1, y2 - y1)))
            except Exception:
                pass

        # marquage
        for label, (x, y, w, h) in hits:
            color = LABELS.get(label, (80, 80, 255))
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            if label == "OVNI":
                cxm, cym = x + w // 2, y + h // 2
                cv2.line(frame, (cxm - 14, cym), (cxm + 14, cym), color, 2)
                cv2.line(frame, (cxm, cym - 14), (cxm, cym + 14), color, 2)
            cv2.putText(frame, label, (x, max(12, y - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return frame, hits


class VisionApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("👁️ ARGOS VISION v1.0 — scan JPEG (avions/bateaux/voitures/camions/ovnis)")
        self.root.geometry("1000x800")
        self.root.configure(bg=self.BG)
        self.source = None
        self.core = None
        self.stop_flag = False
        self.latest = None
        self.photo = None
        self.counts = {}
        self._build()
        self._refresh()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._log("👁️ ARGOS VISION prêt — YOLO: " + ("actif" if HAS_YOLO else "absent (géométrie seule)"))
        self._log(f"📂 Cibles -> {CIBLES_DIR}")
        self.root.mainloop()

    def _build(self):
        tk.Label(self.root, text="👁️ ARGOS VISION v1.0", bg=self.BG2, fg=self.CY,
                 font=("Consolas", 16, "bold")).pack(fill=tk.X, pady=8)
        vf = tk.Frame(self.root, bg=self.BG)
        vf.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(vf, text="🖼️ Source:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.src_var = tk.StringVar()
        tk.Entry(vf, textvariable=self.src_var, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(vf, text="📂 Dossier", bg=self.BTN, fg=self.WH,
                  command=self._browse).pack(side=tk.LEFT, padx=2)

        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=5)
        self.btn_start = tk.Button(bf, text="▶️ Scanner", bg='#4CAF50', fg=self.WH,
                                   font=("Consolas", 12, "bold"), command=self._start)
        self.btn_start.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.btn_stop = tk.Button(bf, text="⏹️ Stop", bg='#ff5252', fg=self.WH,
                                  font=("Consolas", 12, "bold"), command=self._stop,
                                  state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.preview = tk.Label(self.root, bg=self.BG, text="⏳ Choisis un dossier de JPEG…",
                                fg=self.CY, font=("Consolas", 12))
        self.preview.pack(padx=10, pady=5)

        self.status = tk.Label(self.root, text="⏳ Prêt", bg=self.BG, fg=self.OR,
                               font=("Consolas", 10))
        self.status.pack(pady=2)

        self.log = tk.Text(self.root, height=9, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _browse(self):
        try:
            p = filedialog.askdirectory(title="Choisis le dossier de JPEG")
            if p:
                self.source = Path(p)
                self.src_var.set(p)
        except Exception as e:
            self._log(f"❌ browse: {e}")

    def _log(self, msg):
        try:
            self.log.configure(state='normal')
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state='disabled')
        except Exception:
            pass

    def _start(self):
        try:
            if self.source is None or not self.source.exists():
                messagebox.showerror("Erreur", "Choisis d'abord un dossier de JPEG")
                return
            self.stop_flag = False
            self.counts = {}
            self.btn_start.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            threading.Thread(target=self._scan, daemon=True).start()
        except Exception as e:
            self._log(f"❌ start: {e}")

    def _stop(self):
        self.stop_flag = True

    def _scan(self, src=None):
        try:
            src = src or self.source
            files = sorted([p for p in src.glob("*.*") if p.suffix.lower() in EXTS])
            if not files:
                self.root.after(0, lambda: messagebox.showerror("Erreur", "Aucun JPEG lisible"))
                return
            self.core = VisionCore()
            self.root.after(0, lambda: self._log(f"▶️ Scan de {len(files)} JPEG…"))
            for i, p in enumerate(files):
                if self.stop_flag:
                    break
                frame = cv2.imread(str(p))
                if frame is None:
                    continue
                frame, hits = self.core.process(frame)
                if hits:
                    cv2.imwrite(str(CIBLES_DIR / f"vision_{p.stem}.jpg"), frame,
                                [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                for label, _ in hits:
                    self.counts[label] = self.counts.get(label, 0) + 1
                self.latest = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                summary = ", ".join(f"{k}:{v}" for k, v in sorted(self.counts.items())) or "rien"
                self.root.after(0, lambda i=i, t=len(files), p=p, hh=len(hits):
                                self.status.config(text=f"🖼️ {i + 1}/{t} — {p.name} — {hh} détection(s)"))
                if hits:
                    self.root.after(0, lambda p=p, hs=hits: self._log(
                        f"🎯 {p.name}: " + ", ".join(l for l, _ in hs)))
            self.root.after(0, lambda: self._log("✅ Scan terminé — bilan: " +
                        (", ".join(f"{k}={v}" for k, v in sorted(self.counts.items())) or "aucune cible")))
            self.root.after(0, lambda: self.status.config(text="✅ Scan terminé"))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ scan: " + str(e)))
        finally:
            self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))

    def _refresh(self):
        try:
            if self.latest is not None:
                img = Image.fromarray(self.latest)
                img.thumbnail((960, 540))
                self.photo = ImageTk.PhotoImage(img)
                self.preview.config(image=self.photo, text="")
        except Exception:
            pass
        self.root.after(33, self._refresh)

    def _on_close(self):
        self.stop_flag = True
        self.root.destroy()


def run():
    """Point d'entrée module ARGOS (cortex)."""
    VisionApp()
    return "✅ ARGOS VISION fermé proprement"


def main():
    try:
        VisionApp()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()