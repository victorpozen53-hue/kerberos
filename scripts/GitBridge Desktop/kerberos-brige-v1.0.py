# -*- coding: utf-8 -*-
# ==============================================================
# KERBEROS — Bridge Final (v1.0) — (-;
# Sécurité desktop locale — Windows 7/10, matériel ancien, zéro cloud.
# White hat only. GPLv3.
# ==============================================================
# (-; — Victor.Pozen — https://fr.liberapay.com/EthicalKerberos/  

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import shutil
import webbrowser
import urllib.request
import json
import time

# ========== SPLASH EXPLICATIF ==========
print("\n" + "═"*60)
print("KERBEROS — Bridge Final (v1.0) — (-;")
print("Sécurité desktop locale — Windows 7/10, matériel ancien, zéro cloud.")
print("White hat only. GPLv3.")
print("« Pas de trace. Pas de nuage. Juste du code qui protège. »")
print("(-; — Victor.Pozen")
print("https://github.com/victorpozen/kerberos")
print("https://fr.liberapay.com/EthicalKerberos/")
print("══════════════════════════════════════════════════════════════")

# ========== AJOUT MINGW64 AU PATH ==========
def ensure_git_path():
    for cand in [r"H:\PYTHON\mingw64\bin", r"H:\PYTHON\mingw64\usr\bin"]:
        if os.path.isdir(cand) and cand not in os.environ.get("PATH", ""):
            os.environ["PATH"] = cand + ";" + os.environ.get("PATH", "")
            return True
    return False
ensure_git_path()

# ========== CONFIG LOCALE ==========
BRIDGE_BASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    r".kerberos\ibrid"
)
os.makedirs(BRIDGE_BASE, exist_ok=True)

