#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌍 ARGOS GE MANAGER v1.0 — organe PRIVÉ : carnet de coordonnées + pilotage GE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — usage LOCAL, ne jamais partager
- ➕ Carnet local (carnet/carnet.json) : nom + coords (DMS avec O ou décimal)
- 🕊️ Flag sanctuaire : une coordonnée sanctuaire n'est JAMAIS exportée (KML)
- 🚀 Voler : pilote Google Earth (pyautogui) vers la sélection ou le carnet
- 📷 Voler+Capturer : mss -> exports/carnet_<ts>/
- 🎬 KML tour : placemarks + flyto (sanctuaires EXCLUS)
- 🧹 GRID : ratissage serpentin autour d'une coordonnée (rayon + pas)
Usage : bouton organe dans ARGOS v3.0, ou python argos_ge_manager.py
"""
import sys
import re
import math
import time
import json
import threading
import subprocess
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
    HAS_CV = True
except ImportError:
    HAS_CV = False
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
ARGOS_ROOT = _p.parent if (_p.parent / "exports").exists() or _p.name == "modules" else _p
CARNET_DIR = ARGOS_ROOT / "carnet"
CARNET_FILE = CARNET_DIR / "carnet.json"
EXPORTS_DIR = ARGOS_ROOT / "exports"
CARNET_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

GE_CANDIDATES = [Path(r"C:\Program Files\Google\GoogleEarthPro\client\googleearth.exe"),
                 Path(r"C:\Program Files (x86)\Google\GoogleEarthPro\client\googleearth.exe"),
                 Path.home() / "AppData" / "Local" / "Google" / "GoogleEarthPro" / "client" / "googleearth.exe"]


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


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_carnet():
    try:
        return json.loads(CARNET_FILE.read_text(encoding="utf-8")) if CARNET_FILE.exists() else []
    except Exception:
        return []


def save_carnet(data):
    CARNET_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def find_ge():
    for p in GE_CANDIDATES:
        if p.exists():
            return p
    return None


def build_kml(entries, range_m, dwell_s):
    """Placemarks + tour — les sanctuaires sont EXCLUS (jamais divulgués)."""
    pub = [e for e in entries if not e.get("sanctuaire")]
    parts = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
             "<kml xmlns=\"http://www.opengis.net/kml/2.2\" xmlns:gx=\"http://www.google.com/kml/ext/2.2\">",
             "<Document><name>ARGOS CARNET</name>"]
    for e in pub:
        parts.append(f"<Placemark><name>{_esc(e['name'])}</name><Point>"
                     f"<coordinates>{e['lon']:.6f},{e['lat']:.6f},0</coordinates></Point></Placemark>")
    parts.append("<gx:Tour><name>ARGOS CARNET TOUR</name><gx:Playlist>")
    for e in pub:
        parts.append("<gx:FlyTo><gx:duration>5.0</gx:duration><gx:flyToMode>bounce</gx:flyToMode>"
                     f"<LookAt><longitude>{e['lon']:.6f}</longitude><latitude>{e['lat']:.6f}</latitude>"
                     f"<altitude>0</altitude><range>{range_m}</range><tilt>0</tilt><heading>0</heading>"
                     "<altitudeMode>relativeToGround</altitudeMode></LookAt></gx:FlyTo>"
                     f"<gx:Wait><gx:duration>{dwell_s}</gx:duration></gx:Wait>")
    parts.append("</gx:Playlist></gx:Tour></Document></kml>")
    return "\n".join(parts), len(pub), len(entries) - len(pub)


def grid_around(lat, lon, radius_m, step_m):
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * max(0.2, math.cos(math.radians(lat))))
    pts, la, flip = [], lat + dlat, False
    while la >= lat - dlat:
        cosl = max(0.2, math.cos(math.radians(lat)))
        s = step_m / (111320.0 * cosl)
        lons, lo = [], lon - dlon
        while lo <= lon + dlon:
            lons.append(lo)
            lo += s
        if flip:
            lons.reverse()
        pts.extend((la, x) for x in lons)
        flip = not flip
        la -= step_m / 111320.0
    return pts


class GeManagerApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌍 ARGOS GE MANAGER v1.0 — carnet + pilotage Google Earth")
        self.root.geometry("980x760")
        self.root.configure(bg=self.BG)
        self.calib = None
        self.stop_flag = False
        self._build()
        self._refresh_list()
        self._log("🌍 GE MANAGER prêt — ajoute tes coords (DMS avec O ou décimal)")
        self._log("🕊️ une coordonnée sanctuaire n'est JAMAIS exportée ni divulguée")
        self.root.mainloop()

    def _build(self):
        af = tk.Frame(self.root, bg=self.BG)
        af.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(af, text="🏷️ Nom:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        tk.Entry(af, textvariable=self.name_var, width=16, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=3)
        tk.Label(af, text="📍 Coords:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.coord_var = tk.StringVar()
        tk.Entry(af, textvariable=self.coord_var, width=30, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=3)
        self.sanct_var = tk.BooleanVar(value=False)
        tk.Checkbutton(af, text="🕊️ sanctuaire", variable=self.sanct_var, bg=self.BG, fg=self.OR,
                       selectcolor=self.BG2, activebackground=self.BG,
                       activeforeground=self.OR).pack(side=tk.LEFT, padx=5)
        tk.Button(af, text="➕ Ajouter", bg='#4CAF50', fg=self.WH,
                  command=self._add).pack(side=tk.LEFT, padx=5)

        self.listbox = tk.Listbox(self.root, height=10, bg=self.BG2, fg=self.WH,
                                  selectbackground=self.BTN, font=("Consolas", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(bf, text="🗑️ Supprimer", bg='#ff5252', fg=self.WH,
                  command=self._del).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="🕊️ Toggle sanctuaire", bg=self.BTN, fg=self.WH,
                  command=self._toggle).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="🎯 Calibrer", bg=self.BTN, fg=self.WH,
                  command=self._calibrate).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        pf = tk.Frame(self.root, bg=self.BG)
        pf.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(pf, text="🚀 Voler (sélection)", bg='#4CAF50', fg=self.WH,
                  font=("Consolas", 11, "bold"), command=lambda: self._fly(False)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(pf, text="📷 Voler+Capturer", bg='#4CAF50', fg=self.WH,
                  font=("Consolas", 11, "bold"), command=lambda: self._fly(True)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(pf, text="🎬 KML tour", bg=self.BTN, fg=self.WH,
                  font=("Consolas", 11, "bold"), command=self._kml).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(pf, text="🧹 GRID", bg=self.BTN, fg=self.WH,
                  font=("Consolas", 11, "bold"), command=self._grid).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(pf, text="🚀 GE", bg=self.BTN, fg=self.WH, command=self._launch_ge).pack(side=tk.LEFT, padx=2)

        rf = tk.Frame(self.root, bg=self.BG)
        rf.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(rf, text="🛰️ Alt:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.range_var = tk.IntVar(value=2000)
        tk.Scale(rf, from_=300, to=20000, resolution=100, orient=tk.HORIZONTAL, variable=self.range_var,
                 bg=self.BG2, fg=self.CY, highlightthickness=0, length=140).pack(side=tk.LEFT, padx=3)
        tk.Label(rf, text="⏱️:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.dwell_var = tk.IntVar(value=6)
        tk.Scale(rf, from_=3, to=20, orient=tk.HORIZONTAL, variable=self.dwell_var,
                 bg=self.BG2, fg=self.CY, highlightthickness=0, length=90).pack(side=tk.LEFT, padx=3)
        tk.Label(rf, text="🧹 Rayon:", bg=self.BG, fg=self.OR).pack(side=tk.LEFT, padx=(10, 0))
        self.radius_var = tk.IntVar(value=3000)
        tk.Scale(rf, from_=500, to=20000, resolution=500, orient=tk.HORIZONTAL, variable=self.radius_var,
                 bg=self.BG2, fg=self.OR, highlightthickness=0, length=120).pack(side=tk.LEFT, padx=3)
        tk.Label(rf, text="Pas:", bg=self.BG, fg=self.OR).pack(side=tk.LEFT)
        self.step_var = tk.IntVar(value=1000)
        tk.Scale(rf, from_=200, to=5000, resolution=100, orient=tk.HORIZONTAL, variable=self.step_var,
                 bg=self.BG2, fg=self.OR, highlightthickness=0, length=100).pack(side=tk.LEFT, padx=3)

        self.log = tk.Text(self.root, height=8, bg=self.BG2, fg='#4CAF50',
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
        for e in load_carnet():
            flag = "🕊️ " if e.get("sanctuaire") else "📍 "
            self.listbox.insert(tk.END, f"{flag}{e['name']} — {e['lat']:.5f}, {e['lon']:.5f}")

    def _add(self):
        c = parse_coord(self.coord_var.get())
        if not c:
            messagebox.showerror("Erreur", "Coords invalides (décimal ou DMS avec O)")
            return
        data = load_carnet()
        data.append({"name": self.name_var.get().strip() or f"lieu_{len(data) + 1}",
                     "lat": c[0], "lon": c[1], "sanctuaire": self.sanct_var.get()})
        save_carnet(data)
        self._refresh_list()
        self._log(f"➕ Ajouté: {data[-1]['name']}")

    def _sel(self):
        i = self.listbox.curselection()
        if not i:
            return None
        return load_carnet()[i[0]]

    def _del(self):
        i = self.listbox.curselection()
        if not i:
            return
        data = load_carnet()
        gone = data.pop(i[0])
        save_carnet(data)
        self._refresh_list()
        self._log(f"🗑️ Supprimé: {gone['name']}")

    def _toggle(self):
        i = self.listbox.curselection()
        if not i:
            return
        data = load_carnet()
        data[i[0]]["sanctuaire"] = not data[i[0]].get("sanctuaire", False)
        save_carnet(data)
        self._refresh_list()
        st = "🕊️ protégé" if data[i[0]]["sanctuaire"] else "📍 public"
        self._log(f"🔁 {data[i[0]]['name']} -> {st}")

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

    def _fly(self, capture):
        if not HAS_PAG or (capture and not HAS_MSS):
            messagebox.showerror("Erreur", "pip install pyautogui mss")
            return
        if self.calib is None:
            messagebox.showerror("Erreur", "Calibre d'abord (🎯)")
            return
        e = self._sel()
        targets = [e] if e else [x for x in load_carnet() if not x.get("sanctuaire")]
        if not targets:
            messagebox.showerror("Erreur", "Aucune cible publique")
            return
        self.stop_flag = False
        threading.Thread(target=self._fly_work, args=(targets, capture), daemon=True).start()

    def _fly_work(self, targets, capture):
        out = None
        if capture:
            out = EXPORTS_DIR / f"carnet_{time.strftime('%Y%m%d_%H%M%S')}"
            out.mkdir(parents=True, exist_ok=True)
        self.root.after(0, lambda: self._log("🚀 GE au premier plan… (5 s)"))
        time.sleep(5)
        idx = 0
        try:
            with mss.mss() if capture else _NullCtx() as sct:
                for e in targets:
                    if self.stop_flag:
                        break
                    pag.click(self.calib.x, self.calib.y)
                    time.sleep(0.4)
                    pag.hotkey('ctrl', 'a')
                    pag.write(f"{e['lat']:.6f}, {e['lon']:.6f}", interval=0.02)
                    pag.press('enter')
                    time.sleep(self.dwell_var.get())
                    if capture and sct is not None:
                        shot = sct.grab(sct.monitors[1])
                        if HAS_CV:
                            frame = cv2.cvtColor(np.array(shot), cv2.COLOR_BGRA2BGR)
                            cv2.imwrite(str(out / f"{idx:03d}_{e['name'][:20]}.jpg"), frame,
                                        [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                    self.root.after(0, lambda n=e['name']: self._log(f"🚀 -> {n}"))
                    idx += 1
        except Exception as ex:
            self.root.after(0, lambda ex=ex: self._log("❌ vol: " + str(ex)))
        self.root.after(0, lambda: self._log(f"✅ {idx} vol(s) terminé(s)"))

    def _kml(self):
        data = load_carnet()
        if not data:
            messagebox.showerror("Erreur", "Carnet vide")
            return
        kml, pub, hidden = build_kml(data, self.range_var.get(), self.dwell_var.get())
        out = EXPORTS_DIR / "argos_carnet.kml"
        out.write_text(kml, encoding="utf-8")
        self._log(f"🎬 KML: {out.name} — {pub} public(s), {hidden} 🕊️ EXCLU(s)")

    def _grid(self):
        e = self._sel()
        if not e:
            messagebox.showerror("Erreur", "Sélectionne une coordonnée")
            return
        if e.get("sanctuaire"):
            self._log("🕊️ sanctuaire : GRID refusé (protection)")
            return
        pts = grid_around(e["lat"], e["lon"], self.radius_var.get(), self.step_var.get())
        kml, _, _ = build_kml([{"name": f"grid_{i}", "lat": a, "lon": b} for i, (a, b) in enumerate(pts)],
                              self.range_var.get(), self.dwell_var.get())
        out = EXPORTS_DIR / f"argos_grid_{e['name'][:20]}.kml"
        out.write_text(kml, encoding="utf-8")
        self._log(f"🧹 GRID: {len(pts)} points autour de {e['name']} -> {out.name}")

    def _launch_ge(self):
        ge = find_ge()
        if ge is None:
            p = filedialog.askopenfilename(title="googleearth.exe", filetypes=[("EXE", "*.exe")])
            if not p:
                return
            ge = Path(p)
        kml = EXPORTS_DIR / "argos_carnet.kml"
        if not kml.exists():
            self._kml()
        subprocess.Popen([str(ge), str(kml)])
        self._log("🚀 Google Earth lancé avec le carnet")


class _NullCtx:
    def __enter__(self):
        return None

    def __exit__(self, *a):
        return False


def run():
    GeManagerApp()
    return "✅ GE MANAGER fermé"


def main():
    try:
        GeManagerApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()