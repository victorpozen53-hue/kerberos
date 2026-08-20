# -*- coding: utf-8 -*-
# analyseur_disques_profond.v2.4+deep.kbi-enabled.py
# GPLv3 – Projet Kerberos – Sécurité éthique locale pour vieux PCs (Win 7/10)
# 🛡️ https://liberapay.com/EthicalKerberos/ | Full license: https://www.gnu.org/licenses/gpl-3.0.html
# White hat only. Pas de trace. Pas de nuage. Juste du code qui protège. (-; — Victor.Pozen

import sys
import os
import platform
import traceback
import hashlib
from datetime import datetime
import ast
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

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
EXT_IMPORTANTES = {'.py', '.txt', '.log', '.json', '.csv', '.html', '.exe', '.bat', '.ini', '.xml', '.yml'}
MAX_DEPTH = 4
MAX_DEPTH_FULL = 8
MAX_ITEMS_PER_DIR = 200

# === UTILITAIRES DISQUE ===
def lister_lecteurs_windows():
    if platform.system() != "Windows":
        return []
    try:
        import string
        return [f"{c}:\\" for c in string.ascii_uppercase if os.path.exists(f"{c}:\\")] or ["C:\\"]
    except:
        return ["C:\\"]

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

# === ANALYSE .PY ===
DANGEROUS_PATTERNS = [
    (r"exec\s*\(", "exec détecté"),
    (r"eval\s*\(", "eval détecté"),
    (r"__import__\s*\(", "__import__ détecté"),
    (r"subprocess\.(run|Popen|call|check_output)", "subprocess utilisé"),
    (r"import\s+os\s*,\s*sys", "os + sys ensemble → système"),
    (r"shutil\.rmtree", "shutil.rmtree → suppression récursive"),
    (r"ctypes\.windll", "ctypes.windll → accès bas niveau"),
]