# ========== CLASSE PRINCIPALE — v1.0 ==========
class KerberosBridgeCore:
    def __init__(self, root):
        self.root = root
        self.root.title("KERBEROS — Bridge (v1.0) — (-;")
        self.root.geometry("1080x720")
        self.root.minsize(950, 650)
        self.root.configure(bg="#0d1117")

        self.colors = {
            "bg": "#0d1117", "fg": "#c9d1d9", "accent": "#00a0e9",
            "success": "#2ea043", "warn": "#d29922", "error": "#f85149",
            "panel": "#161b22"
        }

        self.local_path = tk.StringVar(value=os.path.expanduser("~"))
        self.github_user = tk.StringVar()
        self.github_pat = tk.StringVar()
        self.github_repo = tk.StringVar(value="kerberos")

        self.create_widgets()
        self.refresh_local_tree()

    def create_widgets(self):
        # === Haut : titre + disques + PAT rapide ===
        top = tk.Frame(self.root, bg=self.colors["bg"], height=50)
        top.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(top, text="KERBEROS — Bridge (v1.0) — (-;", 
                 font=("Consolas", 14, "bold"),
                 fg=self.colors["accent"], bg=self.colors["bg"]).pack(side="left")

        # Disques
        disk_frame = tk.Frame(top, bg=self.colors["bg"])
        disk_frame.pack(side="left", padx=(20, 0))
        tk.Label(disk_frame, text="🪀 ", fg="#8b949e", bg=self.colors["bg"], font=("Consolas", 12)).pack(side="left")
        drives = [d for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
        for drive in drives:
            def make_cmd(d):
                return lambda: self.select_drive(d)
            btn = tk.Button(
                disk_frame, text=f"{drive}:", command=make_cmd(drive),
                bg="#21262d", fg="#8b949e", font=("Consolas", 9), relief="flat", padx=6
            )
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#30363d", fg="white"))
            btn.bind("<Leave>", lambda e, b=btn, d=drive: 
                b.config(bg=self.colors["accent"] if self.local_path.get().upper().startswith(f"{d}:") else "#21262d",
                         fg="white" if self.local_path.get().upper().startswith(f"{d}:") else "#8b949e"))
            btn.pack(side="left", padx=1)

        # ➕ PAT rapide
        pat_frame = tk.Frame(top, bg=self.colors["bg"])
        pat_frame.pack(side="right", padx=(20, 0))
        tk.Button(
            pat_frame, text="❓ À propos", command=self.show_about,
            bg="#21262d", fg=self.colors["fg"], font=("Consolas", 9), relief="flat", padx=8
        ).pack(side="left", padx=4)
        tk.Button(
            pat_frame, text="➕ Créer PAT", command=self.show_pat_menu,
            bg=self.colors["accent"], fg="white", font=("Consolas", 9, "bold"), relief="flat", padx=8
        ).pack(side="left", padx=4)

        # === Deux panneaux ===
        main = tk.Frame(self.root, bg=self.colors["bg"])
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # Gauche : LOCAL
        left = tk.LabelFrame(main, text=" 🖥️ LOCAL (PC)", bg=self.colors["panel"], fg=self.colors["accent"],
                             font=("Consolas", 10, "bold"), bd=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 5))
        tk.Entry(left, textvariable=self.local_path, font=("Consolas", 10), bg="#0d1117", fg="#c9d1d9",
                 state="readonly").pack(fill="x", padx=5, pady=5, ipady=3)
        self.local_tree = ttk.Treeview(left, columns=("size",), show="tree headings")
        self.local_tree.heading("#0", text="Nom", anchor="w")
        self.local_tree.heading("size", text="Taille", anchor="e")
        self.local_tree.column("#0", width=250)
        self.local_tree.column("size", width=80, anchor="e")
        self.local_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.local_tree.bind("<Double-1>", self.on_tree_double_click)

        style = ttk.Style()
        try: style.theme_use("clam")
        except: pass
        style.configure("Treeview", background="#0d1117", foreground="#c9d1d9", font=("Consolas", 9))
        style.configure("Treeview.Heading", background="#161b22", foreground="#8b949e", font=("Consolas", 9, "bold"))

        # Droite : GITHUB
        right = tk.LabelFrame(main, text=" 🌐 GITHUB (REMOTE) — (-;", bg=self.colors["panel"], fg=self.colors["accent"],
                              font=("Consolas", 10, "bold"), bd=1)
        right.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Authentification
        auth_frame = tk.LabelFrame(right, text=" 🔐 Authentification", bg=self.colors["panel"],
                                   fg=self.colors["accent"], font=("Consolas", 9, "bold"))
        auth_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(auth_frame, text="👤 User :", bg=self.colors["panel"], fg=self.colors["fg"],
                 font=("Consolas", 10)).grid(row=0, column=0, sticky="w", padx=(5, 0), pady=3)
        tk.Entry(auth_frame, textvariable=self.github_user, font=("Consolas", 10),
                 bg="#0d1117", fg="#c9d1d9", relief="flat").grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        pat_line = tk.Frame(auth_frame, bg=self.colors["panel"])
        pat_line.grid(row=1, column=0, columnspan=2, sticky="ew", pady=3)
        tk.Label(pat_line, text="🔑 PAT :", bg=self.colors["panel"], fg=self.colors["fg"],
                 font=("Consolas", 10)).pack(side="left", padx=(5, 0))
        tk.Button(pat_line, text="➕ Créer PAT", command=self.show_pat_menu,
                  bg="#004d88", fg="white", font=("Consolas", 9), relief="flat", padx=6).pack(side="left", padx=(5, 0))
        tk.Entry(pat_line, textvariable=self.github_pat, show="•", font=("Consolas", 10),
                 bg="#0d1117", fg="#c9d1d9", relief="flat", width=20).pack(side="left", padx=5, expand=True, fill="x")

        test_frame = tk.Frame(auth_frame, bg=self.colors["panel"])
        test_frame.grid(row=2, column=0, columnspan=2, pady=6, sticky="ew")
        tk.Button(test_frame, text="🔍 Tester l'authentification", command=self.test_github_auth,
                  bg="#21262d", fg=self.colors["accent"], font=("Consolas", 9), relief="flat", padx=10).pack(side="left")
        tk.Label(test_frame, text="|", bg=self.colors["panel"], fg="#30363d", font=("Consolas", 12)).pack(side="left", padx=5)
        link = tk.Label(test_frame, text="📝 Token settings", bg=self.colors["panel"],
                        fg="#58a6ff", font=("Consolas", 9, "underline"), cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/settings/tokens".strip()))

        # Arborescence GitHub
        github_tree_frame = tk.LabelFrame(right, text=" 📁 Dépôts & Fichiers — (-;", bg=self.colors["panel"],
                                          fg=self.colors["accent"], font=("Consolas", 9, "bold"))
        github_tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.github_tree = ttk.Treeview(github_tree_frame, columns=("type",), show="tree headings")
        self.github_tree.heading("#0", text="Nom", anchor="w")
        self.github_tree.heading("type", text="Type", anchor="w")
        self.github_tree.column("#0", width=180)
        self.github_tree.column("type", width=80)
        self.github_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.github_tree.bind("<Double-1>", self.on_github_tree_double_click)

        # ➕ Menu contextuel clic droit — SUPPRESSION v1.0
        def show_menu(event):
            item = self.github_tree.identify_row(event.y)
            if not item:
                return
            values = self.github_tree.item(item, "values")
            if not values or values[0] not in ("file", "folder"):
                return
            self.github_tree.selection_set(item)
            menu = tk.Menu(self.root, tearoff=0, bg="#161b22", fg="#c9d1d9", font=("Consolas", 9))
            menu.add_command(label="🗑️ Supprimer", command=self.delete_github_item)
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        self.github_tree.bind("<Button-3>", show_menu)

        # Boutons repo
        repo_btns = tk.Frame(right, bg=self.colors["panel"])
        repo_btns.pack(fill="x", padx=10, pady=(0, 5))
        tk.Button(repo_btns, text="🔄 Rafraîchir", command=self.refresh_github_tree,
                  bg="#21262d", fg=self.colors["accent"], font=("Consolas", 9), relief="flat", padx=10).pack(side="left", padx=2)
        tk.Button(repo_btns, text="➕ Créer dépôt", command=self.create_repo,
                  bg="#004d88", fg="white", font=("Consolas", 9), relief="flat", padx=10).pack(side="left", padx=2)

        # Envoi
        send_btn = tk.Button(right, text="📤 ENVOYER À LA VOLÉE →", command=self.start_send,
                             bg=self.colors["success"], fg="white", font=("Consolas", 10, "bold"), relief="flat", padx=20)
        send_btn.pack(pady=(5, 10))

        # Barre de statut
        self.status_var = tk.StringVar(value="Prêt • GPLv3 — white hat only • (-;")
        tk.Label(self.root, textvariable=self.status_var, bg="#010409", fg="#8b949e", font=("Consolas", 9),
                 anchor="w", padx=10, pady=4).pack(fill="x", side="bottom")

    # === Méthodes locales ===
    def select_drive(self, d):
        p = f"{d}:\\"
        if os.path.exists(p):
            self.local_path.set(p)
            self.refresh_local_tree()

    def on_tree_double_click(self, _):
        item = self.local_tree.focus()
        if not item: return
        name = self.local_tree.item(item, "text").replace("📁 ", "").replace("📄 ", "")
        new = os.path.join(self.local_path.get(), name)
        if os.path.isdir(new):
            self.local_path.set(new)
            self.refresh_local_tree()

    def refresh_local_tree(self):
        path = self.local_path.get()
        if not os.path.isdir(path): return
        self.local_tree.delete(*self.local_tree.get_children())
        try:
            for item in sorted(os.listdir(path)):
                if item in {"__pycache__", ".git", "logs.anti.spamm", "tokens", "backup"}: continue
                if not (item.endswith((".py", ".txt", ".md", ".html", ".json", ".cfg")) or os.path.isdir(os.path.join(path, item))): continue
                fp = os.path.join(path, item)
                size = "" if os.path.isdir(fp) else f"{os.path.getsize(fp):,}"
                icon = "📁" if os.path.isdir(fp) else "📄"
                self.local_tree.insert("", "end", text=f"{icon} {item}", values=(size,))
        except Exception as e:
            print(f"Erreur lecture {path}: {e}")

    # === GitHub : arborescence ===
    def refresh_github_tree(self):
        self.github_tree.delete(*self.github_tree.get_children())
        pat = self.github_pat.get().strip()
        user = self.github_user.get().strip()
        if not pat or not user:
            self.github_tree.insert("", "end", text="🔐 PAT requis — (-;", tags=("warn",))
            self.github_tree.tag_configure("warn", foreground=self.colors["warn"])
            return

        self.status_var.set("⏳ Chargement des dépôts GitHub… (-;")
        threading.Thread(target=self._load_github_repos, args=(user, pat), daemon=True).start()

    def _load_github_repos(self, user, pat):
        try:
            req = urllib.request.Request(f"https://api.github.com/user/repos?per_page=20", headers={
                "Authorization": f"token {pat}",
                "User-Agent": "kerberos-bridge (-;",
                "Accept": "application/vnd.github.v3+json"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                repos = json.loads(resp.read().decode("utf-8"))

            def update_ui():
                self.github_tree.delete(*self.github_tree.get_children())
                for repo in repos[:15]:
                    rid = self.github_tree.insert("", "end", text=f"📦 {repo['name']}", values=("repo",))
                    default_branch = repo.get("default_branch", "main")
                    bid = self.github_tree.insert(rid, "end", text=f"🌿 {default_branch}", values=("branch",))
                    self.github_tree.insert(bid, "end", text="… (-;", values=("loading",))
            self.root.after(0, update_ui)
            self.root.after(0, lambda: self.status_var.set(f"✅ {len(repos)} dépôts — (-;"))

        except Exception as e:
            def err_ui():
                self.github_tree.delete(*self.github_tree.get_children())
                self.github_tree.insert("", "end", text=f"❌ {type(e).__name__} — (-;", tags=("error",))
                self.github_tree.tag_configure("error", foreground=self.colors["error"])
                self.status_var.set(f"❌ Erreur — (-;")
            self.root.after(0, err_ui)

    def on_github_tree_double_click(self, _):
        item = self.github_tree.focus()
        if not item: return
        values = self.github_tree.item(item, "values")
        if not values: return
        typ = values[0]
        if typ == "branch":
            children = self.github_tree.get_children(item)
            for c in children:
                self.github_tree.delete(c)
            for f in ["📄 .gitignore", "📄 README.md", "📄 main.py", "📁 src", "📁 docs"]:
                self.github_tree.insert(item, "end", text=f"{f} — (-;", values=("file",))
            # Marquer certains comme "folder"
            for i in self.github_tree.get_children(item):
                text = self.github_tree.item(i, "text")
                if "📁" in text:
                    self.github_tree.item(i, values=("folder",))

    # === PAT Menu ===
    def show_pat_menu(self):
        menu = tk.Toplevel(self.root)
        menu.title("🔐 Durée du PAT — (-;")
        menu.geometry("300x180")
        menu.configure(bg=self.colors["panel"])
        menu.transient(self.root)
        menu.grab_set()

        tk.Label(menu, text="Choisissez la durée de validité", 
                 bg=self.colors["panel"], fg=self.colors["fg"], font=("Consolas", 10)).pack(pady=15)

        days_var = tk.IntVar(value=7)
        for days, text in [(7, "7 jours"), (30, "30 jours"), (90, "90 jours")]:
            tk.Radiobutton(menu, text=text, variable=days_var, value=days,
                           bg=self.colors["panel"], fg=self.colors["fg"],
                           selectcolor="#0d1117", font=("Consolas", 9)).pack(anchor="w", padx=30, pady=3)

        def confirm():
            webbrowser.open("https://github.com/settings/tokens/new?scopes=repo&description=Kerberos-Bridge".strip())
            self.status_var.set(f"🌐 Ouvrir GitHub → créez un PAT ({days_var.get()}j) — (-;")
            menu.destroy()

        tk.Button(menu, text="➡️ Créer PAT", command=confirm,
                  bg=self.colors["accent"], fg="white", font=("Consolas", 9), relief="flat", padx=20).pack(pady=15)

    # === Repo ===
    def create_repo(self):
        webbrowser.open("https://github.com/new".strip())
        self.status_var.set("🌐 Ouvrir GitHub → créez un dépôt — (-;")

    # === Auth Test ===
    def test_github_auth(self):
        u, p = self.github_user.get().strip(), self.github_pat.get().strip()
        if not u or not p:
            self.status_var.set("❌ Erreur — User + PAT requis — (-;")
            return
        self.status_var.set("⏳ Test en cours… (-;")
        threading.Thread(target=self._do_test_auth, args=(u, p), daemon=True).start()

    def _do_test_auth(self, user, pat):
        try:
            req = urllib.request.Request("https://api.github.com/user", headers={
                "Authorization": f"token {pat}",
                "User-Agent": "kerberos-bridge (-;"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                login = data.get("login", "").lower()
                if login == user.lower():
                    self.github_pat.set(pat)
                    self.root.after(0, lambda: self.status_var.set(f"✅ Auth OK — {user} — (-;"))
                else:
                    self.root.after(0, lambda: self.status_var.set(f"⚠️ User ≠ {user} — (-;"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"❌ Échec — {e} — (-;"))

    # === Envoi ===
    def start_send(self):
        user = self.github_user.get().strip()
        src = self.local_path.get()
        pat = self.github_pat.get().strip()
        if not os.path.isdir(src):
            self.status_var.set("❌ Dossier invalide — (-;")
            return
        if not user or not pat:
            self.status_var.set("❌ User + PAT requis — (-;")
            return
        self.status_var.set("⏳ Envoi… (-;")
        threading.Thread(target=self.send_to_github, args=(user, pat, src), daemon=True).start()

    def send_to_github(self, user, pat, src):
        try:
            name = os.path.basename(src.rstrip("/\\"))
            repo = self.github_repo.get() or "kerberos"
            tmp = os.path.join(BRIDGE_BASE, f"kb_{int(time.time())}")
            os.makedirs(tmp, exist_ok=True)
            dest = os.path.join(tmp, name)
            shutil.copytree(src, dest, dirs_exist_ok=True)

            for cmd in [
                ["git", "init"],
                ["git", "config", "user.name", "Kerberos (-;"],
                ["git", "config", "user.email", "kerberos@localhost"],
                ["git", "add", "."],
                ["git", "commit", "-m", "auto: kerberos bridge (-;"]
            ]:
                subprocess.run(cmd, cwd=tmp, check=True)

            url = f"https://github.com/{user}/{repo}.git".strip()
            subprocess.run(["git", "remote", "add", "origin", url], cwd=tmp, check=True)
            subprocess.run(["git", "-c", f'http.extraHeader=Authorization: token {pat}', "push", "-u", "origin", "main"],
                           cwd=tmp, check=True)
            self.root.after(0, lambda: self.status_var.set(f"✅ Poussé vers {user}/{repo} — (-;"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"❌ Échec — {e} — (-;"))

    # ✅ v1.0 — SUPPRESSION GITHUB (fichiers + dossiers)
    def delete_github_item(self):
        item = self.github_tree.focus()
        if not item:
            messagebox.showwarning("⚠️", "Sélectionnez un élément à supprimer.", parent=self.root)
            return

        repo_item = item
        while self.github_tree.parent(repo_item):
            repo_item = self.github_tree.parent(repo_item)
        repo_name = self.github_tree.item(repo_item, "text").replace("📦 ", "")
        
        path_parts = []
        cur = item
        while cur != repo_item:
            text = self.github_tree.item(cur, "text")
            clean = text.replace("📄 ", "").replace("📁 ", "").replace(" — (-;", "")
            path_parts.insert(0, clean)
            cur = self.github_tree.parent(cur)
        path = "/".join(path_parts)

        if not path:
            messagebox.showerror("❌", "Chemin invalide.", parent=self.root)
            return

        values = self.github_tree.item(item, "values")
        item_type = values[0] if values else "file"

        target = "dossier" if item_type == "folder" else "fichier"
        if not messagebox.askyesno(
            "❓ Supprimer ?",
            f"Supprimer le {target} :\n\n{path}\n\nde {repo_name} ?\n\n⚠️ Cette action est irréversible.",
            parent=self.root
        ):
            return

        pat = self.github_pat.get().strip()
        user = self.github_user.get().strip()
        if not pat or not user:
            self.status_var.set("❌ PAT ou utilisateur manquant")
            return

        self.status_var.set(f"⏳ Suppression {path}…")
        threading.Thread(
            target=self._delete_github_recursive,
            args=(user, repo_name, path, item_type, pat),
            daemon=True
        ).start()

    def _delete_github_recursive(self, owner, repo, path, item_type, pat):
        try:
            base_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
            headers = {
                "Authorization": f"token {pat}",
                "User-Agent": "kerberos-bridge (-;",
                "Accept": "application/vnd.github.v3+json"
            }

            if item_type == "file":
                req = urllib.request.Request(f"{base_url}/{path}", headers=headers)
                with urllib.request.urlopen(req) as resp:
                    meta = json.loads(resp.read().decode())
                sha = meta["sha"]

                data = json.dumps({
                    "message": f"delete: {path} via Kerberos — (-;",
                    "sha": sha
                }).encode()
                req = urllib.request.Request(
                    f"{base_url}/{path}",
                    data=data,
                    method="DELETE",
                    headers=headers
                )
                with urllib.request.urlopen(req):
                    self.root.after(0, lambda: self.status_var.set(f"✅ {path} supprimé"))

            elif item_type == "folder":
                def list_all_files(subpath):
                    url = f"{base_url}/{subpath}"
                    req = urllib.request.Request(url, headers=headers)
                    try:
                        with urllib.request.urlopen(req) as resp:
                            items = json.loads(resp.read().decode())
                            files = []
                            for item in items:
                                if item["type"] == "file":
                                    files.append(item["path"])
                                elif item["type"] == "dir":
                                    files.extend(list_all_files(item["path"]))
                            return files
                    except:
                        return []

                files = list_all_files(path)
                if not files:
                    self.root.after(0, lambda: self.status_var.set("📭 Dossier vide ou introuvable"))
                    return

                success = 0
                for fp in files:
                    try:
                        req = urllib.request.Request(f"{base_url}/{fp}", headers=headers)
                        with urllib.request.urlopen(req) as resp:
                            meta = json.loads(resp.read().decode())
                        sha = meta["sha"]
                        data = json.dumps({
                            "message": f"delete dir/{path}: {fp}",
                            "sha": sha
                        }).encode()
                        req = urllib.request.Request(
                            f"{base_url}/{fp}",
                            data=data,
                            method="DELETE",
                            headers=headers
                        )
                        with urllib.request.urlopen(req):
                            success += 1
                    except:
                        pass

                self.root.after(0, lambda: self.status_var.set(f"✅ {success}/{len(files)} fichiers supprimés"))

            self.root.after(0, self.refresh_github_tree)

        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode())
                msg = err.get("message", str(e))
            except:
                msg = str(e)
            self.root.after(0, lambda: self.status_var.set(f"❌ GitHub : {msg}"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"💥 {type(e).__name__}"))

    # === À propos ===
    def show_about(self):
        win = tk.Toplevel(self.root)
        win.title("❓ À propos — KERBEROS — (-;")
        win.geometry("680x540")
        win.configure(bg=self.colors["panel"])
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="KERBEROS — Bridge (v1.0) — (-;", 
                 bg=self.colors["panel"], fg=self.colors["accent"],
                 font=("Consolas", 14, "bold")).pack(pady=(15, 5))

        for line in [
            "Sécurité desktop locale — Windows 7/10, matériel ancien, zéro cloud.",
            "White hat only. GPLv3 — liberté, transparence, contrôle total.",
            "",
            "« Pas de trace. Pas de nuage. Juste du code qui protège. »",
            "(-; — Victor.Pozen"
        ]:
            tk.Label(win, text=line, bg=self.colors["panel"], fg=self.colors["fg"],
                     font=("Consolas", 10)).pack(anchor="w", padx=20)

        tk.Label(win, text="\n🔗 Liens :", bg=self.colors["panel"],
                 fg=self.colors["accent"], font=("Consolas", 10, "bold")).pack(anchor="w", padx=20, pady=(10,5))
        links = [
            ("GitHub (code source)", "https://github.com/victorpozen/kerberos"),
            ("Liberapay (EthicalKerberos)", "https://fr.liberapay.com/EthicalKerberos/")
        ]
        for text, url in links:
            lbl = tk.Label(win, text=f"{text} — (-;", bg=self.colors["panel"],
                           fg="#58a6ff", font=("Consolas", 10, "underline"), cursor="hand2")
            lbl.pack(anchor="w", padx=20, pady=2)
            lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u.strip()))

        tk.Label(win, text="\n📜 Licence : GPLv3 — libre, modifiable, partageable.", 
                 bg=self.colors["panel"], fg="#8b949e", font=("Consolas", 9)).pack(anchor="w", padx=20, pady=(15,5))

        tk.Button(win, text="Fermer — (-;", command=win.destroy,
                  bg="#21262d", fg="white", font=("Consolas", 10), relief="flat", padx=20).pack(pady=15)


# === LANCEMENT ===
if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.option_add("*Font", "Consolas 10")
        app = KerberosBridgeCore(root)
        root.mainloop()
    except Exception as e:
        input(f"\n🔒 Erreur fatale : {e} — (-;\nAppuyez sur Entrée pour quitter...")
        sys.exit(1)