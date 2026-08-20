# -*- coding: utf-8 -*-
# kerberos-diag-local.py — Diagnostic local éthique
# Copyright (C) 2025 Victor Pozen — GPLv3
# « Pas de trace. Pas de nuage. Juste du code qui protège. »
# (-; — Victor.Pozen
# 🔗 https://github.com/victorpozen/kerberos
# 💝 https://liberapay.com/EthicalKerberos/

import os
import sys
import platform
import time
import socket
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime

BG = "#1e1e1e"
FG = "#e0e0e0"
ACCENT = "#00ccaa"
SUCCESS = "#00ff00"
DANGER = "#8b0000"

# === UTILS ===
def run_cmd(cmd, timeout=5):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def make_copy_paste(widget):
    menu = tk.Menu(widget, tearoff=0, bg="#2d2d2d", fg="white", font=("Consolas", 9))
    menu.add_command(label="Copier", command=lambda: widget.event_generate("<<Copy>>"))
    def show_menu(e):
        try:
            widget.selection_get()
            menu.entryconfig("Copier", state="normal")
        except:
            menu.entryconfig("Copier", state="disabled")
        menu.tk_popup(e.x_root, e.y_root)
    widget.bind("<Button-3>", show_menu)
    widget.bind("<Control-c>", lambda e: widget.event_generate("<<Copy>>"))

# === DIAGNOSTIC ===
def diag_system():
    results = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    # CPU
    try:
        import psutil
        cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else "N/A"
        results["cpu"] = {
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "freq_mhz": round(cpu_freq) if isinstance(cpu_freq, (int, float)) else "N/A",
            "usage_pct": psutil.cpu_percent(interval=1)
        }
        results["ram"] = {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 1),
            "used_pct": psutil.virtual_memory().percent
        }
    except:
        # Fallback sans psutil (Win7 safe)
        ok, out, _ = run_cmd("wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors /value", 3)
        if ok:
            cores = threads = "N/A"
            for line in out.splitlines():
                if "NumberOfCores=" in line:
                    cores = line.split("=")[1]
                elif "NumberOfLogicalProcessors=" in line:
                    threads = line.split("=")[1]
            results["cpu"] = {"cores": cores, "threads": threads, "freq_mhz": "N/A", "usage_pct": "N/A"}
        else:
            results["cpu"] = {"error": "wmic non disponible"}
        results["ram"] = {"error": "psutil requis pour RAM détaillée"}

    # Disque (réactivité écriture)
    test_file = Path("kerberos_diag_temp.bin")
    start = time.time()
    try:
        with open(test_file, "wb") as f:
            f.write(b"0" * 1024 * 1024)  # 1 Mo
        write_time = time.time() - start
        results["disk_write"] = {
            "time_sec": round(write_time, 3),
            "speed_mbps": round(8 / write_time, 1) if write_time > 0 else 0,
            "status": "✅ Rapide" if write_time < 0.5 else "⚠️ Lent" if write_time < 2 else "❌ Très lent"
        }
    except Exception as e:
        results["disk_write"] = {"error": str(e)}
    finally:
        if test_file.exists():
            try:
                test_file.unlink()
            except:
                pass

    # Internet
    results["internet"] = {"github_api": "❌ Échec", "latency_ms": "N/A", "dns": "N/A"}
    
    # DNS
    try:
        start = time.time()
        socket.getaddrinfo("github.com", 80)
        results["internet"]["dns"] = f"{int((time.time() - start)*1000)} ms"
    except:
        results["internet"]["dns"] = "❌ Échec DNS"
    
    # Latence GitHub API
    try:
        start = time.time()
        sock = socket.create_connection(("api.github.com", 443), timeout=10)
        sock.close()
        results["internet"]["latency_ms"] = f"{int((time.time() - start)*1000)} ms"
    except:
        pass
    
    # Test réel (léger)
    try:
        import urllib.request
        req = urllib.request.Request("https://api.github.com/rate_limit")
        req.add_header("User-Agent", "Kerberos-Diag")
        start = time.time()
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.getcode() == 200:
                results["internet"]["github_api"] = f"✅ OK ({int((time.time() - start)*1000)} ms)"
    except:
        pass

    return results

