#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Victor Pozen — GPLv3
"""
API Detector v5.3 — CERBERUS ENGINE (MODULAIRE)
================================================
Engine pur — Sans GUI
✅ v5.3 : Architecture modulaire (GUI séparée)
"""
import os, sys, ast, json, logging, threading, subprocess, importlib.util
from pathlib import Path
from typing import Set, Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
from dataclasses import dataclass, field
import re

# ============================================================
# 🔧 LOGGING
# ============================================================
def setup_logger(name: str = "cerberus_engine") -> logging.Logger:
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
# 📋 CONFIGURATION
# ============================================================
@dataclass
class Config:
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
    IMPORT_TO_PIP: Dict[str, Optional[str]] = field(default_factory=lambda: {
        'PIL': 'Pillow', 'cv2': 'opencv-python', 'sklearn': 'scikit-learn',
        'skimage': 'scikit-image', 'bs4': 'beautifulsoup4', 'yaml': 'PyYAML',
        'attr': 'attrs', 'OpenSSL': 'pyOpenSSL',
        'win32api': 'pywin32', 'win32com': 'pywin32', 'win32con': 'pywin32',
        'win32process': 'pywin32', 'win32service': 'pywin32', 'win32gui': 'pywin32',
        'msvcrt': None, 'pystray': 'pystray', 'cryptography': 'cryptography',
        'numpy': 'numpy', 'psutil': 'psutil', 'pydub': 'pydub', 'rsa': 'rsa',
        'yara': 'yara-python', 'pyftpdlib': 'pyftpdlib',
        'plyer': 'plyer', 'watchdog': 'watchdog', 'win10toast': 'win10toast',
        'requests': 'requests',
    })
    PROTECTED_PACKAGES: Set[str] = field(default_factory=lambda: {
        'pip', 'setuptools', 'wheel', 'distribute', 'pkg-resources',
        'pkg_resources', 'importlib-metadata', 'zipp', 'typing-extensions',
        'certifi', 'charset-normalizer', 'idna', 'urllib3', 'requests',
        'six', 'packaging', 'pyparsing', 'colorama', 'tomli', 'tomllib',
    })
    PIP_INSTALL_TIMEOUT: int = 600
    PIP_UNINSTALL_TIMEOUT: int = 60
    IGNORE_DIRS: Set[str] = field(default_factory=lambda: {
        'venv', 'env', '__pycache__', '.git', '.idea', '.vscode', 'node_modules'
    })

# ============================================================
# ️ VALIDATEUR
# ============================================================
class PackageValidator:
    VALID_PACKAGE_NAME = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$')
    
    @classmethod
    def sanitize(cls, name: str) -> Optional[str]:
        if not name or len(name) > 200 or not cls.VALID_PACKAGE_NAME.match(name):
            return None
        return name

# ============================================================
# 🧠 ANALYZER
# ============================================================
class ImportVisitor(ast.NodeVisitor):
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
    def __init__(self, config: Config):
        self.config = config
        self.local_modules: Set[str] = set()
        self._lock = threading.Lock()
    
    def detect_local_modules(self, dir_path: Path) -> Set[str]:
        local = set()
        for py_file in dir_path.glob("*.py"):
            local.add(py_file.stem)
        for sub_dir in dir_path.iterdir():
            if sub_dir.is_dir() and not sub_dir.name.startswith('.'):
                if any(sub_dir.glob("*.py")):
                    local.add(sub_dir.name)
        return local
    
    def analyze_directory(self, dir_path: Path) -> Dict[str, Any]:
        with self._lock:
            self.local_modules = self.detect_local_modules(dir_path)
        
        results = {'directory': str(dir_path), 'files_scanned': 0, 'all_imports': set()}
        
        for py_file in dir_path.rglob('*.py'):
            if any(part.startswith('.') for part in py_file.parts):
                continue
            results['files_scanned'] += 1
            try:
                code = py_file.read_text(encoding='utf-8', errors='ignore')
                tree = ast.parse(code, filename=str(py_file))
                visitor = ImportVisitor()
                visitor.visit(tree)
                results['all_imports'].update(visitor.imports)
            except Exception as e:
                logger.error(f"Erreur {py_file}: {e}")
        
        results['all_imports'] = sorted(results['all_imports'])
        return results
    
    def classify_imports(self, imports: List[str]) -> Dict[str, List[str]]:
        stdlib, third_party, local = [], [], []
        for imp in imports:
            if imp in self.local_modules:
                local.append(imp)
            elif imp in self.config.STDLIB_MODULES or imp.startswith('_'):
                stdlib.append(imp)
            else:
                third_party.append(imp)
        return {'stdlib': sorted(stdlib), 'third_party': sorted(third_party), 'local': sorted(local)}

