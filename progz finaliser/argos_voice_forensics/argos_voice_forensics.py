#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎤 ARGOS VOICE FORENSICS v2.6 STRIC — voix humaine vs IA + rapports HTML
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — usage LOCAL
🆕 v2.6 :
- 📊 rapports HTML + JSON auto (brut / nettoyé / split) dans reports/
- 📦 source de numpy affichée (système vs argos_apis/) ; dossier vide = normal
- 📂 bouton Rapports ; 🧼 nettoyage ; ✂️ split ; 📊 progression + sabre
- 5 indices + garde "audio non fiable" ; F0 autocorrélation rapide
"""
import sys
import os
import re
import math
import wave
import json
import shutil
import subprocess
import threading
import traceback
import time
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


def _excepthook(t, v, tb):
    print("❌ ERREUR CRITIQUE:\n" + "".join(traceback.format_exception(t, v, tb)))
    input("Appuyez sur Entrée pour fermer...")


sys.excepthook = _excepthook

# === 📦 BOOTSTRAP APIs LOCALES ===============================================
_p = Path(__file__).resolve().parent
YTD_DIR = _p / "ytdl"
APIS_DIR = _p / "argos_apis"
REPORTS = _p / "reports" / "voice_analysis"
for _d in (APIS_DIR, REPORTS):
    _d.mkdir(parents=True, exist_ok=True)
if str(APIS_DIR) not in sys.path:
    sys.path.insert(0, str(APIS_DIR))
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
CHUNK = 120

np = None


def _try_numpy():
    global np
    try:
        import numpy as _n
        np = _n
        return True
    except Exception:
        return False


HAS_NUMPY = _try_numpy()


def numpy_source():
    if not HAS_NUMPY:
        return "absent"
    try:
        p = Path(np.__file__).resolve()
        return "argos_apis/" if str(p).startswith(str(APIS_DIR)) else "système"
    except Exception:
        return "inconnu"


def repair_apis():
    cmd = [sys.executable, "-m", "pip", "install", "--target", str(APIS_DIR),
           "--disable-pip-version-check", "numpy", "scipy"]
    try:
        subprocess.run(cmd, capture_output=True, creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass
    return _try_numpy()


# === 🎬 OUTILS FFMPEG ========================================================
def find_ffmpeg():
    for c in (YTD_DIR / "ffmpeg.exe", _p / "ffmpeg.exe"):
        if c.exists():
            return str(c)
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def probe_duration(ff, src):
    r = subprocess.run([str(ff), "-i", str(src)], capture_output=True,
                       creationflags=CREATE_NO_WINDOW)
    m = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)",
                  r.stderr.decode("utf-8", errors="ignore"))
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0


def to_wav(ff, src, out, start=None, dur=None):
    cmd = [str(ff), "-y", "-i", str(src)]
    if start is not None:
        cmd += ["-ss", str(start)]
    if dur is not None:
        cmd += ["-t", str(dur)]
    cmd += ["-vn", "-ar", "16000", "-ac", "1", str(out)]
    subprocess.run(cmd, capture_output=True, creationflags=CREATE_NO_WINDOW)
    return out if out.exists() and out.stat().st_size > 1000 else None


# === 🎤 OUTILS AUDIO =========================================================
def read_wav_mono(path):
    with wave.open(str(path)) as wf:
        n, sr = wf.getnchannels(), wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    x = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if n > 1:
        x = x.reshape(-1, n).mean(axis=1)
    return x, sr


def write_wav(path, x, sr):
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def _runs(mask):
    d = np.diff(np.concatenate(([0], mask.astype(np.int8), [0])))
    return np.where(d == 1)[0], np.where(d == -1)[0]


def f0_jitter(x, sr, max_frames=400):
    f0s, done = [], 0
    frame_len, hop = int(sr * 0.05), int(sr * 0.025)
    lo, hi = int(sr / 400), int(sr / 60)
    for start in range(0, max(1, len(x) - frame_len), hop):
        fr = x[start:start + frame_len]
        if np.abs(fr).mean() < 0.01:
            continue
        fr = fr - fr.mean()
        corr = np.correlate(fr, fr, mode='full')
        corr = corr[len(corr) // 2:]
        if len(corr) > hi:
            seg = corr[lo:hi]
            if seg.size and seg.max() > 0:
                f0s.append(sr / (lo + int(np.argmax(seg))))
        done += 1
        if done >= max_frames:
            break
    if len(f0s) < 10:
        return 0.0
    f0s = np.array(f0s)
    return float(np.abs(np.diff(f0s)).mean() / (f0s.mean() + 1e-9))


def clean_voice(x, sr, lo=85.0, hi=3000.0):
    try:
        from scipy.signal import butter, filtfilt
        ny = sr / 2.0
        b, a = butter(4, [max(0.01, lo / ny), min(0.99, hi / ny)], btype='band')
        y = filtfilt(b, a, x)
    except Exception:
        spec = np.fft.rfft(x)
        freqs = np.fft.rfftfreq(len(x), 1.0 / sr)
        y = np.fft.irfft(spec * ((freqs >= lo) & (freqs <= hi)), len(x)).astype(np.float32)
    fr = int(sr * 0.02)
    n = (len(y) // fr) * fr
    if n >= fr * 10:
        rms = np.sqrt((y[:n].reshape(-1, fr) ** 2).mean(axis=1))
        thr = np.percentile(rms, 25)
        g = np.repeat(np.where(rms > thr, 1.0, 0.15), fr)
        win = int(0.03 * sr)
        if win > 1:
            g = np.convolve(g, np.ones(win) / win, mode='same')
        if len(g) < len(y):
            g = np.concatenate([g, np.ones(len(y) - len(g))])
        y = y * g[:len(y)]
    m = np.abs(y).max()
    return 0.9 * y / m if m > 0 else y


# === 🧠 ANALYSE ==============================================================
def analyze_wav(path, cap_sec=120):
    if np is None:
        return {"error": "numpy absent — clique 📦 APIs"}
    x, sr = read_wav_mono(path)
    if len(x) > sr * cap_sec:
        x = x[:sr * cap_sec]
    if len(x) < sr * 3:
        return {"error": "trop court"}
    w, h = int(sr * 0.04), int(sr * 0.02)
    sw = np.lib.stride_tricks.sliding_window_view(x, w)[::h]
    energies = (sw ** 2).mean(axis=1)
    lo_p, hi_p = np.percentile(energies, 30), np.percentile(energies, 95)
    thr = lo_p + 0.15 * (hi_p - lo_p)
    speech = energies > thr
    speech_sec = float(speech.sum()) * h / sr
    starts, ends = _runs(speech)
    pauses = np.array([(starts[i + 1] - ends[i]) * h / sr
                       for i in range(len(ends) - 1)
                       if (starts[i + 1] - ends[i]) * h / sr > 0.12] or [0.0])
    pause_cv = float(pauses.std() / pauses.mean()) if pauses.mean() > 0 else 0.0
    breath_rate = float(np.sum((pauses >= 0.12) & (pauses <= 0.45))) / max(0.2, speech_sec / 60.0)
    jumps = np.abs(np.diff(energies))
    cuts_min = float(np.sum(jumps > 8 * (np.median(energies) + 1e-9))) / max(0.2, len(energies) * h / sr / 60.0)
    fiable = (breath_rate <= 30) and (cuts_min <= 12)
    freqs = np.fft.rfftfreq(w, 1.0 / sr)
    rolls = []
    for i in range(0, len(sw), max(1, len(sw) // 40)):
        if not speech[min(i, len(speech) - 1)]:
            continue
        mag = np.abs(np.fft.rfft(sw[i] * np.hanning(w)))
        cum = np.cumsum(mag)
        cum /= cum[-1] + 1e-9
        rolls.append(freqs[np.searchsorted(cum, 0.95)])
    rolloff = float(np.mean(rolls)) if rolls else 0.0
    e = energies[speech]
    energy_mod = float(np.std(np.diff(e)) / (np.mean(e) + 1e-9)) if e.size else 0.0
    jitter = f0_jitter(x, sr)

    clues, score = [], 0
    if not fiable:
        clues.append(f"🚩 audio non fiable (~{cuts_min:.0f} coupes/min, 'resp.' {breath_rate:.0f}/min) — stats neutralisées")
        if rolloff <= 7500:
            clues.append("ℹ️ bande limitée (codec)")
    else:
        if pause_cv >= 0.55:
            score += 1; clues.append("✅ pauses irrégulières (rythme humain)")
        elif pause_cv <= 0.30 and len(pauses) >= 4:
            score -= 1; clues.append("🚩 pauses trop régulières (prosodie IA)")
        if 6 <= breath_rate <= 30:
            score += 1; clues.append("✅ respirations audibles entre phrases")
        elif breath_rate <= 2:
            score -= 1; clues.append("🚩 quasi aucune respiration (TTS)")
        if rolloff >= 11000:
            score += 1; clues.append("✅ large bande spectrale")
        elif rolloff <= 7500:
            score -= 1; clues.append("🚩 bande limitée (codec/TTS)")
    if energy_mod >= 0.5:
        score += 1; clues.append("✅ dynamique expressive")
    elif energy_mod <= 0.25:
        score -= 1; clues.append("🚩 dynamique plate")
    if 0.010 <= jitter <= 0.12:
        score += 1; clues.append("✅ micro-jitter du pitch (vraie voix)")
    elif 0 < jitter < 0.010:
        score -= 1; clues.append("🚩 pitch trop lisse (synthèse IA)")
    elif jitter > 0.12:
        clues.append("⚠️ jitter trop haut = estimateur perturbé (musique/codec)")
    if speech_sec < 20:
        verdict = "INCONCLUSIF (voix insuffisante)"
    else:
        verdict = ("VOIX HUMAINE probable" if score >= 2
                   else "SUSPECT IA / TTS" if score <= -1 else "INCONCLUSIF")
    return {"voix_sec": round(speech_sec, 1), "cuts_min": round(cuts_min, 1),
            "pause_cv": round(pause_cv, 2), "respirations_min": round(breath_rate, 1),
            "rolloff_hz": int(rolloff), "dynamique": round(energy_mod, 2),
            "jitter": round(jitter, 4), "score": score, "clues": clues, "verdict": verdict}


# === 📊 RAPPORTS JSON + HTML =================================================
def write_reports(name, payload, mode):
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^\w.-]+", "_", name)[:60]
    base = REPORTS / f"forensic_{mode}_{safe}_{stamp}"
    base.with_suffix(".json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    verdict = payload.get("global") or payload.get("verdict", "?")
    color = "#4CAF50" if "HUMAINE" in verdict else "#ff5252" if "IA" in verdict else "#ff9800"
    rows = ""
    for k in ("voix_sec", "cuts_min", "pause_cv", "respirations_min",
              "rolloff_hz", "dynamique", "jitter", "score"):
        if k in payload:
            rows += f"<tr><td>{k}</td><td>{payload[k]}</td></tr>"
    cl = "".join(f"<li>{c}</li>" for c in payload.get("clues", []))
    tr = ""
    for i, t in enumerate(payload.get("tranches", [])):
        tr += f"<tr><td>{i + 1}</td><td>{t['score']}</td><td>{t['verdict']}</td></tr>"
    html = ("<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
            f"<title>Voice Forensics — {name}</title><style>"
            "body{background:#0a0f14;color:#e0e0e0;font-family:Consolas,monospace;}"
            "header{background:#16213e;padding:20px 30px;border-bottom:2px solid #00ffcc;}"
            "h1{color:#00ffcc;margin:0;}h2{color:#ffb347;}"
            ".card{background:#141a20;margin:15px 30px;padding:15px 20px;border-left:3px solid #00ffcc;}"
            "table{border-collapse:collapse;}td,th{padding:4px 12px;border-bottom:1px solid #223;text-align:left;}"
            ".score{font-size:26px;font-weight:bold;}"
            "footer{padding:15px 30px;color:#667;font-size:12px;}</style></head><body>"
            f"<header><h1>🎤 VOICE FORENSICS — {name}</h1>"
            f"<div>{now.strftime('%d/%m/%Y %H:%M')} • mode {mode} • numpy: {numpy_source()} • GPLv3 Victor Pozen</div></header>"
            f"<div class='card'><h2>Verdict</h2><div class='score' style='color:{color}'>{verdict}</div></div>"
            + (f"<div class='card'><h2>Métriques</h2><table>{rows}</table></div>" if rows else "")
            + (f"<div class='card'><h2>Indices</h2><ul>{cl}</ul></div>" if cl else "")
            + (f"<div class='card'><h2>Tranches 2 min</h2><table><tr><th>#</th><th>score</th><th>verdict</th></tr>{tr}</table></div>" if tr else "")
            + "<footer>🎤 ARGOS VOICE FORENSICS — l'oreille observe, l'humain conclut</footer></body></html>")
    base.with_suffix(".html").write_text(html, encoding="utf-8")
    return base.with_suffix(".html").name


# === 🖥️ GUI ==================================================================
class ForensicsApp:
    BG = '#1e1e1e'; BG2 = '#2d2d2d'; CY = '#00ffcc'; OR = '#ff9800'
    RD = '#ff5252'; WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎤 ARGOS VOICE FORENSICS v2.6 STRIC")
        self.root.geometry("950x760")
        self.root.configure(bg=self.BG)
        self._busy = False
        self._spin_i = 0
        self._step_txt = "prêt"
        self._build()
        src = numpy_source()
        self._log(f"📦 numpy: {src} — argos_apis/ vide = NORMAL tant que le système fournit numpy")
        if HAS_NUMPY:
            self._set_analysis(True)
        else:
            self._set_analysis(False)
            self._log("⚠️ numpy absent -> 🔧 réparation AUTO dans argos_apis/…")
            threading.Thread(target=self._auto_repair, daemon=True).start()
        self._log("🎤 brut • 🧼 nettoyé • ✂️ split 2 min — rapports HTML+JSON auto")
        self.root.mainloop()

    def _build(self):
        hdr = tk.Frame(self.root, bg=self.BG2)
        hdr.pack(fill=tk.X, pady=8)
        tk.Label(hdr, text="🎤 KERBEROS VOICE FORENSICS", bg=self.BG2, fg=self.CY,
                 font=("Consolas", 16, "bold")).pack(side=tk.LEFT, padx=15)
        tk.Button(hdr, text="📂 Rapports", bg=self.BTN, fg=self.WH,
                  command=self._open_reports).pack(side=tk.RIGHT, padx=5)
        tk.Button(hdr, text="📦 APIs", bg=self.BTN, fg=self.WH,
                  command=self._manual_repair).pack(side=tk.RIGHT, padx=5)

        f = tk.Frame(self.root, bg=self.BG)
        f.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f, text="📂 Fichier:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.src_var = tk.StringVar()
        tk.Entry(f, textvariable=self.src_var, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="📂", bg=self.BTN, fg=self.WH, command=self._browse).pack(side=tk.LEFT)

        b = tk.Frame(self.root, bg=self.BG)
        b.pack(fill=tk.X, padx=10, pady=5)
        self.btn_go = tk.Button(b, text="🎤 ANALYSER", bg='#4CAF50', fg=self.WH,
                                font=("Consolas", 11, "bold"), command=self._analyze)
        self.btn_go.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        self.btn_clean = tk.Button(b, text="🧼 NETTOYER + ANALYSER", bg=self.CY, fg=self.BG,
                                   font=("Consolas", 11, "bold"), command=self._clean_analyze)
        self.btn_clean.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        self.btn_split = tk.Button(b, text="✂️ SPLIT 2 min", bg=self.OR, fg=self.BG,
                                   font=("Consolas", 11, "bold"), command=self._split)
        self.btn_split.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        pf = tk.Frame(self.root, bg=self.BG)
        pf.pack(fill=tk.X, padx=10, pady=3)
        self.pbar = ttk.Progressbar(pf, mode='determinate', maximum=100)
        self.pbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.step_label = tk.Label(pf, text="⏳ prêt", bg=self.BG, fg=self.OR,
                                   font=("Consolas", 10), width=42, anchor='w')
        self.step_label.pack(side=tk.LEFT)

        self.verdict_label = tk.Label(self.root, text="⏳ …", bg=self.BG, fg=self.CY,
                                      font=("Consolas", 15, "bold"))
        self.verdict_label.pack(pady=8)
        self.details = tk.Text(self.root, height=13, bg=self.BG2, fg='#a0a0c0',
                               font=('Consolas', 9), state='disabled')
        self.details.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log = tk.Text(self.root, height=7, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.X, padx=10, pady=10)

    def _open_reports(self):
        try:
            os.startfile(REPORTS)
        except Exception as e:
            self._log(f"⚠️ {e}")

    def _prog(self, pct, txt):
        self._step_txt = txt
        self.root.after(0, lambda p=pct: self.pbar.config(value=p))

    def _set_busy(self, on):
        self._busy = on
        if on:
            self._spin_loop()

    def _spin_loop(self):
        try:
            if self._busy:
                self._spin_i = 1 - self._spin_i
                self.step_label.config(text=("⏳" if self._spin_i else "⌛") + " " + self._step_txt)
                self.root.after(400, self._spin_loop)
            else:
                self.step_label.config(text="⏳ " + self._step_txt)
        except Exception:
            pass

    def _set_analysis(self, on):
        st = tk.NORMAL if on else tk.DISABLED
        self.btn_go.config(state=st)
        self.btn_clean.config(state=st)
        self.btn_split.config(state=st)

    def _log(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        self.log.configure(state='normal')
        self.log.insert(tk.END, f"[{ts}] {msg}\n")
        self.log.see(tk.END)
        self.log.configure(state='disabled')

    def _show_details(self, txt):
        self.details.configure(state='normal')
        self.details.delete('1.0', tk.END)
        self.details.insert(tk.END, txt)
        self.details.configure(state='disabled')

    def _browse(self):
        p = filedialog.askopenfilename(title="Audio ou vidéo",
                                       filetypes=[("Media", "*.wav *.mp3 *.m4a *.mp4 *.mkv *.avi *.webm *.ogg"),
                                                  ("Tous", "*.*")])
        if p:
            self.src_var.set(p)
            self._log(f"📂 {Path(p).name}")

    def _manual_repair(self):
        self._log("📦 installation locale numpy+scipy dans argos_apis/ (1-2 min)…")
        threading.Thread(target=self._auto_repair, daemon=True).start()

    def _auto_repair(self):
        self._set_busy(True)
        self._prog(10, "réparation APIs…")
        ok = repair_apis()
        self._set_busy(False)
        self._prog(100, "APIs prêtes" if ok else "échec réparation")
        self._set_analysis(ok)
        self.root.after(0, lambda: self._log(
            f"✅ APIs réparées (numpy: {numpy_source()})" if ok else
            "❌ échec réparation (py -m pip install numpy scipy)"))

    def _analyze(self):
        src = Path(self.src_var.get())
        if not src.exists():
            messagebox.showerror("Erreur", "Choisis d'abord un fichier (📂)")
            return
        self._set_analysis(False)
        threading.Thread(target=self._work_single, args=(src,), daemon=True).start()

    def _work_single(self, src):
        self._set_busy(True)
        try:
            self._prog(5, "extraction WAV…")
            ff = find_ffmpeg()
            wav = src if src.suffix.lower() == ".wav" else None
            if wav is None:
                if ff is None:
                    self.root.after(0, lambda: self._log("❌ ffmpeg introuvable"))
                    return
                wav = to_wav(ff, src, REPORTS / ("raw_" + src.stem + ".wav"))
            if wav is None:
                self.root.after(0, lambda: self._log("❌ extraction impossible"))
                return
            self._prog(30, "analyse bio-acoustique…")
            r = analyze_wav(wav)
            self._prog(100, "terminé")
            if "error" not in r:
                rep = write_reports(src.name, r, "brut")
                self.root.after(0, lambda rep=rep: self._log(f"💾 Rapport: {rep}"))
            self.root.after(0, lambda r=r, n=src.name: self._show_one(r, n))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ " + str(e)))
        finally:
            self._set_busy(False)
            self.root.after(0, lambda: self._set_analysis(True))

    def _clean_analyze(self):
        src = Path(self.src_var.get())
        if not src.exists():
            messagebox.showerror("Erreur", "Choisis d'abord un fichier (📂)")
            return
        self._set_analysis(False)
        threading.Thread(target=self._work_clean, args=(src,), daemon=True).start()

    def _work_clean(self, src):
        self._set_busy(True)
        try:
            self._prog(5, "extraction WAV…")
            ff = find_ffmpeg()
            wav = src if src.suffix.lower() == ".wav" else (
                to_wav(ff, src, REPORTS / ("raw_" + src.stem + ".wav")) if ff else None)
            if wav is None:
                self.root.after(0, lambda: self._log("❌ extraction impossible"))
                return
            self._prog(25, "🧼 nettoyage bande voix 85-3000 Hz…")
            x, sr = read_wav_mono(wav)
            y = clean_voice(x, sr)
            clean = REPORTS / ("clean_" + wav.name)
            write_wav(clean, y, sr)
            self._prog(45, "analyse nettoyée…")
            r = analyze_wav(clean)
            self._prog(100, "terminé")
            if "error" not in r:
                rep = write_reports(src.name, r, "nettoye")
                self.root.after(0, lambda rep=rep: self._log(f"💾 Rapport: {rep}"))
            self.root.after(0, lambda r=r, n=src.name: self._show_one(r, "🧼 " + n))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ " + str(e)))
        finally:
            self._set_busy(False)
            self.root.after(0, lambda: self._set_analysis(True))

    def _show_one(self, r, name):
        if "error" in r:
            self._log(f"❌ {name}: {r['error']}")
            return
        self._log(f"⚖️ {name}: score {r['score']} → {r['verdict']}")
        for c in r["clues"]:
            self._log(f"   ├── {c}")
        col = '#4CAF50' if "HUMAINE" in r["verdict"] else self.RD if "IA" in r["verdict"] else self.OR
        self.verdict_label.config(text=f"⚖️ {r['verdict']} (score {r['score']})", fg=col)
        self._show_details(json.dumps(r, indent=2, ensure_ascii=False))

    def _split(self):
        src = Path(self.src_var.get())
        if not src.exists():
            messagebox.showerror("Erreur", "Choisis d'abord un fichier (📂)")
            return
        ff = find_ffmpeg()
        if ff is None:
            messagebox.showerror("Erreur", "ffmpeg introuvable (dossier ytdl/)")
            return
        self._set_analysis(False)
        threading.Thread(target=self._work_split, args=(src, ff), daemon=True).start()

    def _work_split(self, src, ff):
        self._set_busy(True)
        try:
            total = probe_duration(ff, src)
            if total <= 0:
                self.root.after(0, lambda: self._log("❌ durée illisible"))
                return
            n = int(math.ceil(total / CHUNK))
            tmp = REPORTS / f"split_{int(time.time())}"
            tmp.mkdir(parents=True, exist_ok=True)
            self.root.after(0, lambda n=n: self._log(f"✂️ {n} tranche(s) de 2 min…"))
            results = []
            for i in range(n):
                a, b = i * CHUNK, min(total, (i + 1) * CHUNK)
                self._prog(5 + int(85 * i / n), f"tranche {i + 1}/{n}…")
                wav = to_wav(ff, src, tmp / f"seg_{i:02d}.wav", start=a, dur=CHUNK)
                if wav is None:
                    continue
                r = analyze_wav(wav)
                if "error" in r:
                    continue
                results.append(r)
                self.root.after(0, lambda i=i, a=a, b=b, r=r: self._log(
                    f"🎬 tranche {i + 1} ({int(a) // 60:02d}:{int(a) % 60:02d}->"
                    f"{int(b) // 60:02d}:{int(b) % 60:02d}) score {r['score']} → {r['verdict']}"))
            self._prog(100, "terminé")
            if not results:
                self.root.after(0, lambda: self._log("❌ aucune tranche analysable"))
                return
            hum = sum(1 for r in results if "HUMAINE" in r["verdict"])
            ia = sum(1 for r in results if "IA" in r["verdict"])
            moy = sum(r["score"] for r in results) / len(results)
            if hum > ia and hum >= max(1, len(results) // 3):
                glob, col = "VOIX HUMAINE probable", '#4CAF50'
            elif ia > hum and ia >= max(1, len(results) // 3):
                glob, col = "SUSPECT IA / TTS", self.RD
            else:
                glob, col = "INCONCLUSIF", self.OR
            payload = {"file": src.name, "global": glob, "tranches": results}
            rep = write_reports(src.name, payload, "split")
            self.root.after(0, lambda: self._log(
                f"🧮 GLOBAL: {hum} humain(s) • {ia} IA • {len(results) - hum - ia} inconclus → {glob}"))
            self.root.after(0, lambda rep=rep: self._log(f"💾 Rapport: {rep}"))
            self.root.after(0, lambda: self.verdict_label.config(
                text=f"⚖️ {glob} ({hum}✅ / {ia}🚩 sur {len(results)}, moy {moy:+.1f})", fg=col))
            self.root.after(0, lambda: self._show_details(
                json.dumps(payload, indent=2, ensure_ascii=False)))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log("❌ " + str(e)))
        finally:
            self._set_busy(False)
            self.root.after(0, lambda: self._set_analysis(True))


def main():
    try:
        ForensicsApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()