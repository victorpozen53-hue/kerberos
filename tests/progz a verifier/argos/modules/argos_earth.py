#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👁️ ARGOS ORBITAL v2.1 — MONOLITHE (une seule fenêtre, zéro module parasite)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3
TOUT en onglets dans l'engine : VISION / OVNI / SANCTUAIRE / EARTH /
TIMELAPSE / RAPPORTS. Plus aucune fenêtre module qui prend le dessus.
🫀 cœur + 🔐 ADN + 🧬 thymus conservés. modules/ reste pour l'avenir
(uniquement organes sans GUI).
"""
import sys
import re
import math
import time
import json
import shutil
import logging
import subprocess
import threading
import traceback
import importlib.util
import webbrowser
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext


def _excepthook(t, v, tb):
    print("❌ ERREUR CRITIQUE:\n" + "".join(traceback.format_exception(t, v, tb)))
    input("Appuyez sur Entrée pour fermer...")


sys.excepthook = _excepthook

try:
    import cv2
    import numpy as np
except ImportError:
    print("❌ pip install opencv-python numpy")
    input("Appuyez sur Entrée...")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False
try:
    import psutil
    HAS_PSUTIL = True
except Exception:
    HAS_PSUTIL = False
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except Exception:
    HAS_YOLO = False
try:
    import pyautogui as pag
    HAS_PAG = True
    pag.FAILSAFE = True
except Exception:
    HAS_PAG = False
try:
    import mss
    HAS_MSS = True
except Exception:
    HAS_MSS = False

# === 🏗️ MAISON =============================================================
ARGOS_ROOT = Path(__file__).resolve().parent
LYMPH = ARGOS_ROOT / "lymph_argos"; PLASMA = LYMPH / "plasma"
MODULES_DIR = ARGOS_ROOT / "modules"; REPORTS_DIR = ARGOS_ROOT / "reports"
IMG_DIR = ARGOS_ROOT / "img"; CIBLES_DIR = IMG_DIR / "cibles"
CROPS_DIR = ARGOS_ROOT / "crops"; DB_DIR = ARGOS_ROOT / "db"
EXPORTS_DIR = ARGOS_ROOT / "exports"; LOGS_DIR = ARGOS_ROOT / "logs"
LOG_FILE = LOGS_DIR / "argos.log"; GENOME = LYMPH / "genome_argos.json"
DOCTRINE = ARGOS_ROOT / "war_doctrine.txt"; SANCT = ARGOS_ROOT / "sanctuaire"
DIRS = {MODULES_DIR: "Organes externes sans GUI", REPORTS_DIR: "Rapports HTML + tree",
        IMG_DIR: "Images auditées", CIBLES_DIR: "Cibles confirmées",
        CROPS_DIR: "Crops vus du ciel", DB_DIR: "Base rotée x8",
        EXPORTS_DIR: "KML + sorties", LOGS_DIR: "Journal",
        LYMPH: "Biologie", PLASMA: "Sauvegardes", SANCT: "PRIVÉ — masques sanctuaire"}
for _d in DIRS:
    _d.mkdir(parents=True, exist_ok=True)
for _d, _desc in DIRS.items():
    _rd = _d / "README.txt"
    if not _rd.exists():
        try:
            _rd.write_text(f"ARGOS — {_d.name}/\n{_desc}\n", encoding="utf-8")
        except Exception:
            pass
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8")])
logger = logging.getLogger("Argos")

_CLOSING = False
_HEART_LOCK = threading.Lock()
EXTS = (".jpg", ".jpeg", ".png")
JPEG_Q = 90
MAX_POINTS = 1500
UI_TOP, UI_LEFT, UI_BOTTOM = 210, 310, 45
MAX_GRID = 400
LABELS = {"AVION": (255, 255, 255), "BATEAU": (255, 255, 0), "VOITURE": (0, 255, 255),
          "CAMION": (0, 165, 255), "OVNI": (255, 0, 255), "BOUEE": (0, 255, 0)}
YOLO_MAP = {2: "VOITURE", 4: "AVION", 5: "CAMION", 7: "CAMION", 8: "BATEAU"}
DEFAULT_DOCTRINE = """# forme;label;couleur
triangle;CHASSEUR DELTA;orange
rectangle;CAMION;jaune
carre;TANK;magenta
croix;AVION COMMERCIAL;blanc
x;HELICO;cyan
rond;DOME/RADAR;rouge
ligne;PISTE/ROUTE;rouge_sombre
"""
COLOR_NAMES = {"jaune": (0, 255, 255), "orange": (0, 165, 255), "magenta": (255, 0, 255),
               "blanc": (255, 255, 255), "rouge": (0, 0, 255), "rouge_sombre": (80, 80, 255),
               "cyan": (255, 255, 0), "vert": (0, 255, 0)}
GE_CANDIDATES = [Path(r"C:\Program Files\Google\GoogleEarthPro\client\googleearth.exe"),
                 Path(r"C:\Program Files (x86)\Google\GoogleEarthPro\client\googleearth.exe"),
                 Path.home() / "AppData" / "Local" / "Google" / "GoogleEarthPro" / "client" / "googleearth.exe"]


# === 🫀🔐 BIOLOGIE ==========================================================
def _my_dna():
    try:
        import hashlib
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except Exception:
        return "0" * 64


def _thymus_cycle():
    try:
        if DOCTRINE.exists():
            shutil.copy2(DOCTRINE, PLASMA / "war_doctrine.plasma")
            return "doctrine sauvegardée dans le plasma"
        b = PLASMA / "war_doctrine.plasma"
        if b.exists():
            shutil.copy2(b, DOCTRINE)
            return "doctrine RÉGÉNÉRÉE depuis le plasma"
        DOCTRINE.write_text(DEFAULT_DOCTRINE, encoding="utf-8")
        return "doctrine créée"
    except Exception as e:
        return f"thymus: {e}"


def _dna_pulse():
    if _CLOSING:
        return
    try:
        cur = _my_dna()
        g = json.loads(GENOME.read_text(encoding="utf-8")) if GENOME.exists() else {}
        if g.get("argos_dna") != cur:
            g["argos_dna"] = cur
            g["last_pulse"] = time.time()
            GENOME.write_text(json.dumps(g, indent=2), encoding="utf-8")
    except Exception:
        pass
    threading.Timer(60.0, _dna_pulse).start()


def _safe(app, fn):
    try:
        if app is not None and app.root.winfo_exists():
            app.root.after(0, fn)
    except Exception:
        pass


def _start_heart(app):
    def systole():
        if _CLOSING:
            return
        with _HEART_LOCK:
            cpu = psutil.cpu_percent(interval=None) if HAS_PSUTIL else 0.0
            _safe(app, lambda: app.update_heartbeat(f"💗 SYSTOLE • CPU {cpu:.0f}%"))
        threading.Timer(3.0, diastole).start()

    def diastole():
        if _CLOSING:
            return
        with _HEART_LOCK:
            ram = psutil.virtual_memory().percent if HAS_PSUTIL else 0.0
            _safe(app, lambda: app.update_heartbeat(f"🫀 DIASTOLE • RAM {ram:.0f}%"))
        threading.Timer(4.0, pause).start()

    def pause():
        if _CLOSING:
            return
        with _HEART_LOCK:
            _safe(app, lambda: app.update_heartbeat("🫁 PAUSE • respiration orbitale…"))
        threading.Timer(3.0, systole).start()

    threading.Timer(2.0, systole).start()


# === 📖 DOCTRINE ============================================================
def _parse_doctrine(text):
    rules = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(";")]
        if len(parts) < 2 or not parts[0] or not parts[1]:
            continue
        color = (80, 80, 255)
        if len(parts) >= 3 and parts[2]:
            c = parts[2]
            if c in COLOR_NAMES:
                color = COLOR_NAMES[c]
            elif "," in c:
                try:
                    b, g, r = [int(x) for x in c.split(",")]
                    color = (b, g, r)
                except Exception:
                    pass
        rules[parts[0].lower()] = (parts[1], color)
    return rules


def load_doctrine():
    if not DOCTRINE.exists():
        try:
            DOCTRINE.write_text(DEFAULT_DOCTRINE, encoding="utf-8")
        except Exception:
            pass
    try:
        text = DOCTRINE.read_text(encoding="utf-8")
    except Exception:
        text = DEFAULT_DOCTRINE
    return _parse_doctrine(text) or _parse_doctrine(DEFAULT_DOCTRINE)


# === 👁️ VISION ===============================================================
class VisionCore:
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
        bright = (h >= 85) & (h <= 135) & (s >= 25) & (v >= 25)
        dark = (h >= 85) & (h <= 135) & (v < 60) & (s >= 10)
        return (bright | dark).astype(np.uint8) * 255

    @staticmethod
    def _veg_mask(hsv):
        h, s, v = cv2.split(hsv)
        m = ((h >= 30) & (h <= 90) & (s >= 40) & (v >= 40)).astype(np.uint8) * 255
        return cv2.dilate(m, np.ones((3, 3), np.uint8))

    def classify_geo(self, cnt, water, hsv, gray):
        area = cv2.contourArea(cnt)
        per = cv2.arcLength(cnt, True)
        if per == 0:
            return None
        x, y, w, h = cv2.boundingRect(cnt)
        ar = float(w) / max(1, h)
        H, W = water.shape
        X0, Y0 = max(0, x - 2 * w), max(0, y - 2 * h)
        X1, Y1 = min(W, x + 3 * w), min(H, y + 3 * h)
        ctx = water[Y0:Y1, X0:X1]
        cf = float((ctx > 0).mean()) if ctx.size else 0.0
        in_sea = cf > 0.6
        if in_sea and 15 < area < 900 and 0.4 <= ar <= 2.5:
            roi = hsv[y:y + h, x:x + w]
            if roi.size:
                mh = float(roi[:, :, 0].mean()); ms = float(roi[:, :, 1].mean()); mv = float(roi[:, :, 2].mean())
                red = (mh <= 12 or mh >= 168) and ms > 90 and mv > 110
                yellow = (15 <= mh <= 35) and ms > 110 and mv > 140
                if red or yellow:
                    return "BOUEE"
        if not (40 < area < 6000):
            return None
        circ = 4 * math.pi * area / (per * per)
        hull = cv2.convexHull(cnt)
        ha = cv2.contourArea(hull)
        sol = area / ha if ha else 0
        roi_w = water[y:y + h, x:x + w]
        wf = float((roi_w > 0).mean()) if roi_w.size else 0.0
        if in_sea or wf > 0.5:
            return "BATEAU" if (ar >= 2.0 or sol > 0.4) else None
        if circ >= 0.85 and 0.7 <= ar <= 1.3:
            if float(gray[y:y + h, x:x + w].mean()) > 170:
                return "OVNI"
            return None
        if sol < 0.6:
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
        structure = cv2.bitwise_and(cv2.Canny(gray, 60, 140), cv2.bitwise_not(self._veg_mask(hsv)))
        structure[:UI_TOP, :] = 0
        structure[:, :UI_LEFT] = 0
        if UI_BOTTOM:
            structure[-UI_BOTTOM:, :] = 0
        ys, xs = np.nonzero(structure)
        n = len(xs)
        if n > MAX_POINTS:
            idx = np.random.choice(n, MAX_POINTS, replace=False)
            xs, ys = xs[idx], ys[idx]
            n = MAX_POINTS
        if n:
            frame[ys, xs] = (0, 255, 204)
        closed = cv2.morphologyEx(structure, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            label = self.classify_geo(c, water, hsv, gray)
            if label:
                hits.append((label, cv2.boundingRect(c)))
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
        for label, (x, y, w, h) in hits:
            color = LABELS.get(label, (80, 80, 255))
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            if label in ("OVNI", "BOUEE"):
                cxm, cym = x + w // 2, y + h // 2
                cv2.line(frame, (cxm - 12, cym), (cxm + 12, cym), color, 2)
                cv2.line(frame, (cxm, cym - 12), (cxm, cym + 12), color, 2)
            cv2.putText(frame, label, (x, max(12, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return frame, hits


# === 🛸 OVNI (disques) =======================================================
def detect_disc(frame):
    hits = []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    v = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)[:, :, 2]
    closed = cv2.morphologyEx(cv2.Canny(gray, 60, 140), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
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
        if (ring_v > core_v + 20) or (core_v > 190 and ring_v < core_v - 25) or circ >= 0.9:
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


# === 🌍 EARTH ================================================================
def parse_coord(s):
    s = s.strip()
    if not s:
        return None
    m = re.match(r"^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.match(r"^(\d+)°(\d+)'([\d.]+)\"?\s*([NSns])[,;\s]+(\d+)°(\d+)'([\d.]+)\"?\s*([EWOewo])$", s)
    if m:
        lat = int(m.group(1)) + int(m.group(2)) / 60.0 + float(m.group(3)) / 3600.0
        if m.group(4).upper() == "S":
            lat = -lat
        lon = int(m.group(5)) + int(m.group(6)) / 60.0 + float(m.group(7)) / 3600.0
        if m.group(8).upper() in ("W", "O"):
            lon = -lon
        return lat, lon
    return None


def build_kml(points, range_m, dwell_s):
    items = []
    for lat, lon in points:
        items.append("      <gx:FlyTo><gx:duration>5.0</gx:duration><gx:flyToMode>bounce</gx:flyToMode>"
                     f"<LookAt><longitude>{lon:.6f}</longitude><latitude>{lat:.6f}</latitude>"
                     f"<altitude>0</altitude><range>{range_m}</range><tilt>0</tilt><heading>0</heading>"
                     "<altitudeMode>relativeToGround</altitudeMode></LookAt></gx:FlyTo>"
                     f"<gx:Wait><gx:duration>{dwell_s}</gx:duration></gx:Wait>")
    head = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<kml xmlns=\"http://www.opengis.net/kml/2.2\" "
            "xmlns:gx=\"http://www.google.com/kml/ext/2.2\">\n<Document>\n<name>ARGOS TOUR</name>\n"
            "<gx:Tour><name>Argos Flyover</name>\n<gx:Playlist>\n")
    return head + "\n".join(items) + "\n</gx:Playlist>\n</gx:Tour>\n</Document>\n</kml>\n"


def build_grid(c1, c2, step_m):
    lat_min, lat_max = min(c1[0], c2[0]), max(c1[0], c2[0])
    lon_min, lon_max = min(c1[1], c2[1]), max(c1[1], c2[1])
    dlat = step_m / 111320.0
    pts, lat, flip = [], lat_max, False
    while lat >= lat_min and len(pts) < MAX_GRID:
        cosl = max(0.2, math.cos(math.radians((lat_min + lat_max) / 2.0)))
        dlon = step_m / (111320.0 * cosl)
        lons, lon = [], lon_min
        while lon <= lon_max:
            lons.append(lon)
            lon += dlon
        if flip:
            lons.reverse()
        pts.extend((lat, lo) for lo in lons)
        flip = not flip
        lat -= dlat
    return pts


def find_ge():
    for p in GE_CANDIDATES:
        if p.exists():
            return p
    return None


# === 📊 RAPPORTS =============================================================
def build_tree():
    lines = ["ARGOS_ORBITAL/"]
    items = list(DIRS.items())
    for i, (d, desc) in enumerate(items):
        branch = "└──" if i == len(items) - 1 else "├──"
        n = len([p for p in d.glob("*") if p.is_file()]) if d.exists() else 0
        lines.append(f"{branch} {d.name}/ ({n} fichiers) — {desc}")
    return "\n".join(lines)


def generate_html_report(cb):
    now = datetime.now()
    path = REPORTS_DIR / f"argos_report_{now.strftime('%Y%m%d_%H%M%S')}.html"
    css = ("body{background:#0a0f14;color:#e0e0e0;font-family:Consolas,monospace;}"
           "header{background:#16213e;padding:20px 30px;border-bottom:2px solid #00ffcc;}"
           "h1{color:#00ffcc;margin:0;}h2{color:#ffb347;}"
           ".card{background:#141a20;margin:15px 30px;padding:15px 20px;border-left:3px solid #00ffcc;}"
           "pre{color:#7fdbca;}footer{padding:15px 30px;color:#667;font-size:12px;}")
    doc = load_doctrine()
    cibles = sorted(CIBLES_DIR.glob("*.*"))[-10:]
    html = ["<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>",
            "<title>ARGOS</title><style>" + css + "</style></head><body>",
            f"<header><h1>👁️ ARGOS v2.1 — RAPPORT</h1><div>{now.strftime('%d/%m/%Y %H:%M')}</div></header>",
            f"<div class='card'><h2>🔐 ADN</h2><pre>{_my_dna()}</pre></div>",
            "<div class='card'><h2>📖 Doctrine</h2><pre>" +
            "\n".join(f"{k} -> {v[0]}" for k, v in doc.items()) + "</pre></div>",
            "<div class='card'><h2>🎯 Cibles</h2><pre>" +
            ("\n".join(c.name for c in cibles) or "aucune") + "</pre></div>",
            "<div class='card'><h2>🌳 Maison</h2><pre>" + build_tree() + "</pre></div>",
            "<footer>GPLv3 • Victor Pozen</footer></body></html>"]
    path.write_text("\n".join(html), encoding="utf-8")
    if cb:
        cb(f"📊 Rapport: {path.name}")
    return path


# === 🖥️ MOTEUR MONOLITHE ======================================================
class ArgosEngine:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("👁️ ARGOS ORBITAL v2.1 — MONOLITHE")
        self.root.geometry("1100x840")
        self.root.configure(bg=self.BG)
        self.core = None
        self.stop_flag = False
        self.stop_ovni = False
        self.stop_pilot = False
        self.latest = None
        self.photo = None
        self.latest_ovni = None
        self.photo_ovni = None
        self.points = []
        self.calib = None
        self._build()
        self._refresh()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._log("👁️ ARGOS v2.1 MONOLITHE — une seule fenêtre, tout en onglets")
        self._log("🧬 Thymus: " + _thymus_cycle())
        _start_heart(self)
        _dna_pulse()
        self.root.mainloop()

    def _build(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._tab_vision(nb)
        self._tab_ovni(nb)
        self._tab_sanct(nb)
        self._tab_earth(nb)
        self._tab_timelapse(nb)
        self._tab_rapports(nb)
        self.status = tk.Label(self.root, text="⏳ Prêt", bg=self.BG, fg=self.OR, font=("Consolas", 10))
        self.status.pack(pady=2)
        self.log = tk.Text(self.root, height=6, bg=self.BG2, fg='#4CAF50', font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.heartbeat_label = tk.Label(self.root, text="🫀 Cœur orbital", bg='#16213e', fg=self.CY,
                                        font=("Consolas", 11, "bold"))
        self.heartbeat_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

    def _log(self, msg):
        try:
            self.log.configure(state='normal')
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state='disabled')
        except Exception:
            pass

    def update_heartbeat(self, m):
        try:
            if self.root.winfo_exists() and not _CLOSING:
                self.heartbeat_label.config(text=f"🫀 {m}")
        except Exception:
            pass

    # --- 👁️ VISION ---
    def _tab_vision(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text=' 👁️ VISION ')
        f = tk.Frame(t, bg=self.BG)
        f.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f, text="🖼️ Source:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.src_var = tk.StringVar()
        tk.Entry(f, textvariable=self.src_var, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="📂", bg=self.BTN, fg=self.WH, command=self._browse).pack(side=tk.LEFT)
        b = tk.Frame(t, bg=self.BG)
        b.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(b, text="▶️ Scanner", bg='#4CAF50', fg=self.WH, font=("Consolas", 11, "bold"),
                  command=self._start_scan).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(b, text="⏹️", bg='#ff5252', fg=self.WH, command=self._stop_scan).pack(side=tk.LEFT, padx=5)
        self.preview = tk.Label(t, bg=self.BG, text="⏳ aperçu VISION…", fg=self.CY, font=("Consolas", 11))
        self.preview.pack(padx=10, pady=5)

    def _browse(self):
        p = filedialog.askdirectory(title="Dossier JPEG")
        if p:
            self.src_var.set(p)

    def _start_scan(self):
        src = Path(self.src_var.get())
        if not src.exists():
            messagebox.showerror("Erreur", "Choisis un dossier")
            return
        self.stop_flag = False
        threading.Thread(target=self._scan, args=(src,), daemon=True).start()

    def _stop_scan(self):
        self.stop_flag = True

    def _scan(self, src):
        try:
            files = sorted([p for p in src.glob("*.*") if p.suffix.lower() in EXTS])
            self.core = VisionCore()
            counts = {}
            for i, p in enumerate(files):
                if self.stop_flag:
                    break
                frame = cv2.imread(str(p))
                if frame is None:
                    continue
                frame, hits = self.core.process(frame)
                if hits:
                    cv2.imwrite(str(CIBLES_DIR / f"vision_{p.stem}.jpg"), frame,
                                [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_Q])
                for label, _ in hits:
                    counts[label] = counts.get(label, 0) + 1
                self.latest = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.root.after(0, lambda i=i, t=len(files), p=p, hh=len(hits):
                                self.status.config(text=f"👁️ {i + 1}/{t} — {p.name} — {hh}"))
            self.root.after(0, lambda: self._log("✅ VISION: " +
                        (", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "rien")))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ " + str(e)))

    # --- 🛸 OVNI ---
    def _tab_ovni(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text=' 🛸 OVNI ')
        f = tk.Frame(t, bg=self.BG)
        f.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f, text="🖼️ Source:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.ovni_src = tk.StringVar()
        tk.Entry(f, textvariable=self.ovni_src, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="📂", bg=self.BTN, fg=self.WH, command=self._ovni_browse).pack(side=tk.LEFT)
        b = tk.Frame(t, bg=self.BG)
        b.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(b, text="▶️ Chercher", bg='#4CAF50', fg=self.WH, font=("Consolas", 11, "bold"),
                  command=self._start_ovni).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(b, text="⏹️", bg='#ff5252', fg=self.WH, command=self._stop_ovni_f).pack(side=tk.LEFT, padx=5)
        tk.Label(t, text="🕊️ les zones sanctuaire sont détectées en silence, jamais divulguées",
                 bg=self.BG, fg='#4CAF50', font=("Consolas", 9)).pack(pady=2)
        self.prev_ovni = tk.Label(t, bg=self.BG, text="⏳ aperçu OVNI…", fg=self.CY, font=("Consolas", 11))
        self.prev_ovni.pack(padx=10, pady=5)

    def _ovni_browse(self):
        p = filedialog.askdirectory(title="Dossier JPEG")
        if p:
            self.ovni_src.set(p)

    def _start_ovni(self):
        src = Path(self.ovni_src.get())
        if not src.exists():
            messagebox.showerror("Erreur", "Choisis un dossier")
            return
        self.stop_ovni = False
        threading.Thread(target=self._scan_ovni, args=(src,), daemon=True).start()

    def _stop_ovni_f(self):
        self.stop_ovni = True

    def _scan_ovni(self, src):
        try:
            files = sorted([p for p in src.glob("*.*") if p.suffix.lower() in EXTS])
            found, protected = 0, 0
            for p in files:
                if self.stop_ovni:
                    break
                frame = cv2.imread(str(p))
                if frame is None:
                    continue
                keep = []
                for (x, y, w, h) in detect_disc(frame):
                    if in_sanctuaire(p.stem, x + w // 2, y + h // 2):
                        protected += 1
                        self.root.after(0, lambda p=p: self._log(f"🕊️ {p.name}: signature protégée — NON divulguée"))
                    else:
                        keep.append((x, y, w, h))
                for (x, y, w, h) in keep:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
                    cv2.putText(frame, "OVNI", (x, max(12, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
                if keep:
                    found += len(keep)
                    cv2.imwrite(str(CIBLES_DIR / f"ovni_{p.stem}.jpg"), frame)
                self.latest_ovni = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.root.after(0, lambda: self._log(f"🛸 Fin: {found} publique(s), {protected} protégée(s)"))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ " + str(e)))

    # --- 🕊️ SANCTUAIRE ---
    def _tab_sanct(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text=' 🕊️ SANCTUAIRE ')
        f = tk.Frame(t, bg=self.BG)
        f.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f, text="🖼️ Image:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.sanct_src = tk.StringVar()
        tk.Entry(f, textvariable=self.sanct_src, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="📂", bg=self.BTN, fg=self.WH, command=self._sanct_browse).pack(side=tk.LEFT)
        b = tk.Frame(t, bg=self.BG)
        b.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(b, text="🎯 Dessiner zone", bg='#4CAF50', fg=self.WH, font=("Consolas", 11, "bold"),
                  command=self._draw_zone).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        tk.Button(b, text="🕊️ Voiler exports", bg=self.BTN, fg=self.WH, font=("Consolas", 11, "bold"),
                  command=self._veil).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        tk.Label(t, text="PRIVÉ — les masques restent sur cette machine, jamais partagés",
                 bg=self.BG, fg=self.OR, font=("Consolas", 9)).pack(pady=5)

    def _sanct_browse(self):
        p = filedialog.askopenfilename(title="Image", filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if p:
            self.sanct_src.set(p)

    def _draw_zone(self):
        src = Path(self.sanct_src.get())
        if not src.exists():
            messagebox.showerror("Erreur", "Choisis une image")
            return
        threading.Thread(target=self._draw_worker, args=(src,), daemon=True).start()

    def _draw_worker(self, src):
        img = cv2.imread(str(src))
        if img is None:
            return
        mask = np.zeros(img.shape[:2], np.uint8)
        state = {"c": None, "r": 0}
        win = "SANCTUAIRE — clique-glisse, ENTREE valide, ESC annule"

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
            if k == 13 and state["c"] and state["r"] > 3:
                cv2.circle(mask, state["c"], state["r"], 255, -1)
                cv2.imwrite(str(SANCT / f"{src.stem}.png"), mask)
                self.root.after(0, lambda: self._log(f"🎯 Sanctuaire LOCAL: {src.stem}.png"))
                break
            if k == 27:
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
            for folder in (CIBLES_DIR, EXPORTS_DIR):
                for imgp in folder.glob(f"{mp.stem}*.*"):
                    if imgp.suffix.lower() not in EXTS:
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
        self.root.after(0, lambda: self._log(f"🕊️ {n} export(s) voilé(s) — rien n'a fui"))

    # --- 🌍 EARTH ---
    def _tab_earth(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text=' 🌍 EARTH ')
        f = tk.Frame(t, bg=self.BG)
        f.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(f, text="🧹 A:", bg=self.BG, fg=self.OR).pack(side=tk.LEFT)
        self.ca = tk.Entry(f, width=18, bg=self.BG2, fg=self.WH)
        self.ca.pack(side=tk.LEFT, padx=3)
        self.ca.insert(0, "27.95, -15.75")
        tk.Label(f, text="B:", bg=self.BG, fg=self.OR).pack(side=tk.LEFT)
        self.cb = tk.Entry(f, width=18, bg=self.BG2, fg=self.WH)
        self.cb.pack(side=tk.LEFT, padx=3)
        self.cb.insert(0, "27.80, -15.55")
        tk.Label(f, text="Pas:", bg=self.BG, fg=self.OR).pack(side=tk.LEFT, padx=(8, 0))
        self.step_var = tk.IntVar(value=2000)
        tk.Scale(f, from_=200, to=10000, resolution=100, orient=tk.HORIZONTAL, variable=self.step_var,
                 bg=self.BG2, fg=self.OR, highlightthickness=0, length=120).pack(side=tk.LEFT, padx=3)
        tk.Button(f, text="🧹 GRID", bg=self.BTN, fg=self.WH, command=self._gen_grid).pack(side=tk.LEFT, padx=5)
        self.coords_txt = tk.Text(t, height=4, bg=self.BG2, fg=self.WH, font=("Consolas", 10))
        self.coords_txt.pack(fill=tk.X, padx=10, pady=5)
        r = tk.Frame(t, bg=self.BG)
        r.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(r, text="🛰️ Alt:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.range_var = tk.IntVar(value=2000)
        tk.Scale(r, from_=300, to=20000, resolution=100, orient=tk.HORIZONTAL, variable=self.range_var,
                 bg=self.BG2, fg=self.CY, highlightthickness=0, length=140).pack(side=tk.LEFT, padx=3)
        tk.Label(r, text="⏱️:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.dwell_var = tk.IntVar(value=6)
        tk.Scale(r, from_=3, to=20, orient=tk.HORIZONTAL, variable=self.dwell_var,
                 bg=self.BG2, fg=self.CY, highlightthickness=0, length=90).pack(side=tk.LEFT, padx=3)
        b = tk.Frame(t, bg=self.BG)
        b.pack(fill=tk.X, padx=10, pady=3)
        tk.Button(b, text="🎯 Calibrer", bg=self.BTN, fg=self.WH, command=self._calibrate).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(b, text="🤖 PILOTE", bg='#4CAF50', fg=self.WH, font=("Consolas", 11, "bold"),
                  command=self._pilot).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(b, text="🎬 KML", bg=self.BTN, fg=self.WH, command=self._gen_kml).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(b, text="🚀 GE", bg=self.BTN, fg=self.WH, command=self._launch_ge).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

    def _read_points(self):
        return [c for c in (parse_coord(l) for l in self.coords_txt.get("1.0", "end-1c").splitlines()) if c]

    def _gen_grid(self):
        a, b = parse_coord(self.ca.get()), parse_coord(self.cb.get())
        if not a or not b:
            messagebox.showerror("Erreur", "Coins invalides")
            return
        pts = build_grid(a, b, self.step_var.get())
        self.coords_txt.delete("1.0", tk.END)
        self.coords_txt.insert("1.0", "\n".join(f"{la:.6f}, {lo:.6f}" for la, lo in pts))
        self.points = pts
        self._log(f"🧹 GRID: {len(pts)} points")

    def _calibrate(self):
        if not HAS_PAG:
            self._log("❌ pip install pyautogui")
            return
        self._log("🎯 Souris sur la recherche GE… (5 s)")

        def w():
            time.sleep(5)
            self.calib = pag.position()
            self.root.after(0, lambda: self._log(f"🎯 calibré {self.calib}"))

        threading.Thread(target=w, daemon=True).start()

    def _pilot(self):
        if not HAS_PAG or not HAS_MSS:
            messagebox.showerror("Erreur", "pip install pyautogui mss")
            return
        if self.calib is None:
            messagebox.showerror("Erreur", "Calibre d'abord (🎯)")
            return
        self.points = self._read_points() or self.points
        if not self.points:
            messagebox.showerror("Erreur", "Aucune coordonnée")
            return
        threading.Thread(target=self._pilot_work, daemon=True).start()

    def _pilot_work(self):
        out = EXPORTS_DIR / f"earth_{time.strftime('%Y%m%d_%H%M%S')}"
        out.mkdir(parents=True, exist_ok=True)
        self.root.after(0, lambda: self._log("🤖 GE au premier plan… (5 s)"))
        time.sleep(5)
        idx = 0
        try:
            with mss.mss() as sct:
                for lat, lon in self.points:
                    pag.click(self.calib.x, self.calib.y)
                    time.sleep(0.4)
                    pag.hotkey('ctrl', 'a')
                    pag.write(f"{lat:.6f}, {lon:.6f}", interval=0.02)
                    pag.press('enter')
                    time.sleep(self.dwell_var.get())
                    shot = sct.grab(sct.monitors[1])
                    frame = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
                    cv2.imwrite(str(out / f"img_{idx:04d}.jpg"), frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_Q])
                    idx += 1
                    self.root.after(0, lambda i=idx: self.status.config(text=f"🤖 capture {i}"))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ pilote: " + str(e)))
        self.root.after(0, lambda: self._log(f"✅ Pilote: {idx} captures -> {out.name}"))

    def _gen_kml(self):
        self.points = self._read_points() or self.points
        if len(self.points) < 2:
            messagebox.showerror("Erreur", "2 coords minimum")
            return
        (EXPORTS_DIR / "argos_tour.kml").write_text(
            build_kml(self.points, self.range_var.get(), self.dwell_var.get()), encoding="utf-8")
        self._log("🎬 KML prêt")

    def _launch_ge(self):
        self.points = self._read_points() or self.points
        if len(self.points) < 2:
            messagebox.showerror("Erreur", "2 coords minimum")
            return
        ge = find_ge()
        if ge is None:
            p = filedialog.askopenfilename(title="googleearth.exe", filetypes=[("EXE", "*.exe")])
            if not p:
                return
            ge = Path(p)
        (EXPORTS_DIR / "argos_tour.kml").write_text(
            build_kml(self.points, self.range_var.get(), self.dwell_var.get()), encoding="utf-8")
        subprocess.Popen([str(ge), str(EXPORTS_DIR / "argos_tour.kml")])
        self._log("🚀 GE lancé")

    # --- 🎬 TIMELAPSE ---
    def _tab_timelapse(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text=' 🎬 TIMELAPSE ')
        f = tk.Frame(t, bg=self.BG)
        f.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f, text="📂 Dossier:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.tl_var = tk.StringVar()
        tk.Entry(f, textvariable=self.tl_var, width=55, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="📂", bg=self.BTN, fg=self.WH, command=self._tl_browse).pack(side=tk.LEFT)
        f2 = tk.Frame(t, bg=self.BG)
        f2.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f2, text="🎞️ FPS:", bg=self.BG, fg=self.OR).pack(side=tk.LEFT)
        self.fps_var = tk.IntVar(value=10)
        tk.Scale(f2, from_=1, to=30, orient=tk.HORIZONTAL, variable=self.fps_var,
                 bg=self.BG2, fg=self.OR, highlightthickness=0, length=180).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="🎬 Assembler", bg='#4CAF50', fg=self.WH,
                  font=("Consolas", 11, "bold"), command=self._assemble).pack(side=tk.LEFT, padx=10)

    def _tl_browse(self):
        p = filedialog.askdirectory(title="Dossier JPEG")
        if p:
            self.tl_var.set(p)

    def _assemble(self):
        folder = Path(self.tl_var.get())
        if not folder.exists():
            messagebox.showerror("Erreur", "Dossier introuvable")
            return
        fps = self.fps_var.get()

        def w():
            try:
                files = sorted([p for p in folder.glob("*.*") if p.suffix.lower() in EXTS], key=lambda p: p.name)
                first = cv2.imread(str(files[0]))
                h0, w0 = first.shape[:2]
                out = folder.parent / f"timelapse_{folder.name}_{fps}fps.mp4"
                writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*'mp4v'), fps, (w0, h0))
                done = 0
                for p in files:
                    img = cv2.imread(str(p))
                    if img is None:
                        continue
                    if img.shape[1] != w0 or img.shape[0] != h0:
                        img = cv2.resize(img, (w0, h0))
                    writer.write(img)
                    done += 1
                writer.release()
                self.root.after(0, lambda: self._log(f"🎬 {done} img -> {out.name}"))
            except Exception as e:
                self.root.after(0, lambda e=e: self._log("❌ " + str(e)))

        threading.Thread(target=w, daemon=True).start()

    # --- 📊 RAPPORTS ---
    def _tab_rapports(self, nb):
        t = ttk.Frame(nb)
        nb.add(t, text=' 📊 RAPPORTS ')
        f = tk.Frame(t, bg=self.BG)
        f.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(f, text="📊 HTML", bg='#4CAF50', fg=self.WH, font=("Consolas", 11, "bold"),
                  command=lambda: threading.Thread(target=lambda: generate_html_report(self._log),
                                                   daemon=True).start()).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(f, text="🌳 Tree", bg=self.BTN, fg=self.WH, font=("Consolas", 11, "bold"),
                  command=self._do_tree).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(f, text="📂 reports/", bg=self.BTN, fg=self.WH, font=("Consolas", 11, "bold"),
                  command=self._open_reports).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

    def _do_tree(self):
        tree = build_tree()
        self._log(tree)
        try:
            (REPORTS_DIR / "arborescence.txt").write_text(tree, encoding="utf-8")
        except Exception:
            pass

    def _open_reports(self):
        try:
            import os
            os.startfile(REPORTS_DIR)
        except Exception as e:
            self._log(f"⚠️ {e}")

    def _refresh(self):
        try:
            if self.latest is not None and HAS_PIL:
                img = Image.fromarray(self.latest)
                img.thumbnail((940, 470))
                self.photo = ImageTk.PhotoImage(img)
                self.preview.config(image=self.photo, text="")
            if self.latest_ovni is not None and HAS_PIL:
                img = Image.fromarray(self.latest_ovni)
                img.thumbnail((940, 470))
                self.photo_ovni = ImageTk.PhotoImage(img)
                self.prev_ovni.config(image=self.photo_ovni, text="")
        except Exception:
            pass
        self.root.after(33, self._refresh)

    def _on_close(self):
        global _CLOSING
        _CLOSING = True
        self.stop_flag = True
        self.stop_ovni = True
        logger.info("🛑 ARGOS fermé proprement")
        self.root.destroy()


def run():
    ArgosEngine()
    return "✅ ARGOS v2.1 fermé"


def main():
    try:
        ArgosEngine()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()