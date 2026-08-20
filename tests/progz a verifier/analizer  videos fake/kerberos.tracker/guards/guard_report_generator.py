#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📊 GUARD REPORT GENERATOR v3.2 — SÉCURISÉ (Anti-XSS)"""
import webbrowser, logging, json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus, urlparse
from html import escape # ✅ AJOUT CRITIQUE
logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

def sanitize_html(text: str) -> str:
    return escape(str(text), quote=True) if text else ""

def validate_url(url: str) -> str:
    if not url or not isinstance(url, str): return ""
    url = url.strip()
    if url.lower().startswith(("javascript:", "data:", "vbscript:")): return ""
    parsed = urlparse(url)
    return url if parsed.scheme in ("http", "https", "") else ""

def generate_report(stats: Dict[str, Any], analyzed_videos: Optional[List[Dict[str, Any]]] = None) -> bool:
    try:
        video_stats = stats.get('video_analyzer', {})
        total = video_stats.get('total', 0)
        pct_susp = (video_stats.get('suspicious', 0) / total * 100) if total > 0 else 0
        
        risk_level, risk_color = ("ÉLEVÉ ⚠️", "#ff5252") if pct_susp > 20 else ("MODÉRÉ ⚡", "#ff9800") if pct_susp > 5 else ("FAIBLE ✅", "#4CAF50")

        videos_table_html = ""
        if analyzed_videos:
            videos_table_html = """<div class="section"><h2>📋 Vidéos Analysées</h2><div style="overflow-x: auto;"><table class="videos-table"><thead><tr><th>Heure</th><th>Score</th><th>Classification</th><th>Détails</th><th>Appareil</th><th>Filigrane</th><th>Liens OSINT</th></tr></thead><tbody>"""
            for video in analyzed_videos:
                class_color = "#ff5252" if video.get('classification') == 'SUSPICIOUS' else "#ff9800" if video.get('classification') == 'UNCERTAIN' else "#4CAF50"
                class_label = "🤖 IA PROBABLE" if video.get('classification') == 'SUSPICIOUS' else "🎨 Retouchée" if video.get('classification') == 'UNCERTAIN' else "✅ Réelle"
                
                # ✅ SANITIZATION DE TOUTES LES ENTRÉES UTILISATEUR
                safe_details = sanitize_html(video.get('details', 'N/A'))
                safe_ai = sanitize_html(video.get('ai_type', 'N/A'))
                safe_cam = sanitize_html(video.get('camera_type', 'N/A'))
                wm_icon = "✓" if video.get('watermark') else "—"
                
                page_url = validate_url(video.get('page_url', ''))
                if page_url:
                    domain = sanitize_html(urlparse(page_url).netloc)
                    osint_links = f'<a href="{escape(page_url)}" target="_blank" rel="noopener noreferrer" class="osint-btn">🌐</a> <a href="https://yandex.com/images/search?url={quote_plus(page_url)}" target="_blank" rel="noopener noreferrer" class="osint-btn">🔍</a> <a href="https://www.whois.com/whois/{domain}" target="_blank" rel="noopener noreferrer" class="osint-btn">🔗</a>'
                else:
                    osint_links = '<span style="color: #666;">N/A</span>'
                
                videos_table_html += f"""<tr><td>{sanitize_html(video.get('timestamp', 'N/A'))}</td><td style="color: {class_color}; font-weight: bold;">{int(video.get('score', 0))}/100</td><td style="color: {class_color}; font-weight: bold;">{class_label}</td><td style="font-size: 0.85em; color: #ccc;">{safe_details}</td><td>{safe_ai}</td><td>{safe_cam}</td><td>{wm_icon}</td><td>{osint_links}</td></tr>"""
            videos_table_html += "</tbody></table></div></div>"

        html_content = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>Kerberos Rapport</title><meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' data:; style-src 'unsafe-inline';"><style>body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#1e1e2e,#161a2e);color:#fff;padding:20px}}.container{{max-width:1400px;margin:0 auto}}.header{{background:linear-gradient(135deg,#00ffcc,#00cc99);color:#1e1e2e;padding:40px;border-radius:15px;margin-bottom:30px;text-align:center}}.risk-banner{{background:{risk_color};padding:25px;border-radius:10px;margin-bottom:30px;text-align:center;font-size:1.3em;font-weight:bold}}.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:30px}}.stat-card{{background:#2d2d3d;padding:25px;border-radius:12px;text-align:center}}.stat-value{{font-size:3em;font-weight:bold;margin:10px 0}}.section{{background:#2d2d3d;padding:30px;border-radius:12px;margin-bottom:30px}}.section h2{{color:#00ffcc;border-bottom:2px solid #00ffcc;padding-bottom:10px;margin-bottom:20px}}.videos-table{{width:100%;border-collapse:collapse;background:#1e1e2e;border-radius:8px;overflow:hidden}}.videos-table th{{background:linear-gradient(135deg,#00ffcc,#00cc99);color:#1e1e2e;padding:15px 12px;text-align:left}}.videos-table td{{padding:12px;border-bottom:1px solid #3d3d4d;font-size:0.9em}}.osint-btn{{display:inline-block;padding:5px 10px;margin:2px;border-radius:5px;text-decoration:none;font-weight:bold;background:#00ffcc;color:#1e1e2e}}</style></head><body><div class="container"><div class="header"><h1>🛡️ KERBEROS VIDEO ANALYZER</h1><p>Rapport d'Investigation Numérique</p><p>{datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p></div><div class="risk-banner">🛡️ Niveau de Risque: {risk_level}</div><div class="stats-grid"><div class="stat-card"><div>Total</div><div class="stat-value" style="color:#00ffcc">{total}</div></div><div class="stat-card"><div>🤖 IA Probable</div><div class="stat-value" style="color:#ff5252">{video_stats.get('suspicious', 0)}</div></div></div>{videos_table_html}<div style="text-align:center;padding:30px;color:#666"><p><strong>Kerberos Video Analyzer v7.3</strong></p><p>Licence GPLv3 • Victor Pozen</p></div></div></body></html>"""
        
        report_file = REPORTS_DIR / f"video_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        report_file.write_text(html_content, encoding='utf-8')
        webbrowser.open(report_file.resolve().as_uri())
        logger.info(f"✅ Rapport sécurisé généré: {report_file}")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport: {e}")
        return False

def start_guard(kerberos_app=None): return object()
def stop_guard(): pass
def get_stats(): return {}