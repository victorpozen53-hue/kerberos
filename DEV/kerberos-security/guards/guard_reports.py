#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  KERBEROS ULTIMATE v4.2 — Guard Reports
#  Copyright (C) 2025 Victor Pozen
# ============================================================================
#  LICENCE : GPLv3
#  AUTEUR  : Victor Pozen
#  VERSION : 4.2 Ultimate
#  DATE    : 2025
#  🔗 https://github.com/victorpozen
#  💰 https://liberapay.com/EthicalKerberos/
# ============================================================================
"""
📊 Guard Reports — Gestion centralisée des rapports par guard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CE MODULE EST ACTIF :
- Crée automatiquement un dossier par guard au premier rapport
- Base commune : logs.full.option/logs_guards/
- Chaque guard a son sous-dossier dédié
- Export JSON (machine) + HTML (humain) + TXT (simple)
- Nettoyage automatique des anciens rapports (30 jours)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Copyright (C) 2025 Victor Pozen — GPLv3
"""

from pathlib import Path
from datetime import datetime
import json
import os
import sys

# ============================================================================
# === INTÉGRATION KERBEROS ===================================================
# ============================================================================
try:
    _kerberos_main = sys.modules.get("__main__")
    _GUARD_METRICS: dict = getattr(_kerberos_main, "_GUARD_METRICS", {})
except Exception:
    _GUARD_METRICS = {}

_MODULE_NAME = Path(__file__).name

def _publish_metric(level: float):
    """Publie le niveau d'activité du guard (0.0 à 1.0)"""
    _GUARD_METRICS[_MODULE_NAME] = max(0.0, min(1.0, level))

# ============================================================================
# === CONFIGURATION ==========================================================
# ============================================================================
# ← BASE COMMUNE (configurable)
KERBEROS_ROOT = Path(__file__).parent.parent
LOGS_BASE = KERBEROS_ROOT / "logs.full.option" / "logs_guards"
GUARD_LOGS_DIR = LOGS_BASE / "guard_reports"

# Création de la base au premier appel
LOGS_BASE.mkdir(parents=True, exist_ok=True)
GUARD_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# === FONCTIONS PUBLIQUES ====================================================
# ============================================================================

def get_guard_reports_dir(guard_name: str) -> Path:
    """
    Retourne le dossier de rapports d'un guard (créé automatiquement)
    
    Args:
        guard_name: Nom du guard (ex: "guard_plasma_shield")
    
    Returns:
        Path du dossier du guard
    """
    # ← CRÉATION AUTO DU DOSSIER GUARD
    reports_path = LOGS_BASE / guard_name
    reports_path.mkdir(parents=True, exist_ok=True)
    return reports_path

def save_guard_report(guard_name: str, data: dict, prefix: str = "report", 
                      export_html: bool = True, export_txt: bool = True) -> dict:
    """
    Sauvegarde un rapport pour un guard (dossier créé auto)
    
    Args:
        guard_name: Nom du guard (ex: "guard_plasma_shield")
        data: Données du rapport (dict)
        prefix: Préfixe du fichier (ex: "plasma_alert")
        export_html: Exporter en HTML (défaut: True)
        export_txt: Exporter en TXT (défaut: True)
    
    Returns:
        Dict avec les chemins des fichiers créés
    """
    # ← CRÉATION AUTO DU DOSSIER GUARD
    reports_dir = get_guard_reports_dir(guard_name)
    
    # Nom du fichier avec timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    base_name = f"{prefix}_{timestamp}"
    
    files_created = {
        "guard": guard_name,
        "timestamp": timestamp,
        "json": None,
        "html": None,
        "txt": None
    }
    
    # ← SAUVEGARDE JSON (pour machine)
    json_path = reports_dir / f"{base_name}.json"
    json_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    files_created["json"] = str(json_path)
    
    # ← SAUVEGARDE HTML (pour humain — PLUS LISIBLE)
    if export_html:
        html_path = reports_dir / f"{base_name}.html"
        _export_html(data, html_path, guard_name)
        files_created["html"] = str(html_path)
    
    # ← SAUVEGARDE TXT (pour lecture rapide)
    if export_txt:
        txt_path = reports_dir / f"{base_name}.txt"
        _export_txt(data, txt_path, guard_name)
        files_created["txt"] = str(txt_path)
    
    return files_created

