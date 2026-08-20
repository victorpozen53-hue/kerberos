#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 KERBEROS RECON v1.1 — ATR light, version BLINDÉE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3
- GUI tkinter par défaut (ne ferme jamais, log tout, aperçu des cibles)
- Mode console si arguments : python kerberos_recon.py cibles/ scenes/ [out/]
- YOLO 100% optionnel : chargé à la demande, TOUTES erreurs attrapées
- Dossier cibles = crops VUS DU CIEL (Google Earth), pas photos au sol
"""
import sys
import threading
import logging
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox


def _excepthook(t, v, tb):
    msg = "".join(traceback.format_exception(t, v, tb))
    print("❌ ERREUR CRITIQUE:\n" + msg)
    input("Appuyez sur Entrée pour fermer...")


sys.excepthook = _excepthook

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("KerberosRecon")

try:
    import cv2
    import numpy as np
except ImportError as e:
    print("❌ OpenCV/numpy manquant:", e)
    print("   pip install opencv-python numpy")
    input("Appuyez sur Entrée...")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except Exception:
    HAS_YOLO = False
    logger.info("ℹ️ ultralytics absent -> mode template/ORB seul")

EXTS = (".jpg", ".jpeg", ".png")
SCALES = [0.5, 0.7, 0.85, 1.0, 1.2, 1.5, 2.0]
ORB_RATIO = 0.75
TARGETS = {4: "AVION", 5: "BUS", 7: "CAMION", 8: "BATEAU"}


def load_refs(folder: Path):
    refs = []
    for p in sorted(folder.glob("*.*")):
        if p.suffix.lower() in EXTS:
            img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                refs.append((p.stem, img))
    return refs


def match_template(scene_g, ref_g):
    best = (0.0, None)
    for s in SCALES:
        w = int(ref_g.shape[1] * s)
        h = int(ref_g.shape[0] * s)
        if w >= scene_g.shape[1] or h >= scene_g.shape[0] or w < 8 or h < 8:
            continue
        t = cv2.resize(ref_g, (w, h))
        res = cv2.matchTemplate(scene_g, t, cv2.TM_CCOEFF_NORMED)
        _, maxv, _, maxloc = cv2.minMaxLoc(res)
        if maxv > best[0]:
            best = (maxv, (maxloc[0], maxloc[1], w, h))
    return best


def orb_good(scene_crop, ref_g):
    orb = cv2.ORB_create(500)
    _, d1 = orb.detectAndCompute(scene_crop, None)
    _, d2 = orb.detectAndCompute(ref_g, None)
    if d1 is None or d2 is None:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    knn = bf.knnMatch(d2, d1, k=2)
    return sum(1 for pair in knn if len(pair) == 2 and pair[0].distance < ORB_RATIO * pair[1].distance)


def get_yolo():
    """Charge YOLO à la demande ; jamais un crash."""
    if not HAS_YOLO:
        return None
    try:
        return YOLO("yolov8n.pt")
    except Exception as e:
        logger.warning(f"⚠️ YOLO indisponible ({e}) -> template/ORB seul")
        return None


def audit_scene(scene, refs, yolo, thresh):
    g = cv2.cvtColor(scene, cv2.COLOR_BGR2GRAY)
    hits = []
    for name, ref in refs:
        score, box = match_template(g, ref)
        if score >= thresh and box:
            x, y, w, h = box
            good = orb_good(g[y:y + h, x:x + w], ref)
            cv2.rectangle(scene, (x, y), (x + w, y + h), (0, 165, 255), 2)
            cv2.putText(scene, f"{name} {score:.2f}", (x, max(12, y - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
            hits.append(f"{name} score={score:.2f} ORB={good}")
    if yolo is not None:
        try:
            for r in yolo.predict(scene, verbose=False, conf=0.35):
                for b in r.boxes:
                    c = int(b.cls[0])
                    if c in TARGETS:
                        x1, y1, x2, y2 = map(int, b.xyxy[0])
                        cv2.rectangle(scene, (x1, y1), (x2, y2), (0, 255, 204), 2)
                        cv2.putText(scene, TARGETS[c], (x1, max(12, y1 - 6)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 204), 1)
                        hits.append(f"{TARGETS[c]} conf={float(b.conf):.2f}")
        except Exception as e:
            logger.warning(f"⚠️ YOLO en cours de route: {e}")
    return scene, hits


class ReconApp:
    BG = '#1e1e1e'; BG2 = '#2d2d2d'; CY = '#00ffcc'; OR = '#ff9800'
    BTN = '#2d5a7b'; WH = '#ffffff'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 KERBEROS RECON v1.1")
        self.root.geometry("1000x780")
        self.root.configure(bg=self.BG)
        self.refs_dir = None
        self.scenes_dir = None
        self.yolo = None
        self.stop_flag = False
        self.latest = None
        self.photo = None
        self._build()
        self._refresh()
        self._log("🎯 RECON prêt. Choisis le dossier CIBLES puis le dossier SCÈNES.")
        if not HAS_YOLO:
            self._log("ℹ️ ultralytics absent : mode template/ORB (pip install ultralytics pour le bonus)")
        self.root.mainloop()

    def _build(self):
        tk.Label(self.root, text="🎯 KERBEROS RECON — reconnaissance de matériel",
                 bg=self.BG2, fg=self.CY, font=("Consolas", 15, "bold")).pack(fill=tk.X, pady=8)
        cf = tk.Frame(self.root, bg=self.BG)
        cf.pack(fill=tk.X, padx=10, pady=5)

        r1 = tk.Frame(cf, bg=self.BG)
        r1.pack(fill=tk.X, pady=3)
        tk.Label(r1, text="🎯 Cibles:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.refs_var = tk.StringVar()
        tk.Entry(r1, textvariable=self.refs_var, width=55, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(r1, text="📂", bg=self.BTN, fg=self.WH, command=self._browse_refs).pack(side=tk.LEFT)

        r2 = tk.Frame(cf, bg=self.BG)
        r2.pack(fill=tk.X, pady=3)
        tk.Label(r2, text="🛰️ Scènes:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.scenes_var = tk.StringVar()
        tk.Entry(r2, textvariable=self.scenes_var, width=55, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(r2, text="📂", bg=self.BTN, fg=self.WH, command=self._browse_scenes).pack(side=tk.LEFT)

        r3 = tk.Frame(cf, bg=self.BG)
        r3.pack(fill=tk.X, pady=3)
        tk.Label(r3, text="Seuil:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.thresh_var = tk.IntVar(value=72)
        tk.Scale(r3, from_=50, to=90, orient=tk.HORIZONTAL, variable=self.thresh_var,
                 bg=self.BG2, fg=self.CY, highlightthickness=0, length=200).pack(side=tk.LEFT, padx=5)
        self.yolo_var = tk.BooleanVar(value=HAS_YOLO)
        cb = tk.Checkbutton(r3, text="🧠 YOLO (avion/bus/camion/bateau)", variable=self.yolo_var,
                            bg=self.BG, fg=self.OR, selectcolor=self.BG2,
                            activebackground=self.BG, activeforeground=self.OR,
                            state=tk.NORMAL if HAS_YOLO else tk.DISABLED)
        cb.pack(side=tk.LEFT, padx=15)

        self.preview = tk.Label(self.root, bg=self.BG, text="⏳ En attente d'audit…",
                                fg=self.CY, font=("Consolas", 12))
        self.preview.pack(padx=10, pady=5)

        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=5)
        self.btn_go = tk.Button(bf, text="🎯 AUDIT", bg='#4CAF50', fg=self.WH,
                                font=("Consolas", 12, "bold"), command=self._start)
        self.btn_go.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.btn_stop = tk.Button(bf, text="⏹️ Stop", bg='#ff5252', fg=self.WH,
                                  font=("Consolas", 12, "bold"), command=self._stop,
                                  state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.status = tk.Label(self.root, text="⏳ Prêt", bg=self.BG, fg=self.OR,
                               font=("Consolas", 10))
        self.status.pack(pady=2)

        self.log = tk.Text(self.root, height=9, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _browse_refs(self):
        try:
            p = filedialog.askdirectory(title="Dossier des cibles (crops vus du ciel)")
            if p:
                self.refs_dir = Path(p)
                self.refs_var.set(p)
        except Exception as e:
            self._log(f"❌ browse: {e}")

    def _browse_scenes(self):
        try:
            p = filedialog.askdirectory(title="Dossier des scènes à auditer")
            if p:
                self.scenes_dir = Path(p)
                self.scenes_var.set(p)
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
            if self.refs_dir is None or self.scenes_dir is None:
                messagebox.showerror("Erreur", "Choisis les deux dossiers (cibles + scènes)")
                return
            self.stop_flag = False
            self.btn_go.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
            threading.Thread(target=self._audit, daemon=True).start()
        except Exception as e:
            self._log(f"❌ start: {e}")

    def _stop(self):
        self.stop_flag = True

    def _audit(self):
        try:
            refs = load_refs(self.refs_dir)
            self.root.after(0, lambda: self._log(f"🎯 {len(refs)} référence(s) chargée(s)"))
            if not refs:
                self.root.after(0, lambda: messagebox.showerror("Erreur", "Aucune cible lisible dans le dossier"))
                return
            yolo = get_yolo() if self.yolo_var.get() else None
            scenes = sorted([p for p in self.scenes_dir.glob("*.*") if p.suffix.lower() in EXTS])
            out = self.scenes_dir.with_name(self.scenes_dir.name + "_recon")
            out.mkdir(parents=True, exist_ok=True)
            thresh = self.thresh_var.get() / 100.0
            total = 0
            for i, sc in enumerate(scenes):
                if self.stop_flag:
                    break
                scene = cv2.imread(str(sc))
                if scene is None:
                    continue
                scene, hits = audit_scene(scene, refs, yolo, thresh)
                if hits:
                    total += len(hits)
                    cv2.imwrite(str(out / f"recon_{sc.stem}.jpg"), scene,
                                [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                    if HAS_PIL:
                        self.latest = cv2.cvtColor(scene, cv2.COLOR_BGR2RGB)
                    for hmsg in hits:
                        self.root.after(0, lambda s=sc.name, m=hmsg: self._log(f"🎯 {s}: {m}"))
                self.root.after(0, lambda i=i, t=len(scenes), s=sc.name:
                                self.status.config(text=f"🛰️ {i + 1}/{t} — {s} — cibles: {total}"))
            self.root.after(0, lambda: self._log(f"✅ Audit terminé: {total} détection(s) -> {out}"))
            self.root.after(0, lambda: self.status.config(text="✅ Audit terminé"))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ audit: " + str(e)))
        finally:
            self.root.after(0, lambda: self.btn_go.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.btn_stop.config(state=tk.DISABLED))

    def _refresh(self):
        try:
            if self.latest is not None and HAS_PIL:
                img = Image.fromarray(self.latest)
                img.thumbnail((960, 540))
                self.photo = ImageTk.PhotoImage(img)
                self.preview.config(image=self.photo, text="")
        except Exception:
            pass
        self.root.after(33, self._refresh)


def console_mode(args):
    refs = load_refs(Path(args[0]))
    logger.info(f"🎯 {len(refs)} référence(s)")
    if not refs:
        print("❌ Aucune cible lisible")
        input("Appuyez sur Entrée...")
        return
    scenes = sorted([p for p in Path(args[1]).glob("*.*") if p.suffix.lower() in EXTS])
    out = Path(args[2]) if len(args) > 2 else Path(args[1]).with_name("recon_out")
    out.mkdir(parents=True, exist_ok=True)
    yolo = get_yolo()
    for sc in scenes:
        scene = cv2.imread(str(sc))
        if scene is None:
            continue
        scene, hits = audit_scene(scene, refs, yolo, 0.72)
        if hits:
            cv2.imwrite(str(out / f"recon_{sc.stem}.jpg"), scene,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            for hmsg in hits:
                logger.info(f"🎯 {sc.name}: {hmsg}")
    logger.info("✅ Audit RECON terminé")
    input("Appuyez sur Entrée...")


def main():
    try:
        if len(sys.argv) >= 3:
            console_mode(sys.argv[1:])
        else:
            ReconApp()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()