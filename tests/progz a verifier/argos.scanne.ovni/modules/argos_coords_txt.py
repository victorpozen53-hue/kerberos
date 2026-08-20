#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📍 ARGOS COORDS TXT v1.0 — organe PRIVÉ : gestionnaire de coordonnées -> TXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Author: Victor Pozen | GPLv3 — usage LOCAL, ne jamais partager
- ➕ ajoute : nom + coords (DMS avec O ou décimal) + flag 🕊️ sanctuaire
- 📄 Export TXT LOCAL  : tout le carnet (machine + lisible ├──)
- 📄 Export TXT PUBLIC : les sanctuaires sont CENSURÉS (jamais divulgués)
- 📥 Import TXT : lignes name;lat;lon;flag ou coords brutes
- partage carnet/carnet.json avec argos_ge_manager.py
Usage : bouton organe dans ARGOS v3.0, ou python argos_coords_txt.py
"""
import sys
import re
import traceback
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox


def _excepthook(t, v, tb):
    print("❌ ERREUR CRITIQUE:\n" + "".join(traceback.format_exception(t, v, tb)))
    input("Appuyez sur Entrée pour fermer...")


sys.excepthook = _excepthook

_p = Path(__file__).resolve().parent
ARGOS_ROOT = _p.parent if (_p.parent / "carnet").exists() or _p.name == "modules" else _p
CARNET_DIR = ARGOS_ROOT / "carnet"
CARNET_FILE = CARNET_DIR / "carnet.json"
CARNET_DIR.mkdir(parents=True, exist_ok=True)


def parse_coord(s):
    s = s.strip()
    if not s:
        return None
    m = re.match(r"^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$", s)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.match(r"^(\d+)°(\d+)'([\d.]+)\"?\s*([NSns])[,;\s]+(\d+)°(\d+)'([\d.]+)\"?\s*([EWOewo])$", s)
    if m:
        lat = int(m.group(1)) + int(m.group(2)) / 60.0 + float(m.group(3)) / 3600.0
        if m.group(4).upper() == "S":
            lat = -lat
        lon = int(m.group(5)) + int(m.group(6)) / 60.0 + float(m.group(7)) / 3600.0
        if m.group(8).upper() in ("W", "O"):
            lon = -lon
        return lat, lon
    return None


def load_carnet():
    try:
        import json
        return json.loads(CARNET_FILE.read_text(encoding="utf-8")) if CARNET_FILE.exists() else []
    except Exception:
        return []


def save_carnet(data):
    import json
    CARNET_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def build_txt(data, public):
    """TXT machine (name;lat;lon;flag) + bloc lisible en ├──."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines = ["# ══════════════════════════════════════════════",
             "# 👁️ ARGOS CARNET — coords.txt" + (" (PUBLIC)" if public else " (LOCAL/PRIVÉ)"),
             f"# généré le {now} — GPLv3 Victor Pozen",
             "# format : nom;lat;lon;sanctuaire(0/1)",
             "# ══════════════════════════════════════════════"]
    for e in data:
        if e.get("sanctuaire"):
            if public:
                lines.append("# 🕊️ [PROTÉGÉ — non divulgué];;;1")
            else:
                lines.append(f"{e['name']};{e['lat']:.6f};{e['lon']:.6f};1")
        else:
            lines.append(f"{e['name']};{e['lat']:.6f};{e['lon']:.6f};0")
    lines.append("")
    lines.append("# ── version lisible ──")
    shown = [e for e in data if not (public and e.get("sanctuaire"))]
    for i, e in enumerate(shown):
        branch = "└──" if i == len(shown) - 1 else "├──"
        tag = " 🕊️" if e.get("sanctuaire") else ""
        lines.append(f"{branch} {e['name']} : {e['lat']:.6f}, {e['lon']:.6f}{tag}")
    if public and any(e.get("sanctuaire") for e in data):
        n = sum(1 for e in data if e.get("sanctuaire"))
        lines.append(f"└── 🕊️ {n} lieu(x) protégé(s) — coordonnées retenues")
    return "\n".join(lines) + "\n"


