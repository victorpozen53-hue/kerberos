#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Detector v4 — Kerberos Pro + Uninstaller
=============================================
Version refactorisée avec :
✅ Architecture propre (même en un seul fichier)
✅ Sécurité renforcée (validation des packages)
✅ Performance optimisée (AST visitor)
✅ Gestion robuste des threads
✅ Tests unitaires intégrés
✅ Logging professionnel
✅ Type hints complets
✅ 🗑️ Désinstallation sécurisée avec protections

Copyright (C) 2026 Victor Pozen — GPLv3
"""

import os
import sys
import ast
import json
import logging
import threading
import subprocess
import importlib.util
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Set, Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import re

# ============================================================
# 📋 CONFIGURATION
# ============================================================

@dataclass
class Config:
    """Configuration centralisée de l'application"""
    
    # Modules stdlib Python
    STDLIB_MODULES: Set[str] = field(default_factory=lambda: {
        'abc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'base64', 'binascii',
        'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cmath', 'cmd', 'code', 'codecs',
        'collections', 'colorsys', 'concurrent', 'configparser', 'contextlib', 'copy',
        'cProfile', 'csv', 'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
        'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno',
        'faulthandler', 'filecmp', 'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools',
        'gc', 'getopt', 'getpass', 'gettext', 'glob', 'gzip', 'hashlib', 'heapq', 'hmac',
        'html', 'http', 'imaplib', 'imp', 'importlib', 'inspect', 'io', 'ipaddress',
        'itertools', 'json', 'keyword', 'linecache', 'locale', 'logging', 'lzma', 'marshal',
        'math', 'mimetypes', 'mmap', 'multiprocessing', 'netrc', 'numbers', 'operator',
        'optparse', 'os', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
        'platform', 'plistlib', 'poplib', 'pprint', 'profile', 'pstats', 'py_compile',
        'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib', 'rlcompleter',
        'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil',
        'signal', 'site', 'smtplib', 'socket', 'socketserver', 'sqlite3', 'ssl', 'stat',
        'statistics', 'string', 'struct', 'subprocess', 'symtable', 'sys', 'sysconfig',
        'tabnanny', 'tarfile', 'tempfile', 'test', 'textwrap', 'threading', 'time',
        'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tracemalloc',
        'tty', 'turtle', 'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uuid',
        'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref',
        'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib', '_thread', '__future__',
        'ntpath', 'posixpath', 'genericpath', 'copyreg', 'opcode',
    })
    
    # Correspondance import → pip package
    IMPORT_TO_PIP: Dict[str, Optional[str]] = field(default_factory=lambda: {
        'PIL': 'Pillow', 'cv2': 'opencv-python', 'sklearn': 'scikit-learn',
        'skimage': 'scikit-image', 'bs4': 'beautifulsoup4', 'yaml': 'PyYAML',
        'attr': 'attrs', 'OpenSSL': 'pyOpenSSL',
        'win32api': 'pywin32', 'win32com': 'pywin32', 'win32con': 'pywin32',
        'win32process': 'pywin32', 'win32service': 'pywin32', 'win32gui': 'pywin32',
        'msvcrt': None, 'pystray': 'pystray', 'cryptography': 'cryptography',
        'numpy': 'numpy', 'psutil': 'psutil', 'pydub': 'pydub', 'rsa': 'rsa',
        'yara': 'yara-python', 'pyftpdlib': 'pyftpdlib',
    })
    
    # Modules Python 2 obsolètes
    PYTHON2_OBSOLETE: Set[str] = field(default_factory=lambda: {
        'ConfigParser', 'HTMLParser', 'Queue', 'StringIO', 'cPickle',
        'dummy_thread', 'dummy_threading', 'htmlentitydefs', 'httplib',
        'thread', 'urllib2', 'urlparse', 'xmlrpclib', '__builtin__',
    })
    
    # 🛡️ Packages protégés (ne JAMAIS désinstaller)
    PROTECTED_PACKAGES: Set[str] = field(default_factory=lambda: {
        'pip', 'setuptools', 'wheel', 'distribute', 'pkg-resources',
        'pkg_resources', 'importlib-metadata', 'zipp', 'typing-extensions',
        'certifi', 'charset-normalizer', 'idna', 'urllib3', 'requests',
        'six', 'packaging', 'pyparsing', 'colorama', 'tomli', 'tomllib',
    })
    
    # Couleurs thème Kerberos
    BG_COLOR: str = '#1e1e1e'
    BG_LIGHT: str = '#2d2d2d'
    BG_DARK: str = '#252525'
    FG_COLOR: str = '#ffffff'
    FG_GREEN: str = '#00ff00'
    FG_CYAN: str = '#00ffff'
    FG_ORANGE: str = '#ff9800'
    FG_RED: str = '#ff4444'
    FG_PURPLE: str = '#b388ff'
    BTN_COLOR: str = '#3a3a3a'
    
    # Polices
    FONT_MAIN: Tuple[str, int] = ('Consolas', 11)
    FONT_SMALL: Tuple[str, int] = ('Consolas', 10)
    FONT_TITLE: Tuple[str, int, str] = ('Consolas', 12, 'bold')
    
    # Timeouts
    PIP_LIST_TIMEOUT: int = 15
    PYPI_SEARCH_TIMEOUT: int = 30
    PIP_INSTALL_TIMEOUT: int = 180
    PIP_UNINSTALL_TIMEOUT: int = 60
    
    # Dossiers à ignorer
    IGNORE_DIRS: Set[str] = field(default_factory=lambda: {
        'venv', 'env', '__pycache__', '.git', '.idea', '.vscode', 'node_modules'
    })


