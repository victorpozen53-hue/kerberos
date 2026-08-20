#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎵 KERBEROS SONG RECORDER v1.0 — extraction audio de vidéos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 1.0 (vidéo -> MP3 / M4A / WAV, ffmpeg)
Author: Victor Pozen | GPLv3
- choisit une vidéo, extrait UNIQUEMENT le son (-vn)
- MP3 (libmp3lame) / M4A (aac = "mp4 audio") / WAV (pcm)
- ffmpeg : PATH système OU bundled via imageio_ffmpeg
- GUI tkinter style Kerberos + logs + progression + Stop
pip install imageio_ffmpeg   (si pas de ffmpeg.exe système)
"""
import re
import sys
import shutil
import threading
import subprocess
import logging
import traceback
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


def _excepthook(t, v, tb):
    print("❌ ERREUR CRITIQUE:\n" + "".join(traceback.format_exception(t, v, tb)))
    input("Appuyez sur Entrée pour fermer...")


sys.excepthook = _excepthook

REC_ROOT = Path(__file__).parent.resolve()
(REC_ROOT / "logs").mkdir(parents=True, exist_ok=True)
(REC_ROOT / "reports" / "songs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(),
                              logging.FileHandler(REC_ROOT / "logs" / "song_recorder.log",
                                                  encoding="utf-8")])
logger = logging.getLogger("KerberosSong")

CODECS = {"MP3": ("libmp3lame", ".mp3"),
          "M4A (audio mp4)": ("aac", ".m4a"),
          "WAV": ("pcm_s16le", ".wav")}


def find_ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _to_sec(h, m, s):
    return int(h) * 3600 + int(m) * 60 + float(s)


class SongRecorderApp:
    BG = '#1e1e1e'; BG2 = '#2d2d2d'; CY = '#00ffcc'; OR = '#ff9800'
    RD = '#ff5252'; GN = '#4CAF50'; WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎵 KERBEROS SONG RECORDER v1.0")
        self.root.geometry("900x680")
        self.root.configure(bg=self.BG)
        self.proc = None
        self.duration = 0.0
        self._build()
        ff = find_ffmpeg()
        self._log("🎵 Kerberos Song Recorder v1.0 prêt")
        self._log(f"🔧 ffmpeg: {ff if ff else '❌ ABSENT — pip install imageio_ffmpeg'}")
        self._log(f"📁 Sortie par défaut: {REC_ROOT / 'reports' / 'songs'}")
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        self.root.mainloop()

    def _build(self):
        header = tk.Frame(self.root, bg=self.BG2)
        header.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(header, text="🎵 KERBEROS SONG RECORDER", bg=self.BG2, fg=self.CY,
                 font=("Consolas", 16, "bold")).pack(pady=10)
        tk.Label(header, text="Extraction voix & son de vidéos -> MP3 / M4A / WAV",
                 bg=self.BG2, fg='#a0a0c0', font=("Consolas", 9)).pack()

        cfg = tk.LabelFrame(self.root, text="⚙️ Configuration", bg=self.BG, fg=self.CY,
                            font=("Consolas", 10))
        cfg.pack(fill=tk.X, padx=10, pady=5)

        f1 = tk.Frame(cfg, bg=self.BG)
        f1.pack(fill=tk.X, padx=8, pady=5)
        tk.Label(f1, text="🎬 Vidéo:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.src_var = tk.StringVar()
        tk.Entry(f1, textvariable=self.src_var, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(f1, text="📂", bg=self.BTN, fg=self.WH, command=self._browse_src).pack(side=tk.LEFT)

        f2 = tk.Frame(cfg, bg=self.BG)
        f2.pack(fill=tk.X, padx=8, pady=5)
        tk.Label(f2, text="📁 Sortie:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.out_var = tk.StringVar(value=str(REC_ROOT / "reports" / "songs"))
        tk.Entry(f2, textvariable=self.out_var, width=60, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=5)
        tk.Button(f2, text="📂", bg=self.BTN, fg=self.WH, command=self._browse_out).pack(side=tk.LEFT)

        f3 = tk.Frame(cfg, bg=self.BG)
        f3.pack(fill=tk.X, padx=8, pady=5)
        tk.Label(f3, text="🎼 Format:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.fmt_var = tk.StringVar(value="MP3")
        ttk.Combobox(f3, textvariable=self.fmt_var, values=list(CODECS.keys()),
                     width=16, state='readonly').pack(side=tk.LEFT, padx=5)
        tk.Label(f3, text="🎚️ Bitrate:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT, padx=(15, 0))
        self.br_var = tk.StringVar(value="192k")
        ttk.Combobox(f3, textvariable=self.br_var, values=["128k", "192k", "320k"],
                     width=7, state='readonly').pack(side=tk.LEFT, padx=5)

        st = tk.Frame(self.root, bg=self.BG2)
        st.pack(fill=tk.X, padx=10, pady=10)
        self.timer_label = tk.Label(st, text="⏱️ 00:00 / --:--", bg=self.BG2, fg=self.CY,
                                    font=("Consolas", 22, "bold"))
        self.timer_label.pack(pady=8)
        self.status_label = tk.Label(st, text="⏳ En attente", bg=self.BG2, fg='#a0a0c0',
                                     font=("Consolas", 11))
        self.status_label.pack()

        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=10)
        self.btn_go = tk.Button(bf, text="🎵 Extraire le son", bg=self.GN, fg=self.WH,
                                font=("Consolas", 12, "bold"), command=self._start)
        self.btn_go.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.btn_stop = tk.Button(bf, text="⏹️ Stop", bg=self.RD, fg=self.WH,
                                  font=("Consolas", 12, "bold"), command=self._stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        lf = tk.LabelFrame(self.root, text="📟 Logs", bg=self.BG, fg=self.CY,
                           font=("Consolas", 10))
        lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text = tk.Text(lf, height=12, bg=self.BG2, fg=self.GN,
                                font=('Consolas', 10), state='disabled')
        sb = ttk.Scrollbar(lf, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _browse_src(self):
        p = filedialog.askopenfilename(title="Vidéo source",
                                       filetypes=[("Vidéo", "*.mp4 *.mkv *.avi *.mov *.webm *.flv"),
                                                  ("Tous", "*.*")])
        if p:
            self.src_var.set(p)

    def _browse_out(self):
        p = filedialog.askdirectory(title="Dossier de sortie")
        if p:
            self.out_var.set(p)

    def _log(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def _start(self):
        ff = find_ffmpeg()
        if not ff:
            messagebox.showerror("Erreur", "ffmpeg introuvable :\npip install imageio_ffmpeg")
            return
        src = Path(self.src_var.get())
        if not src.exists():
            messagebox.showerror("Erreur", "Choisis une vidéo source")
            return
        out_dir = Path(self.out_var.get())
        out_dir.mkdir(parents=True, exist_ok=True)
        codec, ext = CODECS[self.fmt_var.get()]
        out = out_dir / (src.stem + ext)
        cmd = [str(ff), "-y", "-i", str(src), "-vn", "-acodec", codec]
        if ext != ".wav":
            cmd += ["-b:a", self.br_var.get()]
        cmd += [str(out)]
        self.btn_go.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.status_label.config(text="🎵 Extraction en cours…", fg=self.OR)
        self._log(f"▶️ Extraction: {src.name} -> {out.name}")
        threading.Thread(target=self._work, args=(cmd, out), daemon=True).start()

    def _work(self, cmd, out):
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                         stderr=subprocess.PIPE,
                                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            for raw in iter(self.proc.stderr.readline, b""):
                line = raw.decode("utf-8", errors="ignore")
                m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", line)
                if m:
                    self.duration = _to_sec(*m.groups())
                m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                if m:
                    cur = _to_sec(*m.groups())
                    self.root.after(0, lambda c=cur: self._progress(c))
            self.proc.wait()
            ok = self.proc.returncode == 0 and out.exists()
            self.root.after(0, lambda: self._done(ok, out))
        except Exception as e:
            self.root.after(0, lambda e=e: self._log(f"❌ {e}"))
            self.root.after(0, lambda: self._done(False, out))

    def _progress(self, cur):
        def fmt(s):
            return f"{int(s) // 60:02d}:{int(s) % 60:02d}"
        tot = fmt(self.duration) if self.duration else "--:--"
        self.timer_label.config(text=f"⏱️ {fmt(cur)} / {tot}")

    def _done(self, ok, out):
        self.proc = None
        self.btn_go.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        if ok:
            self.status_label.config(text="✅ Audio extrait", fg=self.GN)
            self._log(f"✅ Sauvegardé: {out}")
            logger.info(f"✅ Audio extrait: {out.name}")
        else:
            self.status_label.config(text="❌ Échec (codec ? essaie M4A)", fg=self.RD)
            self._log("❌ Échec — si MP3 refuse, passe en M4A (aac natif)")

    def _stop(self):
        if self.proc:
            self.proc.terminate()
            self._log("⏹️ Extraction arrêtée")
            self.status_label.config(text="⏹️ Arrêté", fg=self.OR)
            self.btn_go.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)

    def _on_close(self):
        if self.proc:
            self.proc.terminate()
        self.root.destroy()


def main():
    try:
        SongRecorderApp()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()