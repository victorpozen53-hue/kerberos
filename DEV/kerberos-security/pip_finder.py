#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 Pip Finder — Scanner de dépendances Python
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ce script analyse récursivement un dossier contenant du code source Python
pour identifier les packages pip utilisés (imports tiers).

FONCTIONNALITÉS :
✅ Scan récursif de tous les fichiers .py
✅ Parsing des imports (import x, from x import y)
✅ Distinction stdlib vs third-party (pip)
✅ Génération requirements.txt propre
✅ Vérification optionnelle des packages installés
✅ Détection des imports conditionnels et commentaires

Copyright (C) 2025 Victor Pozen — GPLv3
"""
# ============================================================================
#  KERBEROS ULTIMATE v4.3 — Pip Finder
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
import sys
import os
import re
import ast
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, List, Optional, Tuple
from collections import defaultdict

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================
# Liste des modules standards Python (3.8 à 3.12)
# Source : https://docs.python.org/3/py-modindex.html
STDLIB_MODULES = {
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio",
    "asyncore", "atexit", "audioop", "base64", "bdb", "binascii",
    "binhex", "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb",
    "chunk", "cmath", "cmd", "code", "codecs", "codeop", "collections",
    "colorsys", "compileall", "concurrent", "configparser", "contextlib",
    "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal",
    "difflib", "dis", "distutils", "doctest", "email", "encodings",
    "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput",
    "fnmatch", "fractions", "ftplib", "functools", "gc", "getopt",
    "getpass", "gettext", "glob", "graphlib", "grp", "gzip", "hashlib",
    "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr",
    "imp", "importlib", "inspect", "io", "ipaddress", "itertools",
    "json", "keyword", "lib2to3", "linecache", "locale", "logging",
    "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
    "mmap", "modulefinder", "multiprocessing", "netrc", "nis",
    "nntplib", "numbers", "operator", "optparse", "os", "ossaudiodev",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
    "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
    "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib",
    "resource", "rlcompleter", "runpy", "sched", "secrets", "select",
    "selectors", "shelve", "shlex", "shutil", "signal", "site",
    "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "spwd",
    "sqlite3", "ssl", "stat", "statistics", "string", "stringprep",
    "struct", "subprocess", "sunau", "symtable", "sys", "sysconfig",
    "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile", "termios",
    "test", "textwrap", "threading", "time", "timeit", "tkinter",
    "token", "tokenize", "trace", "traceback", "tracemalloc", "tty",
    "turtle", "turtledemo", "types", "typing", "unicodedata", "unittest",
    "urllib", "uu", "uuid", "venv", "warnings", "wave", "weakref",
    "webbrowser", "winreg", "winsound", "wsgiref", "xdrlib", "xml",
    "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib", "_thread",
    # Modules courants souvent confondus
    "setuptools", "pkg_resources", "wheel",
}

# Mapping nom d'import → nom du package pip (quand différents)
IMPORT_TO_PACKAGE = {
    "cv2": "opencv-python",
    "PIL": "pillow",
    "sklearn": "scikit-learn",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "jwt": "pyjwt",
    "serial": "pyserial",
    "usb": "pyusb",
    "git": "gitpython",
    "socks": "pysocks",
    "OpenSSL": "pyopenssl",
    "Crypto": "pycryptodome",
    "googleapiclient": "google-api-python-client",
}

# Fichiers/dossiers à ignorer
IGNORE_PATTERNS = {
    "__pycache__", ".git", ".venv", "venv", "env", ".env",
    "node_modules", ".idea", ".vscode", "build", "dist",
    "*.egg-info", ".pytest_cache", ".mypy_cache",
}

# ============================================================================
# === LOGGING ================================================================
# ============================================================================
def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARN": "⚠️",
        "ERROR": "❌",
    }.get(level, "•")
    print(f"[{ts}] {prefix} {msg}")

# ============================================================================
# === SCANNER D'IMPORTS ======================================================
# ============================================================================
class ImportScanner:
    """Scanne les fichiers Python et extrait les imports"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.imports: Dict[str, List[str]] = defaultdict(list)  # module → [fichiers]
        self.files_scanned = 0
        self.errors: List[str] = []
    
    def _should_ignore(self, path: Path) -> bool:
        """Vérifie si le chemin doit être ignoré"""
        for part in path.parts:
            if part in IGNORE_PATTERNS or part.endswith(".egg-info"):
                return True
            if part.startswith("."):
                return True
        return False
    
    def _extract_imports_from_file(self, filepath: Path) -> Set[str]:
        """Extrait tous les imports d'un fichier Python"""
        imports = set()
        
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Méthode 1: AST (parsing propre)
            try:
                tree = ast.parse(content, filename=str(filepath))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split(".")[0])
            except SyntaxError:
                # Fallback regex si AST échoue
                pass
            
            # Méthode 2: Regex (fallback + imports conditionnels)
            import_patterns = [
                r'^\s*import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'^\s*from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
            ]
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                for pattern in import_patterns:
                    match = re.match(pattern, line)
                    if match:
                        imports.add(match.group(1))
        
        except Exception as e:
            self.errors.append(f"{filepath}: {e}")
        
        return imports
    
    def scan(self) -> Dict[str, List[str]]:
        """Scan récursif du dossier"""
        log(f"🔍 Scan du dossier: {self.root_path}", "INFO")
        
        py_files = list(self.root_path.rglob("*.py"))
        log(f"📄 {len(py_files)} fichiers Python trouvés", "INFO")
        
        for filepath in py_files:
            if self._should_ignore(filepath):
                continue
            
            self.files_scanned += 1
            imports = self._extract_imports_from_file(filepath)
            
            for imp in imports:
                self.imports[imp].append(str(filepath.relative_to(self.root_path)))
        
        log(f"✅ {self.files_scanned} fichiers analysés", "SUCCESS")
        log(f"📦 {len(self.imports)} imports uniques trouvés", "SUCCESS")
        
        return self.imports

