#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Python Error Detector — Détecteur d'erreurs Python avec GUI Tkinter
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Détection erreurs syntaxe (ast)
- Détection erreurs d'import
- Vérification code quality (PEP8 basique)
- Interface Tkinter dark theme
- Export rapports JSON/HTML
- STANDALONE — Aucune dépendance Kerberos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  PYTHON ERROR DETECTOR v1.0 — Standalone
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE : GPLv3
#  AUTEUR  : Victor Pozen
#  VERSION : 1.0
#  DATE    : 2025
#  🔗 https://github.com/victorpozen
# ============================================================================

import ast
import sys
import os
import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ============================================================================
# === MOTEUR D'ANALYSE =======================================================
# ============================================================================
class PythonErrorDetector:
    """Détecteur d'erreurs Python — syntaxe, imports, quality"""
    
    def __init__(self):
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.info: List[Dict] = []
        self.files_scanned = 0
        self.files_ok = 0
        self.files_error = 0
    
    def reset(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.files_scanned = 0
        self.files_ok = 0
        self.files_error = 0
    
    def check_syntax(self, filepath: Path) -> Tuple[bool, Optional[str]]:
        """Vérifie la syntaxe Python avec ast"""
        try:
            source = filepath.read_text(encoding="utf-8")
            ast.parse(source, filename=str(filepath))
            return True, None
        except SyntaxError as e:
            return False, f"SyntaxError: {e.msg} (ligne {e.lineno})"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def check_imports(self, filepath: Path) -> List[str]:
        """Détecte les imports manquants ou problématiques"""
        warnings = []
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        try:
                            __import__(alias.name.split('.')[0])
                        except ImportError:
                            warnings.append(
                                f"Import manquant: '{alias.name}' (ligne {node.lineno})"
                            )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        try:
                            __import__(node.module.split('.')[0])
                        except ImportError:
                            warnings.append(
                                f"Import manquant: '{node.module}' (ligne {node.lineno})"
                            )
        except Exception:
            pass
        
        return warnings
    
    def check_code_quality(self, filepath: Path) -> List[str]:
        """Vérifications quality basiques (style PEP8)"""
        warnings = []
        try:
            lines = filepath.read_text(encoding="utf-8").splitlines()
            
            for i, line in enumerate(lines, 1):
                # Lignes trop longues (>120 caractères)
                if len(line) > 120:
                    warnings.append(f"Ligne {i}: Trop longue ({len(line)} chars)")
                
                # Espaces en fin de ligne
                if line.rstrip() != line:
                    warnings.append(f"Ligne {i}: Espaces en fin de ligne")
                
                # Tabs au lieu de spaces
                if '\t' in line:
                    warnings.append(f"Ligne {i}: Tabulation détectée")
                
                # Encoding magic comment manquant (si caractères spéciaux)
                if i == 1 and any(ord(c) > 127 for c in line):
                    if "# -*- coding:" not in line:
                        warnings.append("Encoding non déclaré en première ligne")
        except Exception:
            pass
        
        return warnings
    
    def scan_file(self, filepath: Path) -> Dict:
        """Scan un fichier Python complet"""
        result = {
            "file": str(filepath),
            "syntax_ok": True,
            "syntax_error": None,
            "import_warnings": [],
            "quality_warnings": [],
            "timestamp": datetime.now().isoformat(),
        }
        
        # Syntaxe
        syntax_ok, error = self.check_syntax(filepath)
        result["syntax_ok"] = syntax_ok
        result["syntax_error"] = error
        
        if not syntax_ok:
            self.errors.append({
                "type": "syntax",
                "file": str(filepath),
                "message": error,
                "severity": "critical",
            })
            self.files_error += 1
        else:
            # Imports (seulement si syntaxe OK)
            result["import_warnings"] = self.check_imports(filepath)
            for w in result["import_warnings"]:
                self.warnings.append({
                    "type": "import",
                    "file": str(filepath),
                    "message": w,
                    "severity": "warning",
                })
            
            # Quality
            result["quality_warnings"] = self.check_code_quality(filepath)
            for w in result["quality_warnings"]:
                self.warnings.append({
                    "type": "quality",
                    "file": str(filepath),
                    "message": w,
                    "severity": "info",
                })
            
            self.files_ok += 1
        
        self.files_scanned += 1
        return result
    
    def scan_directory(self, directory: Path, pattern: str = "*.py") -> Dict:
        """Scan récursif d'un dossier"""
        self.reset()
        
        py_files = list(directory.rglob(pattern))
        
        for filepath in py_files:
            self.scan_file(filepath)
        
        return self.get_report()
    
    def get_report(self) -> Dict:
        return {
            "files_scanned": self.files_scanned,
            "files_ok": self.files_ok,
            "files_error": self.files_error,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "timestamp": datetime.now().isoformat(),
        }
    
    def export_json(self, filepath: Path):
        """Export rapport en JSON"""
        filepath.write_text(
            json.dumps(self.get_report(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def export_html(self, filepath: Path):
        """Export rapport en HTML"""
        report = self.get_report()
        
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapport Python Error Detector — {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#0a0f1a; color:#00ffcc; font-family:Consolas,monospace; padding:20px; }}
        h1 {{ color:#00ffcc; margin-bottom:20px; }}
        h2 {{ color:#ff9800; margin:20px 0 10px; }}
        .stats {{ display:flex; gap:20px; margin:20px 0; }}
        .stat-box {{ background:#1a1a2e; padding:20px; border-radius:10px; border:2px solid #00ffcc; }}
        .stat-value {{ font-size:24px; font-weight:bold; }}
        .stat-label {{ color:#607d8b; }}
        .error {{ background:#2a1a1a; border-left:4px solid #ff5252; padding:10px; margin:5px 0; }}
        .warning {{ background:#2a251a; border-left:4px solid #ff9800; padding:10px; margin:5px 0; }}
        .info {{ background:#1a2a2a; border-left:4px solid #00ffcc; padding:10px; margin:5px 0; }}
        .file-path {{ color:#bb86fc; font-size:12px; }}
    </style>
</head>
<body>
    <h1>🔍 RAPPORT PYTHON ERROR DETECTOR</h1>
    <p>Généré le: {report['timestamp']}</p>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-value">{report['files_scanned']}</div>
            <div class="stat-label">Fichiers scannés</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color:#4CAF50;">{report['files_ok']}</div>
            <div class="stat-label">Fichiers OK</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color:#ff5252;">{report['files_error']}</div>
            <div class="stat-label">Erreurs critiques</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color:#ff9800;">{len(report['warnings'])}</div>
            <div class="stat-label">Warnings</div>
        </div>
    </div>
    
    <h2>🔴 ERREURS CRITIQUES</h2>
    {self._html_items(report['errors'])}
    
    <h2>🟠 WARNINGS</h2>
    {self._html_items(report['warnings'])}
    
    <h2>🔵 INFO</h2>
    {self._html_items(report['info'])}
</body>
</html>"""
        
        filepath.write_text(html, encoding="utf-8")
    
    def _html_items(self, items: List[Dict]) -> str:
        if not items:
            return "<p>Aucun</p>"
        html = ""
        for item in items:
            html += f"""
            <div class="{item.get('severity', 'info')}">
                <div class="file-path">{item.get('file', 'N/A')}</div>
                <div>{item.get('message', 'N/A')}</div>
            </div>"""
        return html

# ============================================================================
# === GUI TKINTER ============================================================
# ============================================================================
class ErrorDetectorGUI:
    """Interface graphique du détecteur d'erreurs"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔍 Python Error Detector — Standalone")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0f1a')
        
        self.detector = PythonErrorDetector()
        self.scanning = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg='#16213e', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🔍 PYTHON ERROR DETECTOR",
                bg='#16213e', fg='#00ffcc',
                font=("Consolas", 18, "bold")).pack(pady=20)
        
        # ── Controls ─────────────────────────────────────────────────────
        controls = tk.Frame(self.root, bg='#0a0f1a')
        controls.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(controls, text="📁 Sélectionner Dossier",
                 bg='#2d5a7b', fg='white',
                 font=("Consolas", 11, "bold"),
                 command=self._select_directory).pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls, text="🔍 Scanner",
                 bg='#2d7b5a', fg='white',
                 font=("Consolas", 11, "bold"),
                 command=self._start_scan).pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls, text="🧹 Clear",
                 bg='#7b2d2d', fg='white',
                 font=("Consolas", 11, "bold"),
                 command=self._clear_results).pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls, text="📄 Export JSON",
                 bg='#2d5a7b', fg='white',
                 font=("Consolas", 10),
                 command=self._export_json).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(controls, text="🌐 Export HTML",
                 bg='#2d5a7b', fg='white',
                 font=("Consolas", 10),
                 command=self._export_html).pack(side=tk.RIGHT, padx=5)
        
        self.path_label = tk.Label(controls, text="Aucun dossier sélectionné",
                                  bg='#0a0f1a', fg='#607d8b',
                                  font=("Consolas", 10))
        self.path_label.pack(side=tk.LEFT, padx=20)
        
        # ── Stats ────────────────────────────────────────────────────────
        stats_frame = tk.Frame(self.root, bg='#0a0f1a')
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.stats_labels = {}
        for i, (key, label, color) in enumerate([
            ("scanned", "📊 Scannés", "#00ffcc"),
            ("ok", "✅ OK", "#4CAF50"),
            ("errors", "🔴 Erreurs", "#ff5252"),
            ("warnings", "🟠 Warnings", "#ff9800"),
        ]):
            box = tk.Frame(stats_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=1)
            box.grid(row=0, column=i, padx=10, sticky="nsew")
            
            tk.Label(box, text=label, bg='#1a1a2e', fg='#a0a0c0',
                    font=("Consolas", 9)).pack(pady=5)
            
            val = tk.Label(box, text="0", bg='#1a1a2e', fg=color,
                          font=("Consolas", 16, "bold"))
            val.pack(pady=5)
            self.stats_labels[key] = val
        
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        stats_frame.columnconfigure(3, weight=1)
        
        # ── Results ──────────────────────────────────────────────────────
        results_frame = tk.LabelFrame(self.root, text=" 📋 Résultats ",
                                     bg='#1e1e2e', fg='#00ffcc',
                                     font=("Consolas", 11, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Notebook pour onglets
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet Erreurs
        self.errors_text = scrolledtext.ScrolledText(
            self.notebook, bg='#0a0a0a', fg='#ff5252',
            font=("Consolas", 10), wrap=tk.WORD
        )
        self.notebook.add(self.errors_text, text=' 🔴 Erreurs ')
        
        # Onglet Warnings
        self.warnings_text = scrolledtext.ScrolledText(
            self.notebook, bg='#0a0a0a', fg='#ff9800',
            font=("Consolas", 10), wrap=tk.WORD
        )
        self.notebook.add(self.warnings_text, text=' 🟠 Warnings ')
        
        # Onglet Info
        self.info_text = scrolledtext.ScrolledText(
            self.notebook, bg='#0a0a0a', fg='#00ffcc',
            font=("Consolas", 10), wrap=tk.WORD
        )
        self.notebook.add(self.info_text, text=' 🔵 Info ')
        
        # ── Progress ─────────────────────────────────────────────────────
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            self.root, variable=self.progress_var,
            maximum=100, mode='determinate'
        )
        self.progress.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.status_label = tk.Label(
            self.root, text="Prêt",
            bg='#0a0f1a', fg='#607d8b',
            font=("Consolas", 10)
        )
        self.status_label.pack(pady=(0, 10))
        
        # ── Footer ───────────────────────────────────────────────────────
        footer = tk.Frame(self.root, bg='#16213e', height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        tk.Label(footer, text="GPLv3 • Victor Pozen • Standalone — Aucune dépendance Kerberos",
                bg='#16213e', fg='#607d8b',
                font=("Consolas", 8)).pack(pady=10)
    
    def _select_directory(self):
        directory = filedialog.askdirectory(title="Sélectionner dossier à scanner")
        if directory:
            self.detector.reset()
            self.path_label.config(text=directory)
            self._clear_results()
    
    def _start_scan(self):
        path = self.path_label.cget("text")
        if path == "Aucun dossier sélectionné":
            messagebox.showwarning("Attention", "Veuillez sélectionner un dossier d'abord")
            return
        
        if self.scanning:
            return
        
        self.scanning = True
        self.status_label.config(text="Scan en cours...")
        self.progress_var.set(0)
        
        # Scan en thread pour ne pas bloquer l'UI
        threading.Thread(target=self._scan_thread, args=(path,), daemon=True).start()
    
    def _scan_thread(self, path: str):
        try:
            directory = Path(path)
            py_files = list(directory.rglob("*.py"))
            total = len(py_files)
            
            for i, filepath in enumerate(py_files):
                if not self.scanning:
                    break
                
                self.detector.scan_file(filepath)
                progress = ((i + 1) / total) * 100 if total > 0 else 100
                
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda s=f"Scan: {i+1}/{total}": self.status_label.config(text=s))
            
            self.root.after(0, self._update_results)
            self.root.after(0, lambda: self.status_label.config(text="✅ Scan terminé"))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"❌ Erreur: {e}"))
        finally:
            self.scanning = False
    
    def _update_results(self):
        report = self.detector.get_report()
        
        # Stats
        self.stats_labels["scanned"].config(text=str(report["files_scanned"]))
        self.stats_labels["ok"].config(text=str(report["files_ok"]))
        self.stats_labels["errors"].config(text=str(report["files_error"]))
        self.stats_labels["warnings"].config(text=str(len(report["warnings"])))
        
        # Erreurs
        self.errors_text.delete("1.0", tk.END)
        for err in report["errors"]:
            self.errors_text.insert(tk.END, f"🔴 {err['file']}\n")
            self.errors_text.insert(tk.END, f"   {err['message']}\n\n")
        
        # Warnings
        self.warnings_text.delete("1.0", tk.END)
        for warn in report["warnings"]:
            self.warnings_text.insert(tk.END, f"🟠 {warn['file']}\n")
            self.warnings_text.insert(tk.END, f"   {warn['message']}\n\n")
        
        # Info
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, f"📊 Fichiers scannés: {report['files_scanned']}\n")
        self.info_text.insert(tk.END, f"✅ Fichiers OK: {report['files_ok']}\n")
        self.info_text.insert(tk.END, f"🔴 Erreurs: {report['files_error']}\n")
        self.info_text.insert(tk.END, f"🟠 Warnings: {len(report['warnings'])}\n")
        self.info_text.insert(tk.END, f"⏰ Timestamp: {report['timestamp']}\n")
    
    def _clear_results(self):
        self.detector.reset()
        self.errors_text.delete("1.0", tk.END)
        self.warnings_text.delete("1.0", tk.END)
        self.info_text.delete("1.0", tk.END)
        self.stats_labels["scanned"].config(text="0")
        self.stats_labels["ok"].config(text="0")
        self.stats_labels["errors"].config(text="0")
        self.stats_labels["warnings"].config(text="0")
        self.progress_var.set(0)
        self.status_label.config(text="Prêt")
    
    def _export_json(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if filepath:
            self.detector.export_json(Path(filepath))
            messagebox.showinfo("Succès", f"Rapport exporté: {filepath}")
    
    def _export_html(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html")]
        )
        if filepath:
            self.detector.export_html(Path(filepath))
            messagebox.showinfo("Succès", f"Rapport exporté: {filepath}")
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _on_close(self):
        self.scanning = False
        self.root.destroy()

# ============================================================================
# === POINT D'ENTRÉE =========================================================
# ============================================================================
if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║  🔍 PYTHON ERROR DETECTOR — Standalone                    ║
║                                                            ║
║  • Détection erreurs syntaxe (ast)                        ║
║  • Détection imports manquants                            ║
║  • Code quality (PEP8 basique)                            ║
║  • Interface Tkinter dark theme                           ║
║  • Export rapports JSON/HTML                              ║
║  • STANDALONE — Aucune dépendance Kerberos                ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
║  🔗 github.com/victorpozen                                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    app = ErrorDetectorGUI()
    app.run()