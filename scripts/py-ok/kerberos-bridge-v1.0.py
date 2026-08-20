# -*- coding: utf-8 -*-
# kerberos-bridge-final-v2.py
# GPLv3 — Sécurité desktop locale (Win 7/10) — White hat only
# 🛡️ Pas de trace. Pas de nuage. Juste du code qui protège. (-; — Victor.Pozen
# 🔗 https://github.com/victorpozen/kerberos
# 💝 https://liberapay.com/EthicalKerberos/

import os
import sys
import locale
import platform
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import urllib.request
import urllib.error
import base64
import json
import traceback

# === KERBEROS STYLE ===
BG = "#1e1e1e"
FG = "#00ff00"
ACCENT = "#8b0000"
FONT = ("Consolas", 9)

# === DEBUG MAISON ===
def log(msg):
    ts = __import__('datetime').datetime.now().strftime("%H:%M:%S")
    full = f"[{ts}] [DEBUG] {msg}"
    print(full, file=sys.stderr)
    return full

# === COPIER-COLLER PARTOUT ===
def make_copyable(widget):
    def copy():
        try:
            text = widget.selection_get()
            widget.clipboard_clear()
            widget.clipboard_append(text)
        except: pass
    widget.bind("<Button-3>", lambda e: copy())  # clic droit
    widget.bind("<Control-c>", lambda e: copy())  # Ctrl+C
    widget.bind("<Button-2>", lambda e: copy())  # clic milieu (X11-style)

# === CMD SAFE (Unicode fix) ===
def run_cmd(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, timeout=10)
        def decode_safe(b):
            if not b: return ""
            for enc in ("utf-8", locale.getpreferredencoding(), "cp1252", "latin-1"):
                try:
                    return b.decode(enc)
                except UnicodeDecodeError:
                    continue
            return b.decode("utf-8", errors="replace")
        return (result.returncode == 0,
                decode_safe(result.stdout),
                decode_safe(result.stderr))
    except Exception as e:
        log(f"run_cmd: {e}")
        return False, "", str(e)

# === GIT CREDENTIAL (Win7+) ===
def probe_git_credential():
    try:
        inp = "protocol=https\nhost=github.com\n"
        proc = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        out, _ = proc.communicate(input=inp.encode(), timeout=3)
        if proc.returncode == 0:
            for line in out.decode("utf-8", errors="ignore").splitlines():
                if line.startswith("password="):
                    return line.split("=", 1)[1]
    except Exception as e:
        log(f"credential probe: {e}")
    return None