# ============================================================
# 🔍 CHECKER
# ============================================================
class APIChecker:
    def __init__(self, config: Config):
        self.config = config
        self.installed_packages = self._get_installed_packages()
    
    def _get_installed_packages(self) -> Dict[str, str]:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                normalized = {}
                for pkg in packages:
                    name = pkg['name'].lower()
                    normalized[name] = pkg['version']
                    if name == 'pillow': normalized['pil'] = pkg['version']
                    if name == 'yara-python': normalized['yara'] = pkg['version']
                return normalized
        except Exception as e:
            logger.error(f"pip list: {e}")
        return {}
    
    def check_all_local(self, third_party_imports: List[str]) -> Dict[str, List[Dict]]:
        results = {'installed': [], 'missing': [], 'skipped': []}
        for module in third_party_imports:
            pip_name = self.config.IMPORT_TO_PIP.get(module, module)
            if pip_name is None:
                results['skipped'].append({'module': module, 'reason': 'Module natif'})
                continue
            
            try:
                spec = importlib.util.find_spec(module)
                if spec:
                    version = self.installed_packages.get(module.lower(), '✓')
                    results['installed'].append({'module': module, 'pip_name': pip_name, 'version': version})
                else:
                    results['missing'].append({'module': module, 'pip_name': pip_name})
            except Exception:
                results['missing'].append({'module': module, 'pip_name': pip_name})
        return results
    
    def install_package(self, package_name: str) -> bool:
        validated = PackageValidator.sanitize(package_name)
        if not validated:
            return False
        
        logger.info(f" Installation de {package_name}...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--user', '--quiet', validated],
                capture_output=True, text=True, timeout=self.config.PIP_INSTALL_TIMEOUT
            )
            if result.returncode == 0:
                logger.info(f"✅ {package_name} installé")
                return True
            else:
                logger.error(f"❌ Échec: {result.stderr.strip()[:100]}")
                return False
        except Exception as e:
            logger.error(f"💥 Erreur: {e}")
            return False

# ============================================================
# 🛡️ GUARD MANAGER (via Cortex)
# ============================================================
class GuardManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.guards_dir = base_dir / "guards"
        self.cortex = None
        self._load_cortex()
    
    def _load_cortex(self):
        cortex_path = self.guards_dir / "guard_cortex.py"
        if cortex_path.exists():
            try:
                spec = importlib.util.spec_from_file_location("guard_cortex", cortex_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self.cortex = mod
                logger.info("✅ Cortex chargé")
            except Exception as e:
                logger.error(f"❌ Erreur chargement Cortex: {e}")
    
    def reload_guards(self):
        if self.cortex and hasattr(self.cortex, 'reload_guards'):
            return self.cortex.reload_guards()
        return []

# ============================================================
# 📊 REPORT GENERATOR
# ============================================================
class ReportGenerator:
    @staticmethod
    def generate_txt(results: Dict, output_path: Path) -> None:
        lines = [
            "=" * 70, "CERBERUS v5.3 — RAPPORT", "=" * 70,
            f"Dossier : {results['target']}",
            f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Fichiers : {results['files_scanned']}", "",
            f"📚 Stdlib : {len(results['stdlib'])}",
            f"🔌 Tiers : {len(results['third_party'])}",
            f"🏠 Locaux : {len(results['local'])}", "",
            "-" * 70, "✅ INSTALLÉS", "-" * 70,
        ]
        for p in results['installed']:
            lines.append(f"  ✓ {p['module']} (pip: {p['pip_name']}) v{p['version']}")
        lines += ["", "-" * 70, " MANQUANTS", "-" * 70]
        for p in results['missing']:
            lines.append(f"  ✗ {p['module']} → pip install {p['pip_name']}")
        lines += ["", "=" * 70]
        
        output_path.write_text('\n'.join(lines), encoding='utf-8')
        logger.info(f"💾 Rapport généré : {output_path}")

# ============================================================
# 🎯 CERBERUS ENGINE (API PUBLIQUE)
# ============================================================
class CerberusEngine:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.config = Config()
        self.analyzer = ImportAnalyzer(self.config)
        self.checker = APIChecker(self.config)
        self.guard_manager = GuardManager(self.base_dir)
        self.report_gen = ReportGenerator()
        self.analysis_results: Optional[Dict] = None
        self._lock = threading.Lock()
        
        logger.info("🐕‍ Cerberus Engine v5.3 prêt")
    
    def scan_directory(self, target_path: Path) -> Dict[str, Any]:
        """Scanne un dossier et retourne les résultats"""
        logger.info(f" Scan de {target_path}...")
        
        result = self.analyzer.analyze_directory(target_path)
        classified = self.analyzer.classify_imports(result['all_imports'])
        local_check = self.checker.check_all_local(classified['third_party'])
        
        with self._lock:
            self.analysis_results = {
                'target': str(target_path),
                'files_scanned': result['files_scanned'],
                'stdlib': classified['stdlib'],
                'third_party': classified['third_party'],
                'local': classified['local'],
                'installed': local_check['installed'],
                'missing': local_check['missing'],
            }
        
        logger.info(f"✅ Scan terminé: {len(local_check['installed'])} installés, {len(local_check['missing'])} manquants")
        return self.analysis_results
    
    def install_packages(self, packages: List[str], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Installe une liste de packages"""
        logger.info(f"📦 Installation de {len(packages)} package(s)...")
        
        success, failed = [], []
        for i, pkg in enumerate(packages):
            if progress_callback:
                progress_callback(i, len(packages), pkg)
            
            if self.checker.install_package(pkg):
                success.append(pkg)
            else:
                failed.append(pkg)
        
        return {'success': success, 'failed': failed}
    
    def generate_report(self, output_path: Path) -> bool:
        """Génère un rapport TXT"""
        if not self.analysis_results:
            logger.error("❌ Aucune analyse disponible")
            return False
        
        self.report_gen.generate_txt(self.analysis_results, output_path)
        return True
    
    def reload_guards(self):
        """Recharge les guards via Cortex"""
        return self.guard_manager.reload_guards()

# Point d'entrée pour tests
if __name__ == '__main__':
    print("=" * 70)
    print("🐕‍🦺 CERBERUS ENGINE v5.3 — MODE TEST")
    print("=" * 70)
    
    engine = CerberusEngine()
    print("✅ Engine initialisé")
    print("💡 Utilise gui_manager.py pour l'interface graphique")