def generate_html_report(data):
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Kerberos Diagnostic</title>
<style>body{{font-family:'Segoe UI',sans-serif;background:#1e1e1e;color:#e0e0e0;margin:20px;}}
h1{{color:#00ff00;}}.section{{margin-bottom:20px;}}
.good{{color:#4caf50;}}.warn{{color:#ff9800;}}.bad{{color:#f44336;}}
</style></head><body>
<h1>🛡️ KERBEROS — Diagnostic Local</h1>
<p><strong>Date :</strong> {data['timestamp']}</p>
<p><strong>Système :</strong> {platform.system()} {platform.release()} ({platform.machine()})</p>
<p><strong>Python :</strong> {platform.python_version()}</p>

<div class="section">
<h2>🧠 CPU</h2>
<p>Cœurs physiques : <strong>{data['cpu'].get('cores', '?')}</strong></p>
<p>Threads logiques : <strong>{data['cpu'].get('threads', '?')}</strong></p>
<p>Fréquence : <strong>{data['cpu'].get('freq_mhz', '?')} MHz</strong></p>
<p>Utilisation : <strong class="{'good' if data['cpu'].get('usage_pct', 0) < 50 else 'warn' if data['cpu'].get('usage_pct', 0) < 80 else 'bad'}">{data['cpu'].get('usage_pct', '?')} %</strong></p>
</div>

<div class="section">
<h2>💾 RAM</h2>
<p>Total : <strong>{data['ram'].get('total_gb', '?')} Go</strong></p>
<p>Disponible : <strong>{data['ram'].get('available_gb', '?')} Go</strong></p>
<p>Utilisée : <strong class="{'good' if data['ram'].get('used_pct', 0) < 60 else 'warn' if data['ram'].get('used_pct', 0) < 85 else 'bad'}">{data['ram'].get('used_pct', '?')} %</strong></p>
</div>

<div class="section">
<h2>💽 Réactivité disque (écriture 1 Mo)</h2>
<p>Temps : <strong class="{data['disk_write'].get('status', '').replace('✅', 'good').replace('⚠️', 'warn').replace('❌', 'bad')}">
{data['disk_write'].get('time_sec', '?')} s</strong></p>
<p>Débit : <strong>{data['disk_write'].get('speed_mbps', '?')} Mbps</strong></p>
</div>

<div class="section">
<h2>🌐 Internet</h2>
<p>DNS github.com : <strong>{data['internet']['dns']}</strong></p>
<p>Latence API GitHub : <strong>{data['internet']['latency_ms']}</strong></p>
<p>Accès GitHub API : <strong class="{'good' if '✅' in data['internet']['github_api'] else 'bad'}">{data['internet']['github_api']}</strong></p>
</div>

<hr>
<p><em>Kerberos — Sécurité desktop locale. Zéro cloud. Zéro trace.<br>
GPLv3 • White hat only • (-; — Victor.Pozen</em></p>
</body></html>"""
    
    report_path = Path(f"kerberos_diag_{datetime.now():%Y%m%d_%H%M%S}.html")
    try:
        report_path.write_text(html, encoding="utf-8")
        return str(report_path)
    except Exception as e:
        return f"❌ Échec génération rapport : {e}"

# === GUI ===
class KerberosDiag:
    def __init__(self, root):
        self.root = root
        root.title("🛡️ Kerberos Diagnostic — Local Only")
        root.geometry("600x500")
        root.configure(bg=BG)

        tk.Label(root, text="KERBEROS", fg=SUCCESS, bg=BG, font=("Consolas", 16, "bold")).pack(pady=(12, 4))
        tk.Label(root, text="Diagnostic local — RAM / CPU / Disque / Internet", fg=ACCENT, bg=BG, font=("Consolas", 10)).pack()
        tk.Label(root, text="« Pas de trace. Pas de nuage. Juste du code qui protège. »", fg="#666", bg=BG, font=("Consolas", 9, "italic")).pack(pady=(2, 10))

        self.text = tk.Text(root, font=("Consolas", 9), bg="#0a0a0a", fg="#e0e0e0", wrap=tk.WORD)
        self.text.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        make_copy_paste(self.text)

        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=(0, 15))
        tk.Button(btn_frame, text="🔍 Lancer le diagnostic", command=self.run_diag,
                  bg="#1e4d2b", fg="white", font=("Consolas", 10), padx=20).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📄 Ouvrir dernier rapport", command=self.open_last_report,
                  bg="#252525", fg=ACCENT, font=("Consolas", 10), padx=15).pack(side=tk.LEFT, padx=5)

        tk.Label(root, text="GPLv3 • White hat only • (-; — Victor.Pozen", fg="#555", bg=BG, font=("Consolas", 8)).pack()

        self.text.insert(tk.END, "ℹ️ Cliquez sur « Lancer le diagnostic » pour analyser :\n")
        self.text.insert(tk.END, " • CPU (cœurs, fréquence, usage)\n")
        self.text.insert(tk.END, " • RAM (totale, disponible)\n")
        self.text.insert(tk.END, " • Disque (vitesse d'écriture)\n")
        self.text.insert(tk.END, " • Internet (DNS, latence, GitHub)\n")
        self.text.config(state=tk.DISABLED)

    def run_diag(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.insert(tk.END, "🔍 Démarrage du diagnostic Kerberos...\n")
        self.text.update()
        time.sleep(0.3)

        data = diag_system()
        self.text.insert(tk.END, f"\n✅ Diagnostic terminé à {data['timestamp']}\n\n")

        # Affichage console
        self.text.insert(tk.END, f"🧠 CPU : {data['cpu'].get('cores', '?')} cœurs, {data['cpu'].get('usage_pct', '?')}% usage\n")
        self.text.insert(tk.END, f"💾 RAM : {data['ram'].get('available_gb', '?')}/{data['ram'].get('total_gb', '?')} Go dispo\n")
        dw = data["disk_write"]
        self.text.insert(tk.END, f"💽 Disque : {dw.get('time_sec', '?')}s ({dw.get('status', '?')})\n")
        net = data["internet"]
        self.text.insert(tk.END, f"🌐 Internet : DNS={net['dns']}, API={net['github_api']}\n")

        # Génération HTML
        report = generate_html_report(data)
        self.text.insert(tk.END, f"\n📄 Rapport HTML : {Path(report).name}\n")
        self.last_report = report
        self.text.config(state=tk.DISABLED)

    def open_last_report(self):
        if hasattr(self, 'last_report') and Path(self.last_report).exists():
            os.startfile(self.last_report)
        else:
            reports = sorted(Path(".").glob("kerberos_diag_*.html"))
            if reports:
                os.startfile(reports[-1])
            else:
                messagebox.showinfo("ℹ️", "Aucun rapport trouvé.")

if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiag(root)
    root.mainloop()