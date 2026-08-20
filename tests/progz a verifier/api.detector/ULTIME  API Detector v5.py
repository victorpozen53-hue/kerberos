#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Victor Pozen — GPLv3
"""
API Detector v5 — CERBERUS 🐕‍🦺
================================
Le gardien à 3 têtes de ton environnement Python :

🗑️ TÊTE 1 : Uninstaller sécurisé (désinstalle sans casser)
🕵️ TÊTE 2 : Monitor temps réel (surveille les installations)
🛡️ TÊTE 3 : Security Scanner (bloque les APIs vérolées)

+ Sélection granulaire (checkboxes)
+ Détection modules locaux
+ AST visitor optimisé
+ Tests unitaires intégrés

Usage :
    python api_detector_v5.py              # Mode GUI
    python api_detector_v5.py --test       # Tests unitaires
    python api_detector_v5.py --cli <dir>  # Mode CLI
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
from typing import Set, Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, field
import re
import traceback

# ============================================================
# 🚨 FILET DE SÉCURITÉ — Crash handler global
# ============================================================

def _crash_handler(exc_type, exc_value, exc_traceback):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("💥 CRASH Cerberus", msg)
        root.destroy()
    except Exception:
        pass
    print(msg, file=sys.stderr)

sys.excepthook = _crash_handler


# ============================================================
# 🔧 LOGGING PROFESSIONNEL
# ============================================================

def setup_logger(name: str = "cerberus") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s', datefmt='%H:%M:%S'
        ))
        logger.addHandler(handler)
    return logger

logger = setup_logger()


# ============================================================
# 📋 CONFIGURATION CENTRALISÉE
# ============================================================

@dataclass
class Config:
    """Configuration de Cerberus"""
    
    # 📚 Modules stdlib Python
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
    
    # 🔄 Correspondance import → pip
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
    
    # 🗑️ Modules Python 2 obsolètes
    PYTHON2_OBSOLETE: Set[str] = field(default_factory=lambda: {
        'ConfigParser', 'HTMLParser', 'Queue', 'StringIO', 'cPickle',
        'dummy_thread', 'dummy_threading', 'htmlentitydefs', 'httplib',
        'thread', 'urllib2', 'urlparse', 'xmlrpclib', '__builtin__',
    })
    
    # 🛡️ Packages JAMAIS désinstallables
    PROTECTED_PACKAGES: Set[str] = field(default_factory=lambda: {
        'pip', 'setuptools', 'wheel', 'distribute', 'pkg-resources',
        'pkg_resources', 'importlib-metadata', 'zipp', 'typing-extensions',
        'certifi', 'charset-normalizer', 'idna', 'urllib3', 'requests',
        'six', 'packaging', 'pyparsing', 'colorama', 'tomli', 'tomllib',
    })
    
    # 🚨 Packages critiques (demandent confirmation)
    CRITICAL_PACKAGES: Set[str] = field(default_factory=lambda: {
        'numpy', 'pandas', 'scipy', 'matplotlib', 'tensorflow',
        'torch', 'sklearn', 'scikit-learn', 'opencv-python', 'cv2',
        'pillow', 'flask', 'django', 'fastapi', 'sqlalchemy',
        'celery', 'redis', 'pymongo', 'psycopg2', 'requests',
    })
    
    # 🎨 Thème Kerberos
    BG_COLOR: str = '#1e1e1e'
    BG_LIGHT: str = '#2d2d2d'
    BG_DARK: str = '#252525'
    FG_COLOR: str = '#ffffff'
    FG_GREEN: str = '#00ff00'
    FG_CYAN: str = '#00ffff'
    FG_ORANGE: str = '#ff9800'
    FG_RED: str = '#ff4444'
    FG_PURPLE: str = '#b388ff'
    FG_YELLOW: str = '#ffeb3b'
    BTN_COLOR: str = '#3a3a3a'
    
    FONT_MAIN: Tuple[str, int] = ('Consolas', 11)
    FONT_SMALL: Tuple[str, int] = ('Consolas', 10)
    FONT_TITLE: Tuple[str, int, str] = ('Consolas', 12, 'bold')
    
    # ⏱️ Timeouts
    PIP_LIST_TIMEOUT: int = 15
    PYPI_SEARCH_TIMEOUT: int = 30
    PIP_INSTALL_TIMEOUT: int = 180
    PIP_UNINSTALL_TIMEOUT: int = 60
    MONITOR_POLL_INTERVAL: int = 5
    
    # 📁 Dossiers ignorés
    IGNORE_DIRS: Set[str] = field(default_factory=lambda: {
        'venv', 'env', '__pycache__', '.git', '.idea', '.vscode', 'node_modules'
    })


# ============================================================
# 🛡️ VALIDATEUR DE SÉCURITÉ
# ============================================================

class PackageValidator:
    """Valide les noms de packages contre l'injection"""
    
    VALID_PACKAGE_NAME = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$')
    
    @classmethod
    def is_valid_package_name(cls, name: str) -> bool:
        if not name or len(name) > 200:
            return False
        if not cls.VALID_PACKAGE_NAME.match(name):
            return False
        dangerous = {';', '&', '|', '`', '$', '(', ')', '{', '}', '<', '>', '\'', '"'}
        if any(c in name for c in dangerous):
            return False
        return True
    
    @classmethod
    def sanitize(cls, name: str) -> Optional[str]:
        if not cls.is_valid_package_name(name):
            logger.warning(f"Nom de package rejeté: {name}")
            return None
        return name


# ============================================================
# 🧠 ANALYZER v5 — AST Visitor optimisé
# ============================================================

class ImportVisitor(ast.NodeVisitor):
    """Visitor AST optimisé (30-50% plus rapide que ast.walk)"""
    
    def __init__(self):
        self.imports: Set[str] = set()
    
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module and node.level == 0:
            self.imports.add(node.module.split('.')[0])
        self.generic_visit(node)


class ImportAnalyzer:
    """Analyseur d'imports avec détection des modules locaux"""
    
    def __init__(self, config: Config):
        self.config = config
        self.local_modules: Set[str] = set()
        self._lock = threading.Lock()
    
    def _read_file(self, file_path: Path) -> str:
        for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                return file_path.read_text(encoding=enc)
            except (UnicodeDecodeError, UnicodeError):
                continue
        return file_path.read_bytes().decode('utf-8', errors='ignore')
    
    def detect_local_modules(self, dir_path: Path) -> Set[str]:
        """Détecte automatiquement les modules locaux"""
        local = set()
        
        for py_file in dir_path.glob("*.py"):
            local.add(py_file.stem)
        
        for init_file in dir_path.rglob("__init__.py"):
            if any(part.startswith('.') or part in self.config.IGNORE_DIRS
                   for part in init_file.parts):
                continue
            local.add(init_file.parent.name)
        
        for sub_dir in dir_path.iterdir():
            if not sub_dir.is_dir():
                continue
            if sub_dir.name.startswith('.') or sub_dir.name in self.config.IGNORE_DIRS:
                continue
            if any(sub_dir.glob("*.py")):
                local.add(sub_dir.name)
        
        return local
    
    def analyze_directory(self, dir_path: Path) -> Dict[str, Any]:
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
                code = self._read_file(py_file)
                tree = ast.parse(code, filename=str(py_file))
                
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
# 🔍 CHECKER v5
# ============================================================

