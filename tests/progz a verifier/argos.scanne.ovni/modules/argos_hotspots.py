#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛰️ ARGOS HOTSPOTS v1.0 — scanner des zones OVNI connues
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — usage LOCAL, ne jamais partager
- Liste intégrée de hotspots historiques (Roswell, Area 51, Hessdalen,
  Trans-en-Provence, Varginha, Colares/Opération Prato, Skinwalker…)
- ➕ ajoute tes zones (DMS avec O ou décimal) + flag 🕊️ sanctuaire
- 🎯 calibration Google Earth -> 🛰️ scan : vole -> capture -> détection
  (réutilise detect_ufo de argos_ufo.py)
- 🛸 scan hors-ligne sur un dossier de JPEG
- 🕊️ sanctuaire : détection locale, jamais exportée vers cibles/
"""
import sys
import re
import time
import json
import threading
import traceback
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox


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

_p = Path(__file__).resolve().parent
sys.path.insert(0, str(_p))
try:
    import argos_ufo as _ufo
    detect_ufo = _ufo.detect_ufo
    HAS_DETECT = True
except Exception:
    HAS_DETECT = False

ARGOS_ROOT = _p.parent if (_p.parent / "img").exists() or _p.name == "modules" else _p
CIBLES = ARGOS_ROOT / "img" / "cibles"
EXPORTS = ARGOS_ROOT / "exports"
HS_FILE = ARGOS_ROOT / "carnet" / "hotspots.json"
CIBLES.mkdir(parents=True, exist_ok=True)
EXPORTS.mkdir(parents=True, exist_ok=True)
HS_FILE.parent.mkdir(parents=True, exist_ok=True)

# === 🛸 ZONES HISTORIQUES (données publiques) ===============================
DEFAULT_HOTSPOTS = [
    {"name": "roswell_1947", "lat": 33.394, "lon": -104.523, "sanctuaire": False},
    {"name": "area51_groom", "lat": 37.235, "lon": -115.811, "sanctuaire": False},
    {"name": "rendlesham_1980", "lat": 52.093, "lon": 1.352, "sanctuaire": False},
    {"name": "hessdalen_lights", "lat": 62.786, "lon": 11.193, "sanctuaire": False},
    {"name": "varginha_1996", "lat": -21.551, "lon": -45.430, "sanctuaire": False},
    {"name": "trans_provence_1981", "lat": 43.504, "lon": 6.711, "sanctuaire": False},
    {"name": "bonnybridge", "lat": 55.998, "lon": -3.893, "sanctuaire": False},
    {"name": "sedona_vortex", "lat": 34.869, "lon": -111.761, "sanctuaire": False},
    {"name": "skinwalker_ranch", "lat": 40.259, "lon": -109.883, "sanctuaire": False},
    {"name": "colares_prato_1977", "lat": -0.933, "lon": -48.283, "sanctuaire": False},
    {"name": "barranco_perso", "lat": 27.906, "lon": -15.706, "sanctuaire": False},
]


def load_hs():
    try:
        return json.loads(HS_FILE.read_text(encoding="utf-8")) if HS_FILE.exists() else None
    except Exception:
        return None


def save_hs(data):
    HS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


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


class HotspotsApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛰️ ARGOS HOTSPOTS v1.0 — scanner zones OVNI connues")
        self.root.geometry("980x720")
        self.root.configure(bg=self.BG)
        self.calib = None
        self.stop_flag = False
        if not HS_FILE.exists():
            save_hs(DEFAULT_HOTSPOTS)
        self._build()
        self._refresh_list()
        self._log("🛰️ HOTSPOTS prêt — " + ("détection OK" if HAS_DETECT else "⚠️ argos_ufo.py introuvable"))
        self._log("🎯 calibre la recherche GE, puis 🛰️ scan")
        self.root.mainloop()

    def _build(self):
        af = tk.Frame(self.root, bg=self.BG)
        af.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(af, text="🏷️ Nom:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        tk.Entry(af, textvariable=self.name_var, width=16, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=3)
        tk.Label(af, text="📍 Coords:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.coord_var = tk.StringVar()
        tk.Entry(af, textvariable=self.coord_var, width=28, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=3)
        self.sanct_var = tk.BooleanVar(value=False)
        tk.Checkbutton(af, text="🕊️", variable=self.sanct_var, bg=self.BG, fg=self.OR,
                       selectcolor=self.BG2).pack(side=tk.LEFT, padx=3)
        tk.Button(af, text="➕", bg='#4CAF50', fg=self.WH, command=self._add).pack(side=tk.LEFT, padx=3)

        self.listbox = tk.Listbox(self.root, height=10, bg=self.BG2, fg=self.WH,
                                  selectbackground=self.BTN, font=("Consolas", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(bf, text="🗑️", bg='#ff5252', fg=self.WH, command=self._del).pack(side=tk.LEFT, padx=2)
        tk.Button(bf, text="🕊️ Toggle", bg=self.BTN, fg=self.WH, command=self._toggle).pack(side=tk.LEFT, padx=2)
        tk.Button(bf, text="🎯 Calibrer", bg=self.BTN, fg=self.WH, command=self._calibrate).pack(side=tk.LEFT, padx=2)
        tk.Button(bf, text="🛰️ SCAN GE", bg='#4CAF50', fg=self.WH,
                  font=("Consolas", 11, "bold"), command=self._scan_ge).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="🛸 Scan dossier", bg=self.BTN, fg=self.WH,
                  font=("Consolas", 11, "bold"), command=self._scan_folder).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="⏹️", bg='#ff5252', fg=self.WH, command=self._stop).pack(side=tk.LEFT, padx=2)

        rf = tk.Frame(self.root, bg=self.BG)
        rf.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(rf, text="⏱️ Pause/point (s):", bg=self.BG, fg=self.OR).pack(side=tk.LEFT)
        self.dwell_var = tk.IntVar(value=7)
        tk.Scale(rf, from_=4, to=20, orient=tk.HORIZONTAL, variable=self.dwell_var,
                 bg=self.BG2, fg=self.OR, highlightthickness=0, length=160).pack(side=tk.LEFT, padx=5)

        self.log = tk.Text(self.root, height=9, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _log(self, msg):
        try:
            self.log.configure(state='normal')
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state='disabled')
        except Exception:
            pass

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for e in load_hs() or []:
            flag = "🕊️ " if e.get("sanctuaire") else "🛸 "
            self.listbox.insert(tk.END, f"{flag}{e['name']} — {e['lat']:.4f}, {e['lon']:.4f}")

    def _add(self):
        c = parse_coord(self.coord_var.get())
        if not c:
            messagebox.showerror("Erreur", "Coords invalides")
            return
        data = load_hs() or []
        data.append({"name": self.name_var.get().strip() or f"zone_{len(data) + 1}",
                     "lat": c[0], "lon": c[1], "sanctuaire": self.sanct_var.get()})
        save_hs(data)
        self._refresh_list()

    def _sel(self):
        i = self.listbox.curselection()
        return (load_hs() or [])[i[0]] if i else None

    def _del(self):
        i = self.listbox.curselection()
        if not i:
            return
        data = load_hs() or []
        gone = data.pop(i[0])
        save_hs(data)
        self._refresh_list()
        self._log(f"🗑️ {gone['name']}")

    def _toggle(self):
        i = self.listbox.curselection()
        if not i:
            return
        data = load_hs() or []
        data[i[0]]["sanctuaire"] = not data[i[0]].get("sanctuaire", False)
        save_hs(data)
        self._refresh_list()

    def _stop(self):
        self.stop_flag = True

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

    def _analyze(self, frame, name, sanct, out_dir):
        """Détection + sauvegarde respectueuse du sanctuaire."""
        hits = detect_ufo(frame) if HAS_DETECT else []
        if len(hits) > 30:
            self.root.after(0, lambda n=name: self._log(f"⚠️ {n}: texture naturelle, ignoré"))
            return 0
        if hits:
            for (x, y, w, h) in hits:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
                cv2.putText(frame, "OVNI", (x, max(12, y - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            cv2.imwrite(str(out_dir / f"hotspot_{name}.jpg"), frame,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            if not sanct:
                cv2.imwrite(str(CIBLES / f"hotspot_{name}.jpg"), frame,
                            [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        self.root.after(0, lambda n=name, hh=len(hits), s=sanct: self._log(
            f"🛸 {n}: {hh} signature(s)" + (" 🕊️ (local seul)" if s and hh else "")))
        return len(hits)

    def _scan_ge(self):
        if not HAS_PAG or not HAS_MSS:
            messagebox.showerror("Erreur", "pip install pyautogui mss")
            return
        if self.calib is None:
            messagebox.showerror("Erreur", "Calibre d'abord (🎯)")
            return
        targets = load_hs() or []
        if not targets:
            messagebox.showerror("Erreur", "Aucun hotspot")
            return
        self.stop_flag = False
        threading.Thread(target=self._scan_ge_work, args=(targets,), daemon=True).start()

    def _scan_ge_work(self, targets):
        out = EXPORTS / f"hotspots_{time.strftime('%Y%m%d_%H%M%S')}"
        out.mkdir(parents=True, exist_ok=True)
        self.root.after(0, lambda: self._log("🛰️ GE au premier plan… (5 s)"))
        time.sleep(5)
        total = 0
        try:
            with mss.mss() as sct:
                for e in targets:
                    if self.stop_flag:
                        break
                    pag.click(self.calib.x, self.calib.y)
                    time.sleep(0.4)
                    pag.hotkey('ctrl', 'a')
                    pag.write(f"{e['lat']:.6f}, {e['lon']:.6f}", interval=0.02)
                    pag.press('enter')
                    time.sleep(self.dwell_var.get())
                    shot = sct.grab(sct.monitors[1])
                    frame = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
                    cv2.imwrite(str(out / f"{e['name']}.jpg"), frame,
                                [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                    total += self._analyze(frame, e["name"], e.get("sanctuaire", False), out)
        except Exception as ex:
            self.root.after(0, lambda ex=ex: self._log("❌ scan: " + str(ex)))
        self.root.after(0, lambda: self._log(f"✅ Tournée hotspots terminée : {total} signature(s)"))

    def _scan_folder(self):
        p = filedialog.askdirectory(title="Dossier de JPEG (hors-ligne)")
        if not p:
            return
        self.stop_flag = False
        threading.Thread(target=self._scan_folder_work, args=(Path(p),), daemon=True).start()

    def _scan_folder_work(self, src):
        files = sorted([f for f in src.glob("*.*") if f.suffix.lower() in (".jpg", ".jpeg", ".png")])
        total = 0
        for f in files:
            if self.stop_flag:
                break
            frame = cv2.imread(str(f))
            if frame is None:
                continue
            total += self._analyze(frame, f.stem, False, src)
        self.root.after(0, lambda: self._log(f"✅ Dossier terminé : {total} signature(s)"))


def run():
    HotspotsApp()
    return "✅ HOTSPOTS fermé"


def main():
    try:
        HotspotsApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()