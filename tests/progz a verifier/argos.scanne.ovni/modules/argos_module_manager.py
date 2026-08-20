#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧩 ARGOS MODULE MANAGER v1.0 — gestionnaire d'organes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3
- Liste TOUS les modules argos_*.py présents dans modules/
- ✅ Activer / ❌ Désactiver (écrit argos_manifest.json)
- 🔄 SYNC : reconnaît TOUS les modules présents
  (corrige le manifest ancien qui cachait 5 modules sur 7)
- ❓ Info : docstring du module (analyse AST)
Après modification : dans l'engine, bouton 🔄 Redécouvrir (ou redémarrer).
Usage : bouton organe dans ARGOS, ou python argos_module_manager.py
"""
import sys
import json
import ast
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


def _excepthook(t, v, tb):
    print("❌ ERREUR CRITIQUE:\n" + "".join(traceback.format_exception(t, v, tb)))
    input("Appuyez sur Entrée pour fermer...")


sys.excepthook = _excepthook

_p = Path(__file__).resolve().parent
ARGOS_ROOT = _p.parent if (_p.parent / "modules").exists() or _p.name == "modules" else _p
MODULES_DIR = ARGOS_ROOT / "modules"
MANIFEST = ARGOS_ROOT / "argos_manifest.json"


def load_manifest():
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    except Exception:
        return {}


def save_manifest(active):
    MANIFEST.write_text(json.dumps({"version": "4.0", "active_modules": sorted(active)},
                                   indent=2, ensure_ascii=False), encoding="utf-8")


class ManagerApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🧩 ARGOS MODULE MANAGER v1.0")
        self.root.geometry("760x560")
        self.root.configure(bg=self.BG)
        self.disc = []
        self.enabled = set()
        self._build()
        self._load()
        self.root.mainloop()

    def _build(self):
        tk.Label(self.root, text="🧩 MODULE MANAGER — tous les organes, un par un",
                 bg=self.BG2, fg=self.CY, font=("Consolas", 13, "bold")).pack(fill=tk.X, pady=8)

        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(bf, text="✅ Activer", bg='#4CAF50', fg=self.WH,
                  command=lambda: self._toggle(True)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="❌ Désactiver", bg='#ff5252', fg=self.WH,
                  command=lambda: self._toggle(False)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="🔄 SYNC TOUT", bg=self.OR, fg=self.BG,
                  font=("Consolas", 11, "bold"), command=self._sync).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="❓ Info", bg=self.BTN, fg=self.WH,
                  command=self._info).pack(side=tk.LEFT, padx=2)

        self.listbox = tk.Listbox(self.root, height=14, bg=self.BG2, fg=self.WH,
                                  selectbackground=self.BTN, font=("Consolas", 11))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.listbox.bind("<Double-Button-1>", lambda e: self._toggle(None))

        self.status = tk.Label(self.root, text="⏳ …", bg=self.BG, fg=self.OR,
                               font=("Consolas", 10))
        self.status.pack(pady=2)

        self.log = tk.Text(self.root, height=6, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.X, padx=10, pady=10)

    def _log(self, msg):
        try:
            self.log.configure(state='normal')
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state='disabled')
        except Exception:
            pass

    def _load(self):
        self.disc = sorted(MODULES_DIR.glob("argos_*.py"))
        man = load_manifest()
        active = man.get("active_modules")
        if active is None:
            self.enabled = {p.name for p in self.disc}
        else:
            self.enabled = set(active)
        hidden = [p.name for p in self.disc if p.name not in self.enabled]
        if hidden:
            self._log(f"⚠️ manifest ancien : {len(hidden)} module(s) caché(s) -> {', '.join(hidden)}")
            self._log("   clique 🔄 SYNC TOUT pour tous les reconnaître")
        self._refresh()
        self._log(f"🧩 {len(self.disc)} module(s) présent(s), {len(self.enabled)} actif(s)")

    def _refresh(self):
        self.listbox.delete(0, tk.END)
        for p in self.disc:
            flag = "✅ " if p.name in self.enabled else "❌ "
            self.listbox.insert(tk.END, flag + p.name)
        self.status.config(text=f"🧩 {len(self.disc)} présent(s) • {len(self.enabled)} actif(s)")

    def _sel(self):
        i = self.listbox.curselection()
        return self.disc[i[0]] if i else None

    def _toggle(self, state):
        p = self._sel()
        if p is None:
            return
        if state is None:
            state = p.name not in self.enabled
        if state:
            self.enabled.add(p.name)
        else:
            self.enabled.discard(p.name)
        save_manifest(self.enabled)
        self._refresh()
        self._log(f"{'✅' if state else '❌'} {p.name} -> {'actif' if state else 'désactivé'} (manifest écrit)")

    def _sync(self):
        self.enabled = {p.name for p in self.disc}
        save_manifest(self.enabled)
        self._refresh()
        self._log(f"🔄 SYNC : {len(self.enabled)} module(s) reconnu(s) — manifest réécrit")
        self._log("   dans l'engine : 🔄 Redécouvrir (ou redémarrer)")

    def _info(self):
        p = self._sel()
        if p is None:
            return
        try:
            doc = ast.get_docstring(ast.parse(p.read_text(encoding="utf-8"))) or "Aucune description."
        except Exception:
            doc = "Aucune description."
        messagebox.showinfo(f"📄 {p.name}", doc)


def run():
    ManagerApp()
    return "✅ MODULE MANAGER fermé"


def main():
    try:
        ManagerApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()