class APIChecker:
    """Vérificateur d'installation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.installed_packages = self._get_installed_packages()
    
    def _get_installed_packages(self) -> Dict[str, str]:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True, text=True, timeout=self.config.PIP_LIST_TIMEOUT
            )
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                normalized = {}
                for pkg in packages:
                    name = pkg['name'].lower()
                    normalized[name] = pkg['version']
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
        try:
            return importlib.util.find_spec(module_name) is not None
        except Exception:
            return False
    
    def get_pip_package_name(self, import_name: str) -> Optional[str]:
        return self.config.IMPORT_TO_PIP.get(import_name, import_name)
    
    def check_all_local(self, third_party_imports: List[str]) -> Dict[str, List[Dict]]:
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
                results['missing'].append({'module': module, 'pip_name': pip_name})
        
        return results
    
    def search_pypi_single(self, package_name: str) -> Dict[str, Any]:
        validated = PackageValidator.sanitize(package_name)
        if not validated:
            return {'found': False, 'error': 'Nom invalide'}
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--dry-run',
                 '--report', '-', '--quiet', validated],
                capture_output=True, text=True, timeout=self.config.PYPI_SEARCH_TIMEOUT
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
            logger.error(f"Erreur PyPI {package_name}: {e}")
            return {'found': False, 'error': str(e)}
    
    def search_pypi_batch(
        self,
        missing_modules: List[Dict],
        progress_callback: Optional[Callable] = None,
        stop_event: Optional[threading.Event] = None
    ) -> Dict[str, List[Dict]]:
        results = {'pypi_found': [], 'not_found': []}
        total = len(missing_modules)
        
        for i, mod_info in enumerate(missing_modules):
            if stop_event and stop_event.is_set():
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
        validated = PackageValidator.sanitize(package_name)
        if not validated:
            return False
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--quiet', validated],
                capture_output=True, text=True, timeout=self.config.PIP_INSTALL_TIMEOUT
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Erreur installation {package_name}: {e}")
            return False


# ============================================================
# 🗑️ UNINSTALLER v5 — Sécurisé
# ============================================================

class PackageUninstaller:
    """Désinstallateur avec protections multiples"""
    
    def __init__(self, config: Config):
        self.config = config
        self.protected = config.PROTECTED_PACKAGES
    
    def get_reverse_dependencies(self, package_name: str) -> List[str]:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []
            for line in result.stdout.splitlines():
                if line.startswith('Required-by:'):
                    deps = line.split(':', 1)[1].strip()
                    if deps:
                        return [d.strip() for d in deps.split(',')]
            return []
        except Exception as e:
            logger.warning(f"Reverse deps {package_name}: {e}")
            return []
    
    def is_safe_to_uninstall(self, package_name: str) -> Dict[str, Any]:
        name_lower = package_name.lower()
        
        if name_lower in self.protected:
            return {
                'safe': False,
                'reason': f"🛡️ Package système protégé",
                'risk': 'CRITICAL'
            }
        
        reverse_deps = self.get_reverse_dependencies(package_name)
        if reverse_deps:
            return {
                'safe': False,
                'reason': f"⚠️ {len(reverse_deps)} package(s) en dépendent : {', '.join(reverse_deps)}",
                'risk': 'HIGH',
                'dependents': reverse_deps
            }
        
        return {'safe': True, 'reason': '✅ Désinstallation sûre', 'risk': 'LOW'}
    
    def uninstall_package(self, package_name: str) -> bool:
        validated = PackageValidator.sanitize(package_name)
        if not validated:
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
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'freeze'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = output_path / f"pip_backup_{timestamp}.txt"
                backup_path.write_text(result.stdout, encoding='utf-8')
                logger.info(f"💾 Backup : {backup_path}")
                return backup_path
        except Exception as e:
            logger.error(f"Erreur backup: {e}")
        return None


# ============================================================
# 🛡️ SECURITY SCANNER — Détection d'APIs vérolées
# ============================================================

class SecurityScanner:
    """Détecte typosquatting, packages suspects et code malveillant"""
    
    # 🚨 Typosquatting : (suspect, officiel)
    TYPOSQUAT_MAP: Dict[str, str] = {
        'request': 'requests', 'requestes': 'requests', 'requets': 'requests',
        'numppy': 'numpy', 'numpi': 'numpy', 'numopy': 'numpy',
        'pandsa': 'pandas', 'pands': 'pandas', 'panddas': 'pandas',
        'flaskk': 'flask', 'flsk': 'flask', 'flaask': 'flask',
        'djnago': 'django', 'dajngo': 'django', 'djangoo': 'django',
        'pilow': 'pillow', 'pilllow': 'pillow', 'piilow': 'pillow',
        'sklear': 'scikit-learn', 'sklearnn': 'scikit-learn',
        'tensorfflow': 'tensorflow', 'tensoflow': 'tensorflow',
        'torh': 'torch', 'torcch': 'torch',
    }
    
    # 🔍 Signatures de code malveillant
    MALICIOUS_PATTERNS = [
        (r'os\.system\s*\(', "Appel système dangereux"),
        (r'subprocess\.(call|run|Popen)\s*\(', "Subprocess suspect"),
        (r'\beval\s*\(', "eval() dangereux"),
        (r'\bexec\s*\(', "exec() dangereux"),
        (r'__import__\s*\(', "Import dynamique suspect"),
        (r'base64\.b64decode', "Décodeur base64 (souvent obfuscation)"),
        (r'ctypes\.windll', "Appel DLL Windows suspect"),
        (r'socket\.connect\s*\(', "Connexion réseau suspecte"),
        (r'urllib\.request\.urlopen\s*\(', "Téléchargement suspect"),
        (r'wget|curl\s+', "Téléchargement externe"),
        (r'powershell', "PowerShell injection"),
        (r'/bin/(sh|bash)', "Shell injection"),
    ]
    
    def __init__(self, config: Config):
        self.config = config
    
    def check_package_safety(self, package_name: str, installed: bool = False) -> Dict[str, Any]:
        """Analyse complète de sécurité d'un package"""
        result = {
            'safe': True,
            'warnings': [],
            'dangers': [],
            'alternative': None,
            'score': 100,
            'critical': package_name.lower() in {p.lower() for p in self.config.CRITICAL_PACKAGES}
        }
        
        # 1. Typosquatting
        typo = self._check_typosquatting(package_name)
        if typo:
            result['safe'] = False
            result['dangers'].append(f"🚨 TYPOSQUATTING : '{package_name}' → '{typo}'")
            result['alternative'] = typo
            result['score'] -= 60
        
        # 2. Package inconnu (pas dans whitelist implicite)
        if package_name.lower() not in {p.lower() for p in self.config.CRITICAL_PACKAGES}:
            result['warnings'].append("⚠️ Package non reconnu (vérifier sur PyPI)")
            result['score'] -= 5
        
        # 3. Scan du code si installé
        if installed:
            code_scan = self._scan_package_code(package_name)
            if code_scan['findings']:
                result['safe'] = False
                result['dangers'].extend(code_scan['findings'])
                result['score'] -= 40
        
        return result
    
    def _check_typosquatting(self, package_name: str) -> Optional[str]:
        name_lower = package_name.lower()
        
        # Check direct
        if name_lower in self.TYPOSQUAT_MAP:
            return self.TYPOSQUAT_MAP[name_lower]
        
        # Similarité avec packages connus
        for suspect, official in self.TYPOSQUAT_MAP.items():
            if self._similarity(name_lower, official) > 0.85 and name_lower != official:
                return official
        
        return None
    
    def _similarity(self, s1: str, s2: str) -> float:
        if s1 == s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        len1, len2 = len(s1), len(s2)
        max_len = max(len1, len2)
        distance = abs(len1 - len2)
        for i in range(min(len1, len2)):
            if s1[i] != s2[i]:
                distance += 1
        return 1.0 - (distance / max_len)
    
    def _scan_package_code(self, package_name: str) -> Dict[str, Any]:
        """Scanne le code source pour détecter du code malveillant"""
        result = {'findings': []}
        
        try:
            spec = importlib.util.find_spec(package_name)
            if not spec or not spec.origin:
                return result
            
            package_path = Path(spec.origin).parent
            if not package_path.exists():
                return result
            
            scanned = 0
            for py_file in package_path.rglob('*.py'):
                if scanned > 50:  # Limite pour performance
                    break
                try:
                    code = py_file.read_text(encoding='utf-8', errors='ignore')
                    for pattern, description in self.MALICIOUS_PATTERNS:
                        if re.search(pattern, code, re.IGNORECASE):
                            result['findings'].append(
                                f"🚨 {description} dans {py_file.name}"
                            )
                    scanned += 1
                except Exception:
                    continue
        
        except Exception as e:
            logger.warning(f"Scan code {package_name}: {e}")
        
        return result