# === UPLOAD TO GITHUB (avec chemin complet) ===
def upload_to_github(token, local_path, repo_path):
    try:
        with open(local_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        url_check = f"https://api.github.com/repos/victorpozen/kerberos/contents/{repo_path}?ref=main"
        req = urllib.request.Request(url_check)
        req.add_header("Authorization", f"token {token}")
        req.add_header("User-Agent", "Kerberos-Bridge")
        sha = None
        try:
            with urllib.request.urlopen(req, timeout=5) as res:
                data = json.loads(res.read().decode())
                sha = data.get("sha")
        except: pass
        url = f"https://api.github.com/repos/victorpozen/kerberos/contents/{repo_path}"
        payload = {
            "message": f"Kerberos Bridge — {repo_path}",
            "content": content,
            "branch": "main"
        }
        if sha: payload["sha"] = sha
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, method="PUT")
        req.add_header("Authorization", f"token {token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "Kerberos-Bridge")
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.getcode() in (200, 201)
    except Exception as e:
        log(f"upload: {e}")
        return False

# === SUPPRIMER SUR GITHUB ===
def delete_from_github(token, path):
    try:
        url = f"https://api.github.com/repos/victorpozen/kerberos/contents/{path}?ref=main"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"token {token}")
        req.add_header("User-Agent", "Kerberos-Bridge")
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            sha = data["sha"]
        url = f"https://api.github.com/repos/victorpozen/kerberos/contents/{path}"
        payload = {
            "message": f"Suppression via Kerberos — {path}",
            "sha": sha,
            "branch": "main"
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, method="DELETE")
        req.add_header("Authorization", f"token {token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "Kerberos-Bridge")
        with urllib.request.urlopen(req) as res:
            return res.getcode() == 200
    except Exception as e:
        log(f"delete: {e}")
        return False

# === HDD SCAN ===
def lister_lecteurs_windows():
    if platform.system() != "Windows":
        return ["C:\\"]
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
        return "?"

ALLOWED_EXTS = {'.py', '.txt', '.md', '.json', '.csv', '.ini', '.bat', '.yml', '.yaml', '.log'}

def arbre_to_dict(racine, max_prof=4, _prof=0):
    if _prof >= max_prof:
        return {"[...]": {"type": "dir", "path": "", "children": {}}}
    try:
        items = sorted(os.listdir(racine))
    except (OSError, PermissionError):
        return {"[accès refusé]": {"type": "dir", "path": "", "children": {}}}
    result = {}
    for item in items:
        chemin = os.path.join(racine, item)
        try:
            if os.path.isdir(chemin):
                result[item] = {
                    "type": "dir",
                    "path": chemin,
                    "children": arbre_to_dict(chemin, max_prof, _prof + 1)
                }
            elif os.path.isfile(chemin):
                _, ext = os.path.splitext(item)
                if ext.lower() in ALLOWED_EXTS:
                    result[item] = {
                        "type": "file",
                        "path": chemin,
                        "size": os.path.getsize(chemin)
                    }
        except (OSError, ValueError):
            continue
    return result

# === GUI — KERBEROS STYLE ===
class KerberosBridge:
    def __init__(self, root):
        self.root = root
        self.token = ""
        self.github_user = ""
        self.drag_file = None

        root.title("🛡️ Kerberos Bridge — Local ↔ GitHub (GPLv3)")
        root.geometry("1080x660")
        root.configure(bg=BG)

        tk.Label(root, text="KERBEROS", fg=FG, bg=BG, font=("Consolas", 14, "bold")).pack(pady=(6,2))
        tk.Label(root, text="White hat only • Zéro cloud • GPLv3", fg="#555", bg=BG, font=("Consolas", 9)).pack()

        # Barre d'outils
        bar = tk.Frame(root, bg=BG)
        bar.pack(pady=5, padx=10, fill=tk.X)

        tk.Button(bar, text="🔐 Login", command=self._login,
                  bg=ACCENT, fg="white", font=FONT).pack(side=tk.LEFT, padx=2)
        tk.Button(bar, text="📼 Scan HDD", command=self._scan_hdds,
                  bg="#333333", fg="white", font=FONT).pack(side=tk.LEFT, padx=2)
        tk.Button(bar, text="ℹ️ À propos", command=self._about,
                  bg="#2d2d2d", fg=FG, font=FONT).pack(side=tk.RIGHT, padx=2)

        # Split
        pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, bg="#444", sashwidth=8)
        pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 🖥️ Client
        left = tk.Frame(pane, bg=BG)
        tk.Label(left, text="🖥️ Client — Fichiers réels", fg="#00ccaa", bg=BG, font=("Consolas", 10, "bold")).pack(anchor="w", padx=5)
        self.client_tree = self._create_tree(left)
        self.client_tree.insert("", "end", text="📼 Cliquez 'Scan HDD'", values=("", ""))
        pane.add(left, width=500)

        # ☁️ GitHub
        right = tk.Frame(pane, bg=BG)
        tk.Label(right, text="☁️ GitHub — victorpozen/kerberos", fg="#6a99ff", bg=BG, font=("Consolas", 10, "bold")).pack(anchor="w", padx=5)
        self.gh_tree = self._create_tree(right)
        self.gh_tree.insert("", "end", text="⚠️ Login requis", values=("", ""))
        pane.add(right, width=500)

        # Console debug
        self.console = tk.Text(root, height=4, font=("Consolas", 8),
                               bg="#000", fg="#00cc66", wrap=tk.WORD)
        self.console.pack(fill=tk.X, padx=10, pady=(0,5))
        self.console.insert(tk.END, "ℹ️ Kerberos Bridge — GPLv3\n")
        make_copyable(self.console)

        tk.Label(root, text="GPLv3 — Pas de trace. Pas de nuage. Juste du code qui protège.",
                 fg="#555", bg=BG, font=("Consolas", 8)).pack()

        # Bindings
        self.client_tree.bind("<<TreeviewSelect>>", self._on_client_select)
        self.gh_tree.bind("<Button-1>", self._on_gh_click)
        self.gh_tree.bind("<Button-3>", self._on_gh_right_click)  # clic droit → supprimer
        make_copyable(self.client_tree)
        make_copyable(self.gh_tree)

    def _create_tree(self, parent):
        tree = ttk.Treeview(parent, columns=("size", "type"), show="tree headings", height=22)
        tree.heading("#0", text="Name", anchor=tk.W)
        tree.heading("size", text="Size", anchor=tk.E)
        tree.heading("type", text="Type", anchor=tk.W)
        tree.column("#0", width=300)
        tree.column("size", width=60, anchor=tk.E)
        tree.column("type", width=40)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

    def _on_client_select(self, event):
        sel = self.client_tree.selection()
        if not sel: return
        item = sel[0]
        text = self.client_tree.item(item, "text")
        if not text.endswith(tuple(ALLOWED_EXTS)) or not text.endswith(('.py', '.txt')):
            return
        parts = [text]
        p = self.client_tree.parent(item)
        while p:
            parts.insert(0, self.client_tree.item(p, "text"))
            p = self.client_tree.parent(p)
        for drv in getattr(self, 'scanned_roots', []):
            full = os.path.join(drv, *parts)
            if os.path.isfile(full):
                self.drag_file = full
                rel = os.path.relpath(full, drv).replace("\\", "/")
                self.console.delete(1.0, tk.END)
                self.console.insert(tk.END, f"📎 Prêt : {rel}\n")
                return

    def _on_gh_click(self, event):
        if not self.drag_file:
            messagebox.showinfo("ℹ️", "Sélectionnez un .py ou .txt dans le Client.")
            return
        if not self.token:
            messagebox.showwarning("⚠️", "Connectez-vous à GitHub d’abord.")
            return

        # 🔷 Chemin relatif complet
        rel_path = None
        for drv in getattr(self, 'scanned_roots', []):
            if self.drag_file.startswith(drv):
                rel_path = os.path.relpath(self.drag_file, drv).replace("\\", "/")
                break
        if not rel_path:
            rel_path = os.path.basename(self.drag_file)

        if messagebox.askyesno("📤 Upload", f"Envoyer vers :\n{rel_path} ?"):
            self.console.insert(tk.END, f"📤 {rel_path} ...\n")
            if upload_to_github(self.token, self.drag_file, rel_path):
                self.console.insert(tk.END, "✅ Téléversé\n")
                self._refresh_github()
            else:
                self.console.insert(tk.END, "❌ Échec\n")

    def _on_gh_right_click(self, event):
        item = self.gh_tree.identify_row(event.y)
        if not item: return
        name = self.gh_tree.item(item, "text")
        if not name or name.startswith("📁") or name.endswith("/") or name == "⚠️ Login requis":
            return
        if messagebox.askyesno("🗑️ Supprimer", f"Supprimer {name} sur GitHub ?"):
            self.console.insert(tk.END, f"🗑️ {name} ...\n")
            if delete_from_github(self.token, name):
                self.console.insert(tk.END, "✅ Supprimé\n")
                self._refresh_github()
            else:
                self.console.insert(tk.END, "❌ Échec\n")

    def _refresh_github(self):
        self.gh_tree.delete(*self.gh_tree.get_children())
        if not self.token:
            self.gh_tree.insert("", "end", text="⚠️ Login requis", values=("", ""))
            return
        try:
            url = "https://api.github.com/repos/victorpozen/kerberos/contents?ref=main"
            req = urllib.request.Request(url)
            req.add_header("Authorization", f"token {self.token}")
            req.add_header("User-Agent", "Kerberos-Bridge")
            with urllib.request.urlopen(req, timeout=8) as res:
                items = json.loads(res.read().decode())
                for item in sorted(items, key=lambda x: (x["type"], x["name"])):
                    icon = "📁" if item["type"] == "dir" else "🐍" if item["name"].endswith(".py") else "📄"
                    self.gh_tree.insert("", "end", text=item["name"], values=("", icon))
        except Exception as e:
            log(f"github refresh: {e}")
            self.gh_tree.insert("", "end", text="❌ Erreur", values=("", ""))

    def _scan_hdds(self):
        lecteurs = lister_lecteurs_windows()
        if not lecteurs:
            messagebox.showwarning("⚠️", "Aucun lecteur détecté.")
            return

        win = tk.Toplevel(self.root, bg=BG)
        win.title("📼 Scanner HDD")
        win.geometry("380x360")
        win.grab_set()

        tk.Label(win, text="Cochez les lecteurs :", fg=FG, bg=BG, font=FONT).pack(pady=(10,5))
        frame = tk.Frame(win, bg=BG)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        vars = {}
        for drv in lecteurs:
            var = tk.BooleanVar(value=(drv == "C:\\"))
            vars[drv] = var
            tk.Checkbutton(frame, text=f"{drv} ({espace_disque_win(drv)})", variable=var,
                           bg=BG, fg=FG, selectcolor="#333", font=FONT).pack(anchor="w", padx=5, pady=1)

        def start_scan():
            cibles = [d for d, v in vars.items() if v.get()]
            if not cibles:
                messagebox.showwarning("⚠️", "Sélectionnez au moins un lecteur.")
                return
            win.destroy()
            self._do_scan(cibles)

        tk.Button(win, text="🚀 Lancer", command=start_scan,
                  bg=ACCENT, fg="white", font=FONT).pack(pady=10)

    def _do_scan(self, cibles):
        self.console.insert(tk.END, f"🔍 Scan de {len(cibles)} lecteur(s)...\n")
        self.client_tree.delete(*self.client_tree.get_children())
        self.scanned_roots = cibles

        for drv in cibles:
            node = self.client_tree.insert("", "end", text=drv, values=(espace_disque_win(drv), "📁"))
            try:
                arbre = arbre_to_dict(drv, max_prof=3)
                self._populate_tree(node, arbre)
            except Exception as e:
                log(f"scan error {drv}: {e}")
                self.client_tree.insert(node, "end", text=f"❌ {e}", values=("", ""))
        self.console.insert(tk.END, "✅ Scan terminé.\n")

    def _populate_tree(self, parent_node, data):
        for name, info in sorted(data.items()):
            if info["type"] == "dir":
                node = self.client_tree.insert(parent_node, "end", text=name, values=("", "📁"))
                self._populate_tree(node, info["children"])
            else:
                size = f"{info['size']//1024}K" if info['size'] < 1024*1024 else f"{info['size']//(1024*1024)}M"
                icon = "🐍" if name.endswith(".py") else "📄" if name.endswith(".txt") else "📝"
                self.client_tree.insert(parent_node, "end", text=name, values=(size, icon))

    def _login(self):
        win = tk.Toplevel(self.root, bg=BG)
        win.title("🔐 GitHub Login — Sécurité éthique")
        win.geometry("600x460")
        win.grab_set()

        tk.Label(win, text="🔒 Sécurité Kerberos — Aucun mot de passe n’est récupéré.",
                 fg="#ff6666", bg=BG, font=("Consolas", 9, "bold")).pack(pady=(10,5))
        msg = (
            "✅ Créez un Personal Access Token (PAT) fine-grained :\n"
            "   → Cliquez ici pour ouvrir la page : "
        )
        tk.Label(win, text=msg, justify=tk.LEFT, fg=FG, bg=BG, font=("Consolas", 8)).pack(anchor="w", padx=20)

        # 🔗 Lien cliquable
        link = tk.Label(win, text="https://github.com/settings/tokens?type=beta",
                        fg="#6a99ff", bg=BG, font=("Consolas", 8, "underline"), cursor="hand2")
        link.pack(anchor="w", padx=20)
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/settings/tokens?type=beta"))

        msg2 = (
            "\nConfigurez-le ainsi :\n"
            "   • Token name : Kerberos Bridge\n"
            "   • Resource owner : victorpozen\n"
            "   • Repository access : Only select repositories → kerberos\n"
            "   • Permissions :\n"
            "        Contents → Read and write\n"
            "        Metadata → Read-only\n\n"
            "💡 Une fois généré, copiez-le (Ctrl+C) et collez-le ci-dessous (Ctrl+V fonctionne).\n"
            "Le token reste en mémoire — jamais sauvegardé sur disque."
        )
        tk.Label(win, text=msg2, justify=tk.LEFT, fg=FG, bg=BG, font=("Consolas", 8)).pack(padx=20)

        tk.Label(win, text="🗝️ Collez votre PAT ici :", fg="#00ccaa", bg=BG, font=FONT).pack(pady=(10,2))
        entry = tk.Entry(win, width=75, font=("Consolas", 9), bg="#0a0a0a", fg="#00ff00", show="•")
        entry.pack(padx=20, pady=(0,10))
        entry.focus()

        def submit():
            token = entry.get().strip()
            if token:
                self._set_token(token)
                win.destroy()
            else:
                messagebox.showwarning("⚠️", "Collez un PAT valide.")

        tk.Button(win, text="✅ Valider", command=submit,
                  bg="#1e4d2b", fg="white", font=FONT).pack(pady=5)

    def _set_token(self, token):
        try:
            req = urllib.request.Request("https://api.github.com/user")
            req.add_header("Authorization", f"token {token}")
            req.add_header("User-Agent", "Kerberos-Bridge")
            with urllib.request.urlopen(req, timeout=5) as res:
                user = json.loads(res.read().decode()).get("login", "unknown")
                self.token = token
                self.github_user = user
                self.console.insert(tk.END, f"🔐 Auth OK → {user}\n")
                self._refresh_github()
        except Exception as e:
            messagebox.showerror("❌", f"Token invalide :\n{e}")

    def _about(self):
        win = tk.Toplevel(self.root, bg=BG)
        win.title("ℹ️ À propos — Kerberos")
        win.geometry("440x280")

        tk.Label(win, text="KERBEROS — Sécurité desktop locale",
                 fg=FG, bg=BG, font=("Consolas", 11, "bold")).pack(pady=(10,2))
        tk.Label(win, text="GPLv3 • White hat only • Zéro cloud",
                 fg="#555", bg=BG, font=("Consolas", 9)).pack()

        tk.Label(win, text="\n🔗 Dépôt officiel :", bg=BG, fg="#6a99ff", font=("Consolas", 10)).pack()
        btn1 = tk.Button(win, text="https://github.com/victorpozen/kerberos",
                         command=lambda: webbrowser.open("https://github.com/victorpozen/kerberos"),
                         bg="#2d2d2d", fg="#6a99ff", font=("Consolas", 9), relief="raised")
        btn1.pack(pady=2)

        tk.Label(win, text="\n💝 Soutien éthique :", bg=BG, fg="#ffaa00", font=("Consolas", 10)).pack()
        btn2 = tk.Button(win, text="https://liberapay.com/EthicalKerberos/",
                         command=lambda: webbrowser.open("https://liberapay.com/EthicalKerberos/"),
                         bg="#2d2d2d", fg="#ffaa00", font=("Consolas", 9), relief="raised")
        btn2.pack(pady=2)

        tk.Label(win, text="\n« Pas de trace. Pas de nuage.\nJuste du code qui protège. »\n(-; — Victor.Pozen",
                 fg="#555", bg=BG, font=("Consolas", 8), justify=tk.CENTER).pack(pady=10)

        tk.Button(win, text="Fermer", command=win.destroy,
                  bg="#1e4d2b", fg="white", font=FONT).pack(pady=5)

# === STYLE DARK ===
if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background="#0a0a0a", foreground=FG, fieldbackground="#0a0a0a")
    style.configure("Treeview.Heading", background=BG, foreground="#00ccaa")
    style.map("Treeview", background=[("selected", "#2d2d2d")], foreground=[("selected", "#ffffff")])
    app = KerberosBridge(root)
    root.mainloop()