# ============================================================================
# === FILTRE STANDARD VS THIRD-PARTY =========================================
# ============================================================================
def filter_third_party(imports: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Filtre les modules standards pour ne garder que les pip packages"""
    third_party = {}
    
    for module, files in imports.items():
        if module.lower() not in {m.lower() for m in STDLIB_MODULES}:
            # Ignorer les imports relatifs ou locaux
            if not module.startswith("_"):
                third_party[module] = files
    
    return third_party

# ============================================================================
# === VÉRIFICATION PACKAGES INSTALLÉS ========================================
# ============================================================================
def check_installed_packages(packages: Set[str]) -> Dict[str, bool]:
    """Vérifie quels packages sont installés dans l'environnement actuel"""
    installed = {}
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            installed_names = {
                pkg["name"].lower().replace("-", "_")
                for pkg in json.loads(result.stdout)
            }
            for pkg in packages:
                installed[pkg] = (
                    pkg.lower().replace("-", "_") in installed_names or
                    pkg.lower() in installed_names
                )
    except Exception as e:
        log(f"⚠️ Impossible de vérifier les packages installés: {e}", "WARN")
    
    return installed

# ============================================================================
# === GÉNÉRATION REQUIREMENTS.TXT ============================================
# ============================================================================
def generate_requirements(third_party: Dict[str, List[str]], 
                          output_path: Optional[Path] = None) -> str:
    """Génère un fichier requirements.txt propre"""
    lines = [
        "# Requirements générés par Pip Finder",
        f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Fichiers analysés: {sum(len(v) for v in third_party.values())}",
        "",
    ]
    
    # Trier et mapper les noms de packages
    packages = set()
    for module in sorted(third_party.keys()):
        package_name = IMPORT_TO_PACKAGE.get(module, module)
        packages.add(package_name.lower())
    
    for pkg in sorted(packages):
        lines.append(pkg)
    
    content = "\n".join(lines)
    
    if output_path:
        output_path.write_text(content, encoding="utf-8")
        log(f"📄 requirements.txt généré: {output_path}", "SUCCESS")
    
    return content

# ============================================================================
# === RAPPORT DÉTAILLÉ =======================================================
# ============================================================================
def generate_report(third_party: Dict[str, List[str]], 
                    installed: Dict[str, bool],
                    output_path: Optional[Path] = None) -> str:
    """Génère un rapport détaillé des dépendances"""
    lines = [
        "=" * 70,
        "🔍 RAPPORT DÉPENDANCES PYTHON — Pip Finder",
        "=" * 70,
        f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Modules tiers trouvés: {len(third_party)}",
        "",
        "-" * 70,
        "📦 PACKAGES TIERS DÉTECTÉS",
        "-" * 70,
    ]
    
    not_installed = []
    
    for module in sorted(third_party.keys()):
        package_name = IMPORT_TO_PACKAGE.get(module, module)
        is_installed = installed.get(module, installed.get(package_name, False))
        status = "✅" if is_installed else "❌"
        files_count = len(third_party[module])
        
        lines.append(f"{status} {package_name:<30} (import: {module}) — {files_count} fichier(s)")
        
        if not is_installed:
            not_installed.append(package_name)
        
        # Afficher 3 fichiers max en exemple
        for filepath in third_party[module][:3]:
            lines.append(f"      └─ {filepath}")
        if len(third_party[module]) > 3:
            lines.append(f"      └─ ... et {len(third_party[module]) - 3} autre(s)")
    
    if not_installed:
        lines.extend([
            "",
            "-" * 70,
            "⚠️ PACKAGES NON INSTALLÉS",
            "-" * 70,
        ])
        for pkg in not_installed:
            lines.append(f"   • {pkg}")
        lines.append(f"\n💡 Commande: pip install {' '.join(not_installed)}")
    
    lines.extend([
        "",
        "=" * 70,
        "📄 REQUIREMENTS.TXT (copier-coller)",
        "=" * 70,
    ])
    
    packages = {IMPORT_TO_PACKAGE.get(m, m).lower() for m in third_party.keys()}
    for pkg in sorted(packages):
        lines.append(pkg)
    
    content = "\n".join(lines)
    
    if output_path:
        output_path.write_text(content, encoding="utf-8")
        log(f"📄 Rapport généré: {output_path}", "SUCCESS")
    
    return content

# ============================================================================
# === POINT D'ENTRÉE =========================================================
# ============================================================================
def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="🔍 Pip Finder — Scanner de dépendances Python"
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Dossier à scanner (défaut: répertoire courant)"
    )
    parser.add_argument(
        "-o", "--output", default="requirements.txt",
        help="Fichier requirements.txt de sortie (défaut: requirements.txt)"
    )
    parser.add_argument(
        "-r", "--report", action="store_true",
        help="Générer un rapport détaillé (défaut: non)"
    )
    parser.add_argument(
        "--no-check", action="store_true",
        help="Ne pas vérifier les packages installés"
    )
    args = parser.parse_args()
    
    print("""
╔════════════════════════════════════════════════════════════╗
║  🔍 KERBEROS PIP FINDER v1.0                              ║
║  Scanner de dépendances Python — Code Source Analysis    ║
║  GPLv3 — Victor Pozen                                    ║
╚════════════════════════════════════════════════════════════╝
""")
    
    root_path = Path(args.path).resolve()
    if not root_path.exists():
        log(f"Dossier inexistant: {root_path}", "ERROR")
        sys.exit(1)
    
    if not root_path.is_dir():
        log(f"Ce n'est pas un dossier: {root_path}", "ERROR")
        sys.exit(1)
    
    # 1. Scan des imports
    scanner = ImportScanner(root_path)
    all_imports = scanner.scan()
    
    if not all_imports:
        log("Aucun import trouvé !", "WARN")
        sys.exit(0)
    
    # 2. Filtrer stdlib
    third_party = filter_third_party(all_imports)
    log(f"📦 {len(third_party)} packages tiers identifiés", "SUCCESS")
    
    # 3. Vérifier installation
    installed = {}
    if not args.no_check:
        log("🔍 Vérification des packages installés...", "INFO")
        installed = check_installed_packages(set(third_party.keys()))
        installed_count = sum(1 for v in installed.values() if v)
        log(f"✅ {installed_count}/{len(installed)} packages installés", "INFO")
    
    # 4. Générer requirements.txt
    req_path = Path(args.output)
    generate_requirements(third_party, req_path)
    
    # 5. Générer rapport si demandé
    if args.report:
        report_path = root_path / "dependency_report.txt"
        generate_report(third_party, installed, report_path)
    
    # 6. Résumé console
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"Fichiers analysés: {scanner.files_scanned}")
    print(f"Imports totaux: {len(all_imports)}")
    print(f"Packages tiers: {len(third_party)}")
    print(f"Requirements: {req_path}")
    if args.report:
        print(f"Rapport: dependency_report.txt")
    print("=" * 60)
    
    if scanner.errors:
        print(f"\n⚠️ {len(scanner.errors)} erreur(s) de lecture (voir logs)")

if __name__ == "__main__":
    main()