def _export_html(data: dict, filepath: Path, guard_name: str):
    """Exporte le rapport en HTML lisible"""
    
    # Style CSS intégré
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport {guard_name} — {data.get('timestamp', 'N/A')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #0a0f1a;
            color: #00ffcc;
            font-family: 'Consolas', monospace;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            background: linear-gradient(135deg, #16213e 0%, #1a1a2e 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            border: 2px solid #00ffcc;
            text-align: center;
        }}
        header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
            text-shadow: 0 0 10px #00ffcc;
        }}
        .timestamp {{
            color: #607d8b;
            font-size: 14px;
        }}
        .section {{
            background: #1a1a2e;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #00ffcc;
        }}
        .section h2 {{
            margin-bottom: 15px;
            color: #00ffcc;
        }}
        .data-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .data-card {{
            background: #16213e;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #2d2d3d;
        }}
        .data-label {{
            color: #607d8b;
            font-size: 12px;
            margin-bottom: 5px;
        }}
        .data-value {{
            color: #00ffcc;
            font-size: 18px;
            font-weight: bold;
        }}
        .alert {{
            background: #2a1a1a;
            border-left: 4px solid #ff5252;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .alert.warning {{
            background: #2a251a;
            border-left-color: #ff9800;
        }}
        .alert.info {{
            background: #1a2a2a;
            border-left-color: #00ffcc;
        }}
        .alert.success {{
            background: #1a2a1a;
            border-left-color: #4CAF50;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #2d2d3d;
        }}
        th {{
            background: #16213e;
            color: #00ffcc;
        }}
        tr:hover {{
            background: #16213e;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            margin-top: 30px;
            border-top: 1px solid #2d2d3d;
            color: #607d8b;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-success {{ background: #2d7b5a; color: white; }}
        .badge-warning {{ background: #7b5a2d; color: white; }}
        .badge-error {{ background: #7b2d2d; color: white; }}
        .badge-info {{ background: #2d5a7b; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ RAPPORT {guard_name.upper()}</h1>
            <p class="timestamp">📅 Généré le: {data.get('timestamp', datetime.now().isoformat())}</p>
        </header>
        
        {_generate_html_sections(data)}
        
        <div class="footer">
            <p>🛡️ KERBEROS ULTIMATE v4.2 — GPLv3 • Victor Pozen</p>
            <p>🔗 github.com/victorpozen</p>
        </div>
    </div>
</body>
</html>"""
    
    filepath.write_text(html_content, encoding="utf-8")

def _generate_html_sections(data: dict) -> str:
    """Génère les sections HTML dynamiquement selon les données"""
    sections = []
    
    # Section résumé
    if any(key in data for key in ["status", "guard", "action", "threats"]):
        summary_html = '<div class="section"><h2>📊 Résumé</h2><div class="data-grid">'
        
        for key, value in data.items():
            if isinstance(value, (str, int, float)) and key not in ["details", "items", "list"]:
                badge_class = "badge-info"
                if "error" in str(value).lower() or "fail" in str(value).lower():
                    badge_class = "badge-error"
                elif "success" in str(value).lower() or "ok" in str(value).lower():
                    badge_class = "badge-success"
                elif "warn" in str(value).lower():
                    badge_class = "badge-warning"
                
                summary_html += f"""
                <div class="data-card">
                    <div class="data-label">{key.upper()}</div>
                    <div class="data-value"><span class="badge {badge_class}">{value}</span></div>
                </div>"""
        
        summary_html += '</div></div>'
        sections.append(summary_html)
    
    # Section détails (tableau)
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            table_html = f'<div class="section"><h2>📋 {key.upper()}</h2><table>'
            table_html += '<thead><tr>'
            
            # En-têtes
            if isinstance(value[0], dict):
                for col in value[0].keys():
                    table_html += f'<th>{col.upper()}</th>'
            else:
                table_html += '<th>VALEUR</th>'
            
            table_html += '</tr></thead><tbody>'
            
            # Lignes
            for item in value:
                table_html += '<tr>'
                if isinstance(item, dict):
                    for val in item.values():
                        table_html += f'<td>{val}</td>'
                else:
                    table_html += f'<td>{item}</td>'
                table_html += '</tr>'
            
            table_html += '</tbody></table></div>'
            sections.append(table_html)
        
        elif isinstance(value, dict) and key not in ["timestamp", "guard"]:
            dict_html = f'<div class="section"><h2>📁 {key.upper()}</h2><div class="data-grid">'
            for k, v in value.items():
                dict_html += f"""
                <div class="data-card">
                    <div class="data-label">{k.upper()}</div>
                    <div class="data-value">{v}</div>
                </div>"""
            dict_html += '</div></div>'
            sections.append(dict_html)
    
    return '\n'.join(sections)

def _export_txt(data: dict, filepath: Path, guard_name: str):
    """Exporte le rapport en TXT simple"""
    
    txt_content = f"""
╔════════════════════════════════════════════════════════════╗
║  🛡️ RAPPORT {guard_name.upper()}
╠════════════════════════════════════════════════════════════╣
║  📅 Généré le: {data.get('timestamp', datetime.now().isoformat())}
╚════════════════════════════════════════════════════════════╝

"""
    
    # Résumé
    txt_content += "📊 RÉSUMÉ :\n"
    txt_content += "─" * 60 + "\n"
    for key, value in data.items():
        if isinstance(value, (str, int, float)) and key not in ["details", "items", "list"]:
            txt_content += f"   • {key.upper()}: {value}\n"
    txt_content += "\n"
    
    # Détails
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            txt_content += f"📋 {key.upper()} :\n"
            txt_content += "─" * 60 + "\n"
            for i, item in enumerate(value, 1):
                if isinstance(item, dict):
                    txt_content += f"   [{i}]\n"
                    for k, v in item.items():
                        txt_content += f"      • {k}: {v}\n"
                else:
                    txt_content += f"   [{i}] {item}\n"
            txt_content += "\n"
        
        elif isinstance(value, dict) and key not in ["timestamp", "guard"]:
            txt_content += f"📁 {key.upper()} :\n"
            txt_content += "─" * 60 + "\n"
            for k, v in value.items():
                txt_content += f"   • {k}: {v}\n"
            txt_content += "\n"
    
    txt_content += """
╔════════════════════════════════════════════════════════════╗
║  🛡️ KERBEROS ULTIMATE v4.2 — GPLv3 • Victor Pozen        ║
║  🔗 github.com/victorpozen                                ║
╚════════════════════════════════════════════════════════════╝
"""
    
    filepath.write_text(txt_content, encoding="utf-8")

def get_guard_reports(guard_name: str, limit: int = 10) -> list:
    """
    Récupère les derniers rapports d'un guard
    
    Args:
        guard_name: Nom du guard
        limit: Nombre max de rapports à retourner
    
    Returns:
        Liste des Paths des rapports (triés par date décroissante)
    """
    reports_dir = get_guard_reports_dir(guard_name)
    
    if not reports_dir.exists():
        return []
    
    reports = sorted(
        reports_dir.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    return reports[:limit]

def clear_guard_reports(guard_name: str, older_than_days: int = 30) -> int:
    """
    Supprime les rapports anciens d'un guard
    
    Args:
        guard_name: Nom du guard
        older_than_days: Âge max en jours (par défaut 30)
    
    Returns:
        Nombre de fichiers supprimés
    """
    reports_dir = get_guard_reports_dir(guard_name)
    
    if not reports_dir.exists():
        return 0
    
    deleted = 0
    cutoff = datetime.now().timestamp() - (older_than_days * 86400)
    
    for report in reports_dir.glob("*"):
        if report.stat().st_mtime < cutoff:
            report.unlink()
            deleted += 1
    
    return deleted

def list_all_guards_reports() -> dict:
    """
    Liste tous les guards ayant des rapports
    
    Returns:
        Dict {guard_name: nombre_de_rapports}
    """
    guards_reports = {}
    
    if not LOGS_BASE.exists():
        return guards_reports
    
    for guard_dir in LOGS_BASE.iterdir():
        if guard_dir.is_dir():
            reports_count = len(list(guard_dir.glob("*.json")))
            if reports_count > 0:
                guards_reports[guard_dir.name] = reports_count
    
    return guards_reports

def get_all_reports_summary() -> dict:
    """
    Retourne un résumé de tous les rapports
    
    Returns:
        Dict avec stats globales
    """
    guards_reports = list_all_guards_reports()
    
    return {
        "total_guards": len(guards_reports),
        "total_reports": sum(guards_reports.values()),
        "guards": guards_reports,
        "base_path": str(LOGS_BASE),
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# === POINT D'ENTRÉE KERBEROS ================================================
# ============================================================================
def start_guard():
    """Point d'entrée pour Kerberos — Module de rapports"""
    _publish_metric(0.2)
    print("📊 [Guard Reports] Module de rapports centralisés actif")
    print(f"   └─ Base : {LOGS_BASE}")
    
    # Sauvegarde rapport initial
    _save_reports(get_stats())
    
    _publish_metric(0.1)
    return None

def get_stats() -> dict:
    """Stats pour l'onglet Guards"""
    summary = get_all_reports_summary()
    
    report = {
        "guard": "guard_reports",
        "timestamp": datetime.now().isoformat(),
        "status": "active",
        "total_guards": summary["total_guards"],
        "total_reports": summary["total_reports"],
        "guards_with_reports": summary["guards"],
        "base_path": str(LOGS_BASE),
        "logs_dir": str(GUARD_LOGS_DIR),
    }
    
    # Sauvegarde automatique des rapports
    _save_reports(report)
    
    return report

def stop_guard():
    """Arrêt propre du guard"""
    _publish_metric(0.0)
    print("📊 [Guard Reports] Module arrêté")

# ============================================================================
# === MODE STANDALONE ========================================================
# ============================================================================

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║  📊 GUARD REPORTS — Gestion des rapports par guard        ║
║                                                            ║
║  Base : logs.full.option/logs_guards/                     ║
║  Chaque guard a son dossier auto-créé                     ║
║                                                            ║
║  Formats exportés :                                       ║
║    • JSON → Machine (données brutes)                      ║
║    • HTML → Humain (rapport lisible avec style)           ║
║    • TXT  → Simple (lecture rapide)                       ║
║                                                            ║
║  Usage dans un guard :                                    ║
║    from guard_reports import save_guard_report            ║
║    save_guard_report("guard_plasma_shield", data)         ║
║                                                            ║
║  Licence : GPLv3 — Victor Pozen                           ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Démo
    summary = get_all_reports_summary()
    print(f"\n📊 RÉSUMÉ DES RAPPORTS :")
    print(f"   • Total guards : {summary['total_guards']}")
    print(f"   • Total rapports : {summary['total_reports']}")
    print(f"   • Base : {summary['base_path']}")
    
    if summary['guards']:
        print(f"\n📁 GUARDS AVEC RAPPORTS :")
        for guard, count in summary['guards'].items():
            print(f"   • {guard} : {count} rapport(s)")