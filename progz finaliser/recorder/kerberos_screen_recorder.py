#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎬 KERBEROS SCREEN RECORDER — Capture Vidéo d'Écran
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 1.3.1 (Corrigé pour Python 3.13)
Author: Victor Pozen | GPLv3
"""
import os
import sys
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import cv2
    import numpy as np
    HAS_CV = True
except ImportError:
    HAS_CV = False
    print("❌ OpenCV requis: python -m pip install opencv-python numpy")
    input("Appuyez sur Entrée pour quitter...")
    sys.exit(1)

try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

if not HAS_MSS and not HAS_PIL:
    print("❌ mss ou PIL requis: python -m pip install mss Pillow")
    input("Appuyez sur Entrée pour quitter...")
    sys.exit(1)

RECORDER_ROOT = Path(__file__).parent.resolve()
(RECORDER_ROOT / "logs").mkdir(parents=True, exist_ok=True)
(RECORDER_ROOT / "reports" / "screen_recordings").mkdir(parents=True, exist_ok=True)
(RECORDER_ROOT / "reports" / "timelapse").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(RECORDER_ROOT / 'logs' / 'recorder.log', encoding='utf-8')
    ]
)
logger = logging.getLogger("KerberosRecorder")

class ScreenRecorderEngine:
    """Moteur de capture : vidéo MP4 ou intervallomètre photo"""
    def __init__(self, output_path: Path, duration: int = 60, fps: int = 10,
                 monitor: Optional[int] = None, region: Optional[Tuple[int, int, int, int]] = None,
                 timelapse: bool = False, interval: int = 5,
                 timelapse_dir: Optional[Path] = None):
        self.output_path = output_path
        self.duration = duration
        self.fps = fps
        self.monitor = monitor
        self.region = region
        self.timelapse = timelapse
        self.interval = max(1, interval)
        self.timelapse_dir = timelapse_dir
        self.is_recording = False
        self.is_paused = False
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self.frames_captured = 0
        self.start_time = None
        self.elapsed = 0.0
        self.writer: Optional[cv2.VideoWriter] = None
        self.frame_size: Optional[Tuple[int, int]] = None

    def _get_monitor_dict(self) -> Dict[str, Any]:
        if self.monitor is not None:
            with mss.mss() as sct:
                return sct.monitors[self.monitor]
        elif self.region:
            return {"left": self.region[0], "top": self.region[1],
                    "width": self.region[2], "height": self.region[3]}
        else:
            with mss.mss() as sct:
                return sct.monitors[0]

    def _capture_frame(self) -> Optional[np.ndarray]:
        try:
            if HAS_MSS:
                with mss.mss() as sct:
                    mon = self._get_monitor_dict()
                    screenshot = sct.grab(mon)
                    frame = np.array(screenshot)
                    return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            else:
                if self.region:
                    l, t, w, h = self.region
                    bbox = (l, t, l + w, t + h)
                else:
                    bbox = None
                img = ImageGrab.grab(bbox=bbox)
                return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Erreur capture: {e}")
            return None

    def start(self) -> bool:
        if self.is_recording:
            logger.warning("⚠️ Déjà en cours")
            return False
        
        test_frame = self._capture_frame()
        if test_frame is None:
            logger.error("❌ Impossible de capturer l'écran")
            return False
        
        h, w = test_frame.shape[:2]
        self.frame_size = (w, h)
        
        if not self.timelapse:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(str(self.output_path), fourcc, self.fps, self.frame_size)
            if not self.writer.isOpened():
                logger.error(f"❌ Impossible d'ouvrir {self.output_path}")
                return False
        
        self.is_recording = True
        self.is_paused = False
        self._stop_event.clear()
        self._pause_event.set()
        self.frames_captured = 0
        self.start_time = time.time()
        
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        
        mode = f"INTERVALLO 1 photo/{self.interval}s" if self.timelapse else f"VIDÉO {w}x{h} @ {self.fps} FPS"
        logger.info(f"▶️ Enregistrement démarré ({mode}): {self.output_path.name}")
        return True

    def _record_loop(self):
        if self.timelapse:
            self._timelapse_loop()
            self._finalize()
            return
        
        frame_interval = 1.0 / self.fps
        while not self._stop_event.is_set():
            if not self._pause_event.is_set():
                time.sleep(0.1)
                continue
            
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration:
                logger.info(f"⏱️ Durée atteinte ({self.duration}s)")
                break
            
            frame = self._capture_frame()
            if frame is not None:
                if frame.shape[1] != self.frame_size[0] or frame.shape[0] != self.frame_size[1]:
                    frame = cv2.resize(frame, self.frame_size)
                self.writer.write(frame)
                self.frames_captured += 1
            
            self.elapsed = time.time() - self.start_time
            time.sleep(frame_interval)
        
        self._finalize()

    def _timelapse_loop(self):
        """Mode reflex : 1 photo toutes les interval secondes."""
        next_shot = time.time()
        while not self._stop_event.is_set():
            if not self._pause_event.is_set():
                time.sleep(0.1)
                continue
            
            self.elapsed = time.time() - self.start_time
            if self.elapsed >= self.duration:
                logger.info(f"️ Durée atteinte ({self.duration}s)")
                break
            
            if time.time() >= next_shot:
                frame = self._capture_frame()
                if frame is not None:
                    p = self.timelapse_dir / f"img_{self.frames_captured:04d}.jpg"
                    cv2.imwrite(str(p), frame)
                    self.frames_captured += 1
                    logger.info(f"📷 Photo {self.frames_captured}: {p.name}")
                next_shot = time.time() + self.interval
            time.sleep(0.05)

    def _finalize(self):
        self.is_recording = False
        if self.writer:
            self.writer.release()
            self.writer = None
        duration = time.time() - self.start_time if self.start_time else 0
        if self.timelapse:
            logger.info(f"📷 Intervallomètre terminé: {self.frames_captured} photos en {duration:.0f}s -> {self.timelapse_dir}")
        else:
            logger.info(f"⏹️ Enregistrement terminé: {self.frames_captured} frames, {duration:.1f}s")

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()

    def pause(self):
        self._pause_event.clear()
        self.is_paused = True
        logger.info("⏸️ Pause")

    def resume(self):
        self._pause_event.set()
        self.is_paused = False
        logger.info("▶️ Reprise")

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_recording": self.is_recording,
            "is_paused": self.is_paused,
            "frames_captured": self.frames_captured,
            "elapsed": self.elapsed,
            "duration": self.duration,
            "fps": self.fps,
            "output": str(self.output_path)
        }

class KerberosRecorderApp:
    BG_DARK = '#1e1e1e'
    BG_MEDIUM = '#2d2d2d'
    FG_CYAN = '#00ffcc'
    FG_GREEN = '#4CAF50'
    FG_RED = '#ff5252'
    FG_ORANGE = '#ff9800'
    FG_WHITE = '#ffffff'
    BTN_COLOR = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(" KERBEROS SCREEN RECORDER v1.3")
        self.root.geometry("900x740")
        self.root.configure(bg=self.BG_DARK)
        self.engine: Optional[ScreenRecorderEngine] = None
        self._update_timer_running = False
        self._setup_styles()
        self._build_ui()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        logger.info("Kerberos Screen Recorder v1.3 prêt")
        self.root.mainloop()

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TFrame', background=self.BG_DARK)
        style.configure('TLabel', background=self.BG_DARK, foreground=self.FG_CYAN, font=('Consolas', 10))
        style.configure('TButton', background=self.BTN_COLOR, foreground=self.FG_WHITE, font=('Consolas', 10))
        style.configure('TLabelframe', background=self.BG_DARK, foreground=self.FG_CYAN)
        style.configure('TLabelframe.Label', background=self.BG_DARK, foreground=self.FG_CYAN)

    def _build_ui(self):
        header = tk.Frame(self.root, bg=self.BG_MEDIUM)
        header.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(header, text="🎬 KERBEROS SCREEN RECORDER", bg=self.BG_MEDIUM, fg=self.FG_CYAN, font=("Consolas", 16, "bold")).pack(pady=10)
        tk.Label(header, text="Capture vidéo + intervallomètre forensique", bg=self.BG_MEDIUM, fg='#a0a0c0', font=("Consolas", 9)).pack()

        config_frame = ttk.LabelFrame(self.root, text="⚙️ Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        # Durée
        dur_frame = tk.Frame(config_frame, bg=self.BG_DARK)
        dur_frame.pack(fill=tk.X, pady=5)
        tk.Label(dur_frame, text="⏱️ Durée:", bg=self.BG_DARK, fg=self.FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.duration_min_var = tk.IntVar(value=1)
        tk.Scale(dur_frame, from_=1, to=60, orient=tk.HORIZONTAL, variable=self.duration_min_var, bg=self.BG_MEDIUM, fg=self.FG_CYAN, highlightthickness=0, length=450, showvalue=0, resolution=1, command=self._on_duration_change).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.duration_label = tk.Label(dur_frame, text="1 min", bg=self.BG_DARK, fg=self.FG_ORANGE, font=("Consolas", 11, "bold"), width=10, anchor='w')
        self.duration_label.pack(side=tk.LEFT, padx=5)

        # FPS
        fps_frame = tk.Frame(config_frame, bg=self.BG_DARK)
        fps_frame.pack(fill=tk.X, pady=5)
        tk.Label(fps_frame, text="🎞️ FPS:", bg=self.BG_DARK, fg=self.FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.fps_var = tk.IntVar(value=10)
        ttk.Spinbox(fps_frame, textvariable=self.fps_var, from_=5, to=30, increment=5, width=5).pack(side=tk.LEFT, padx=5)
        tk.Label(fps_frame, text="(5-30, 10 recommandé)", bg=self.BG_DARK, fg='#a0a0c0', font=("Consolas", 9)).pack(side=tk.LEFT, padx=5)

        # Écran
        mon_frame = tk.Frame(config_frame, bg=self.BG_DARK)
        mon_frame.pack(fill=tk.X, pady=5)
        tk.Label(mon_frame, text="🖥️ Écran:", bg=self.BG_DARK, fg=self.FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.monitor_var = tk.StringVar(value="0 (Tous)")
        ttk.Combobox(mon_frame, textvariable=self.monitor_var, values=["0 (Tous)", "1 (Écran 1)", "2 (Écran 2)"], width=15, state='readonly').pack(side=tk.LEFT, padx=5)

        # Intervallomètre
        tl_frame = tk.Frame(config_frame, bg=self.BG_DARK)
        tl_frame.pack(fill=tk.X, pady=5)
        self.timelapse_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tl_frame, text="📷 Intervallomètre (image par image)", variable=self.timelapse_var, bg=self.BG_DARK, fg=self.FG_CYAN, selectcolor=self.BG_MEDIUM, activebackground=self.BG_DARK, activeforeground=self.FG_CYAN, command=self._on_timelapse_toggle).pack(side=tk.LEFT, padx=5)
        tk.Label(tl_frame, text="Intervalle:", bg=self.BG_DARK, fg=self.FG_CYAN).pack(side=tk.LEFT, padx=(15, 0))
        self.interval_var = tk.IntVar(value=5)
        self.interval_scale = tk.Scale(tl_frame, from_=1, to=60, orient=tk.HORIZONTAL, variable=self.interval_var, bg=self.BG_MEDIUM, fg=self.FG_CYAN, highlightthickness=0, length=220, showvalue=1, resolution=1, state=tk.DISABLED)
        self.interval_scale.pack(side=tk.LEFT, padx=5)
        tk.Label(tl_frame, text="s (1 s -> 1 min)", bg=self.BG_DARK, fg='#a0a0c0', font=("Consolas", 9)).pack(side=tk.LEFT, padx=5)

        # Dossier de sortie
        out_frame = tk.Frame(config_frame, bg=self.BG_DARK)
        out_frame.pack(fill=tk.X, pady=5)
        tk.Label(out_frame, text="📁 Sortie:", bg=self.BG_DARK, fg=self.FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.output_var = tk.StringVar(value=str(RECORDER_ROOT / "reports" / "screen_recordings"))
        ttk.Entry(out_frame, textvariable=self.output_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(out_frame, text="📂 Parcourir", bg=self.BTN_COLOR, fg=self.FG_WHITE, command=self._browse_output).pack(side=tk.LEFT, padx=5)

        # Status
        status_frame = tk.Frame(self.root, bg=self.BG_MEDIUM)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        self.timer_label = tk.Label(status_frame, text="⏱️ 00:00 / 01:00", bg=self.BG_MEDIUM, fg=self.FG_CYAN, font=("Consolas", 24, "bold"))
        self.timer_label.pack(pady=10)
        self.status_label = tk.Label(status_frame, text="⏳ En attente", bg=self.BG_MEDIUM, fg='#a0a0c0', font=("Consolas", 11))
        self.status_label.pack()
        self.frames_label = tk.Label(status_frame, text="🎞️ 0 frames", bg=self.BG_MEDIUM, fg='#a0a0c0', font=("Consolas", 10))
        self.frames_label.pack(pady=5)

        # Boutons
        btn_frame = tk.Frame(self.root, bg=self.BG_DARK)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        self.btn_start = tk.Button(btn_frame, text="▶️ Démarrer", bg=self.FG_GREEN, fg=self.FG_WHITE, font=("Consolas", 12, "bold"), command=self._start_recording)
        self.btn_start.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.btn_pause = tk.Button(btn_frame, text="⏸️ Pause", bg=self.FG_ORANGE, fg=self.FG_WHITE, font=("Consolas", 12, "bold"), command=self._toggle_pause, state=tk.DISABLED)
        self.btn_pause.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.btn_stop = tk.Button(btn_frame, text="⏹️ Arrêter", bg=self.FG_RED, fg=self.FG_WHITE, font=("Consolas", 12, "bold"), command=self._stop_recording, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Logs
        log_frame = ttk.LabelFrame(self.root, text=" Logs", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text = tk.Text(log_frame, height=12, bg=self.BG_MEDIUM, fg=self.FG_GREEN, font=('Consolas', 10), state='disabled')
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self._log("Kerberos Screen Recorder v1.3 prêt")
        self._log(f"📁 Sortie par défaut: {self.output_var.get()}")

    def _on_timelapse_toggle(self):
        self.interval_scale.config(state=tk.NORMAL if self.timelapse_var.get() else tk.DISABLED)

    def _on_duration_change(self, val):
        minutes = int(float(val))
        txt = "1 h" if minutes == 60 else f"{minutes} min"
        self.duration_label.config(text=txt)
        self.timer_label.config(text=f"⏱️ 00:00 / {minutes:02d}:00")

    def _browse_output(self):
        path = filedialog.askdirectory(title="Dossier de sortie")
        if path:
            self.output_var.set(path)

    def _log(self, msg: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def _start_recording(self):
        duration = self.duration_min_var.get() * 60
        fps = self.fps_var.get()
        output_dir = Path(self.output_var.get())
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"kerberos_rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = output_dir / filename
        monitor_idx = int(self.monitor_var.get().split()[0])
        monitor = monitor_idx if monitor_idx > 0 else None
        timelapse = self.timelapse_var.get()
        interval = self.interval_var.get()
        
        tl_dir = None
        if timelapse:
            tl_dir = RECORDER_ROOT / "reports" / "timelapse" / f"tl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            tl_dir.mkdir(parents=True, exist_ok=True)

        self.engine = ScreenRecorderEngine(
            output_path=output_path, duration=duration, fps=fps, monitor=monitor,
            timelapse=timelapse, interval=interval, timelapse_dir=tl_dir
        )

        if self.engine.start():
            self.btn_start.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.NORMAL)
            self.status_label.config(text="🔴 ENREGISTREMENT", fg=self.FG_RED)
            if timelapse:
                self._log(f"📷 Intervallomètre: 1 photo / {interval}s dans {tl_dir}")
            else:
                self._log(f"▶️ Enregistrement démarré: {filename}")
                self._log(f"⏱️ Durée: {duration}s ({duration // 60} min)")
            self._start_timer_update()
        else:
            messagebox.showerror("Erreur", "Impossible de démarrer l'enregistrement")

    def _toggle_pause(self):
        if not self.engine: return
        if self.engine.is_paused:
            self.engine.resume()
            self.btn_pause.config(text="️ Pause")
            self.status_label.config(text="🔴 ENREGISTREMENT", fg=self.FG_RED)
            self._log("▶️ Reprise")
        else:
            self.engine.pause()
            self.btn_pause.config(text="▶️ Reprendre")
            self.status_label.config(text="️ PAUSE", fg=self.FG_ORANGE)
            self._log("⏸️ Pause")

    def _stop_recording(self):
        if self.engine:
            self.engine.stop()
            self.btn_start.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED, text="️ Pause")
            self.btn_stop.config(state=tk.DISABLED)
            self.status_label.config(text="⏹️ Terminé", fg=self.FG_GREEN)
            self._log("️ Enregistrement arrêté")
            self._update_timer_running = False

    def _start_timer_update(self):
        self._update_timer_running = True
        self._update_timer()

    def _update_timer(self):
        if not self._update_timer_running or not self.engine:
            return
        
        status = self.engine.get_status()
        elapsed = int(status["elapsed"])
        duration = status["duration"]
        frames = status["frames_captured"]
        
        mins_e, secs_e = divmod(elapsed, 60)
        mins_d, secs_d = divmod(duration, 60)
        self.timer_label.config(text=f"⏱️ {mins_e:02d}:{secs_e:02d} / {mins_d:02d}:{secs_d:02d}")
        
        lbl = "📷" if self.engine.timelapse else "🎞️"
        self.frames_label.config(text=f"{lbl} {frames} {'photos' if self.engine.timelapse else 'frames'}")
        
        if status["is_recording"]:
            self.root.after(100, self._update_timer)
        else:
            self._update_timer_running = False
            if self.engine.timelapse:
                self._log(f"✅ {frames} photos sauvegardées: {self.engine.timelapse_dir}")
                messagebox.showinfo("Terminé", f"Intervallomètre terminé:\n{frames} photos\n{self.engine.timelapse_dir}")
            else:
                self._log(f"✅ Vidéo sauvegardée: {status['output']}")
                messagebox.showinfo("Terminé", f"Vidéo enregistrée:\n{status['output']}\n{frames} frames capturées")

    def _on_close(self):
        if self.engine and self.engine.is_recording:
            if messagebox.askyesno("Fermer", "Enregistrement en cours. Arrêter ?"):
                self.engine.stop()
        self.root.destroy()

def main():
    try:
        KerberosRecorderApp()
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        input("Appuyez sur Entrée pour quitter...")

if __name__ == '__main__':
    main()