def analyser_fichier_py(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read(1024 * 10)
        try:
            ast.parse(source, filename=filepath)
            syntax_ok = True
        except SyntaxError:
            return "⚠️ SyntaxError"
        except:
            syntax_ok = False

        imports = []
        try:
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except: pass

        risks = []
        for pattern, msg in DANGEROUS_PATTERNS:
            if re.search(pattern, source):
                risks.append(msg)

        parts = []
        if not syntax_ok: parts.append("❌ Syntaxe")
        if imports: parts.append("imports:" + ",".join(imports[:2]))
        if risks: parts.append("⚠️ " + " | ".join(risks[:1]))
        return " | ".join(parts) if parts else "✅ Clean"
    except:
        return "❓ Lecture impossible"

# === ARBRE SÉCURISÉ ===
def arbre_securise(racine, prefix="", prof=0, max_prof=4, ignore_recycle=True, limit_per_dir=MAX_ITEMS_PER_DIR):
    if prof >= max_prof:
        return [f"{prefix}└── [...] (limite profondeur {prof}/{max_prof})"]
    lignes = []
    try:
        elements = sorted(os.listdir(racine))
    except (OSError, PermissionError, FileNotFoundError):
        return [f"{prefix}📁 [accès refusé]"]

    if ignore_recycle and os.path.basename(racine).startswith("$RECYCLE.BIN"):
        return [f"{prefix}📁 $RECYCLE.BIN (exclu)"]

    elements = elements[:limit_per_dir]
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
        except: pass

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
        sous = arbre_securise(os.path.join(racine, d), suite, prof+1, max_prof, ignore_recycle, limit_per_dir)
        lignes.extend(sous)

    for f in sorted(fichiers_imp):
        idx += 1
        marque = "└── " if idx == total else "├── "
        if f.endswith('.py'):
            analyse = analyser_fichier_py(os.path.join(racine, f))
            lignes.append(f"{prefix}{marque}🐍 {f}  [{analyse}]")
        else:
            lignes.append(f"{prefix}{marque}📄 {f}")

    if autres > 0:
        idx += 1
        marque = "└── " if idx == total else "├── "
        lignes.append(f"{prefix}{marque}📄 [{autres} autre(s) fichier(s)]")

    return lignes

# === INTERFACE KERBEROS v2.4+deep.kbi-enabled ===
class KerberosDiskAnalyzer:
    def __init__(self, root):
        self.root = root
        self.selected_path = None
        self.last_kbi = None  # ← pour [📄 Ouvrir .kbi]
        root.title("🔍 Kerberos – Analyseur de Disques v2.4+deep (GPLv3)")
        root.geometry("940x740")
        root.configure(bg=BG)

        tk.Label(root, text="KERBEROS – Analyse Profonde + 📸 Image HDD",
                 fg=FG, bg=BG, font=("Consolas", 13, "bold")).pack(pady=8)

        # Options
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
        self.deep_scan = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_frame, text="🗑️ Ignorer $RECYCLE.BIN", variable=self.ignore_recycle,
                       bg=BG, fg=FG, selectcolor="#333", font=FONT_UI).pack(anchor="w")
        tk.Checkbutton(opt_frame, text="🔍 Profondeur étendue (max 8 niveaux)", variable=self.deep_scan,
                       bg=BG, fg="#88ccff", selectcolor="#333", font=FONT_UI).pack(anchor="w")

        # Boutons
        btn_frame1 = tk.Frame(root, bg=BG)
        btn_frame1.pack(pady=6)
        tk.Button(btn_frame1, text="📂 Choisir dossier", command=self.choisir_dossier,
                  bg="#2d2d2d", fg="white", font=FONT_UI).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame1, text="🔍 Prescan (rapide)", command=self.prescan,
                  bg="#3a3a3a", fg="#00ccff", font=FONT_UI).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame1, text="📸 Créer image", command=self.creer_image,
                  bg="#004d00", fg="white", font=FONT_UI).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame1, text="📄 Ouvrir .kbi", command=self.ouvrir_kbi,
                  bg="#1e4d1e", fg="#aaffaa", font=FONT_UI).pack(side=tk.LEFT, padx=4)

        btn_frame2 = tk.Frame(root, bg=BG)
        btn_frame2.pack(pady=4)
        tk.Button(btn_frame2, text="🚀 Analyser TOUT", command=self.analyser,
                  bg="#8b0000", fg="white", font=("Consolas", 11, "bold")).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame2, text="🔍 Full scan (tous les fichiers)", command=self.full_scan,
                  bg="#0066aa", fg="white", font=("Consolas", 10)).pack(side=tk.LEFT, padx=4)

        # Console
        self.console = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=FONT_MONO,
            bg="#0a0a0a", fg=FG, insertbackground=FG
        )
        self.console.pack(fill=tk.BOTH, expand=True, padx=14, pady=(8,12))
        self.console.bind("<Key>", lambda e: "break")

        self.console.insert(tk.END, "ℹ️ Kerberos v2.4+deep.kbi-enabled – GPLv3\n")
        self.console.insert(tk.END, "   📸 Créer image → .kbi + .sha256\n")
        self.console.insert(tk.END, "   📄 Ouvrir .kbi → lance automatiquement le dernier fichier\n")
        self.console.insert(tk.END, "   💾 Local only — HDD-friendly — White hat only\n\n")

    def prescan(self):
        dossier = filedialog.askdirectory(title="🔍 Prescan — Sélectionner un dossier")
        if not dossier:
            return
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, f"🔍 Prescan de : {dossier}\n")
        self.console.insert(tk.END, "   (profondeur limitée à 2, max 50 éléments)\n\n")
        self.console.insert(tk.END, "\n".join(arbre_securise(dossier, max_prof=2, limit_per_dir=50, ignore_recycle=self.ignore_recycle.get())))

    def creer_image(self):
        if not self.selected_path:
            messagebox.showwarning("⚠️", "Sélectionnez d’abord un dossier avec [📂 Choisir dossier].")
            return
        if not os.path.isdir(self.selected_path):
            messagebox.showerror("❌", "Dossier invalide.")
            return

        basename = os.path.basename(self.selected_path.strip(":\\/"))
        sortie = f"kerb_image_{basename.lower().replace(' ', '_')}.kbi"
        try:
            lignes = [
                f"KERBEROS IMAGE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Cible : {os.path.abspath(self.selected_path)}",
                "-" * 60
            ]

            def walk_safe(racine, rel="", depth=0, count=[0]):
                if depth > 8 or count[0] > 500:
                    lignes.append(f"[...] (limite atteinte — profondeur {depth}/8, {count[0]} éléments)")
                    return
                try:
                    for e in sorted(os.listdir(racine))[:100]:
                        if count[0] > 500:
                            break
                        chemin = os.path.join(racine, e)
                        rel_path = os.path.join(rel, e).lstrip("\\/")
                        try:
                            if os.path.isdir(chemin):
                                lignes.append(f"D {rel_path}/")
                                count[0] += 1
                                walk_safe(chemin, rel_path, depth + 1, count)
                            elif os.path.isfile(chemin):
                                size = os.path.getsize(chemin)
                                try:
                                    with open(chemin, 'rb') as f:
                                        sample = f.read(4096)
                                    h = hashlib.sha1(sample).hexdigest()[:8]
                                except:
                                    h = "err"
                                lignes.append(f"F {rel_path} | {size} octets | SHA1:{h}")
                                count[0] += 1
                        except OSError:
                            continue
                except (OSError, PermissionError):
                    lignes.append(f"# ACCÈS REFUSÉ : {rel}")

            walk_safe(self.selected_path)
            contenu = "\n".join(lignes)

            with open(sortie, "w", encoding="utf-8") as f:
                f.write(contenu)
            sha256 = hashlib.sha256(contenu.encode("utf-8")).hexdigest()[:16]
            with open(sortie + ".sha256", "w") as f:
                f.write(f"{sha256} *{sortie}\n")

            self.last_kbi = sortie
            self.console.insert(tk.END, f"\n📸 Image générée : {sortie}\n")
            messagebox.showinfo(
                "✅ Image Kerberos",
                f"✅ Image sauvegardée :\n   {sortie}\n   + {sortie}.sha256\n\n"
                f"➡️ Utilisez [📄 Ouvrir .kbi] pour la consulter."
            )
        except Exception as e:
            self.console.insert(tk.END, f"\n❌ Échec image : {e}\n")
            messagebox.showerror("❌ Échec", f"Impossible de créer l’image :\n{e}")

    def ouvrir_kbi(self):
        if not self.last_kbi or not os.path.exists(self.last_kbi):
            messagebox.showinfo("ℹ️", "Aucun fichier .kbi récent trouvé.\nGénérez-en un avec [📸 Créer image].")
            return
        try:
            os.startfile(self.last_kbi)
            self.console.insert(tk.END, f"\n📄 Ouverture : {self.last_kbi}\n")
        except Exception as e:
            self.console.insert(tk.END, f"\n❌ Impossible d’ouvrir {self.last_kbi} : {e}\n")

    def analyser(self):
        cibles = [d for d, v in self.vars.items() if v.get()]
        if not cibles and self.lecteurs:
            messagebox.showwarning("Sélection requise", "Cochez au moins un lecteur.")
            return
        self.generer_rapport(cibles if cibles else ["C:\\"], full=False)

    def full_scan(self):
        cibles = [d for d, v in self.vars.items() if v.get()]
        if not cibles and self.lecteurs:
            messagebox.showwarning("Sélection requise", "Cochez au moins un lecteur.")
            return
        self.generer_rapport(cibles if cibles else ["C:\\"], full=True)

    def choisir_dossier(self):
        dossier = filedialog.askdirectory(title="📂 Choisir un dossier à analyser / imager")
        if dossier:
            self.selected_path = dossier
            self.console.delete(1.0, tk.END)
            self.console.insert(tk.END, f"🎯 Dossier sélectionné : {dossier}\n")
            self.console.insert(tk.END, "   ➤ Utilisez [📸 Créer image] ou [🔍 Prescan] avec ce dossier.\n")

    def generer_rapport(self, cibles, full=False):
        self.console.delete(1.0, tk.END)
        self.console.insert(tk.END, f"🚀 Génération du rapport {'FULL' if full else 'standard'}… (patientez)\n\n")

        lignes = []
        lignes.append("=" * 60)
        lignes.append("RAPPORT KERBEROS – ANALYSE DE DISQUES v2.4+deep")
        lignes.append("=" * 60)
        lignes.append(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lignes.append(f"Système : {platform.system()} {platform.release()}")
        prof_reelle = MAX_DEPTH_FULL if full or self.deep_scan.get() else MAX_DEPTH
        lignes.append(f"Profondeur : {prof_reelle} (max)")
        lignes.append("Corbeille exclue : " + ("Oui" if self.ignore_recycle.get() else "Non"))
        lignes.append("Licence : GNU GPLv3 – https://liberapay.com/EthicalKerberos/")
        lignes.append("Code : https://github.com/victorpozen/kerberos")
        lignes.append("=" * 60)
        lignes.append("")

        for cible in cibles:
            lignes.append(f"\n{'='*60}\nCIBLE : {cible}\n{'='*60}")
            if os.path.exists(cible) and len(cible) == 3 and cible[1:] == ":\\": 
                lignes.append(f"📊 Espace : {espace_disque_win(cible)}")
            else:
                lignes.append("📊 Espace : N/A")
            lignes.append("\nArborescence :")
            lignes.extend(arbre_securise(
                cible,
                max_prof=prof_reelle,
                ignore_recycle=self.ignore_recycle.get(),
                limit_per_dir=MAX_ITEMS_PER_DIR
            ))
            lignes.append("")

        lignes.append("✅ Rapport généré – Projet Kerberos (GPLv3)")
        rapport = "\n".join(lignes)
        self.console.insert(tk.END, rapport)

        try:
            nom = "rapport_full_scan.txt" if full else "rapport_disques_profond.txt"
            with open(nom, "w", encoding="utf-8") as f:
                f.write(rapport)
            self.console.insert(tk.END, f"\n\n💾 Sauvegardé : {nom}")
            messagebox.showinfo("✅ Succès", f"Analyse {'FULL' if full else 'standard'} terminée !\nRapport : {nom}")
        except Exception as e:
            self.console.insert(tk.END, f"\n\n⚠️ Erreur sauvegarde : {e}")

# === LANCEMENT ===
if __name__ == "__main__":
    root = tk.Tk()
    app = KerberosDiskAnalyzer(root)
    root.mainloop()