# ============================================================
# 🔧 LOGGING
# ============================================================

def setup_logger(name: str = "api_detector") -> logging.Logger:
    """Configure et retourne un logger professionnel"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


logger = setup_logger()


# ============================================================
# 🛡️ SÉCURITÉ
# ============================================================

class PackageValidator:
    """Validateur de sécurité pour les noms de packages"""
    
    # Regex stricte pour valider les noms de packages PyPI
    VALID_PACKAGE_NAME = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$')
    
    @classmethod
    def is_valid_package_name(cls, name: str) -> bool:
        """Vérifie si le nom du package est valide et sûr"""
        if not name or len(name) > 200:
            return False
        
        if not cls.VALID_PACKAGE_NAME.match(name):
            return False
        
        # Caractères dangereux
        dangerous_chars = {';', '&', '|', '`', '$', '(', ')', '{', '}', '<', '>', '\'', '"'}
        if any(char in name for char in dangerous_chars):
            return False
        
        return True
    
    @classmethod
    def sanitize_package_name(cls, name: str) -> Optional[str]:
        """Sanitize et valide un nom de package"""
        if not cls.is_valid_package_name(name):
            logger.warning(f"Nom de package invalide rejeté: {name}")
            return None
        return name


# ============================================================
# 🧠 ANALYZER v4 — Performance optimisée
# ============================================================

class ImportVisitor(ast.NodeVisitor):
    """Visitor AST optimisé pour extraire les imports"""
    
    def __init__(self):
        self.imports: Set[str] = set()
    
    def visit_Import(self, node: ast.Import) -> None:
        """Traite les imports simples: import x, y"""
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Traite les imports from: from x import y"""
        if node.module and node.level == 0:  # level > 0 = import relatif
            self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)


class ImportAnalyzer:
    """Analyseur d'imports Python avec détection des modules locaux"""
    
    def __init__(self, config: Config):
        self.config = config
        self.local_modules: Set[str] = set()
        self._lock = threading.Lock()
    
    def _read_file_with_fallback(self, file_path: Path) -> str:
        """Lit un fichier avec fallback d'encodage"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for enc in encodings:
            try:
                return file_path.read_text(encoding=enc)
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Dernier recours
        return file_path.read_bytes().decode('utf-8', errors='ignore')
    
    def detect_local_modules(self, dir_path: Path) -> Set[str]:
        """Détecte automatiquement les modules locaux au projet"""
        local = set()
        
        # 1. Fichiers .py à la racine
        for py_file in dir_path.glob("*.py"):
            local.add(py_file.stem)
        
        # 2. Dossiers avec __init__.py (packages Python)
        for init_file in dir_path.rglob("__init__.py"):
            if any(part.startswith('.') or part in self.config.IGNORE_DIRS
                   for part in init_file.parts):
                continue
            local.add(init_file.parent.name)
        
        # 3. Dossiers contenant des .py
        for sub_dir in dir_path.iterdir():
            if not sub_dir.is_dir():
                continue
            if sub_dir.name.startswith('.') or sub_dir.name in self.config.IGNORE_DIRS:
                continue
            if any(sub_dir.glob("*.py")):
                local.add(sub_dir.name)
        
        return local
    
    def analyze_directory(self, dir_path: Path) -> Dict[str, Any]:
        """Analyse tous les fichiers Python d'un dossier"""
        with self._lock:
            self.local_modules = self.detect_local_modules(dir_path)
        
        results = {
            'directory': str(dir_path),
            'files_scanned': 0,
            'files_in_error': [],
            'all_imports': set(),
            'files_detail': [],
            'local_modules_detected': sorted(self.local_modules)
        }
        
        for py_file in dir_path.rglob('*.py'):
            if any(part.startswith('.') or part in self.config.IGNORE_DIRS
                   for part in py_file.parts):
                continue
            
            results['files_scanned'] += 1
            
            try:
                code = self._read_file_with_fallback(py_file)
                tree = ast.parse(code, filename=str(py_file))
                
                # ✅ Utilise le visitor optimisé
                visitor = ImportVisitor()
                visitor.visit(tree)
                file_imports = visitor.imports
                
                results['all_imports'].update(file_imports)
                results['files_detail'].append({
                    'file': str(py_file.relative_to(dir_path)),
                    'imports': sorted(file_imports)
                })
            
            except Exception as e:
                logger.error(f"Erreur analyse {py_file}: {e}")
                results['files_in_error'].append({
                    'file': str(py_file.relative_to(dir_path)),
                    'error': str(e)
                })
        
        results['all_imports'] = sorted(results['all_imports'])
        return results
    
    def classify_imports(self, imports: List[str]) -> Dict[str, List[str]]:
        """Classifie les imports en 4 catégories"""
        stdlib, third_party, obsolete, local = [], [], [], []
        
        for imp in imports:
            if imp in self.config.PYTHON2_OBSOLETE:
                obsolete.append(imp)
            elif imp in self.local_modules:
                local.append(imp)
            elif imp in self.config.STDLIB_MODULES or imp.startswith('_'):
                stdlib.append(imp)
            else:
                third_party.append(imp)
        
        return {
            'stdlib': sorted(stdlib),
            'third_party': sorted(third_party),
            'obsolete': sorted(obsolete),
            'local': sorted(local)
        }


# ============================================================
# 🔍 CHECKER v4 — Sécurisé
# ============================================================

