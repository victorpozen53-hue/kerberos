# -*- coding: utf-8 -*-
# ==============================================================
# kerberos-browser.py — v1.1 — (-;
# Navigateur éthique maison — sans Chromium, sans Firefox, sans cloud.
# White hat only. GPLv3.
# ==============================================================

import os
import sys
import urllib.request
import urllib.parse
import ssl
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import html
import re
import threading
import time

# === UTILITAIRE : MENU CONTEXTE CLIC DROIT ===
def add_context_menu(widget):
    def copy():
        try:
            if hasattr(widget, 'selection_get'):
                text = widget.selection_get()
            elif hasattr(widget, 'get') and widget.tag_ranges("sel"):
                text = widget.get("sel.first", "sel.last")
            else:
                return
            widget.clipboard_clear()
            widget.clipboard_append(text)
        except tk.TclError:
            pass

    def paste():
        try:
            text = widget.clipboard_get()
            if hasattr(widget, 'insert'):
                widget.insert("insert", text)
            elif hasattr(widget, 'set'):
                widget.set(text)
        except tk.TclError:
            pass

    def select_all():
        try:
            if hasattr(widget, 'tag_add'):
                widget.tag_add("sel", "1.0", "end")
                widget.mark_set("insert", "end")
            elif hasattr(widget, 'selection_range'):
                widget.selection_range(0, 'end')
        except:
            pass

    def show_menu(event):
        menu = tk.Menu(widget, tearoff=0, bg="#21262d", fg="white", font=("Consolas", 9))
        try:
            _ = widget.selection_get()
            menu.add_command(label="📋 Copier", command=copy)
        except tk.TclError:
            menu.add_command(label="📋 Copier", state="disabled")

        try:
            _ = widget.clipboard_get()
            menu.add_command(label="📥 Coller", command=paste)
        except tk.TclError:
            menu.add_command(label="📥 Coller", state="disabled")

        menu.add_separator()
        menu.add_command(label="✅ Tout sélectionner", command=select_all)
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)
    widget.bind("<Control-c>", lambda e: copy())
    widget.bind("<Control-v>", lambda e: paste())
    widget.bind("<Control-a>", lambda e: select_all())

# === SSL AVEC CERTIFICATS LOCAUX ===
CERT_PATH = r"H:\navigator\certs\cacert.pem"
if os.path.isfile(CERT_PATH):
    SSL_CONTEXT = ssl.create_default_context(cafile=CERT_PATH)
else:
    SSL_CONTEXT = ssl.create_default_context()

# === GUARDS — via kerberos_brain ===
try:
    from kerberos_brain import get_brain
    brain = get_brain()
except Exception as e:
    brain = None
    print(f"[ALERT] kerberos_brain non chargé : {e} — (-;")

# === PANNEAU DÉPLIABLE — ÉTAT DES GUARDS ===
class GuardStatusPanel:
    def __init__(self, parent):
        self.is_expanded = True
        self.frame = tk.Frame(parent, bg="#0d1117")
        self.frame.pack(fill="x", padx=10, pady=(0,5))

        self.title_frame = tk.Frame(self.frame, bg="#161b22")
        self.title_frame.pack(fill="x")
        self.title_label = tk.Label(
            self.title_frame, text=" 🛡️ Guards — État — (-; ▼",
            bg="#161b22", fg="#58a6ff", font=("Consolas", 10, "bold"), cursor="hand2"
        )
        self.title_label.pack(fill="x", padx=8, pady=4)
        self.title_label.bind("<Button-1>", self.toggle)

        self.content_frame = tk.Frame(self.frame, bg="#161b22")
        self.content_frame.pack(fill="x", padx=1, pady=(0,1))

        self.guards_frame = tk.Frame(self.content_frame, bg="#161b22")
        self.guards_frame.pack(fill="x", padx=5, pady=5)

        self.labels = {}
        expected_guards = [
            "guard_bubble", "guard_no_shodan", "guard_no_tracker",
            "guard_no_pub", "guard_no_spamm", "guard_pe_arch", "guard_image"
        ]
        for name in expected_guards:
            row = tk.Frame(self.guards_frame, bg="#161b22")
            row.pack(fill="x", pady=1)
            status = tk.Label(row, text="⏳", bg="#161b22", fg="#d29922", font=("Consolas", 10))
            status.pack(side="left", padx=(0,6))
            tk.Label(row, text=name, bg="#161b22", fg="#c9d1d9", font=("Consolas", 10)).pack(side="left")
            self.labels[name] = status

        self.update_status()

    def toggle(self, _=None):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.content_frame.pack(fill="x", padx=1, pady=(0,1))
            self.title_label.config(text=" 🛡️ Guards — État — (-; ▼")
        else:
            self.content_frame.pack_forget()
            self.title_label.config(text=" 🛡️ Guards — (-; ▶")

    def update_status(self):
        status = {}
        if brain:
            try:
                status = brain.get_guard_status()
            except:
                pass
        for name, label in self.labels.items():
            state = status.get(name, "❌")
            fg = "#2ea043" if "✅" in state else "#f85149" if "❌" in state else "#d29922"
            label.config(text=state, fg=fg)
        if self.is_expanded:
            self.content_frame.after(5000, self.update_status)

