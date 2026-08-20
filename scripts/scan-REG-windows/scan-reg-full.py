#!/usr/bin/env python3
# kerberos_reggui_full.py - Binôme & Victor Pozen (-;
# SCAN COMPLET du registre Windows → rapport TXT + HTML
# Thread-safe | Anti-double-scan | Profondeur configurable | Zero crash

import sys
import os

if os.name != 'nt':
    print("[!] Ce script fonctionne uniquement sous Windows.")
    input("Appuyez sur Entrée pour quitter...")
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
    import winreg
    import hashlib
    import time
    import webbrowser
    import threading
    from pathlib import Path
except Exception as e:
    print(f"[ERREUR CRITIQUE] Chargement échoué : {e}")
    input("Appuyez sur Entrée pour quitter...")
    sys.exit(1)

# --- Style Kerberos ---
BG_DARK = "#0a0a0a"
FG_GREEN = "#00ff00"
FONT_MONO = ("Consolas", 10)
BTN_COLOR = "#1a3a1a"
BTN_HOVER = "#2a5a2a"

HIVES = {
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKCR": winreg.HKEY_CLASSES_ROOT,
}

class RegExplorerFullGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🐸 KERBEROS - RegExplorer FULL")
        self.root.geometry("820x600")
        self.root.configure(bg=BG_DARK)

        self.log_text = tk.Text(
            root, bg=BG_DARK, fg=FG_GREEN,
            font=FONT_MONO, wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(root, bg=BG_DARK)
        btn_frame.pack(pady=5)

        self.btn_scan = tk.Button(
            btn_frame, text="🔍 Scanner TOUT le Registre",
            command=self.start_full_scan,
            bg=BTN_COLOR, fg=FG_GREEN, font=FONT_MONO,
            activebackground=BTN_HOVER
        )
        self.btn_scan.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(
            btn_frame, text="📤 Sauver Rapport (TXT + HTML)",
            command=self.save_report,
            bg=BTN_COLOR, fg=FG_GREEN, font=FONT_MONO,
            activebackground=BTN_HOVER
        )
        self.btn_save.pack(side=tk.LEFT, padx=5)

        self.scan_data = None
        self.scanning = False
        self.log("[✓] Prêt pour un scan complet du registre.")

    def log(self, msg):
        def _append():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def walk_key(self, hkey, base_path="", current_depth=0, max_depth=8):
        if current_depth > max_depth:
            return

        try:
            key_handle = winreg.OpenKey(hkey, base_path, 0, winreg.KEY_READ)
        except OSError:
            return

        values = []
        try:
            i = 0
            while True:
                name, data, _ = winreg.EnumValue(key_handle, i)
                values.append((name, str(data)[:60]))
                i += 1
        except OSError:
            pass

        adn_input = "".join(f"{n}={d}" for n, d in values).encode("utf-8", errors="ignore")
        adn_hash = hashlib.sha256(adn_input).hexdigest()[:16]

        yield (base_path or "(root)", len(values), adn_hash, values[:3])

        try:
            i = 0
            while True:
                subkey = winreg.EnumKey(key_handle, i)
                full = f"{base_path}\\{subkey}" if base_path else subkey
                yield from self.walk_key(hkey, full, current_depth + 1, max_depth)
                i += 1
        except OSError:
            pass

        winreg.CloseKey(key_handle)

    def do_full_scan(self, depth):
        try:
            self.log("[+] Démarrage du scan COMPLET du registre...")
            self.scan_data = {}
            start = time.time()
            total = 0

            for hive_name, hive_handle in HIVES.items():
                self.log(f"[.] Hive: {hive_name} (profondeur={depth})")
                entries = []
                for item in self.walk_key(hive_handle, "", 0, depth):
                    entries.append(item)
                    total += 1
                    if total % 500 == 0:
                        self.log(f"    → {total} clés explorées...")
                self.scan_data[hive_name] = entries

            elapsed = time.time() - start
            self.log(f"\n[✓] Scan terminé : {total} clés en {elapsed:.1f}s")
            self.log("[💡] Données prêtes pour export (TXT/HTML).")

        except Exception as e:
            self.log(f"[FATALE] Erreur pendant le scan : {e}")
        finally:
            self.scanning = False

    def start_full_scan(self):
        if self.scanning:
            messagebox.showinfo("Info", "Scan déjà en cours.")
            return

        depth = simpledialog.askinteger(
            "Profondeur",
            "Profondeur max (recommandé: 6-8)\n0 = racine seulement",
            initialvalue=7, minvalue=0, maxvalue=12
        )
        if depth is None:
            self.log("[!] Scan annulé.")
            return

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        self.scanning = True
        threading.Thread(target=self.do_full_scan, args=(depth,), daemon=True).start()

    def generate_reports(self, data):
        ts = int(time.time())
        base = f"reg_fullscan_{ts}"

        txt = Path(base + ".txt")
        with txt.open("w", encoding="utf-8") as f:
            f.write("=== KERBEROS - SCAN COMPLET DU REGISTRE ===\n\n")
            for hive, entries in data.items():
                f.write(f"\n[{hive}]\n")
                for path, count, adn, vals in entries:
                    f.write(f"{path}\n  Entrées: {count} | ADN: {adn}\n")
                    for n, v in vals:
                        f.write(f"    • {n} = {v}\n")

        html = Path(base + ".html")
        html.write_text("<html><body><pre>" + txt.read_text() + "</pre></body></html>", encoding="utf-8")

        try:
            webbrowser.open(html.resolve().as_uri())
        except:
            pass

        return str(txt), str(html)

    def save_report(self):
        if self.scanning:
            messagebox.showinfo("Info", "Scan en cours. Veuillez attendre.")
            return
        if not self.scan_data:
            messagebox.showwarning("⚠️ Attention", "Aucun scan effectué.")
            return
        txt, html = self.generate_reports(self.scan_data)
        self.log(f"[✅] Rapports générés :\n  • {txt}\n  • {html}")

def main():
    root = tk.Tk()
    RegExplorerFullGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
