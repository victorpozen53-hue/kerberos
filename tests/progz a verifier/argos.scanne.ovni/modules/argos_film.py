#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎞️ ARGOS FILM FORENSIC v1.0 — organe PRIVÉ d'analyse de fuites 8mm/VHS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — usage LOCAL, ne jamais partager
Spécial vidéos type qtecqot ("disclosure 8mm") :
- 🎥 SUPPORT : film 8mm/Super8 numérisé vs vidéo analogique vs CGI
  (grain temporel vivant, coins vignettés, flicker, interlacement)
- 🧮 Entropie de Shannon globale + bruit résiduel (empreinte capteur)
- ⏱️ Horodatage : présence + type (overlay numérique moderne = suspect)
-  Fils/câbles suspects (maquettes suspendues) par black-hat fin
- 🧬 ELA (zones recompressées = compositing)
- 📋 Fragments déclarés : parse les cartons "Tape/Case HH:MM:SS"
- 📊 Score de crédibilité technique + rapport HTML & TXT
L'entropie prouve le capteur, PAS le sujet — le score est un INDICE.
"""
import sys
import re
import math
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
except ImportError as e:
    print("❌ OpenCV/numpy manquant:", e)
    input("Appuyez sur Entrée...")
    sys.exit(1)

_p = Path(__file__).resolve().parent
ARGOS_ROOT = _p.parent if (_p.parent / "reports").exists() or _p.name == "modules" else _p
REPORTS = ARGOS_ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)
EXTS_VIDEO = (".mp4", ".avi", ".mkv", ".mov", ".webm")


# === 🧰 BOÎTE À OUTILS FORENSIQUE ===========================================
def shannon(gray):
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    p = hist / hist.sum()
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def noise_residual(gray):
    return cv2.absdiff(gray, cv2.GaussianBlur(gray, (5, 5), 0))


def corner_vignette(gray):
    """Coins sombres + arrondis = optique film ancien."""
    h, w = gray.shape
    c = 60
    corners = [gray[:c, :c], gray[:c, -c:], gray[-c:, :c], gray[-c:, -c:]]
    return float(np.mean(gray)) - float(np.mean([x.mean() for x in corners]))


def scanline_ratio(gray):
    """Interlacement vidéo : énergie verticale anormale (peigne)."""
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    ey, ex = float(np.abs(gy).mean()), float(np.abs(gx).mean())
    return ey / ex if ex > 0 else 0.0


def timestamp_detect(gray):
    """Overlay blanc en bas = horodatage ; moderne si police nette."""
    h, w = gray.shape
    strip = gray[int(h * 0.82):int(h * 0.97), :]
    white = (strip > 190).astype(np.uint8)
    ratio = float(white.mean())
    present = 0.002 < ratio < 0.25
    net = 0.0
    if present:
        edges = cv2.Canny(strip, 100, 200)
        net = float(edges.mean())   # contours très nets = overlay numérique
    return present, ratio, net


def wire_score(gray):
    """Fils/câbles fins sombres = maquette suspendue possible."""
    best = 0.0
    for k in (cv2.getStructuringElement(cv2.MORPH_RECT, (41, 3)),
              cv2.getStructuringElement(cv2.MORPH_RECT, (3, 41))):
        bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k)
        vals = np.sort(bh.flatten())[-200:]
        best = max(best, float(vals.mean()))
    return best


def ela_score(gray):
    """Zones recompressées = compositing possible."""
    ok, buf = cv2.imencode(".jpg", gray, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        return 0.0
    rec = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
    diff = cv2.absdiff(gray, rec)
    return float((diff > 12).mean())


# === 🎥 ANALYSE VIDÉO ========================================================
def analyze_video(path, max_frames=48, cb=None):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return None
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    step = max(1, total // max_frames)
    grays, means, noises = [], [], []
    i = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if i % step == 0:
            g = cv2.cvtColor(cv2.resize(frame, (640, 480)), cv2.COLOR_BGR2GRAY)
            grays.append(g)
            means.append(float(g.mean()))
            noises.append(noise_residual(g))
        i += 1
        if len(grays) >= max_frames:
            break
    cap.release()
    if len(grays) < 4:
        return None
    h, w = grays[0].shape
    grain_vars = [float(cv2.absdiff(noises[j], noises[j + 1]).mean())
                  for j in range(len(noises) - 1)]
    ts_p, ts_r, ts_net = timestamp_detect(grays[len(grays) // 2])
    m = {
        "frames": len(grays),
        "aspect": round(w / h, 3),
        "entropie": round(float(np.mean([shannon(g) for g in grays])), 2),
        "bruit_entropie": round(float(np.mean([shannon(n) for n in noises])), 2),
        "grain_vivant": round(float(np.mean(grain_vars)), 2),
        "flicker": round(float(np.std(means)), 2),
        "vignette": round(float(np.mean([corner_vignette(g) for g in grays])), 1),
        "interlacement": round(float(np.mean([scanline_ratio(g) for g in grays])), 2),
        "horodatage": bool(ts_p),
        "horodatage_net": round(ts_net, 2),
        "fil_suspect": round(float(np.mean([wire_score(g) for g in grays])), 1),
        "ela": round(float(np.mean([ela_score(g) for g in grays])), 4),
    }
    return m


def classify_support(m):
    """Le verdict support : indices croisés, jamais un seul critère."""
    clues, score = [], 50
    if m["grain_vivant"] > 2.0:
        clues.append("✅ grain temporel VIVANT (pellicule réelle probable)")
        score += 15
    elif m["grain_vivant"] < 1.0:
        clues.append("🚩 grain quasi statique (ajout numérique suspect)")
        score -= 15
    if m["vignette"] > 18:
        clues.append("✅ coins vignettés/arrondis (optique film ancien)")
        score += 10
    if 1.25 <= m["aspect"] <= 1.4:
        clues.append("ℹ️ format 4:3 (stocks 8mm/16mm/VHS)")
        score += 5
    if m["interlacement"] > 1.15:
        clues.append("ℹ️ interlacement détecté = chaîne VIDÉO (VHS/telecine)")
    if m["horodatage"]:
        if m["horodatage_net"] > 1.5:
            clues.append("🚩 horodatage overlay NUMÉRIQUE net (pas une incrustation optique)")
            score -= 10
        else:
            clues.append("ℹ️ horodatage présent, contours doux (brûlé pellicule possible)")
            score += 5
    if m["fil_suspect"] > 18:
        clues.append("🚩 fils/câbles fins détectés (maquette suspendue possible)")
        score -= 10
    if m["ela"] > 0.02:
        clues.append("🚩 zones recompressées hétérogènes (compositing possible)")
        score -= 8
    if m["entropie"] > 6.3:
        clues.append("✅ entropie haute (bruit capteur/pellicule réel)")
        score += 5
    score = max(0, min(100, score))
    if score >= 70:
        verdict = "COHÉRENT avec film d'époque numérisé"
    elif score >= 40:
        verdict = "MIXTE / INCONCLUSIF (effets pratiques possibles)"
    else:
        verdict = "ARTEFACTS MODERNES SUSPECTS (CGI/compositing probable)"
    return clues, score, verdict


def parse_fragments(text):
    """Parse les cartons 'Tape XX / Case NN/name HH:MM:SS - HH:MM:SS'."""
    out = []
    for tape in re.finditer(r"Tape (\d+)[^\n]*\n((?:Case[^\n]+\n?)+)", text):
        for c in re.finditer(r"Case (\d+)/([^\d\n]+) (\d\d:\d\d:\d\d) - (\d\d:\d\d:\d\d)", tape.group(2)):
            out.append((f"Tape {tape.group(1)}", c.group(1), c.group(2).strip(),
                        c.group(3), c.group(4)))
    return out


# === 📊 RAPPORTS =============================================================
def write_reports(name, m, clues, score, verdict, frags, notes):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in m.items())
    cl = "".join(f"<li>{c}</li>" for c in clues)
    fr = "".join(f"<li>{a} — Case {b} {c} ({d} → {e})</li>" for a, b, c, d, e in frags) or "<li>aucun carton collé</li>"
    html = ("<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'><title>FILM FORENSIC</title><style>"
            "body{background:#0a0f14;color:#e0e0e0;font-family:Consolas,monospace;}"
            "header{background:#16213e;padding:20px 30px;border-bottom:2px solid #00ffcc;}"
            "h1{color:#00ffcc;margin:0;}h2{color:#ffb347;}"
            ".card{background:#141a20;margin:15px 30px;padding:15px 20px;border-left:3px solid #00ffcc;}"
            "table{border-collapse:collapse;}td{padding:4px 12px;border-bottom:1px solid #223;}"
            ".score{font-size:28px;font-weight:bold;}"
            "footer{padding:15px 30px;color:#667;font-size:12px;}</style></head><body>"
            f"<header><h1>🎞️ FILM FORENSIC — {name}</h1><div>{now} • ARGOS • GPLv3 Victor Pozen</div></header>"
            f"<div class='card'><h2>Verdict technique</h2><div class='score' style='color:{'#4CAF50' if score >= 70 else '#ff9800' if score >= 40 else '#ff5252'}'>{score}/100</div>"
            f"<p><b>{verdict}</b></p><ul>{cl}</ul>"
            "<p>Rappel : l'entropie prouve le capteur, pas le sujet. Score = indice, pas tribunal.</p></div>"
            f"<div class='card'><h2>Métriques</h2><table>{rows}</table></div>"
            f"<div class='card'><h2>Fragments déclarés</h2><ul>{fr}</ul></div>"
            f"<div class='card'><h2>Notes opérateur</h2><pre>{notes.replace('<', '&lt;')}</pre></div>"
            "<footer>🎞️ ARGOS FILM FORENSIC — l'œil observe, l'humain conclut</footer></body></html>")
    hp = REPORTS / f"film_{name}.html"
    hp.write_text(html, encoding="utf-8")
    lines = ["═" * 60, f"🎞️ FILM FORENSIC — {name} • {now}", "═" * 60,
             f"SCORE : {score}/100 — {verdict}", "", "── Métriques ──"]
    lines += [f"├── {k}: {v}" for k, v in m.items()]
    lines += ["", "── Indices ──"] + [f"├── {c}" for c in clues]
    lines += ["", "── Fragments déclarés ──"] + [f"├── {a} Case {b} {c} ({d}->{e})" for a, b, c, d, e in frags]
    lines += ["", "── Notes ──", notes or "(aucune)", "", "═" * 60]
    tp = REPORTS / f"film_{name}.txt"
    tp.write_text("\n".join(lines), encoding="utf-8")
    return hp.name, tp.name


# === 🖥️ GUI ==================================================================
class FilmApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎞️ ARGOS FILM FORENSIC v1.0 — analyse fuites 8mm")
        self.root.geometry("950x720")
        self.root.configure(bg=self.BG)
        self._build()
        self._log("🎞️ FILM FORENSIC prêt — support, grain, entropie, fils, ELA, horodatage")
        self._log("Colle les cartons Tape/Case dans NOTES pour le rapport.")
        self.root.mainloop()

    def _build(self):
        f = tk.Frame(self.root, bg=self.BG)
        f.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f, text="🎬 Vidéo:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.src_var = tk.StringVar()
        tk.Entry(f, textvariable=self.src_var, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="📂", bg=self.BTN, fg=self.WH, command=self._browse).pack(side=tk.LEFT)
        tk.Label(self.root, text="📋 NOTES / cartons (Tape 03 … Case 18/Mk.4 02:13:18 - 02:23:57) :",
                 bg=self.BG, fg=self.OR, font=("Consolas", 9)).pack(anchor='w', padx=12)
        self.notes = tk.Text(self.root, height=6, bg=self.BG2, fg=self.WH, font=("Consolas", 10))
        self.notes.pack(fill=tk.X, padx=10, pady=3)
        b = tk.Frame(self.root, bg=self.BG)
        b.pack(fill=tk.X, padx=10, pady=5)
        self.btn_go = tk.Button(b, text="🎞️ ANALYSER", bg='#4CAF50', fg=self.WH,
                                font=("Consolas", 12, "bold"), command=self._start)
        self.btn_go.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.log = tk.Text(self.root, height=16, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _browse(self):
        p = filedialog.askopenfilename(title="Vidéo fuite",
                                       filetypes=[("Vidéo", "*.mp4 *.avi *.mkv *.mov *.webm"), ("Tous", "*.*")])
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
            messagebox.showerror("Erreur", "Choisis une vidéo")
            return
        self.btn_go.config(state=tk.DISABLED)
        threading.Thread(target=self._work, args=(src,), daemon=True).start()

    def _work(self, src):
        try:
            self.root.after(0, lambda: self._log(f"🎞️ Analyse de {src.name}…"))
            m = analyze_video(src)
            if m is None:
                self.root.after(0, lambda: self._log("❌ vidéo illisible ou trop courte"))
                return
            clues, score, verdict = classify_support(m)
            frags = parse_fragments(self.notes.get("1.0", "end-1c"))
            h, t = write_reports(src.stem, m, clues, score, verdict, frags,
                                 self.notes.get("1.0", "end-1c"))
            self.root.after(0, lambda: self._log(f"📊 {src.name}:"))
            for k, v in m.items():
                self.root.after(0, lambda k=k, v=v: self._log(f"   ├── {k}: {v}"))
            for c in clues:
                self.root.after(0, lambda c=c: self._log(f"   ├── {c}"))
            self.root.after(0, lambda: self._log(f"   └── SCORE {score}/100 — {verdict}"))
            self.root.after(0, lambda: self._log(f"📄 Rapports: {h} + {t}"))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ " + str(e)))
        finally:
            self.root.after(0, lambda: self.btn_go.config(state=tk.NORMAL))


def run():
    FilmApp()
    return "✅ FILM FORENSIC fermé"


def main():
    try:
        FilmApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()