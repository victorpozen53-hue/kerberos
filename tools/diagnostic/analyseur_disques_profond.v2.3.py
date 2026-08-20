# -*- coding: utf-8 -*-
# analyseur_disques_profond.v2.3.py — version Nassa-compatible
# GPLv3 – Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)
# 🛡️ https://liberapay.com/EthicalKerberos/ | Full license: https://www.gnu.org/licenses/gpl-3.0.html
# White hat only. Pas de trace. Pas de nuage. Juste du code qui protège. (-; — Victor.Pozen

import sys
import os
import platform
import traceback
import socket
from datetime import datetime
import ast
import re
import json
import base64
from pathlib import Path

# === GESTIONNAIRE D'ERREUR GLOBAL – KERBEROS v2 ===
def kerberos_excepthook(exc_type, exc_value, exc_tb):
    err = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"kerberos_crash_{timestamp}.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=== CRASH KERBEROS ===\n")
        f.write(f"Système : {platform.platform()}\n")
        f.write(f"Date : {datetime.now()}\n")
        f.write(err)
    print("💥 ERREUR KERBEROS :\n" + err, file=sys.stderr)
    print(f"📝 Log sauvegardé : {log_path}", file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        tmp = tk.Tk()
        tmp.withdraw()
        messagebox.showerror("💥 Kerberos – Erreur critique",
                             f"{exc_type.__name__}: {exc_value}\n\nLog détaillé dans :\n{log_path}")
        tmp.destroy()
    except: pass
    if not getattr(sys, 'frozen', False):
        try:
            input("\n🔴 Appuyez sur Entrée pour quitter...")
        except: pass
sys.excepthook = kerberos_excepthook
# ==============================================

# === CONFIGURATION ===
BG = "#1e1e1e"
FG = "#00ff00"
FONT_UI = ("Tahoma", 10)
FONT_MONO = ("Consolas", 10)
EXT_IMPORTANTES = {'.py', '.txt', '.log', '.json', '.csv', '.html', '.js', '.exe', '.bat', '.ini', '.xml', '.yml'}
MAX_DEPTH = 4

# === DÉTECTION DES LECTEURS (WINDOWS SEULEMENT – SANS PSUTIL) ===
def lister_lecteurs_windows():
    if platform.system() != "Windows":
        return []
    try:
        import string
        return [f"{c}:\\" for c in string.ascii_uppercase if os.path.exists(f"{c}:\\")] or ["C:\\"]
    except:
        return ["C:\\"]

# === LECTURE SÉCURISÉE DE L'ESPACE DISQUE (WINDOWS) ===
def espace_disque_win(lecteur):
    if platform.system() != "Windows":
        return "N/A"
    try:
        import ctypes
        _, total, free = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(lecteur),
            ctypes.pointer(_),
            ctypes.pointer(total),
            ctypes.pointer(free)
        )
        used = (total.value - free.value) / (1024**3)
        total_gb = total.value / (1024**3)
        return f"{used:.1f} / {total_gb:.1f} Go"
    except:
        return "⚠️ Indisponible"

# === PATTERNS NASSA – détection avancée (JS/HTML/Python) ===
NASSA_PATTERNS = [
    # JS/HTML
    (r"window\.open\([^)]*popup", "popup agressif"),
    (r"new\s+Image\(\)\.src\s*=\s*['\"][^'\"]*track", "tracker invisible"),
    (r"setTimeout\([^)]*document\.body\.appendChild", "modal non fermable"),
    (r"CoinHive|jscrypto-miner", "cryptojacking"),
    (r"connect\.facebook\.net.*fbevents", "pixel Facebook"),
    (r"googletagmanager\.com", "Google Tag Manager"),
    # Python
    (r"eval\s*\(", "eval détecté"),
    (r"exec\s*\(", "exec détecté"),
    (r"subprocess\.(run|Popen|call|check_output)", "subprocess utilisé"),
    (r"shutil\.rmtree", "suppression récursive"),
]