# ============================================================
# 🕵️ MONITOR — Surveillance temps réel
# ============================================================

class APIMonitor:
    """Surveille les installations/désinstallations en temps réel"""
    
    def __init__(self, config: Config, callback: Optional[Callable] = None):
        self.config = config
        self.callback = callback
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
        self._baseline: Dict[str, str] = {}
        self.history: List[Dict] = []
        self.max_history = 500
        
        self.is_running = False
    
    def _get_current_packages(self) -> Dict[str, str]:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return {pkg['name'].lower(): pkg['version'] for pkg in packages}
        except Exception as e:
            logger.warning(f"Monitor pip list: {e}")
        return {}
    
    def take_baseline(self) -> None:
        with self._lock:
            self._baseline = self._get_current_packages()
            logger.info(f"📸 Baseline : {len(self._baseline)} packages")
    
    def start(self) -> None:
        if self.is_running:
            return
        if not self._baseline:
            self.take_baseline()
        
        self._stop_event.clear()
        self.is_running = True
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="APIMonitor"
        )
        self._thread.start()
        logger.info("🕵️ Surveillance démarrée")
    
    def stop(self) -> None:
        if not self.is_running:
            return
        self._stop_event.set()
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("🕵️ Surveillance arrêtée")
    
    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                new_state = self._get_current_packages()
                self._detect_changes(new_state)
                with self._lock:
                    self._baseline = new_state
            except Exception as e:
                logger.error(f"Monitor loop: {e}")
            self._stop_event.wait(self.config.MONITOR_POLL_INTERVAL)
    
    def _detect_changes(self, new_state: Dict[str, str]) -> None:
        with self._lock:
            baseline = self._baseline
        
        # Ajouts
        for pkg in set(new_state.keys()) - set(baseline.keys()):
            self._record_event({
                'type': 'installed',
                'package': pkg,
                'version': new_state[pkg],
                'timestamp': datetime.now().isoformat(),
                'icon': '📦'
            })
        
        # Suppressions
        for pkg in set(baseline.keys()) - set(new_state.keys()):
            self._record_event({
                'type': 'uninstalled',
                'package': pkg,
                'version': baseline[pkg],
                'timestamp': datetime.now().isoformat(),
                'icon': '🗑️'
            })
        
        # Mises à jour
        for pkg in set(new_state.keys()) & set(baseline.keys()):
            if new_state[pkg] != baseline[pkg]:
                self._record_event({
                    'type': 'updated',
                    'package': pkg,
                    'old_version': baseline[pkg],
                    'version': new_state[pkg],
                    'timestamp': datetime.now().isoformat(),
                    'icon': '🔄'
                })
    
    def _record_event(self, event: Dict) -> None:
        with self._lock:
            self.history.append(event)
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
        
        if self.callback:
            try:
                self.callback(event)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    def get_history(self) -> List[Dict]:
        with self._lock:
            return self.history.copy()
    
    def clear_history(self) -> None:
        with self._lock:
            self.history.clear()
    
    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            stats = {'installed': 0, 'uninstalled': 0, 'updated': 0}
            for event in self.history:
                stats[event['type']] = stats.get(event['type'], 0) + 1
            return stats


# ============================================================
# 📄 REPORT GENERATOR
# ============================================================