class APIChecker:
    """Vérificateur d'installation des packages avec sécurité renforcée"""
    
    def __init__(self, config: Config):
        self.config = config
        self.installed_packages = self._get_installed_packages()
    
    def _get_installed_packages(self) -> Dict[str, str]:
        """Récupère la liste des packages installés"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=self.config.PIP_LIST_TIMEOUT
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                normalized = {}
                
                for pkg in packages:
                    name = pkg['name'].lower()
                    normalized[name] = pkg['version']
                    
                    # Alias spéciaux
                    if name == 'pillow':
                        normalized['pil'] = pkg['version']
                    if name == 'pywin32':
                        for k in ['win32api', 'win32com', 'win32con', 'win32process']:
                            normalized[k] = pkg['version']
                    if name == 'yara-python':
                        normalized['yara'] = pkg['version']
                
                return normalized
        
        except Exception as e:
            logger.error(f"pip list indisponible: {e}")
        
        return {}
    
    def is_installed_locally(self, module_name: str) -> bool:
        """Vérifie si un module est installé localement"""
        try:
            return importlib.util.find_spec(module_name) is not None
        except Exception:
            return False
    
    def get_pip_package_name(self, import_name: str) -> Optional[str]:
        """Retourne le nom du package pip correspondant"""
        return self.config.IMPORT_TO_PIP.get(import_name, import_name)
    
    def check_all_local(self, third_party_imports: List[str]) -> Dict[str, List[Dict]]:
        """Vérifie l'installation de tous les modules tiers"""
        results = {'installed': [], 'missing': [], 'skipped': []}
        
        for module in third_party_imports:
            pip_name = self.get_pip_package_name(module)
            
            if pip_name is None:
                results['skipped'].append({'module': module, 'reason': 'Module natif'})
                continue
            
            if self.is_installed_locally(module):
                version = self.installed_packages.get(module.lower(), '✓')
                results['installed'].append({
                    'module': module,
                    'pip_name': pip_name,
                    'version': version
                })
            else:
                results['missing'].append({
                    'module': module,
                    'pip_name': pip_name
                })
        
        return results
    
    def search_pypi_single(self, package_name: str) -> Dict[str, Any]:
        """Recherche un package sur PyPI (avec validation)"""
        # ✅ Validation de sécurité
        validated_name = PackageValidator.sanitize_package_name(package_name)
        if not validated_name:
            return {'found': False, 'error': 'Nom de package invalide'}
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--dry-run',
                 '--report', '-', '--quiet', validated_name],
                capture_output=True,
                text=True,
                timeout=self.config.PYPI_SEARCH_TIMEOUT
            )
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    report = json.loads(result.stdout)
                    if 'install' in report and report['install']:
                        meta = report['install'][0].get('metadata', {})
                        return {
                            'found': True,
                            'name': meta.get('name', package_name),
                            'version': meta.get('version', 'latest')
                        }
                except json.JSONDecodeError:
                    pass
            
            return {'found': False}
        
        except Exception as e:
            logger.error(f"Erreur recherche PyPI {package_name}: {e}")
            return {'found': False, 'error': str(e)}
    
    def search_pypi_batch(
        self,
        missing_modules: List[Dict],
        progress_callback: Optional[callable] = None,
        stop_event: Optional[threading.Event] = None
    ) -> Dict[str, List[Dict]]:
        """Recherche batch sur PyPI avec annulation"""
        results = {'pypi_found': [], 'not_found': []}
        total = len(missing_modules)
        
        for i, mod_info in enumerate(missing_modules):
            # ✅ Vérification d'annulation
            if stop_event and stop_event.is_set():
                logger.info("Recherche PyPI annulée")
                break
            
            if progress_callback:
                progress_callback(i, total, f"🌐 PyPI : {mod_info['pip_name']}")
            
            pypi_result = self.search_pypi_single(mod_info['pip_name'])
            
            if pypi_result.get('found'):
                results['pypi_found'].append({
                    'module': mod_info['module'],
                    'pypi_name': pypi_result.get('name', mod_info['pip_name']),
                    'version': pypi_result.get('version', 'latest')
                })
            else:
                results['not_found'].append(mod_info)
        
        if progress_callback:
            progress_callback(total, total, "✅ PyPI terminé")
        
        return results
    
    def install_package(self, package_name: str) -> bool:
        """Installe un package avec validation de sécurité"""
        # ✅ Validation de sécurité
        validated_name = PackageValidator.sanitize_package_name(package_name)
        if not validated_name:
            logger.error(f"Installation refusée: nom invalide {package_name}")
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--quiet', validated_name],
                capture_output=True,
                text=True,
                timeout=self.config.PIP_INSTALL_TIMEOUT
            )
            return result.returncode == 0
        
        except Exception as e:
            logger.error(f"Erreur installation {package_name}: {e}")
            return False


# ============================================================
# 🗑️ UNINSTALLER v4 — Sécurisé
# ============================================================