# ==============================================================

class KerberosBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("KERBEROS BROWSER — v1.1 — (-;")
        self.root.geometry("1200x760")
        self.root.minsize(800, 500)
        self.root.configure(bg="#0d1117")

        self.colors = {
            "bg": "#0d1117", "fg": "#c9d1d9", "accent": "#00a0e9",
            "link": "#58a6ff", "hover": "#30363d", "panel": "#161b22",
            "status": "#010409", "button": "#21262d"
        }

        self.history = []
        self.history_index = -1
        self.current_url = ""
        self.create_widgets()

    def create_widgets(self):
        toolbar = tk.Frame(self.root, bg=self.colors["panel"], height=40)
        toolbar.pack(fill="x", padx=5, pady=5)

        btns = [
            ("◀️", self.go_back),
            ("▶️", self.go_forward),
            ("🔄", self.reload),
            ("🏠", self.go_home),
        ]
        for text, cmd in btns:
            btn = tk.Button(toolbar, text=text, command=cmd,
                            bg=self.colors["button"], fg=self.colors["fg"],
                            font=("Segoe UI", 9, "bold"), relief="flat", padx=8)
            btn.pack(side="left", padx=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colors["hover"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colors["button"]))

        tk.Label(toolbar, text="🌐", bg=self.colors["panel"], fg="#8b949e", font=("Segoe UI", 10)).pack(side="left", padx=(10,2))
        self.url_var = tk.StringVar(value="https://httpbin.org/get")
        self.url_entry = tk.Entry(toolbar, textvariable=self.url_var,
                                  bg="#0d1117", fg="#c9d1d9", insertbackground="#c9d1d9",
                                  font=("Consolas", 10), relief="flat")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.url_entry.bind("<Return>", self.load_url)
        self.url_entry.bind("<Button-1>", self.select_url)
        add_context_menu(self.url_entry)

        tk.Button(toolbar, text="▶️ Go", command=self.load_url,
                  bg=self.colors["accent"], fg="white", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=12).pack(side="left", padx=2)

        content = tk.Frame(self.root, bg=self.colors["bg"])
        content.pack(fill="both", expand=True, padx=10, pady=(0,5))

        # PANNEAU DE CONTRÔLE
        GuardStatusPanel(content)

        self.text = scrolledtext.ScrolledText(
            content, bg=self.colors["bg"], fg=self.colors["fg"],
            font=("Consolas", 10), wrap="word",
            relief="flat", padx=16, pady=16, spacing1=4, spacing3=6
        )
        self.text.pack(fill="both", expand=True)
        self.text.config(state="disabled")
        add_context_menu(self.text)

        self.text.tag_config("title", font=("Segoe UI", 18, "bold"), foreground=self.colors["accent"])
        self.text.tag_config("h1", font=("Segoe UI", 16, "bold"), foreground="#f0f6fc")
        self.text.tag_config("h2", font=("Segoe UI", 14, "bold"), foreground="#c9d1d9")
        self.text.tag_config("link", foreground=self.colors["link"], underline=1)
        self.text.tag_config("code", font=("Consolas", 9), background="#161b22", foreground="#79c0ff")
        self.text.tag_config("pre", font=("Consolas", 9), background="#0d1117", foreground="#8b949e", spacing1=6, spacing3=6)
        self.text.tag_config("warn", foreground="#d29922", font=("Consolas", 9, "italic"))
        self.text.tag_bind("link", "<Button-1>", self.on_link_click)
        self.text.tag_bind("link", "<Enter>", lambda e: self.text.config(cursor="hand2"))
        self.text.tag_bind("link", "<Leave>", lambda e: self.text.config(cursor=""))

        status = tk.Frame(self.root, bg=self.colors["status"], height=24)
        status.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar(value="Prêt • GPLv3 — white hat only • (-;")
        tk.Label(status, textvariable=self.status_var,
                 bg=self.colors["status"], fg="#8b949e",
                 font=("Consolas", 9), anchor="w", padx=10).pack(side="left")

        self.hover_url = tk.StringVar()
        tk.Label(status, textvariable=self.hover_url,
                 bg=self.colors["status"], fg="#58a6ff",
                 font=("Consolas", 9), anchor="e", padx=10).pack(side="right")

        self.text.bind("<Motion>", self.on_mouse_move)
        self.text.bind("<Leave>", lambda e: self.hover_url.set(""))
        self.text.bind("<Configure>", lambda e: self.text.yview_moveto(0))

        self.load_url()

    def select_url(self, _=None):
        self.url_entry.selection_range(0, "end")
        self.url_entry.focus()

    def go_home(self):
        self.url_var.set("https://httpbin.org/get")
        self.load_url()

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.url_var.set(self.history[self.history_index])
            self.load_url()

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.url_var.set(self.history[self.history_index])
            self.load_url()

    def reload(self):
        self.load_url()

    def load_url(self, _=None):
        url = self.url_var.get().strip()
        if not url:
            return

        if url.startswith("http://") and not url.startswith("http://localhost"):
            url = "https://" + url[7:]
            self.url_var.set(url)

        self.current_url = url
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        if not self.history or self.history[-1] != url:
            self.history.append(url)
        self.history_index = len(self.history) - 1

        self.status_var.set(f"⏳ Chargement {url}… — (-;")
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", f"Chargement de {url}…\n")
        self.text.config(state="disabled")

        threading.Thread(target=self._fetch_and_render, args=(url,), daemon=True).start()

    def _fetch_and_render(self, url):
        try:
            if url.startswith("file://"):
                path = urllib.parse.unquote(url[7:])
                if not os.path.isfile(path):
                    raise FileNotFoundError(f"Non trouvé : {path}")
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                title = os.path.basename(path)
                self.root.after(0, lambda: self.render_text(content, title, url))
                self.root.after(0, lambda: self.status_var.set(f"✅ Local — {title} — (-;"))
                return

            if not url.startswith("https://"):
                raise ValueError("HTTP non sécurisé bloqué — éthique Kerberos")

            # Analyse avec le cerveau
            alerts = []
            if brain:
                try:
                    alerts = brain.scan_content("", url)
                except:
                    pass

            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "kerberos-browser/1.1 (-;",
                    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8"
                }
            )
            with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=20) as resp:
                content_type = resp.headers.get_content_type()
                raw = resp.read()

                if "json" in content_type:
                    import json
                    data = json.loads(raw.decode("utf-8", errors="replace"))
                    pretty = json.dumps(data, indent=2, ensure_ascii=False)
                    self.root.after(0, lambda: self.render_text(pretty, url))
                else:
                    html_content = raw.decode("utf-8", errors="replace")
                    if brain:
                        try:
                            alerts.extend(brain.scan_content(html_content, url))
                        except:
                            pass
                    for alert in alerts:
                        self.root.after(0, lambda a=alert: self.text.insert("1.0", f"[ALERTE] {a}\n", "warn"))
                    title = self._extract_title(html_content) or url
                    self.root.after(0, lambda: self.render_html(html_content, title, url))

                self.root.after(0, lambda: self.status_var.set(f"✅ {url} — (-;"))

        except Exception as e:
            msg = f"❌ {type(e).__name__}: {e} — (-;"
            self.root.after(0, lambda: self.status_var.set(msg))
            self.root.after(0, lambda: self.text.config(state="normal"))
            self.root.after(0, lambda: self.text.delete("1.0", "end"))
            self.root.after(0, lambda: self.text.insert("1.0", msg, "warn"))
            self.root.after(0, lambda: self.text.config(state="disabled"))

    def _extract_title(self, html_str):
        m = re.search(r"<title>(.*?)</title>", html_str, re.IGNORECASE)
        return html.unescape(m.group(1)) if m else None

    def render_text(self, text, url):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text)
        self.text.config(state="disabled")

    def render_html(self, html_str, title, url):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("end", title + "\n", "title")
        self.text.insert("end", "═" * len(title) + "\n\n")

        text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"## \1", html_str, flags=re.IGNORECASE)
        text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"### \1", text, flags=re.IGNORECASE)
        text = re.sub(r"<strong>(.*?)</strong>", r"**\1**", text, flags=re.IGNORECASE)
        text = re.sub(r"<em>(.*?)</em>", r"*\1*", text, flags=re.IGNORECASE)
        text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE)
        text = re.sub(r"<pre><code>(.*?)</code></pre>", r"```\1```", text, flags=re.DOTALL)
        text = re.sub(r"<a\s+href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", r"[\2](\1)", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                self.text.insert("end", "\n")
                continue
            if line.startswith("## "):
                self.text.insert("end", line[3:] + "\n", "h1")
            elif line.startswith("### "):
                self.text.insert("end", line[4:] + "\n", "h2")
            elif line.startswith("```"):
                code = []
                for next_line in iter(lambda: next(iter(text.split("\n")), ""), ""):
                    if next_line == "```":
                        break
                    code.append(next_line)
                self.text.insert("end", "\n".join(code) + "\n", "pre")
            elif "`" in line:
                parts = line.split("`")
                for i, part in enumerate(parts):
                    tag = "code" if i % 2 == 1 else ""
                    self.text.insert("end", part, tag)
                self.text.insert("end", "\n")
            elif line.startswith("- ") or line.startswith("* "):
                self.text.insert("end", "• " + line[2:] + "\n")
            elif "[" in line and "](" in line and ")" in line:
                self._insert_link_line(line)
            else:
                self.text.insert("end", line + "\n")

        self.text.config(state="disabled")
        self.text.yview_moveto(0)

    def _insert_link_line(self, line):
        i = 0
        while i < len(line):
            m = re.search(r"\[([^\]]+)\]\(([^)]+)\)", line[i:])
            if not m:
                self.text.insert("end", line[i:] + "\n")
                break
            before = line[i:i + m.start()]
            if before:
                self.text.insert("end", before)
            text, url = m.group(1), m.group(2)
            self.text.insert("end", text, ("link", url))
            i += m.end()
        if not line.strip():
            self.text.insert("end", "\n")

    def on_link_click(self, event):
        index = self.text.index(f"@{event.x},{event.y}")
        tags = self.text.tag_names(index)
        for tag in tags:
            if tag and (tag.startswith("http") or tag.startswith("file://")):
                self.url_var.set(tag)
                self.load_url()
                return

    def on_mouse_move(self, event):
        index = self.text.index(f"@{event.x},{event.y}")
        tags = self.text.tag_names(index)
        for tag in tags:
            if tag and (tag.startswith("http") or tag.startswith("file://")):
                self.hover_url.set(tag)
                return
        self.hover_url.set("")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        root.option_add("*Font", "Consolas 10")
        app = KerberosBrowser(root)
        root.mainloop()
    except Exception as e:
        input(f"\n🔒 Erreur : {e} — (-;\nAppuyez sur Entrée pour quitter...")
        sys.exit(1)