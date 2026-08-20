import sys
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import datetime
import os

# Tentative d'import moderne (Python 3.8+)
try:
    from importlib.metadata import distributions
except ImportError:
    try:
        import pkg_resources
        distributions = lambda: [d for d in pkg_resources.working_set]
    except ImportError:
        distributions = None

class APIScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Kerberos - API & Modules Scanner")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        self.root.configure(bg="#1e1e1e")

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#2d2d2d",
                        foreground="#ffffff",
                        fieldbackground="#2d2d2d",
                        font=("Consolas", 10))
        style.map("Treeview", background=[("selected", "#4a6fa5")])
        style.configure("Treeview.Heading",
                        background="#1a1a1a",
                        foreground="#00ccff",
                        font=("Consolas", 10, "bold"))

        # Titre
        title = tk.Label(root, text="Modules & APIs Installés", 
                         bg="#1e1e1e", fg="#00ccff", font=("Consolas", 14, "bold"))
        title.pack(pady=10)

        # Arbre
        self.tree = ttk.Treeview(root, columns=("Name", "Version"), show="headings", selectmode="browse")
        self.tree.heading("Name", text="Nom du module")
        self.tree.heading("Version", text="Version")
        self.tree.column("Name", width=500)
        self.tree.column("Version", width=150, anchor="center")

        vsb = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(root, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(20,0), pady=(0,20))
        vsb.pack(side="right", fill="y", pady=(0,20))
        hsb.pack(side="bottom", fill="x", padx=(20,0))

        self.tree.bind("<Control-c>", self.copy_selection)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Copier", command=self.copy_selection)

        # Bouton de scan
        scan_btn = tk.Button(root, text="🔄 Scanner et générer rapport", command=self.start_scan,
                             bg="#003366", fg="white", font=("Consolas", 10, "bold"),
                             relief="flat", padx=10, pady=5)
        scan_btn.pack(side="bottom", pady=(0,20))

        self.status = tk.Label(root, text="Prêt", bg="#1e1e1e", fg="#aaaaaa", font=("Consolas", 9))
        self.status.pack(side="bottom")

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_selection(self, event=None):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            name = item["values"][0] if item["values"] else ""
            self.root.clipboard_clear()
            self.root.clipboard_append(name)
            self.status.config(text=f"Copié : {name}")

    def start_scan(self):
        self.status.config(text="Scan en cours...")
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self.scan_modules, daemon=True).start()

    def scan_modules(self):
        packages = []
        try:
            if distributions is not None:
                dists = distributions()
                for dist in dists:
                    try:
                        name = dist.metadata.get("Name", "Inconnu") if hasattr(dist, 'metadata') else str(dist)
                        version = getattr(dist, 'version', "N/A")
                        packages.append((name or "Inconnu", version or "N/A"))
                    except Exception:
                        continue
            else:
                result = subprocess.run([sys.executable, "-m", "pip", "freeze"],
                                        capture_output=True, text=True, timeout=30)
                for line in result.stdout.strip().splitlines():
                    if "==" in line:
                        name, ver = line.split("==", 1)
                        packages.append((name.strip(), ver.strip()))
                    elif line.strip():
                        packages.append((line.strip(), "N/A"))

            packages.sort(key=lambda x: x[0].lower())
            self.root.after(0, self.display_and_save, packages)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erreur", f"Échec du scan :\n{str(e)}"))
            self.root.after(0, lambda: self.status.config(text="Erreur"))

    def display_and_save(self, packages):
        # Affichage dans l’UI
        for name, version in packages:
            self.tree.insert("", "end", values=(name, version))

        # Génération du rapport TXT
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rapport = f"Rapport des modules Python installés\n"
        rapport += f"Généré le : {now}\n"
        rapport += f"Nombre total de modules : {len(packages)}\n"
        rapport += "="*60 + "\n\n"

        for name, version in packages:
            rapport += f"{name} == {version}\n"

        # Sauvegarde
        chemin_rapport = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules_installes.txt")
        try:
            with open(chemin_rapport, "w", encoding="utf-8") as f:
                f.write(rapport)
            self.status.config(text=f"✅ {len(packages)} modules – Rapport sauvegardé : modules_installes.txt")
        except Exception as e:
            self.status.config(text=f"⚠️ Rapport non sauvegardé : {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = APIScannerApp(root)
    root.mainloop()

# === KERBEROS ENTRY POINT (auto-patché) ===
def run():
    """
    Point d'entrée standardisé pour Kerberos.
    Ce module n'avait pas de fonction run() → ajoutée automatiquement.
    """
    print("⚠️  [AUTO-PATCH] Module 'Api Scanner Kerberos' exécuté (pas d'action définie).")
    print("💡 Conseil : Implémentez une logique utile dans run() ou supprimez ce bloc.")
    return True

if __name__ == "__main__":
    run()