class PackageUninstaller:
    """Désinstallateur de packages avec multiples sécurités"""
    
    def __init__(self, config: Config):
        self.config = config
        self.protected = config.PROTECTED_PACKAGES
    
    def get_reverse_dependencies(self, package_name: str) -> List[str]:
        """Trouve quels packages installés dépendent de celui-ci"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            # Cherche la ligne "Required-by: pkg1, pkg2"
            for line in result.stdout.splitlines():
                if line.startswith('Required-by:'):
                    deps = line.split(':', 1)[1].strip()
                    if deps:
                        return [d.strip() for d in deps.split(',')]
            return []
        
        except Exception as e:
            logger.warning(f"Impossible de vérifier les dépendances de {package_name}: {e}")
            return []
    
    def is_safe_to_uninstall(self, package_name: str) -> Dict[str, Any]:
        """Vérifie si un package peut être désinstallé sans danger"""
        name_lower = package_name.lower()
        
        # 1. Package protégé ?
        if name_lower in self.protected:
            return {
                'safe': False,
                'reason': f"🛡️ Package système protégé : {package_name}",
                'risk': 'CRITICAL'
            }
        
        # 2. Dépendances inverses ?
        reverse_deps = self.get_reverse_dependencies(package_name)
        if reverse_deps:
            return {
                'safe': False,
                'reason': f"⚠️ {len(reverse_deps)} package(s) en dépendent : {', '.join(reverse_deps)}",
                'risk': 'HIGH',
                'dependents': reverse_deps
            }
        
        return {'safe': True, 'reason': '✅ Désinstallation sûre', 'risk': 'LOW'}
    
    def dry_run_uninstall(self, package_name: str) -> Dict[str, Any]:
        """Simule la désinstallation sans rien faire"""
        validated = PackageValidator.sanitize_package_name(package_name)
        if not validated:
            return {'success': False, 'error': 'Nom invalide'}
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', '--dry-run', validated],
                capture_output=True, text=True, timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def uninstall_package(self, package_name: str) -> bool:
        """Désinstalle un package après validation"""
        validated = PackageValidator.sanitize_package_name(package_name)
        if not validated:
            logger.error(f"Désinstallation refusée: nom invalide {package_name}")
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', '--quiet', validated],
                capture_output=True, text=True, timeout=self.config.PIP_UNINSTALL_TIMEOUT
            )
            return result.returncode == 0
        
        except Exception as e:
            logger.error(f"Erreur désinstallation {package_name}: {e}")
            return False
    
    def backup_installed_list(self, output_path: Path) -> Optional[Path]:
        """Crée un backup de la liste actuelle avant désinstallation"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'freeze'],
                capture_output=True, text=True, timeout=15
            )
            
            if result.returncode == 0:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = output_path / f"pip_backup_{timestamp}.txt"
                backup_path.write_text(result.stdout, encoding='utf-8')
                logger.info(f"💾 Backup créé : {backup_path}")
                return backup_path
        
        except Exception as e:
            logger.error(f"Erreur backup: {e}")
        
        return None


# ============================================================
# 📄 REPORT GENERATOR
# ============================================================

