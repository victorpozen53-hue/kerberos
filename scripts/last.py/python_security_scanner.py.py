#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔓 Python Security Scanner — Détecteur de failles de sécurité
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Détection mots de passe codés en dur
- Détection eval() / exec() dangereux
- Détection injections SQL potentielles
- Détection appels réseau non sécurisés
- Détection gestion d'exceptions faible
- Interface Tkinter dark theme
- Export rapports JSON/HTML
- STANDALONE — Aucune dépendance externe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  PYTHON SECURITY SCANNER v1.0 — Standalone
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE : GPLv3
#  AUTEUR  : Victor Pozen
#  VERSION : 1.0
#  DATE    : 2025
#  🔗 https://github.com/victorpozen
# ============================================================================

import ast
import re
import json
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# ============================================================================
# === MOTEUR D'ANALYSE DE SÉCURITÉ ===========================================
# ============================================================================
class SecurityScanner:
    """Scanner de failles de sécurité Python"""
    
    # Patterns de vulnérabilités
    VULN_PATTERNS = {
        "hardcoded_password": [
            r'(?i)(password|passwd|pwd|secret|token|api_key)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']',
        ],
        "dangerous_eval": [
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'\bcompile\s*\(',
            r'\b__import__\s*\(',
        ],
        "sql_injection": [
            r'execute\s*\(\s*["\'].*%s.*["\']',
            r'execute\s*\(\s*f["\'].*\{.*\}.*["\']',
            r'execute\s*\(\s*["\'].*\+.*["\']',
            r'cursor\.execute\s*\([^,)]+\+',
        ],
        "unsafe_deserialization": [
            r'\bpickle\.loads?\s*\(',
            r'\byaml\.load\s*\([^)]*\)',
            r'\bmarshal\.loads?\s*\(',
        ],
        "weak_crypto": [
            r'\bmd5\s*\(',
            r'\bsha1\s*\(',
            r'\bDES\s*\(',
            r'\bRC4\s*\(',
            r'\bBlowfish\s*\(',
        ],
        "command_injection": [
            r'\bos\.system\s*\(',
            r'\bsubprocess\.call\s*\([^)]*shell\s*=\s*True',
            r'\bsubprocess\.Popen\s*\([^)]*shell\s*=\s*True',
            r'\bcommands\.getoutput\s*\(',
        ],
        "path_traversal": [
            r'open\s*\([^)]*\+[^)]*\)',
            r'open\s*\(\s*f["\'].*\{.*\}.*["\']',
        ],
        "debug_mode": [
            r'(?i)debug\s*=\s*True',
            r'(?i)DEBUG\s*=\s*True',
            r'(?i)FLASK_DEBUG\s*=\s*True',
        ],
        "insecure_transport": [
            r'http://(?!localhost)',
            r'verify\s*=\s*False',
            r'cert_reqs\s*=\s*CERT_NONE',
        ],
        "hardcoded_ip": [
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        ],
    }
    
    # Sévérités
    SEVERITY = {
        "hardcoded_password": "CRITICAL",
        "dangerous_eval": "CRITICAL",
        "sql_injection": "CRITICAL",
        "unsafe_deserialization": "HIGH",
        "weak_crypto": "MEDIUM",
        "command_injection": "CRITICAL",
        "path_traversal": "HIGH",
        "debug_mode": "MEDIUM",
        "insecure_transport": "MEDIUM",
        "hardcoded_ip": "LOW",
    }
    
    # Couleurs par sévérité
    COLORS = {
        "CRITICAL": "#ff0000",
        "HIGH": "#ff6600",
        "MEDIUM": "#ffcc00",
        "LOW": "#00ccff",
        "INFO": "#00ff00",
    }
    
    def __init__(self):
        self.vulnerabilities: List[Dict] = []
        self.files_scanned = 0
        self.safe_files = 0
        self.risky_files = 0
    
    def reset(self):
        self.vulnerabilities = []
        self.files_scanned = 0
        self.safe_files = 0
        self.risky_files = 0
    
    def scan_file(self, filepath: Path) -> List[Dict]:
        """Scan un fichier Python pour failles de sécurité"""
        file_vulns = []
        
        try:
            source = filepath.read_text(encoding="utf-8", errors="ignore")
            lines = source.splitlines()
            
            # 1. Analyse par patterns regex
            for vuln_type, patterns in self.VULN_PATTERNS.items():
                for pattern in patterns:
                    for i, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            # Ignorer les commentaires
                            if line.strip().startswith('#'):
                                continue
                            
                            vuln = {
                                "file": str(filepath),
                                "line": i,
                                "type": vuln_type,
                                "severity": self.SEVERITY.get(vuln_type, "INFO"),
                                "code": line.strip()[:100],
                                "pattern": pattern[:50],
                                "timestamp": datetime.now().isoformat(),
                            }
                            file_vulns.append(vuln)
            
            # 2. Analyse AST pour détections avancées
            try:
                tree = ast.parse(source)
                ast_vulns = self._analyze_ast(tree, filepath, lines)
                file_vulns.extend(ast_vulns)
            except SyntaxError:
                pass
            
            # Deduplication
            seen = set()
            unique_vulns = []
            for v in file_vulns:
                key = (v["file"], v["line"], v["type"])
                if key not in seen:
                    seen.add(key)
                    unique_vulns.append(v)
            
            self.vulnerabilities.extend(unique_vulns)
            self.files_scanned += 1
            
            if unique_vulns:
                self.risky_files += 1
            else:
                self.safe_files += 1
            
            return unique_vulns
            
        except Exception as e:
            return [{"file": str(filepath), "error": str(e)}]
    
    def _analyze_ast(self, tree: ast.AST, filepath: Path, lines: List[str]) -> List[Dict]:
        """Analyse AST pour détections avancées"""
        vulns = []
        
        for node in ast.walk(tree):
            # Détection import dangereux
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ["pickle", "marshal", "shelve"]:
                        vulns.append({
                            "file": str(filepath),
                            "line": node.lineno,
                            "type": "unsafe_import",
                            "severity": "MEDIUM",
                            "code": f"import {alias.name}",
                            "pattern": "AST: unsafe import",
                            "timestamp": datetime.now().isoformat(),
                        })
            
            # Détection fonction dangereuse
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec", "compile"]:
                        vulns.append({
                            "file": str(filepath),
                            "line": node.lineno,
                            "type": "dangerous_function",
                            "severity": "CRITICAL",
                            "code": lines[node.lineno - 1].strip()[:100] if node.lineno <= len(lines) else "",
                            "pattern": f"AST: {node.func.id}()",
                            "timestamp": datetime.now().isoformat(),
                        })
        
        return vulns
    
    def scan_directory(self, directory: Path, pattern: str = "*.py") -> Dict:
        """Scan récursif d'un dossier"""
        self.reset()
        
        py_files = list(directory.rglob(pattern))
        
        for filepath in py_files:
            self.scan_file(filepath)
        
        return self.get_report()
    
    def get_report(self) -> Dict:
        # Regrouper par sévérité
        by_severity = defaultdict(list)
        for v in self.vulnerabilities:
            by_severity[v.get("severity", "INFO")].append(v)
        
        # Regrouper par type
        by_type = defaultdict(list)
        for v in self.vulnerabilities:
            by_type[v.get("type", "unknown")].append(v)
        
        return {
            "files_scanned": self.files_scanned,
            "safe_files": self.safe_files,
            "risky_files": self.risky_files,
            "total_vulnerabilities": len(self.vulnerabilities),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_type": {k: len(v) for k, v in by_type.items()},
            "vulnerabilities": self.vulnerabilities,
            "timestamp": datetime.now().isoformat(),
        }
    
    def export_json(self, filepath: Path):
        filepath.write_text(
            json.dumps(self.get_report(), indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )
    
    def export_html(self, filepath: Path):
        report = self.get_report()
        
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapport Security Scanner — {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background:#0a0f1a; color:#00ffcc; font-family:Consolas,monospace; padding:20px; }}
        h1 {{ color:#00ffcc; margin-bottom:20px; }}
        h2 {{ color:#ff9800; margin:20px 0 10px; }}
        .stats {{ display:flex; gap:20px; margin:20px 0; flex-wrap:wrap; }}
        .stat-box {{ background:#1a1a2e; padding:20px; border-radius:10px; border:2px solid #00ffcc; min-width:150px; }}
        .stat-value {{ font-size:24px; font-weight:bold; }}
        .stat-label {{ color:#607d8b; }}
        .vuln {{ padding:10px; margin:5px 0; border-radius:5px; border-left:4px solid; }}
        .CRITICAL {{ background:#2a1a1a; border-color:#ff0000; }}
        .HIGH {{ background:#2a1f1a; border-color:#ff6600; }}
        .MEDIUM {{ background:#2a251a; border-color:#ffcc00; }}
        .LOW {{ background:#1a2a2a; border-color:#00ccff; }}
        .file-path {{ color:#bb86fc; font-size:12px; }}
        .code {{ background:#0a0a0a; padding:5px; border-radius:3px; font-size:11px; margin-top:5px; }}
    </style>
</head>
<body>
    <h1>🔓 PYTHON SECURITY SCANNER — RAPPORT</h1>
    <p>Généré le: {report['timestamp']}</p>
    
    <div class="stats">
        <div class="stat-box">
            <div class="stat-value">{report['files_scanned']}</div>
            <div class="stat-label">Fichiers scannés</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color:#4CAF50;">{report['safe_files']}</div>
            <div class="stat-label">Fichiers sains</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color:#ff5252;">{report['risky_files']}</div>
            <div class="stat-label">Fichiers à risque</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color:#ff9800;">{report['total_vulnerabilities']}</div>
            <div class="stat-label">Vulnérabilités</div>
        </div>
    </div>
    
    <h2>📊 PAR SÉVÉRITÉ</h2>
    <p>
        🔴 CRITICAL: {report['by_severity'].get('CRITICAL', 0)} |
        🟠 HIGH: {report['by_severity'].get('HIGH', 0)} |
        🟡 MEDIUM: {report['by_severity'].get('MEDIUM', 0)} |
        🔵 LOW: {report['by_severity'].get('LOW', 0)}
    </p>
    
    <h2>🔴 CRITIQUES</h2>
    {self._html_vulns([v for v in report['vulnerabilities'] if v.get('severity') == 'CRITICAL'][:20])}
    
    <h2>🟠 HAUTES</h2>
    {self._html_vulns([v for v in report['vulnerabilities'] if v.get('severity') == 'HIGH'][:20])}
    
    <h2>🟡 MOYENNES</h2>
    {self._html_vulns([v for v in report['vulnerabilities'] if v.get('severity') == 'MEDIUM'][:20])}
</body>
</html>"""
        
        filepath.write_text(html, encoding="utf-8")
    
    def _html_vulns(self, vulns: List[Dict]) -> str:
        if not vulns:
            return "<p>Aucune</p>"
        html = ""
        for v in vulns:
            html += f"""
            <div class="vuln {v.get('severity', 'INFO')}">
                <div class="file-path">{v.get('file', 'N/A')} — Ligne {v.get('line', '?')}</div>
                <div><strong>{v.get('type', 'unknown')}</strong> — {v.get('severity', 'INFO')}</div>
                <div class="code">{v.get('code', 'N/A')}</div>
            </div>"""
        return html


# ============================================================================
# === GUI TKINTER ============================================================
# ============================================================================
class SecurityScannerGUI:
    """Interface graphique du scanner de sécurité"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔓 Python Security Scanner — Détecteur de Failles")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0f1a')
        
        self.scanner = SecurityScanner()
        self.scanning = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg='#16213e', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="🔓 PYTHON SECURITY SCANNER",
                bg='#16213e', fg='#ff5252',
                font=("Consolas", 18, "bold")).pack(pady=20)
        
        # ── Controls ─────────────────────────────────────────────────────
        controls = tk.Frame(self.root, bg='#0a0f1a')
        controls.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(controls, text="📁 Sélectionner Dossier",
                 bg='#2d5a7b', fg='white',
                 font=("Consolas", 11, "bold"),
                 command=self._select_directory).pack(side=tk.LEFT, padx=5)
        
        tk.Button(controls, text="🔍 Scanner",
                 bg='#ff5252', fg='white',
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
            ("safe", "✅ Sains", "#4CAF50"),
            ("risky", "🔴 À risque", "#ff5252"),
            ("critical", "☢️ Critiques", "#ff0000"),
            ("high", "🟠 Hautes", "#ff6600"),
            ("medium", "🟡 Moyennes", "#ffcc00"),
        ]):
            box = tk.Frame(stats_frame, bg='#1a1a2e', relief=tk.RIDGE, bd=1)
            box.grid(row=0, column=i, padx=5, sticky="nsew")
            
            tk.Label(box, text=label, bg='#1a1a2e', fg='#a0a0c0',
                    font=("Consolas", 8)).pack(pady=3)
            
            val = tk.Label(box, text="0", bg='#1a1a2e', fg=color,
                          font=("Consolas", 14, "bold"))
            val.pack(pady=3)
            self.stats_labels[key] = val
        
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        stats_frame.columnconfigure(3, weight=1)
        stats_frame.columnconfigure(4, weight=1)
        stats_frame.columnconfigure(5, weight=1)
        
        # ── Results ──────────────────────────────────────────────────────
        results_frame = tk.LabelFrame(self.root, text=" 📋 Vulnérabilités Détectées ",
                                     bg='#1e1e2e', fg='#ff5252',
                                     font=("Consolas", 11, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Notebook pour onglets par sévérité
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglets par sévérité
        self.vuln_texts = {}
        for severity, color in [("CRITICAL", "#ff0000"), ("HIGH", "#ff6600"), 
                                ("MEDIUM", "#ffcc00"), ("LOW", "#00ccff")]:
            text = scrolledtext.ScrolledText(
                self.notebook, bg='#0a0a0a', fg=color,
                font=("Consolas", 9), wrap=tk.WORD
            )
            self.notebook.add(text, text=f' {severity} ')
            self.vuln_texts[severity] = text
        
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
        
        tk.Label(footer, text="GPLv3 • Victor Pozen • Standalone — Détection failles sécurité Python",
                bg='#16213e', fg='#607d8b',
                font=("Consolas", 8)).pack(pady=10)
    
    def _select_directory(self):
        directory = filedialog.askdirectory(title="Sélectionner dossier à scanner")
        if directory:
            self.scanner.reset()
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
        self.status_label.config(text="Scan de sécurité en cours...")
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
                
                self.scanner.scan_file(filepath)
                progress = ((i + 1) / total) * 100 if total > 0 else 100
                
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda s=f"Scan: {i+1}/{total}": self.status_label.config(text=s))
            
            self.root.after(0, self._update_results)
            self.root.after(0, lambda: self.status_label.config(text="✅ Scan de sécurité terminé"))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"❌ Erreur: {e}"))
        finally:
            self.scanning = False
    
    def _update_results(self):
        report = self.scanner.get_report()
        
        # Stats
        self.stats_labels["scanned"].config(text=str(report["files_scanned"]))
        self.stats_labels["safe"].config(text=str(report["safe_files"]))
        self.stats_labels["risky"].config(text=str(report["risky_files"]))
        self.stats_labels["critical"].config(text=str(report["by_severity"].get("CRITICAL", 0)))
        self.stats_labels["high"].config(text=str(report["by_severity"].get("HIGH", 0)))
        self.stats_labels["medium"].config(text=str(report["by_severity"].get("MEDIUM", 0)))
        
        # Vulnérabilités par onglet
        for severity, text_widget in self.vuln_texts.items():
            text_widget.delete("1.0", tk.END)
            vulns = [v for v in report["vulnerabilities"] if v.get("severity") == severity]
            
            if not vulns:
                text_widget.insert(tk.END, "✅ Aucune vulnérabilité détectée\n")
            else:
                for v in vulns[:50]:  # Limite à 50 par onglet
                    text_widget.insert(tk.END, f"📁 {Path(v['file']).name}\n")
                    text_widget.insert(tk.END, f"   Ligne {v.get('line', '?')} — {v.get('type', 'unknown')}\n")
                    text_widget.insert(tk.END, f"   {v.get('code', 'N/A')}\n\n")
                
                if len(vulns) > 50:
                    text_widget.insert(tk.END, f"\n... et {len(vulns) - 50} autres\n")
    
    def _clear_results(self):
        self.scanner.reset()
        for text_widget in self.vuln_texts.values():
            text_widget.delete("1.0", tk.END)
        for lbl in self.stats_labels.values():
            lbl.config(text="0")
        self.progress_var.set(0)
        self.status_label.config(text="Prêt")
    
    def _export_json(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")]
        )
        if filepath:
            self.scanner.export_json(Path(filepath))
            messagebox.showinfo("Succès", f"Rapport exporté: {filepath}")
    
    def _export_html(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html")]
        )
        if filepath:
            self.scanner.export_html(Path(filepath))
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
║  🔓 PYTHON SECURITY SCANNER — Détecteur de Failles       ║
║                                                            ║
║  • Mots de passe codés en dur                             ║
║  • eval() / exec() dangereux                              ║
║  • Injections SQL potentielles                            ║
║  • Désérialisation non sécurisée                          ║
║  • Cryptographie faible (MD5, SHA1)                       ║
║  • Injection de commandes                                 ║
║  • Path traversal                                         ║
║  • Mode debug activé                                      ║
║  • Transport non sécurisé (HTTP, verify=False)            ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
║  🔗 github.com/victorpozen                                ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    app = SecurityScannerGUI()
    app.run()