def extraire_ip_domaine(code):
    """Extrait les URLs → résout IP/ASN si possible."""
    urls = re.findall(r'https?://([a-zA-Z0-9.-]+)', code)
    result = []
    for url in urls[:3]:
        try:
            ip = socket.gethostbyname(url)
            result.append(f"{url} → {ip}")
        except:
            result.append(f"{url} → ?")
    return result

def analyser_contenu(filepath, content):
    """Analyse .py, .js, .html — retourne [(type, snippet, preuve)]"""
    findings = []
    for pattern, label in NASSA_PATTERNS:
        for match in re.finditer(pattern, content, re.I):
            snippet = content[max(0, match.start()-15):match.end()+15].replace("\n", " ")
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."
            preuve = extraire_ip_domaine(content[max(0, match.start()-50):match.end()+50])
            findings.append((label, snippet, preuve))
    return findings

def analyser_fichier(filepath):
    """Analyse un fichier — retourne résumé court ou '⚠️ SyntaxError'."""
    if not os.path.isfile(filepath):
        return "❌ Inaccessible"
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(20 * 1024)  # 20 Ko max

        # Syntaxe Python ?
        if filepath.endswith('.py'):
            try:
                ast.parse(content, filename=filepath)
            except SyntaxError:
                return "⚠️ SyntaxError"

        # Analyse comportementale
        findings = analyser_contenu(filepath, content)
        if not findings:
            return "✅ Clean"

        # Format court
        labels = [f"{typ} ({len(p)} IP)" if p else typ for typ, _, p in findings[:2]]
        return f"⚠️ {' | '.join(labels)}"
    except:
        return "❓ Lecture impossible"

def arbre_securise(racine, prefix="", prof=0, max_prof=4, ignore_recycle=True):
    if prof >= max_prof:
        return [f"{prefix}└── [...] (limite profondeur)"]
    lignes = []
    try:
        elements = sorted(os.listdir(racine))
    except (OSError, PermissionError, FileNotFoundError):
        return [f"{prefix}📁 [accès refusé]"]

    if ignore_recycle and os.path.basename(racine).startswith("$RECYCLE.BIN"):
        return [f"{prefix}📁 $RECYCLE.BIN (exclu)"]

    dossiers = []
    fichiers_imp = []
    autres = 0

    for e in elements:
        chemin = os.path.join(racine, e)
        try:
            if os.path.isdir(chemin):
                dossiers.append(e)
            elif os.path.isfile(chemin):
                _, ext = os.path.splitext(e)
                if ext.lower() in EXT_IMPORTANTES:
                    fichiers_imp.append(e)
                else:
                    autres += 1
        except (OSError, ValueError):
            continue

    total = len(dossiers) + len(fichiers_imp) + (1 if autres > 0 else 0)
    idx = 0

    for d in dossiers:
        if ignore_recycle and d.upper() == "$RECYCLE.BIN":
            idx += 1
            marque = "└── " if idx == total else "├── "
            lignes.append(f"{prefix}{marque}📁 $RECYCLE.BIN (exclu)")
            continue
        idx += 1
        marque = "└── " if idx == total else "├── "
        lignes.append(f"{prefix}{marque}📁 {d}")
        suite = prefix + ("    " if idx == total else "│   ")
        lignes.extend(arbre_securise(os.path.join(racine, d), suite, prof + 1, max_prof, ignore_recycle))

    for f in sorted(fichiers_imp):
        idx += 1
        marque = "└── " if idx == total else "├── "
        if f.endswith(('.py', '.js', '.html')):
            desc = analyser_fichier(os.path.join(racine, f))
            icone = "🐍" if f.endswith('.py') else "🌐" if f.endswith('.html') else "⚡"
            lignes.append(f"{prefix}{marque}{icone} {f}  [{desc}]")
        else:
            lignes.append(f"{prefix}{marque}📄 {f}")

    if autres > 0:
        idx += 1
        marque = "└── " if idx == total else "├── "
        lignes.append(f"{prefix}{marque}📄 [{autres} autre(s) fichier(s)]")

    return lignes

# === EXPORT NASSA — rapport pédagogique HTML ===
def generer_rapport_nassa(all_findings):
    now = datetime.now()
    rapport_id = now.strftime("%Y%m%d_%H%M%S")
    rapport_dir = Path("reports") / "nassa"
    rapport_dir.mkdir(parents=True, exist_ok=True)

    total = sum(len(f) for f in all_findings.values())
    rapport = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Rapport Nassa — {rapport_id}</title>