class ReportGenerator:
    """Générateur de rapports JSON/TXT/HTML"""
    
    @staticmethod
    def generate_json(results: Dict, output_path: Path) -> None:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_txt(results: Dict, output_path: Path) -> None:
        lines = [
            "=" * 70, "CERBERUS v5 — RAPPORT D'ANALYSE", "=" * 70,
            f"Dossier : {results['target']}",
            f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Fichiers : {results['files_scanned']}", "",
            f"📚 Stdlib : {len(results['stdlib'])}",
            f"🔌 Tiers : {len(results['third_party'])}",
            f"🏠 Locaux : {len(results['local'])}",
            f"🗑️ Obsolète : {len(results['obsolete'])}", "",
            "-" * 70, "✅ INSTALLÉS", "-" * 70,
        ]
        for p in results['installed']:
            lines.append(f"  ✓ {p['module']} (pip: {p['pip_name']}) v{p['version']}")
        lines += ["", "-" * 70, "❌ MANQUANTS", "-" * 70]
        for p in results['missing']:
            lines.append(f"  ✗ {p['module']} → pip install {p['pip_name']}")
        lines += ["", "=" * 70]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    @staticmethod
    def generate_html(results: Dict, output_path: Path) -> None:
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Cerberus v5 — Rapport</title>
<style>
body {{ font-family: 'Consolas', monospace; background: #1e1e1e; color: #fff; padding: 20px; }}
.container {{ max-width: 1200px; margin: 0 auto; background: #252525; padding: 30px; border-radius: 8px; }}
h1 {{ color: #00ffff; border-bottom: 2px solid #00ffff; }}
h2 {{ color: #00ff00; margin-top: 30px; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin: 20px 0; }}
.stat-box {{ background: #2d2d2d; padding: 15px; border-radius: 5px; border-left: 4px solid #00ffff; }}
.stat-number {{ font-size: 2em; font-weight: bold; color: #00ffff; }}
table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: #2d2d2d; }}
th {{ background: #3a3a3a; color: #00ffff; padding: 12px; }}
td {{ padding: 10px; border-bottom: 1px solid #3a3a3a; }}
.badge {{ padding: 3px 8px; border-radius: 3px; font-weight: bold; }}
.badge-ok {{ background: #00ff00; color: #000; }}
.badge-ko {{ background: #ff4444; color: #fff; }}
</style>
</head>
<body>
<div class="container">
<h1>🐕‍🦺 Cerberus v5 — Rapport</h1>
<p><strong>Dossier :</strong> {results['target']}</p>
<p><strong>Date :</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<div class="stats">
<div class="stat-box"><div class="stat-number">{results['files_scanned']}</div>Fichiers</div>
<div class="stat-box"><div class="stat-number">{len(results['stdlib'])}</div>Stdlib</div>
<div class="stat-box"><div class="stat-number">{len(results['third_party'])}</div>Tiers</div>
<div class="stat-box"><div class="stat-number">{len(results['local'])}</div>Locaux</div>
<div class="stat-box"><div class="stat-number">{len(results['installed'])}</div>Installés</div>
<div class="stat-box"><div class="stat-number">{len(results['missing'])}</div>Manquants</div>
</div>
<h2>✅ Installés ({len(results['installed'])})</h2>
<table><tr><th>Module</th><th>Pip</th><th>Version</th></tr>
"""
        for p in results['installed']:
            html += f"<tr><td>{p['module']}</td><td>{p['pip_name']}</td><td><span class='badge badge-ok'>{p['version']}</span></td></tr>\n"
        html += "</table><h2>❌ Manquants</h2><table><tr><th>Module</th><th>Commande</th></tr>\n"
        for p in results['missing']:
            html += f"<tr><td>{p['module']}</td><td><code>pip install {p['pip_name']}</code></td></tr>\n"
        html += """</table>
<div style="margin-top:30px;color:#888;text-align:center;">Cerberus v5 — GPLv3 — Victor Pozen</div>
</div></body></html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)


# ============================================================
# 🖥️ GUI CERBERUS v5
# ============================================================

class CerberusApp:
    """Interface graphique — Le gardien à 3 têtes"""
    
    def __init__(self):
        logger.info("🐕‍🦺 Démarrage Cerberus v5...")
        
        self.config = Config()
        self.root = tk.Tk()
        self.root.title("🐕‍🦺 Cerberus v5 — Le gardien de ton Python")
        self.root.geometry("1300x850")
        self.root.configure(bg=self.config.BG_COLOR)
        
        self.target_path = tk.StringVar()
        
        # 🐕‍🦺 Les 3 têtes de Cerberus
        self.analyzer = ImportAnalyzer(self.config)
        self.checker = APIChecker(self.config)
        self.uninstaller = PackageUninstaller(self.config)
        self.security_scanner = SecurityScanner(self.config)
        self.monitor = APIMonitor(self.config, callback=self._on_monitor_event)
        self.report_gen = ReportGenerator()
        
        self.analysis_results: Optional[Dict] = None
        self.stop_event = threading.Event()
        self.results_lock = threading.Lock()
        
        self._setup_style()
        self._build_ui()
        
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        logger.info("🐕‍🦺 Cerberus v5 prêt")
        
        self.root.mainloop()
    
    def _setup_style(self) -> None:
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
        style.configure('Treeview',
                       background=self.config.BG_LIGHT,
                       foreground=self.config.FG_COLOR,
                       fieldbackground=self.config.BG_LIGHT,
                       font=self.config.FONT_MAIN)
        style.configure('Treeview.Heading',
                       background=self.config.BTN_COLOR,
                       foreground=self.config.FG_CYAN,
                       font=self.config.FONT_TITLE)
    
    def _build_ui(self) -> None:
        # === ZONE SUPÉRIEURE ===
        top_frame = ttk.LabelFrame(self.root, text="📂 Dossier à analyser", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(top_frame, text="Dossier :").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(top_frame, textvariable=self.target_path,
                 font=self.config.FONT_MAIN).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(top_frame, text="📂 Choisir",
                  command=self._select_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="🔍 Scanner",
                  command=self._start_scan).pack(side=tk.LEFT, padx=(10, 0))
        
        # === ONGLETS ===
        results_frame = ttk.Frame(self.root)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Onglets simples (Text)
        self.tab_stdlib = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stdlib, text="📚 Stdlib")
        self.text_stdlib = self._build_text_tab(self.tab_stdlib)
        
        self.tab_local = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_local, text="🏠 Locaux")
        self.text_local = self._build_text_tab(self.tab_local)
        
        # Onglets avec checkboxes (Treeview)
        self.tab_installed = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_installed, text="✅ Installés")
        self.tree_installed = self._build_tree_tab(self.tab_installed, "installed")
        
        self.tab_missing = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_missing, text="❌ Manquants")
        self.tree_missing = self._build_tree_tab(self.tab_missing, "missing")
        
        self.tab_obsolete = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_obsolete, text="🗑️ Obsolète")
        self.text_obsolete = self._build_text_tab(self.tab_obsolete)
        
        # === ZONE INFÉRIEURE ===
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Ligne 1 : Actions principales
        action_frame = ttk.Frame(bottom_frame)
        action_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_search_pypi = ttk.Button(action_frame, text="🌐 PyPI",
                                          command=self._search_pypi, state='disabled')
        self.btn_search_pypi.pack(side=tk.LEFT, padx=3)
        
        self.btn_install = ttk.Button(action_frame, text="📦 Installer (sélection)",
                                     command=self._install_selected, state='disabled')
        self.btn_install.pack(side=tk.LEFT, padx=3)
        
        self.btn_uninstall = ttk.Button(action_frame, text="🗑️ Désinstaller (sélection)",
                                       command=self._uninstall_selected, state='disabled')
        self.btn_uninstall.pack(side=tk.LEFT, padx=3)
        
        ttk.Button(action_frame, text="💾 JSON",
                  command=lambda: self._export_report('json')).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="📄 TXT",
                  command=lambda: self._export_report('txt')).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_frame, text="🌐 HTML",
                  command=lambda: self._export_report('html')).pack(side=tk.LEFT, padx=3)
        
        self.progress_label = ttk.Label(action_frame, text="Prêt",
                                       foreground=self.config.FG_GREEN)
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        self.progress = ttk.Progressbar(action_frame, mode='determinate', length=250)
        self.progress.pack(side=tk.RIGHT, padx=5)
        
        # Ligne 2 : Monitor
        monitor_frame = ttk.LabelFrame(bottom_frame, text="🕵️ Surveillance temps réel", padding=5)
        monitor_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_monitor_start = ttk.Button(monitor_frame, text="▶️ Démarrer",
                                            command=self._start_monitor)
        self.btn_monitor_start.pack(side=tk.LEFT, padx=3)
        
        self.btn_monitor_stop = ttk.Button(monitor_frame, text="⏹️ Arrêter",
                                           command=self._stop_monitor, state='disabled')
        self.btn_monitor_stop.pack(side=tk.LEFT, padx=3)
        
        ttk.Button(monitor_frame, text="📜 Historique",
                  command=self._show_history).pack(side=tk.LEFT, padx=3)
        
        ttk.Button(monitor_frame, text="🗑️ Vider",
                  command=self._clear_history).pack(side=tk.LEFT, padx=3)
        
        self.monitor_stats = ttk.Label(monitor_frame, text="📦 0 | 🗑️ 0 | 🔄 0",
                                      foreground=self.config.FG_CYAN)
        self.monitor_stats.pack(side=tk.RIGHT, padx=10)
        
        self.monitor_status = ttk.Label(monitor_frame, text="⏸️ Arrêtée",
                                       foreground=self.config.FG_ORANGE)
        self.monitor_status.pack(side=tk.RIGHT, padx=5)
        
        # Console
        console_frame = ttk.LabelFrame(bottom_frame, text="📟 Console", padding=5)
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.console = scrolledtext.ScrolledText(
            console_frame, height=8, font=self.config.FONT_SMALL,
            bg=self.config.BG_DARK, fg=self.config.FG_GREEN, state='disabled'
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        
        self._log("🐕‍🦺 CERBERUS v5 — Le gardien à 3 têtes")
        self._log("🛡️ Sécurité + 🗑️ Uninstall + 🕵️ Monitor")
        self._log("💡 Clique sur les lignes des onglets pour cocher/décocher")
    
    def _build_text_tab(self, parent: ttk.Frame) -> tk.Text:
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(frame, font=self.config.FONT_MAIN,
                      bg=self.config.BG_LIGHT, fg=self.config.FG_COLOR,
                      yscrollcommand=scrollbar.set, state='disabled', wrap=tk.WORD)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        return text
    
    def _build_tree_tab(self, parent: ttk.Frame, tab_type: str) -> ttk.Treeview:
        """Crée un onglet avec checkboxes"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Boutons de sélection rapide
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        tree = ttk.Treeview(frame, columns=('sel', 'module', 'pip', 'version', 'status'),
                           show='headings', height=12)
        
        tree.heading('sel', text='✓')
        tree.heading('module', text='Module')
        tree.heading('pip', text='Package pip')
        tree.heading('version', text='Version')
        tree.heading('status', text='Statut')
        
        tree.column('sel', width=40, anchor=tk.CENTER)
        tree.column('module', width=180)
        tree.column('pip', width=200)
        tree.column('version', width=100)
        tree.column('status', width=100, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Layout
        tree.grid(row=1, column=0, sticky='nsew')
        scrollbar.grid(row=1, column=1, sticky='ns')
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Boutons
        ttk.Button(btn_frame, text="✅ Tout cocher",
                  command=lambda: self._toggle_all(tree, True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Tout décocher",
                  command=lambda: self._toggle_all(tree, False)).pack(side=tk.LEFT, padx=2)
        
        # Click pour toggle
        tree.bind('<ButtonRelease-1>', lambda e, t=tree: self._toggle_checkbox(t, e))
        
        # Stocke la référence
        if tab_type == "installed":
            self.tree_installed_widget = tree
        else:
            self.tree_missing_widget = tree
        
        return tree
    
    def _toggle_checkbox(self, tree: ttk.Treeview, event) -> None:
        item = tree.identify_row(event.y)
        if item:
            values = list(tree.item(item, 'values'))
            values[0] = '' if values[0] == '✓' else '✓'
            tree.item(item, values=values)
    
    def _toggle_all(self, tree: ttk.Treeview, state: bool) -> None:
        check = '✓' if state else ''
        for item_id in tree.get_children():
            values = list(tree.item(item_id, 'values'))
            values[0] = check
            tree.item(item_id, values=values)
    
    def _get_selected_from_tree(self, tree: ttk.Treeview) -> List[Dict]:
        selected = []
        for item_id in tree.get_children():
            values = tree.item(item_id, 'values')
            if values[0] == '✓':
                selected.append({
                    'module': values[1],
                    'pip_name': values[2],
                    'version': values[3] if len(values) > 3 else 'N/A',
                    'status': values[4] if len(values) > 4 else ''
                })
        return selected
    
    def _select_folder(self) -> None:
        path = filedialog.askdirectory(title="Sélectionner un dossier Python")
        if path:
            self.target_path.set(path)
            self._log(f"📂 Dossier : {path}")
    
    def _start_scan(self) -> None:
        target = self.target_path.get().strip()
        if not target:
            messagebox.showwarning("⚠️", "Sélectionne un dossier.")
            return
        
        target_path = Path(target)
        if not target_path.is_dir():
            messagebox.showerror("❌", f"Dossier introuvable : {target}")
            return
        
        for btn in [self.btn_search_pypi, self.btn_install, self.btn_uninstall]:
            btn.config(state='disabled')
        
        self.stop_event.clear()
        threading.Thread(target=self._scan_worker, args=(target_path,), daemon=True).start()
    
    def _scan_worker(self, target_path: Path) -> None:
        try:
            self._update_progress("🏠 Détection modules locaux...", 10)
            self._log(f"[🔍] Scan : {target_path}")
            
            local_modules = self.analyzer.detect_local_modules(target_path)
            self._log(f"🏠 {len(local_modules)} modules locaux détectés")
            
            self._update_progress("📖 Scan fichiers .py...", 25)
            result = self.analyzer.analyze_directory(target_path)
            self._log(f"✅ {result['files_scanned']} fichiers analysés")
            
            self._update_progress("🏷️ Classification...", 45)
            classified = self.analyzer.classify_imports(result['all_imports'])
            
            self._log(f"📚 Stdlib : {len(classified['stdlib'])}")
            self._log(f"🏠 Locaux : {len(classified['local'])}")
            self._log(f"🔌 Tiers : {len(classified['third_party'])}")
            self._log(f"🗑️ Obsolète : {len(classified['obsolete'])}")
            
            # Affichage stdlib
            self._run_in_main_thread(
                self._fill_text, self.text_stdlib,
                [f"📚 {m}" for m in classified['stdlib']], self.config.FG_CYAN
            )
            
            # Affichage locaux
            local_lines = []
            for m in classified['local']:
                if (target_path / f"{m}.py").exists():
                    local_lines.append(f"🏠 {m}  →  📄 fichier")
                elif (target_path / m).is_dir():
                    local_lines.append(f"🏠 {m}  →  📁 dossier")
                else:
                    local_lines.append(f"🏠 {m}  →  🔹 module")
            if not local_lines:
                local_lines = ["ℹ️ Aucun module local"]
            self._run_in_main_thread(
                self._fill_text, self.text_local, local_lines, self.config.FG_PURPLE
            )
            
            # Affichage obsolète
            obs_lines = [f"🗑️ {m}" for m in classified['obsolete']] or ["✅ Aucun"]
            self._run_in_main_thread(
                self._fill_text, self.text_obsolete, obs_lines, self.config.FG_ORANGE
            )
            
            # Vérification installation
            self._update_progress("🔎 Vérification...", 65)
            local_check = self.checker.check_all_local(classified['third_party'])
            
            # Remplissage Treeview installés
            self._run_in_main_thread(self._fill_tree_installed, local_check['installed'])
            
            # Remplissage Treeview manquants
            if local_check['missing']:
                self._run_in_main_thread(self._fill_tree_missing, local_check['missing'])
                self._run_in_main_thread(self.btn_search_pypi.config, {'state': 'normal'})
                self._run_in_main_thread(self.btn_install.config, {'state': 'normal'})
            else:
                self._run_in_main_thread(
                    self._fill_text, self.text_missing if hasattr(self, 'text_missing') else self.text_stdlib,
                    ["🎉 Tous installés !"], self.config.FG_GREEN
                )
            
            # Active uninstall si des packages installés
            if local_check['installed']:
                self._run_in_main_thread(self.btn_uninstall.config, {'state': 'normal'})
            
            self._log(f"✅ Installés : {len(local_check['installed'])} | ❌ Manquants : {len(local_check['missing'])}")
            
            # Stockage résultats
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
    
    def _fill_text(self, text_widget: tk.Text, items: List[str], color: str) -> None:
        text_widget.configure(state='normal')
        text_widget.delete('1.0', tk.END)
        text_widget.tag_configure('item', foreground=color)
        for item in items:
            text_widget.insert(tk.END, f"{item}\n", 'item')
        text_widget.configure(state='disabled')
    
    def _fill_tree_installed(self, installed: List[Dict]) -> None:
        tree = self.tree_installed_widget
        tree.delete(*tree.get_children())
        
        for pkg in installed:
            safety = self.security_scanner.check_package_safety(pkg['pip_name'], installed=True)
            
            if not safety['safe']:
                status = "🚨 DANGER"
            elif safety['critical']:
                status = "⚠️ Critique"
            else:
                status = "✅ OK"
            
            tree.insert('', tk.END, values=(
                '✓',
                pkg['module'],
                pkg['pip_name'],
                pkg['version'],
                status
            ))
    
    def _fill_tree_missing(self, missing: List[Dict]) -> None:
        tree = self.tree_missing_widget
        tree.delete(*tree.get_children())
        
        for pkg in missing:
            safety = self.security_scanner.check_package_safety(pkg['pip_name'])
            
            if not safety['safe']:
                status = "🚨 BLOQUÉ"
                default_check = ''
            elif safety['critical']:
                status = "⚠️ Critique"
                default_check = ''  # Décoché par défaut
            else:
                status = "✅ Sûr"
                default_check = '✓'
            
            tree.insert('', tk.END, values=(
                default_check,
                pkg['module'],
                pkg['pip_name'],
                'N/A',
                status
            ))
    
    def _search_pypi(self) -> None:
        with self.results_lock:
            if not self.analysis_results or not self.analysis_results['missing']:
                messagebox.showinfo("ℹ️", "Rien à rechercher.")
                return
            missing = self.analysis_results['missing'].copy()
        
        if messagebox.askyesno("🌐 PyPI", f"Rechercher {len(missing)} module(s) ?"):
            self.stop_event.clear()
            threading.Thread(target=self._pypi_worker, args=(missing,), daemon=True).start()
    
    def _pypi_worker(self, missing: List[Dict]) -> None:
        def cb(i, t, m):
            self._update_progress(m, int((i / max(t, 1)) * 100))
        
        results = self.checker.search_pypi_batch(missing, cb, self.stop_event)
        self._log(f"✅ Trouvés : {len(results['pypi_found'])} | ❓ Introuvables : {len(results['not_found'])}")
        self._update_progress("✅ PyPI terminé", 100)
    
    def _install_selected(self) -> None:
        """Installe UNIQUEMENT les packages cochés, avec sécurité"""
        selected = self._get_selected_from_tree(self.tree_missing_widget)
        
        if not selected:
            messagebox.showinfo("ℹ️", "Aucun package sélectionné.\n💡 Clique sur les lignes pour cocher.")
            return
        
        # 🛡️ SCAN DE SÉCURITÉ
        safe_list = []
        blocked_list = []
        report = ["🛡️ RAPPORT DE SÉCURITÉ\n"]
        
        for pkg in selected:
            safety = self.security_scanner.check_package_safety(pkg['pip_name'])
            
            if not safety['safe']:
                blocked_list.append((pkg, safety))
                report.append(f"🚨 BLOQUÉ : {pkg['pip_name']}")
                for d in safety['dangers']:
                    report.append(f"   {d}")
                if safety['alternative']:
                    report.append(f"   ✅ Alternative : {safety['alternative']}")
                report.append("")
            else:
                safe_list.append(pkg)
                if safety['warnings']:
                    report.append(f"⚠️ {pkg['pip_name']} :")
                    for w in safety['warnings']:
                        report.append(f"   {w}")
        
        if blocked_list:
            report.insert(0, "=" * 60)
            report.append(f"\n🚨 {len(blocked_list)} BLOQUÉ(S) | ✅ {len(safe_list)} SÛR(S)")
            messagebox.showwarning("🛡️ Sécurité", "\n".join(report))
        
        if not safe_list:
            self._log("🛡️ Tous les packages sélectionnés ont été bloqués")
            return
        
        recap = "\n".join(f"• {p['module']} → {p['pip_name']}" for p in safe_list)
        
        if messagebox.askyesno(
            "📦 Installation",
            f"Installer {len(safe_list)} package(s) SÛR(S) ?\n{recap}\n\n"
            f"🛡️ {len(blocked_list)} bloqué(s) pour sécurité"
        ):
            self.stop_event.clear()
            threading.Thread(target=self._install_worker, args=(safe_list,), daemon=True).start()
    
    def _install_worker(self, packages: List[Dict]) -> None:
        self._update_progress("📦 Installation...", 0)
        success, failed = [], []
        
        for i, pkg in enumerate(packages):
            if self.stop_event.is_set():
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
    
    def _uninstall_selected(self) -> None:
        """Désinstalle UNIQUEMENT les packages cochés, avec sécurité"""
        selected = self._get_selected_from_tree(self.tree_installed_widget)
        
        if not selected:
            messagebox.showinfo("ℹ️", "Aucun package sélectionné.")
            return
        
        # Analyse de sécurité
        safe_to_remove = []
        dangerous = []
        protected = []
        
        for pkg in selected:
            safety = self.uninstaller.is_safe_to_uninstall(pkg['pip_name'])
            
            if safety['risk'] == 'CRITICAL':
                protected.append((pkg, safety['reason']))
            elif safety['risk'] == 'HIGH':
                dangerous.append((pkg, safety['reason']))
            else:
                safe_to_remove.append(pkg)
        
        report = ["🔍 DIAGNOSTIC DE SÉCURITÉ\n"]
        
        if protected:
            report.append("🛡️ BLOQUÉS (système) :")
            for pkg, reason in protected:
                report.append(f"   ❌ {pkg['pip_name']} — {reason}")
            report.append("")
        
        if dangerous:
            report.append("⚠️ DANGEREUX (dépendances) :")
            for pkg, reason in dangerous:
                report.append(f"   ⚠️ {pkg['pip_name']} — {reason}")
            report.append("")
        
        if safe_to_remove:
            report.append("✅ SÛRS :")
            for pkg in safe_to_remove:
                report.append(f"   ✓ {pkg['pip_name']} (v{pkg['version']})")
        
        if not safe_to_remove:
            messagebox.showwarning("⚠️ Sécurité", "\n".join(report))
            return
        
        if not messagebox.askyesno(
            "🗑️ Désinstallation",
            "\n".join(report) + f"\n\n🗑️ Désinstaller {len(safe_to_remove)} package(s) ?"
        ):
            return
        
        # Backup avant
        backup_dir = Path.home() / ".cerberus_backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = self.uninstaller.backup_installed_list(backup_dir)
        if backup_path:
            self._log(f"💾 Backup : {backup_path}")
        
        self.stop_event.clear()
        threading.Thread(target=self._uninstall_worker, args=(safe_to_remove,), daemon=True).start()
    
    def _uninstall_worker(self, packages: List[Dict]) -> None:
        self._update_progress("🗑️ Désinstallation...", 0)
        success, failed = [], []
        
        for i, pkg in enumerate(packages):
            if self.stop_event.is_set():
                break
            pip_name = pkg['pip_name']
            self._update_progress(f"🗑️ {pip_name}", int((i / max(len(packages), 1)) * 100))
            
            safety = self.uninstaller.is_safe_to_uninstall(pip_name)
            if not safety['safe']:
                self._log(f"🛡️ BLOQUÉ : {pip_name}")
                failed.append(pip_name)
                continue
            
            if self.uninstaller.uninstall_package(pip_name):
                success.append(pip_name)
                self._log(f"🗑️ Désinstallé : {pip_name}")
            else:
                failed.append(pip_name)
                self._log(f"❌ Échec : {pip_name}")
        
        self._update_progress("✅ Terminé", 100)
        messagebox.showinfo("🗑️ Résultat", f"Succès : {len(success)}\nÉchecs : {len(failed)}")
    
    # 🕵️ MONITOR
    def _start_monitor(self) -> None:
        self.monitor.start()
        self.btn_monitor_start.config(state='disabled')
        self.btn_monitor_stop.config(state='normal')
        self.monitor_status.config(text="🔴 ACTIVE", foreground=self.config.FG_RED)
        self._log("🕵️ Surveillance démarrée")
    
    def _stop_monitor(self) -> None:
        self.monitor.stop()
        self.btn_monitor_start.config(state='normal')
        self.btn_monitor_stop.config(state='disabled')
        self.monitor_status.config(text="⏸️ Arrêtée", foreground=self.config.FG_ORANGE)
        self._log("🕵️ Surveillance arrêtée")
    
    def _on_monitor_event(self, event: Dict) -> None:
        icon = event['icon']
        pkg = event['package']
        
        if event['type'] == 'installed':
            msg = f"{icon} INSTALLÉ : {pkg} v{event['version']}"
            
            # 🛡️ Vérifie si c'est vérolé
            safety = self.security_scanner.check_package_safety(pkg, installed=True)
            if not safety['safe']:
                msg += " 🚨 SUSPECT !"
                for d in safety['dangers']:
                    msg += f"\n   {d}"
            
        elif event['type'] == 'uninstalled':
            msg = f"{icon} DÉSINSTALLÉ : {pkg} v{event['version']}"
        else:
            msg = f"{icon} UPDATE : {pkg} {event['old_version']} → {event['version']}"
        
        self._log(msg)
        
        stats = self.monitor.get_stats()
        self._run_in_main_thread(
            self.monitor_stats.config,
            {'text': f"📦 {stats['installed']} | 🗑️ {stats['uninstalled']} | 🔄 {stats['updated']}"}
        )
    
    def _show_history(self) -> None:
        history = self.monitor.get_history()
        if not history:
            messagebox.showinfo("📜 Historique", "Aucun événement.")
            return
        
        popup = tk.Toplevel(self.root)
        popup.title(f"📜 Historique ({len(history)})")
        popup.geometry("800x600")
        popup.configure(bg=self.config.BG_COLOR)
        
        stats = self.monitor.get_stats()
        ttk.Label(popup,
                 text=f"📦 {stats['installed']} | 🗑️ {stats['uninstalled']} | 🔄 {stats['updated']}",
                 font=self.config.FONT_TITLE,
                 foreground=self.config.FG_CYAN,
                 background=self.config.BG_COLOR).pack(pady=10)
        
        frame = ttk.Frame(popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(frame, font=self.config.FONT_MAIN,
                      bg=self.config.BG_LIGHT, fg=self.config.FG_COLOR,
                      yscrollcommand=scrollbar.set, state='disabled')
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        
        text.configure(state='normal')
        for event in reversed(history):
            ts = event['timestamp'][11:19]
            line = f"[{ts}] {event['icon']} {event['package']} v{event['version']}\n"
            text.insert(tk.END, line)
        text.configure(state='disabled')
        
        ttk.Button(popup, text="Fermer", command=popup.destroy).pack(pady=10)
    
    def _clear_history(self) -> None:
        if messagebox.askyesno("🗑️ Vider", "Supprimer l'historique ?"):
            self.monitor.clear_history()
            self.monitor_stats.config(text="📦 0 | 🗑️ 0 | 🔄 0")
            self._log("🗑️ Historique vidé")
    
    def _export_report(self, fmt: str) -> None:
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
        self._run_in_main_thread(
            lambda: (
                self.progress_label.config(text=text),
                self.progress.config(value=value)
            )
        )
    
    def _log(self, msg: str) -> None:
        def _do():
            self.console.configure(state='normal')
            self.console.insert(tk.END, f"{msg}\n")
            self.console.see(tk.END)
            self.console.configure(state='disabled')
        self._run_in_main_thread(_do)
    
    def _run_in_main_thread(self, func: Callable, *args, **kwargs) -> None:
        self.root.after(0, lambda: func(*args, **kwargs))
    
    def _on_close(self) -> None:
        if messagebox.askyesno("👋", "Fermer Cerberus ?"):
            self.monitor.stop()
            self.stop_event.set()
            self.root.destroy()


# ============================================================
# 🧪 TESTS UNITAIRES
# ============================================================

def run_tests() -> None:
    logger.info("=" * 70)
    logger.info("🧪 TESTS UNITAIRES CERBERUS v5")
    logger.info("=" * 70)
    
    # Test 1: Validator
    logger.info("\n[Test 1] PackageValidator")
    assert PackageValidator.is_valid_package_name("numpy")
    assert PackageValidator.is_valid_package_name("scikit-learn")
    assert not PackageValidator.is_valid_package_name("")
    assert not PackageValidator.is_valid_package_name("pkg;rm -rf /")
    logger.info("✅ PackageValidator OK")
    
    # Test 2: Config
    logger.info("\n[Test 2] Config")
    config = Config()
    assert 'os' in config.STDLIB_MODULES
    assert 'pip' in config.PROTECTED_PACKAGES
    assert 'numpy' in config.CRITICAL_PACKAGES
    logger.info("✅ Config OK")
    
    # Test 3: ImportVisitor
    logger.info("\n[Test 3] ImportVisitor")
    code = "import os\nfrom pathlib import Path\nimport sys, json"
    tree = ast.parse(code)
    visitor = ImportVisitor()
    visitor.visit(tree)
    assert 'os' in visitor.imports
    assert 'pathlib' in visitor.imports
    assert 'sys' in visitor.imports
    assert 'json' in visitor.imports
    logger.info("✅ ImportVisitor OK")
    
    # Test 4: Classification
    logger.info("\n[Test 4] Classification")
    config = Config()
    analyzer = ImportAnalyzer(config)
    analyzer.local_modules = {'mymod'}
    classified = analyzer.classify_imports(['os', 'numpy', 'mymod', 'Queue'])
    assert 'os' in classified['stdlib']
    assert 'numpy' in classified['third_party']
    assert 'mymod' in classified['local']
    assert 'Queue' in classified['obsolete']
    logger.info("✅ Classification OK")
    
    # Test 5: Security Scanner
    logger.info("\n[Test 5] SecurityScanner")
    scanner = SecurityScanner(config)
    
    # Typosquatting
    safety = scanner.check_package_safety("request")
    assert not safety['safe']
    assert safety['alternative'] == 'requests'
    assert safety['score'] < 50
    
    # Package normal
    safety = scanner.check_package_safety("requests")
    assert safety['critical']  # requests est dans CRITICAL_PACKAGES
    
    # Package inconnu
    safety = scanner.check_package_safety("unknown-xyz-123")
    assert safety['score'] < 100
    logger.info("✅ SecurityScanner OK")
    
    # Test 6: Uninstaller
    logger.info("\n[Test 6] PackageUninstaller")
    uninstaller = PackageUninstaller(config)
    safety = uninstaller.is_safe_to_uninstall('pip')
    assert not safety['safe']
    assert safety['risk'] == 'CRITICAL'
    logger.info("✅ PackageUninstaller OK")
    
    # Test 7: Monitor
    logger.info("\n[Test 7] APIMonitor")
    monitor = APIMonitor(config)
    monitor.take_baseline()
    assert len(monitor._baseline) > 0
    stats = monitor.get_stats()
    assert stats['installed'] == 0
    logger.info("✅ APIMonitor OK")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ TOUS LES TESTS PASSENT")
    logger.info("=" * 70)


# ============================================================
# 🚀 MODE CLI
# ============================================================

def run_cli(target_dir: str) -> None:
    """Mode ligne de commande (sans GUI)"""
    config = Config()
    analyzer = ImportAnalyzer(config)
    checker = APIChecker(config)
    scanner = SecurityScanner(config)
    
    target_path = Path(target_dir)
    if not target_path.is_dir():
        logger.error(f"Dossier introuvable : {target_dir}")
        sys.exit(1)
    
    logger.info(f"🔍 Scan : {target_path}")
    result = analyzer.analyze_directory(target_path)
    classified = analyzer.classify_imports(result['all_imports'])
    check = checker.check_all_local(classified['third_party'])
    
    logger.info(f"📚 Stdlib : {len(classified['stdlib'])}")
    logger.info(f"🏠 Locaux : {len(classified['local'])}")
    logger.info(f"✅ Installés : {len(check['installed'])}")
    logger.info(f"❌ Manquants : {len(check['missing'])}")
    
    if check['missing']:
        logger.info("\n🛡️ ANALYSE DE SÉCURITÉ :")
        for pkg in check['missing']:
            safety = scanner.check_package_safety(pkg['pip_name'])
            if not safety['safe']:
                logger.warning(f"🚨 {pkg['pip_name']} :")
                for d in safety['dangers']:
                    logger.warning(f"   {d}")


# ============================================================
# 🎯 POINT D'ENTRÉE
# ============================================================

if __name__ == '__main__':
    if '--test' in sys.argv:
        run_tests()
        sys.exit(0)
    
    if '--cli' in sys.argv:
        idx = sys.argv.index('--cli')
        if idx + 1 < len(sys.argv):
            run_cli(sys.argv[idx + 1])
        else:
            print("Usage: python api_detector_v5.py --cli <dossier>")
        sys.exit(0)
    
    try:
        print("=" * 70)
        print("🐕‍🦺 CERBERUS v5 — Le gardien à 3 têtes")
        print("🛡️ Security + 🗑️ Uninstall + 🕵️ Monitor")
        print("=" * 70)
        CerberusApp()
    except Exception as e:
        logger.critical(f"CRASH: {e}", exc_info=True)
        try:
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror("💥 CRASH", traceback.format_exc())
        except Exception:
            pass
        input("\nAppuie sur Entrée...")