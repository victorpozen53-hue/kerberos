#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧮 ARGOS ENTROPY v1.0 — organe PRIVÉ : authenticité par entropie de Shannon
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — usage LOCAL, ne jamais partager
H = -Σ p(x) log2 p(x)
- entropie GLOBALE (histogramme 8 bits) : trop basse = trop propre = CGI suspect
- entropie du BRUIT résiduel (gray - blur) : l'empreinte du capteur
- comparaison A/B : comme la vidéo Skinny Bob (CGI 6.18 vs réel 6.50)
L'entropie est un INDICE, pas une preuve : croise avec multi-dates & ELA.
Usage : bouton organe dans ARGOS, ou python argos_entropy.py
"""
import sys
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

_p = Path(__file__).resolve().parent
ARGOS_ROOT = _p.parent if (_p.parent / "img").exists() or _p.name == "modules" else _p
EXTS = (".jpg", ".jpeg", ".png")


def shannon_entropy(gray):
    """H = -Σ p log2 p sur l'histogramme 8 bits."""
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    p = hist / hist.sum()
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def noise_entropy(gray):
    """Entropie du bruit résiduel = empreinte du capteur."""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    res = cv2.absdiff(gray, blur)
    return shannon_entropy(res)


class EntropyApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🧮 ARGOS ENTROPY v1.0 — Shannon anti-CGI")
        self.root.geometry("900x620")
        self.root.configure(bg=self.BG)
        self.stop_flag = False
        self._build()
        self._log("🧮 ENTROPY prêt — H globale + H du bruit (empreinte capteur)")
        self._log("Référence vidéo : CGI ≈ 6.18 • Skinny Bob ≈ 6.50")
        self.root.mainloop()

    def _build(self):
        f = tk.Frame(self.root, bg=self.BG)
        f.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(f, text="🅰️ Dossier A:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.a_var = tk.StringVar()
        tk.Entry(f, textvariable=self.a_var, width=40, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=3)
        tk.Button(f, text="📂", bg=self.BTN, fg=self.WH,
                  command=lambda: self._pick(self.a_var)).pack(side=tk.LEFT)
        tk.Label(f, text="🅱️ B:", bg=self.BG, fg=self.OR).pack(side=tk.LEFT, padx=(10, 0))
        self.b_var = tk.StringVar()
        tk.Entry(f, textvariable=self.b_var, width=40, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=3)
        tk.Button(f, text="📂", bg=self.BTN, fg=self.WH,
                  command=lambda: self._pick(self.b_var)).pack(side=tk.LEFT)

        s = tk.Frame(self.root, bg=self.BG)
        s.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(s, text="🚧 Seuil 'trop propre':", bg=self.BG, fg=self.OR).pack(side=tk.LEFT)
        self.thr_var = tk.DoubleVar(value=6.3)
        tk.Scale(s, from_=5.0, to=7.5, resolution=0.1, orient=tk.HORIZONTAL, variable=self.thr_var,
                 bg=self.BG2, fg=self.OR, highlightthickness=0, length=220).pack(side=tk.LEFT, padx=5)

        b = tk.Frame(self.root, bg=self.BG)
        b.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(b, text="🧮 Scanner A", bg='#4CAF50', fg=self.WH,
                  font=("Consolas", 11, "bold"), command=lambda: self._scan(self.a_var.get(), "A")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(b, text="🧮 Scanner B", bg='#4CAF50', fg=self.WH,
                  font=("Consolas", 11, "bold"), command=lambda: self._scan(self.b_var.get(), "B")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)
        tk.Button(b, text="⚖️ Comparer A/B", bg=self.OR, fg=self.BG,
                  font=("Consolas", 11, "bold"), command=self._compare).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        self.log = tk.Text(self.root, height=18, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _pick(self, var):
        p = filedialog.askdirectory(title="Dossier de JPEG")
        if p:
            var.set(p)

    def _log(self, msg):
        try:
            self.log.configure(state='normal')
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state='disabled')
        except Exception:
            pass

    def _stats(self, folder):
        hs, hns = [], []
        files = sorted([p for p in folder.glob("*.*") if p.suffix.lower() in EXTS])
        for p in files:
            if self.stop_flag:
                break
            img = cv2.imread(str(p))
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            hg, hn = shannon_entropy(gray), noise_entropy(gray)
            hs.append(hg)
            hns.append(hn)
            verdict = "⚠️ trop propre (CGI suspect)" if hg < self.thr_var.get() else "✅ signature capteur"
            self.root.after(0, lambda n=p.name, a=hg, c=hn, v=verdict:
                            self._log(f"🧮 {n}: H={a:.2f} bruit={c:.2f} -> {v}"))
        return (float(np.mean(hs)) if hs else 0.0, float(np.mean(hns)) if hns else 0.0, len(hs))

    def _scan(self, path_str, tag):
        folder = Path(path_str)
        if not path_str.strip() or not folder.exists():
            messagebox.showerror("Erreur", f"Choisis le dossier {tag}")
            return
        self.stop_flag = False
        threading.Thread(target=self._scan_work, args=(folder, tag), daemon=True).start()

    def _scan_work(self, folder, tag):
        avg_h, avg_hn, n = self._stats(folder)
        self.root.after(0, lambda: self._log(
            f"📊 {tag}: moyenne H={avg_h:.2f} • bruit={avg_hn:.2f} sur {n} image(s)"))

    def _compare(self):
        a, b = Path(self.a_var.get()), Path(self.b_var.get())
        if not a.exists() or not b.exists():
            messagebox.showerror("Erreur", "Il faut les dossiers A ET B")
            return
        self.stop_flag = False
        threading.Thread(target=self._compare_work, args=(a, b), daemon=True).start()

    def _compare_work(self, a, b):
        self.root.after(0, lambda: self._log("⚖️ Comparaison A/B (mode Skinny Bob)…"))
        ha, hna, na = self._stats(a)
        hb, hnb, nb = self._stats(b)
        diff = ha - hb

        def verdict():
            if abs(diff) < 0.1:
                return "🤝 entropies proches — même nature de bruit"
            lo = "A" if diff < 0 else "B"
            return f"🧊 {lo} est plus LISSE -> {lo} suspect CGI / retouche"

        self.root.after(0, lambda: self._log(
            f"⚖️ A H={ha:.2f} vs B H={hb:.2f} (Δ={diff:+.2f}) -> {verdict()}"))


def run():
    EntropyApp()
    return "✅ ARGOS ENTROPY fermé"


def main():
    try:
        EntropyApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()