class CoordsTxtApp:
    BG = '#101418'; BG2 = '#1a2026'; CY = '#00ffcc'; OR = '#ffb347'
    WH = '#ffffff'; BTN = '#2d5a7b'

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📍 ARGOS COORDS TXT v1.0 — gestionnaire -> TXT")
        self.root.geometry("900x640")
        self.root.configure(bg=self.BG)
        self._build()
        self._refresh_list()
        self._log("📍 COORDS TXT prêt — le carnet est partagé avec le GE Manager")
        self._log("🕊️ export PUBLIC = sanctuaires automatiquement censurés")
        self.root.mainloop()

    def _build(self):
        af = tk.Frame(self.root, bg=self.BG)
        af.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(af, text="🏷️ Nom:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        tk.Entry(af, textvariable=self.name_var, width=16, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=3)
        tk.Label(af, text="📍 Coords:", bg=self.BG, fg=self.CY).pack(side=tk.LEFT)
        self.coord_var = tk.StringVar()
        tk.Entry(af, textvariable=self.coord_var, width=30, bg=self.BG2, fg=self.WH).pack(side=tk.LEFT, padx=3)
        self.sanct_var = tk.BooleanVar(value=False)
        tk.Checkbutton(af, text="🕊️ sanctuaire", variable=self.sanct_var, bg=self.BG, fg=self.OR,
                       selectcolor=self.BG2, activebackground=self.BG,
                       activeforeground=self.OR).pack(side=tk.LEFT, padx=5)
        tk.Button(af, text="➕ Ajouter", bg='#4CAF50', fg=self.WH, command=self._add).pack(side=tk.LEFT, padx=5)

        self.listbox = tk.Listbox(self.root, height=12, bg=self.BG2, fg=self.WH,
                                  selectbackground=self.BTN, font=("Consolas", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        bf = tk.Frame(self.root, bg=self.BG)
        bf.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(bf, text="🗑️ Supprimer", bg='#ff5252', fg=self.WH,
                  command=self._del).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="🕊️ Toggle", bg=self.BTN, fg=self.WH,
                  command=self._toggle).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="📥 Import TXT", bg=self.BTN, fg=self.WH,
                  command=self._import).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="📄 TXT LOCAL", bg='#4CAF50', fg=self.WH,
                  font=("Consolas", 11, "bold"), command=lambda: self._export(False)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(bf, text="📄 TXT PUBLIC", bg=self.BTN, fg=self.WH,
                  font=("Consolas", 11, "bold"), command=lambda: self._export(True)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.log = tk.Text(self.root, height=7, bg=self.BG2, fg='#4CAF50',
                           font=('Consolas', 10), state='disabled')
        self.log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _log(self, msg):
        try:
            self.log.configure(state='normal')
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state='disabled')
        except Exception:
            pass

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for e in load_carnet():
            flag = "🕊️ " if e.get("sanctuaire") else "📍 "
            self.listbox.insert(tk.END, f"{flag}{e['name']} — {e['lat']:.5f}, {e['lon']:.5f}")

    def _add(self):
        c = parse_coord(self.coord_var.get())
        if not c:
            messagebox.showerror("Erreur", "Coords invalides (décimal ou DMS avec O)")
            return
        data = load_carnet()
        data.append({"name": self.name_var.get().strip() or f"lieu_{len(data) + 1}",
                     "lat": c[0], "lon": c[1], "sanctuaire": self.sanct_var.get()})
        save_carnet(data)
        self._refresh_list()
        self._log(f"➕ Ajouté: {data[-1]['name']}")

    def _sel_idx(self):
        i = self.listbox.curselection()
        return i[0] if i else None

    def _del(self):
        i = self._sel_idx()
        if i is None:
            return
        data = load_carnet()
        gone = data.pop(i)
        save_carnet(data)
        self._refresh_list()
        self._log(f"🗑️ Supprimé: {gone['name']}")

    def _toggle(self):
        i = self._sel_idx()
        if i is None:
            return
        data = load_carnet()
        data[i]["sanctuaire"] = not data[i].get("sanctuaire", False)
        save_carnet(data)
        self._refresh_list()
        self._log(f"🔁 {data[i]['name']} -> " + ("🕊️ protégé" if data[i]["sanctuaire"] else "📍 public"))

    def _export(self, public):
        data = load_carnet()
        if not data:
            messagebox.showerror("Erreur", "Carnet vide")
            return
        out = CARNET_DIR / ("coords_public.txt" if public else "coords.txt")
        out.write_text(build_txt(data, public), encoding="utf-8")
        n_hid = sum(1 for e in data if e.get("sanctuaire")) if public else 0
        self._log(f"📄 {out.name} écrit ({len(data)} entrée(s)" +
                  (f", {n_hid} 🕊️ censurée(s))" if public else ")"))

    def _import(self):
        p = filedialog.askopenfilename(title="Fichier coords txt",
                                       filetypes=[("TXT", "*.txt"), ("Tous", "*.*")])
        if not p:
            return
        try:
            text = Path(p).read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            self._log(f"❌ lecture: {e}")
            return
        data = load_carnet()
        added = 0
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [x.strip() for x in line.split(";")]
            if len(parts) >= 3:
                try:
                    lat, lon = float(parts[1]), float(parts[2])
                    flag = parts[3] == "1" if len(parts) >= 4 else False
                    data.append({"name": parts[0], "lat": lat, "lon": lon, "sanctuaire": flag})
                    added += 1
                    continue
                except Exception:
                    pass
            c = parse_coord(line)
            if c:
                data.append({"name": f"lieu_{len(data) + 1}", "lat": c[0], "lon": c[1],
                             "sanctuaire": False})
                added += 1
        save_carnet(data)
        self._refresh_list()
        self._log(f"📥 Import: {added} coordonnée(s) ajoutée(s)")


def run():
    CoordsTxtApp()
    return "✅ COORDS TXT fermé"


def main():
    try:
        CoordsTxtApp()
    except Exception as e:
        print(f"❌ {e}")
        traceback.print_exc()
        input("Appuyez sur Entrée...")


if __name__ == '__main__':
    main()