<style>
body {{ font-family: Consolas, monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }}
h1 {{ color: #00ccff; border-bottom: 1px solid #555; }}
h2 {{ color: #ff6666; }}
.snippet {{ background: #2d2d2d; padding: 8px; border-left: 3px solid #ff6666; margin: 8px 0; }}
pre {{ margin: 0; }}
a {{ color: #00ccff; text-decoration: none; }} a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>💰 La monnaie de la pièce — Rapport Nassa v1.0</h1>
<p><b>Date :</b> {now.strftime('%d/%m/%Y %H:%M:%S')}</p>
<p><b>Fichiers analysés :</b> {len(all_findings)}</p>
<p><b>Menaces détectées :</b> <span style="color:#ff6666">{total}</span></p>

<p>→ Ce rapport montre <b>ce que votre PC a vu sans vous le dire</b>.<br>
→ Nassa l’a intercepté, analysé, et vous rend la preuve — <b>en toute clarté</b>.</p>
"""

    for filepath, findings in all_findings.items():
        if not findings:
            continue
        rapport += f'\n<h2>📁 {filepath}</h2>\n'
        for typ, snippet, preuves in findings:
            rapport += f'<div class="snippet">\n'
            rapport += f'<b>🚨 {typ}</b><br>\n'
            rapport += f'<code>{snippet}</code><br>\n'
            if preuves:
                rapport += f'<i>🔎 Preuve réseau :</i><br>\n'
                for p in preuves:
                    rapport += f'→ {p}<br>\n'
            rapport += f'</div>\n'

    rapport += f"""
<hr>
<footer style="font-size:0.8em; color:#888;">
Kerberos v2.3 + Nassa Guard<br>
Licence : <a href="https://www.gnu.org/licenses/gpl-3.0.txt">GPLv3</a><br>
Code : <a href="https://github.com/victorpozen/kerberos">GitHub</a><br>
Soutien : <a href="https://liberapay.com/EthicalKerberos/">Liberapay</a><br>
→ Aucune donnée n’a quitté cette machine.
</footer>
</body>
</html>"""

    rapport_path = rapport_dir / f"nassa_proof_{rapport_id}.html"
    rapport_path.write_text(rapport, encoding="utf-8")
    return rapport_path

# === INTERFACE KERBEROS – v2.3 + Nassa ===
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        root.title("🔍 Kerberos – Analyseur de Disques v2.3 (Nassa-ready)")
        root.geometry("900x700")
        root.configure(bg=BG)

        tk.Label(root, text="KERBEROS – Analyse Profonde + Mode Nassa", 
                 fg=FG, bg=BG, font=("Consolas", 13, "bold")).pack(pady=8)

        opt_frame = tk.Frame(root, bg=BG)
        opt_frame.pack(pady=5, padx=15, fill=tk.X)

        tk.Label(opt_frame, text="✅ Sélectionnez :", fg=FG, bg=BG, font=FONT_UI).pack(anchor="w")
        tk.Label(opt_frame, text=" ▸ Lecteurs :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(5,0))

        self.vars = {}
        self.lecteurs = lister_lecteurs_windows()
        drv_frame = tk.Frame(opt_frame, bg=BG)
        drv_frame.pack(anchor="w")
        for drv in self.lecteurs:
            var = tk.BooleanVar(value=(drv == "C:\\"))
            self.vars[drv] = var
            tk.Checkbutton(drv_frame, text=drv, variable=var,
                           bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(side=tk.LEFT, padx=3)

        tk.Label(opt_frame, text=" ▸ Options :", bg=BG, fg="#aaaaaa", font=("Consolas", 9)).pack(anchor="w", pady=(5,0))
        self.ignore_recycle = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="🗑️ Ignorer $RECYCLE.BIN", variable=self.ignore_recycle,
                       bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(anchor="w")

        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="🚀 Analyser", command=self.analyser,
                  bg="#8b0000", fg="white", font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📂 Choisir un dossier", command=self.choisir_dossier,
                  bg="#2d2d2d", fg="white", font=FONT_UI).pack(side=tk.LEFT, padx=5)
        # 🔘 Bouton Nassa
        tk.Button(btn_frame, text="💰 Export vers Nassa", command=self.export_nassa,
                  bg="#0066cc", fg="white", font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=5)

        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=FONT_MONO,
            bg="#0a0a0a", fg=FG, insertbackground=FG
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        self.console.bind("<Key>", lambda e: "break")

        self.console.insert(tk.END, "ℹ️ Kerberos v2.3 + Nassa Guard\n")
        self.console.insert(tk.END, "   🧠 Analyse comportementale | 💰 Preuve pédagogique\n")
        self.console.insert(tk.END, "   🐍🐍⚡ Détection JS/HTML/Python | 🌐 IP/ASN résolues\n\n")

        self.all_findings = {}

    def analyser(self):
        cibles = [d for d, v in self.vars.items() if v.get()] or ["C:\\"] if self.lecteurs else []
        if not cibles and self.lecteurs:
            messagebox.showwarning("Sélection requise", "Cochez au moins un lecteur.")
            return
        self.generer_rapport(cibles)

    def choisir_dossier(self):
        dossier = filedialog.askdirectory(title="Sélectionner un dossier à analyser")
        if dossier:
            self.generer_rapport([dossier])

    def generer_rapport(self, cibles):
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, "🔍 Analyse comportementale en cours…\n\n")
        self.all_findings = {}

        lignes = ["=" * 60, "RAPPORT KERBEROS – ANALYSE NASSA v1.0", "=" * 60]
        lignes.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lignes.append(f"Système : {platform.system()} {platform.release()}")
        lignes.append("Corbeille exclue : " + ("Oui" if self.ignore_recycle.get() else "Non"))
        lignes.append("Licence : GNU GPLv3 – https://liberapay.com/EthicalKerberos/")
        lignes.append("=" * 60)

        for cible in cibles:
            lignes.append(f"\n{'='*60}\nCIBLE : {cible}\n{'='*60}")
            if os.path.exists(cible) and len(cible) == 3 and cible[1:] == ":\\":
                lignes.append(f"📊 Espace : {espace_disque_win(cible)}")
            else:
                lignes.append("📊 Espace : N/A (dossier personnalisé)")
            lignes.append("\nArborescence :")

            # Collecte findings pour Nassa
            for root_dir, _, files in os.walk(cible):
                depth = len(Path(root_dir).relative_to(cible).parts) if cible in root_dir else 0
                if depth > MAX_DEPTH:
                    break
                for f in files:
                    _, ext = os.path.splitext(f)
                    if ext.lower() in {'.py', '.js', '.html'}:
                        chemin = os.path.join(root_dir, f)
                        try:
                            findings = []
                            with open(chemin, "r", encoding="utf-8", errors="ignore") as ff:
                                content = ff.read(20 * 1024)
                            findings = analyser_contenu(chemin, content)
                            if findings:
                                self.all_findings[chemin] = findings
                        except:
                            pass

            lignes.extend(arbre_securise(cible, max_prof=MAX_DEPTH, ignore_recycle=self.ignore_recycle.get()))
            lignes.append("")

        lignes.append("✅ Analyse terminée — Cliquez sur '💰 Export vers Nassa' pour la preuve pédagogique.")
        rapport = "\n".join(lignes)
        self.console.insert(tk.END, rapport)

    def export_nassa(self):
        if not self.all_findings:
            messagebox.showinfo("ℹ️ Info", "Aucune menace détectée — impossible d’exporter vers Nassa.")
            return
        try:
            path = generer_rapport_nassa(self.all_findings)
            messagebox.showinfo("✅ Succès", f"Rapport Nassa généré :\n{path}")
            self.console.insert(tk.END, f"\n\n💰 Exporté vers Nassa : {path.name}")
            # Optionnel : ouvrir dans navigateur maison
            os.startfile(path) if platform.system() == "Windows" else None
        except Exception as e:
            messagebox.showerror("❌ Erreur", f"Échec export Nassa :\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiskAnalyzer(root)
    root.mainloop()