class ReportGenerator:
    """Générateur de rapports dans différents formats"""
    
    @staticmethod
    def generate_json(analysis_results: Dict, output_path: Path) -> None:
        """Export en JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_txt(analysis_results: Dict, output_path: Path) -> None:
        """Export en TXT"""
        lines = [
            "=" * 70,
            "API DETECTOR v4 — RAPPORT D'ANALYSE",
            "=" * 70,
            f"Dossier : {analysis_results['target']}",
            f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Fichiers scannés : {analysis_results['files_scanned']}",
            "",
            f"📚 Stdlib : {len(analysis_results['stdlib'])}",
            f"🔌 Tiers : {len(analysis_results['third_party'])}",
            f"🏠 Modules locaux : {len(analysis_results['local'])}",
            f"🗑️ Python 2 obsolète : {len(analysis_results['obsolete'])}",
            ""
        ]
        
        if analysis_results['local']:
            lines += ["-" * 70, "🏠 MODULES LOCAUX DÉTECTÉS", "-" * 70]
            for m in analysis_results['local']:
                lines.append(f"  🏠 {m}")
            lines.append("")
        
        lines += ["-" * 70, "✅ INSTALLÉS", "-" * 70]
        for p in analysis_results['installed']:
            lines.append(f"  ✓ {p['module']} (pip: {p['pip_name']}) v{p['version']}")
        
        lines += ["", "-" * 70, "❌ MANQUANTS", "-" * 70]
        for p in analysis_results['missing']:
            lines.append(f"  ✗ {p['module']} → pip install {p['pip_name']}")
        
        lines += ["", "=" * 70, "Fin du rapport", "=" * 70]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    @staticmethod
    def generate_html(analysis_results: Dict, output_path: Path) -> None:
        """Export en HTML (version simplifiée pour l'exemple)"""
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>API Detector v4 — Rapport</title>
    <style>
        body {{ font-family: 'Consolas', monospace; background: #1e1e1e; color: #fff; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #252525; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #00ffff; border-bottom: 2px solid #00ffff; padding-bottom: 10px; }}
        h2 {{ color: #00ff00; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: #2d2d2d; }}
        th {{ background: #3a3a3a; color: #00ffff; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #3a3a3a; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 API Detector v4 — Rapport</h1>
        <p><strong>Dossier :</strong> {analysis_results['target']}</p>
        <p><strong>Date :</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <h2>📊 Statistiques</h2>
        <ul>
            <li>Fichiers scannés : {analysis_results['files_scanned']}</li>
            <li>Stdlib : {len(analysis_results['stdlib'])}</li>
            <li>Tiers : {len(analysis_results['third_party'])}</li>
            <li>Locaux : {len(analysis_results['local'])}</li>
            <li>Installés : {len(analysis_results['installed'])}</li>
            <li>Manquants : {len(analysis_results['missing'])}</li>
        </ul>
    </div>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


# ============================================================
# 🖥️ GUI TKINTER v4 — Thread-safe + Uninstaller
# ============================================================

class APIDetectorApp:
    """Interface graphique avec gestion robuste des threads et désinstallation"""
    
    def __init__(self):
        logger.info("Démarrage API Detector v4...")
        
        self.config = Config()
        self.root = tk.Tk()
        self.root.title("🔍 API Detector v4 — Kerberos Pro + Uninstaller")
        self.root.geometry("1200x800")
        self.root.configure(bg=self.config.BG_COLOR)
        
        self.target_path = tk.StringVar()
        self.analyzer = ImportAnalyzer(self.config)
        self.checker = APIChecker(self.config)
        self.uninstaller = PackageUninstaller(self.config)
        self.report_gen = ReportGenerator()
        
        self.analysis_results: Optional[Dict] = None
        self.stop_event = threading.Event()
        self.results_lock = threading.Lock()
        
        self._setup_style()
        self._build_ui()
        
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        logger.info("API Detector v4 prêt")
        
        self.root.mainloop()
    
    def _setup_style(self) -> None:
        """Configure le style de l'interface"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        
        style.configure('TFrame', background=self.config.BG_COLOR)
        style.configure('TLabel', background=self.config.BG_COLOR,
                       foreground=self.config.FG_COLOR, font=self.config.FONT_MAIN)
        style.configure('TButton', background=self.config.BTN_COLOR,
                       foreground=self.config.FG_COLOR, font=self.config.FONT_MAIN)
        style.map('TButton', background=[('active', '#4a4a4a')])
        style.configure('TLabelframe', background=self.config.BG_COLOR,
                       foreground=self.config.FG_CYAN, font=self.config.FONT_TITLE)
        style.configure('TLabelframe.Label', background=self.config.BG_COLOR,
                       foreground=self.config.FG_CYAN)
        style.configure('TProgressbar', troughcolor=self.config.BG_DARK,
                       background=self.config.FG_GREEN)
        style.configure('TNotebook', background=self.config.BG_COLOR)
        style.configure('TEntry', fieldbackground=self.config.BG_LIGHT,
                       foreground=self.config.FG_COLOR)
    
    def _build_ui(self) -> None:
        """Construit l'interface utilisateur"""
        # Zone supérieure
        top_frame = ttk.LabelFrame(self.root, text="📂 Dossier Python à analyser", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(top_frame, text="Dossier :").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(top_frame, textvariable=self.target_path,
                 font=self.config.FONT_MAIN).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(top_frame, text="📂 Choisir",
                  command=self._select_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="🔍 Scanner",
                  command=self._start_scan).pack(side=tk.LEFT, padx=(10, 0))
        
        # Onglets
        results_frame = ttk.Frame(self.root)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.tab_stdlib = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stdlib, text="📚 Stdlib")
        self.text_stdlib = self._build_result_tab(self.tab_stdlib)
        
        self.tab_local = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_local, text="🏠 Modules locaux")
        self.text_local = self._build_result_tab(self.tab_local)
        
        self.tab_installed = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_installed, text="✅ Installés")
        self.text_installed = self._build_result_tab(self.tab_installed)
        
        self.tab_missing = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_missing, text="❌ Manquants")
        self.text_missing = self._build_result_tab(self.tab_missing)
        
        # Zone inférieure
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        action_frame = ttk.Frame(bottom_frame)
        action_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_search_pypi = ttk.Button(action_frame, text="🌐 Rechercher PyPI",
                                          command=self._search_pypi, state='disabled')
        self.btn_search_pypi.pack(side=tk.LEFT, padx=5)
        
        self.btn_install = ttk.Button(action_frame, text="📦 Installer",
                                     command=self._install_missing, state='disabled')
        self.btn_install.pack(side=tk.LEFT, padx=5)
        
        # 🗑️ NOUVEAU : Bouton désinstallation
        self.btn_uninstall = ttk.Button(action_frame, text="🗑️ Désinstaller",
                                       command=self._uninstall_installed, state='disabled')
        self.btn_uninstall.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="💾 JSON",
                  command=lambda: self._export_report('json')).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📄 TXT",
                  command=lambda: self._export_report('txt')).pack(side=tk.LEFT, padx=5)
        
        self.progress_label = ttk.Label(action_frame, text="Prêt",
                                       foreground=self.config.FG_GREEN)
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        self.progress = ttk.Progressbar(action_frame, mode='determinate', length=300)
        self.progress.pack(side=tk.RIGHT, padx=5)
        
        # Console
        console_frame = ttk.LabelFrame(bottom_frame, text="📟 Console", padding=5)
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.console = scrolledtext.ScrolledText(
            console_frame, height=8, font=self.config.FONT_SMALL,
            bg=self.config.BG_DARK, fg=self.config.FG_GREEN, state='disabled'
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        
        self._log("🛡️ API Detector v4 — Version professionnelle")
        self._log("✅ Sécurité renforcée + Performance optimisée + Désinstallation sécurisée")
    
    def _build_result_tab(self, parent: ttk.Frame) -> tk.Text:
        """Construit un onglet de résultats"""
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(
            list_frame, font=self.config.FONT_MAIN,
            bg=self.config.BG_LIGHT, fg=self.config.FG_COLOR,
            yscrollcommand=scrollbar.set, state='disabled', wrap=tk.WORD
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        return text_widget
    
    def _select_folder(self) -> None:
        """Sélectionne un dossier"""
        path = filedialog.askdirectory(title="Sélectionner un dossier Python")
        if path:
            self.target_path.set(path)
            self._log(f"📂 Dossier : {path}")
    
    def _start_scan(self) -> None:
        """Lance le scan dans un thread"""
        target = self.target_path.get().strip()
        
        if not target:
            messagebox.showwarning("⚠️", "Sélectionne un dossier.")
            return
        
        target_path = Path(target)
        if not target_path.is_dir():
            messagebox.showerror("❌", f"Dossier introuvable : {target}")
            return
        
        self.btn_search_pypi.config(state='disabled')
        self.btn_install.config(state='disabled')
        self.btn_uninstall.config(state='disabled')
        self.stop_event.clear()
        
        threading.Thread(
            target=self._scan_worker,
            args=(target_path,),
            daemon=True
        ).start()
    
    def _scan_worker(self, target_path: Path) -> None:
        """Worker de scan (thread-safe)"""
        try:
            self._update_progress("🏠 Détection modules locaux...", 10)
            self._log(f"[🔍] Scan : {target_path}")
            
            local_modules = self.analyzer.detect_local_modules(target_path)
            self._log(f"🏠 {len(local_modules)} modules locaux détectés")
            
            self._update_progress("📖 Scan fichiers .py...", 20)
            result = self.analyzer.analyze_directory(target_path)
            self._log(f"✅ {result['files_scanned']} fichiers analysés")
            
            self._update_progress("🏷️ Classification...", 40)
            classified = self.analyzer.classify_imports(result['all_imports'])
            
            self._log(f"📚 Stdlib : {len(classified['stdlib'])}")
            self._log(f"🏠 Locaux : {len(classified['local'])}")
            self._log(f"🔌 Tiers : {len(classified['third_party'])}")
            
            # Affichage
            self._run_in_main_thread(
                self._fill_text, self.text_stdlib,
                [f"📚 {m}" for m in classified['stdlib']], self.config.FG_CYAN
            )
            
            local_lines = [f"🏠 {m}" for m in classified['local']] or ["ℹ️ Aucun"]
            self._run_in_main_thread(
                self._fill_text, self.text_local,
                local_lines, self.config.FG_PURPLE
            )
            
            self._update_progress("🔎 Vérification...", 60)
            local_check = self.checker.check_all_local(classified['third_party'])
            
            inst_lines = [
                f"✅ {p['module']} → {p['pip_name']} (v{p['version']})"
                for p in local_check['installed']
            ]
            self._run_in_main_thread(
                self._fill_text, self.text_installed,
                inst_lines, self.config.FG_GREEN
            )
            
            if local_check['missing']:
                miss_lines = [
                    f"❌ {p['module']} → pip install {p['pip_name']}"
                    for p in local_check['missing']
                ]
                self._run_in_main_thread(
                    self._fill_text, self.text_missing,
                    miss_lines, self.config.FG_ORANGE
                )
                self._run_in_main_thread(self.btn_search_pypi.config, {'state': 'normal'})
                self._run_in_main_thread(self.btn_install.config, {'state': 'normal'})
            else:
                self._run_in_main_thread(
                    self._fill_text, self.text_missing,
                    ["🎉 Tous installés !"], self.config.FG_GREEN
                )
            
            # 🗑️ Active le bouton désinstallation si des packages sont installés
            if local_check['installed']:
                self._run_in_main_thread(self.btn_uninstall.config, {'state': 'normal'})
            
            # Stockage thread-safe des résultats
            with self.results_lock:
                self.analysis_results = {
                    'target': str(target_path),
                    'files_scanned': result['files_scanned'],
                    'stdlib': classified['stdlib'],
                    'third_party': classified['third_party'],
                    'local': classified['local'],
                    'obsolete': classified['obsolete'],
                    'installed': local_check['installed'],
                    'missing': local_check['missing'],
                }
            
            self._update_progress("✅ Terminé", 100)
            self._log("✅ Scan terminé")
        
        except Exception as e:
            logger.error(f"Erreur scan: {e}", exc_info=True)
            self._log(f"❌ ERREUR : {e}")
            self._update_progress("❌ Erreur", 0)
    
    def _search_pypi(self) -> None:
        """Lance la recherche PyPI"""
        with self.results_lock:
            if not self.analysis_results or not self.analysis_results['missing']:
                messagebox.showinfo("ℹ️", "Rien à rechercher.")
                return
            missing = self.analysis_results['missing'].copy()
        
        if messagebox.askyesno("🌐 PyPI", f"Rechercher {len(missing)} module(s) ?"):
            self.stop_event.clear()
            threading.Thread(
                target=self._pypi_worker,
                args=(missing,),
                daemon=True
            ).start()
    
    def _pypi_worker(self, missing: List[Dict]) -> None:
        """Worker recherche PyPI"""
        def callback(i, t, msg):
            self._update_progress(msg, int((i / max(t, 1)) * 100))
        
        pypi_results = self.checker.search_pypi_batch(
            missing, callback, self.stop_event
        )
        
        found = len(pypi_results['pypi_found'])
        not_found = len(pypi_results['not_found'])
        self._log(f"✅ Trouvés : {found} | ❓ Introuvables : {not_found}")
        
        with self.results_lock:
            if self.analysis_results:
                self.analysis_results['pypi_found'] = pypi_results['pypi_found']
        
        self._update_progress("✅ PyPI terminé", 100)
    
    def _install_missing(self) -> None:
        """Lance l'installation des manquants"""
        with self.results_lock:
            if not self.analysis_results or not self.analysis_results['missing']:
                messagebox.showinfo("ℹ️", "Rien à installer.")
                return
            missing = self.analysis_results['missing'].copy()
        
        recap = "\n".join(f"• {m['module']} → {m['pip_name']}" for m in missing)
        
        if messagebox.askyesno("📦 Installation",
                              f"Installer {len(missing)} package(s) ?\n{recap}\n\n⚠️ Modifier l'environnement ?"):
            self.stop_event.clear()
            threading.Thread(
                target=self._install_worker,
                args=(missing,),
                daemon=True
            ).start()
    
    def _install_worker(self, packages: List[Dict]) -> None:
        """Worker installation"""
        self._update_progress("📦 Installation...", 0)
        success, failed = [], []
        
        for i, pkg in enumerate(packages):
            if self.stop_event.is_set():
                self._log("⚠️ Installation annulée")
                break
            
            pip_name = pkg['pip_name']
            self._update_progress(f"📦 {pip_name}", int((i / max(len(packages), 1)) * 100))
            
            if self.checker.install_package(pip_name):
                success.append(pip_name)
                self._log(f"✅ Installé : {pip_name}")
            else:
                failed.append(pip_name)
                self._log(f"❌ Échec : {pip_name}")
        
        self._update_progress("✅ Terminé", 100)
        messagebox.showinfo("📦 Résultat", f"Succès : {len(success)}\nÉchecs : {len(failed)}")
    
    # 🗑️ NOUVELLE MÉTHODE : Désinstallation sécurisée
    def _uninstall_installed(self) -> None:
        """Désinstalle les packages installés avec multiples vérifications"""
        with self.results_lock:
            if not self.analysis_results or not self.analysis_results['installed']:
                messagebox.showinfo("ℹ️", "Rien à désinstaller.")
                return
            installed = self.analysis_results['installed'].copy()
        
        # === ÉTAPE 1 : Analyse de sécurité ===
        safe_to_remove = []
        dangerous = []
        protected = []
        
        for pkg in installed:
            pip_name = pkg['pip_name']
            safety = self.uninstaller.is_safe_to_uninstall(pip_name)
            
            if safety['risk'] == 'CRITICAL':
                protected.append((pkg, safety['reason']))
            elif safety['risk'] == 'HIGH':
                dangerous.append((pkg, safety['reason']))
            else:
                safe_to_remove.append(pkg)
        
        # === ÉTAPE 2 : Affichage du diagnostic ===
        report = ["🔍 DIAGNOSTIC DE SÉCURITÉ\n"]
        
        if protected:
            report.append("🛡️ BLOQUÉS (packages système) :")
            for pkg, reason in protected:
                report.append(f"   ❌ {pkg['pip_name']} — {reason}")
            report.append("")
        
        if dangerous:
            report.append("⚠️ DANGEREUX (dépendances) :")
            for pkg, reason in dangerous:
                report.append(f"   ⚠️ {pkg['pip_name']} — {reason}")
            report.append("")
        
        if safe_to_remove:
            report.append("✅ SÛRS à désinstaller :")
            for pkg in safe_to_remove:
                report.append(f"   ✓ {pkg['pip_name']} (v{pkg['version']})")
        else:
            report.append("\n❌ Aucun package ne peut être désinstallé sans risque.")
        
        # === ÉTAPE 3 : Demande de confirmation ===
        if not safe_to_remove:
            messagebox.showwarning("⚠️ Sécurité", "\n".join(report))
            return
        
        confirm = messagebox.askyesno(
            "🗑️ Désinstallation",
            "\n".join(report) + f"\n\n🗑️ Désinstaller {len(safe_to_remove)} package(s) SÛR(S) ?",
            icon='warning'
        )
        
        if not confirm:
            return
        
        # === ÉTAPE 4 : Backup AVANT désinstallation ===
        backup_dir = Path.home() / ".api_detector_backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = self.uninstaller.backup_installed_list(backup_dir)
        
        if backup_path:
            self._log(f"💾 Backup de sécurité : {backup_path}")
        
        # === ÉTAPE 5 : Désinstallation ===
        self.stop_event.clear()
        threading.Thread(
            target=self._uninstall_worker,
            args=(safe_to_remove,),
            daemon=True
        ).start()
    
    def _uninstall_worker(self, packages: List[Dict]) -> None:
        """Worker de désinstallation"""
        self._update_progress("🗑️ Désinstallation...", 0)
        success, failed = [], []
        
        for i, pkg in enumerate(packages):
            if self.stop_event.is_set():
                self._log("⚠️ Désinstallation annulée")
                break
            
            pip_name = pkg['pip_name']
            self._update_progress(
                f"🗑️ {pip_name}", 
                int((i / max(len(packages), 1)) * 100)
            )
            
            # Double vérification juste avant
            safety = self.uninstaller.is_safe_to_uninstall(pip_name)
            if not safety['safe']:
                self._log(f"🛡️ BLOQUÉ (sécurité) : {pip_name} — {safety['reason']}")
                failed.append(pip_name)
                continue
            
            if self.uninstaller.uninstall_package(pip_name):
                success.append(pip_name)
                self._log(f"🗑️ Désinstallé : {pip_name}")
            else:
                failed.append(pip_name)
                self._log(f"❌ Échec désinstallation : {pip_name}")
        
        self._update_progress("✅ Terminé", 100)
        
        result_msg = f"✅ Désinstallés : {len(success)}\n❌ Échecs : {len(failed)}"
        if failed:
            result_msg += f"\n\nPackages en échec : {', '.join(failed)}"
        
        messagebox.showinfo("🗑️ Résultat", result_msg)
    
    def _fill_text(self, text_widget: tk.Text, items: List[str], color: str) -> None:
        """Remplit un widget texte (thread-safe)"""
        text_widget.configure(state='normal')
        text_widget.delete('1.0', tk.END)
        text_widget.tag_configure('item', foreground=color)
        
        for item in items:
            text_widget.insert(tk.END, f"{item}\n", 'item')
        
        text_widget.configure(state='disabled')
    
    def _export_report(self, fmt: str) -> None:
        """Exporte le rapport"""
        with self.results_lock:
            if not self.analysis_results:
                messagebox.showwarning("⚠️", "Aucune analyse.")
                return
            results = self.analysis_results.copy()
        
        ext = {'json': '.json', 'txt': '.txt', 'html': '.html'}.get(fmt, '.json')
        path = filedialog.asksaveasfilename(
            title=f"Export ({fmt.upper()})",
            defaultextension=ext,
            filetypes=[(fmt.upper(), f"*{ext}")]
        )
        
        if not path:
            return
        
        try:
            p = Path(path)
            if fmt == 'json':
                self.report_gen.generate_json(results, p)
            elif fmt == 'txt':
                self.report_gen.generate_txt(results, p)
            elif fmt == 'html':
                self.report_gen.generate_html(results, p)
            
            self._log(f"💾 Exporté : {path}")
            messagebox.showinfo("✅", f"Rapport exporté :\n{path}")
        
        except Exception as e:
            logger.error(f"Erreur export: {e}")
            self._log(f"❌ Erreur export : {e}")
    
    def _update_progress(self, text: str, value: int) -> None:
        """Met à jour la progression (thread-safe)"""
        self._run_in_main_thread(
            lambda: (
                self.progress_label.config(text=text),
                self.progress.config(value=value)
            )
        )
    
    def _log(self, msg: str) -> None:
        """Log dans la console (thread-safe)"""
        def _do_log():
            self.console.configure(state='normal')
            self.console.insert(tk.END, f"{msg}\n")
            self.console.see(tk.END)
            self.console.configure(state='disabled')
        
        self._run_in_main_thread(_do_log)
    
    def _run_in_main_thread(self, func: callable, *args, **kwargs) -> None:
        """Exécute une fonction dans le thread principal"""
        self.root.after(0, lambda: func(*args, **kwargs))
    
    def _on_close(self) -> None:
        """Gestion de la fermeture"""
        if messagebox.askyesno("👋", "Fermer ?"):
            self.stop_event.set()
            self.root.destroy()


# ============================================================
# 🧪 TESTS UNITAIRES
# ============================================================

def run_tests() -> None:
    """Tests unitaires intégrés"""
    logger.info("=" * 70)
    logger.info("🧪 EXÉCUTION DES TESTS UNITAIRES")
    logger.info("=" * 70)
    
    # Test 1: Validation des packages
    logger.info("\n[Test 1] PackageValidator")
    assert PackageValidator.is_valid_package_name("numpy") == True
    assert PackageValidator.is_valid_package_name("scikit-learn") == True
    assert PackageValidator.is_valid_package_name("Pillow") == True
    assert PackageValidator.is_valid_package_name("") == False
    assert PackageValidator.is_valid_package_name("package;rm -rf /") == False
    logger.info("✅ PackageValidator OK")
    
    # Test 2: Configuration
    logger.info("\n[Test 2] Config")
    config = Config()
    assert 'os' in config.STDLIB_MODULES
    assert 'numpy' in config.IMPORT_TO_PIP
    assert 'Queue' in config.PYTHON2_OBSOLETE
    assert 'pip' in config.PROTECTED_PACKAGES
    logger.info("✅ Config OK")
    
    # Test 3: ImportVisitor
    logger.info("\n[Test 3] ImportVisitor")
    code = """
import os
import sys, json
from pathlib import Path
from typing import Dict, List
"""
    tree = ast.parse(code)
    visitor = ImportVisitor()
    visitor.visit(tree)
    assert 'os' in visitor.imports
    assert 'sys' in visitor.imports
    assert 'json' in visitor.imports
    assert 'pathlib' in visitor.imports
    assert 'typing' in visitor.imports
    logger.info("✅ ImportVisitor OK")
    
    # Test 4: Classification
    logger.info("\n[Test 4] Classification")
    config = Config()
    analyzer = ImportAnalyzer(config)
    analyzer.local_modules = {'mymodule'}
    
    classified = analyzer.classify_imports(['os', 'numpy', 'mymodule', 'Queue'])
    assert 'os' in classified['stdlib']
    assert 'numpy' in classified['third_party']
    assert 'mymodule' in classified['local']
    assert 'Queue' in classified['obsolete']
    logger.info("✅ Classification OK")
    
    # Test 5: Sécurité désinstallation
    logger.info("\n[Test 5] PackageUninstaller")
    uninstaller = PackageUninstaller(config)
    safety = uninstaller.is_safe_to_uninstall('pip')
    assert safety['safe'] == False
    assert safety['risk'] == 'CRITICAL'
    logger.info("✅ PackageUninstaller OK")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ TOUS LES TESTS PASSENT")
    logger.info("=" * 70)


# ============================================================
# 🚀 POINT D'ENTRÉE
# ============================================================

if __name__ == '__main__':
    import sys
    
    # Mode test
    if '--test' in sys.argv:
        run_tests()
        sys.exit(0)
    
    # Mode normal
    try:
        print("=" * 70)
        print("🔍 API Detector v4 — Kerberos Pro + Uninstaller")
        print("✅ Sécurité + Performance + Tests + Désinstallation")
        print("=" * 70)
        APIDetectorApp()
    except Exception as e:
        logger.critical(f"CRASH: {e}", exc_info=True)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("💥 CRASH", str(e))
        except Exception:
            pass
        input("\nAppuie sur Entrée...")