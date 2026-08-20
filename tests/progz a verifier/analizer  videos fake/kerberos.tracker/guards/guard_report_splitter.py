#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 GUARD REPORT SPLITTER — Fractionneur de Rapports HTML
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 1.0.0
Author: Victor Pozen
License: GPLv3

Fractionne automatiquement les rapports HTML en chunks configurables (50-500 vidéos).
S'installe sans modifier les fichiers existants.
"""
import webbrowser
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus, urlparse
from guards.guard_interface import GuardInterface

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


class ReportSplitterGuard(GuardInterface):
    """Guard qui fractionne les rapports HTML en chunks configurables"""
    
    def __init__(self, kerberos_app=None):
        super().__init__("report_splitter")
        self.kerberos = kerberos_app
        self.is_running = False
        
        # Configuration par défaut (50 vidéos par rapport)
        self.chunk_size = 50
        
        # Stats
        self.stats = {
            "reports_generated": 0,
            "total_videos_split": 0,
            "last_chunk_size": 50,
            "last_report_path": ""
        }
        
        logger.info(f"📊 ReportSplitterGuard initialisé (chunk_size: {self.chunk_size})")
    
    def set_chunk_size(self, size: int) -> None:
        """Définit la taille des chunks (50-500)"""
        self.chunk_size = max(50, min(500, int(size)))
        self.stats["last_chunk_size"] = self.chunk_size
        logger.info(f"📊 Chunk size ajusté à {self.chunk_size} vidéos")
    
    def generate_split_reports(self, analyzed_videos: List[Dict[str, Any]], chunk_size: Optional[int] = None) -> List[str]:
        """
        Génère des rapports fractionnés.
        Retourne la liste des chemins des rapports générés.
        """
        if not analyzed_videos:
            logger.warning("Aucune vidéo à analyser")
            return []
        
        # Utiliser le chunk_size passé en paramètre ou celui par défaut
        if chunk_size:
            self.set_chunk_size(chunk_size)
        
        # Découper en chunks
        chunks = [analyzed_videos[i:i + self.chunk_size] 
                  for i in range(0, len(analyzed_videos), self.chunk_size)]
        
        generated_reports = []
        
        for chunk_index, chunk in enumerate(chunks, 1):
            report_path = self._generate_chunk_report(chunk, chunk_index, len(chunks))
            if report_path:
                generated_reports.append(report_path)
        
        self.stats["reports_generated"] += len(generated_reports)
        self.stats["total_videos_split"] += len(analyzed_videos)
        
        logger.info(f"📊 {len(generated_reports)} rapports générés ({len(analyzed_videos)} vidéos)")
        
        # Ouvrir le premier rapport
        if generated_reports:
            webbrowser.open(Path(generated_reports[0]).resolve().as_uri())
        
        return generated_reports
    
    def _generate_chunk_report(self, videos: List[Dict[str, Any]], chunk_index: int, total_chunks: int) -> Optional[str]:
        """Génère un rapport HTML pour un chunk"""
        try:
            # Statistiques du chunk
            total = len(videos)
            real = sum(1 for v in videos if v.get('classification') == 'REAL')
            suspicious = sum(1 for v in videos if v.get('classification') == 'SUSPICIOUS')
            uncertain = sum(1 for v in videos if v.get('classification') == 'UNCERTAIN')
            
            pct_real = (real / total * 100) if total > 0 else 0
            pct_susp = (suspicious / total * 100) if total > 0 else 0
            pct_unc = (uncertain / total * 100) if total > 0 else 0
            
            # Niveau de risque
            if pct_susp > 20:
                risk_level, risk_color = "ÉLEVÉ ⚠️", "#ff5252"
            elif pct_susp > 5:
                risk_level, risk_color = "MODÉRÉ ⚡", "#ff9800"
            else:
                risk_level, risk_color = "FAIBLE ✅", "#4CAF50"
            
            # Tableau des vidéos
            videos_table_html = ""
            if videos:
                videos_table_html = """
                <div class="section">
                    <h2>📋 Vidéos Analysées (Chunk {chunk_index}/{total_chunks})</h2>
                    <div style="overflow-x: auto;">
                        <table class="videos-table">
                            <thead>
                                <tr>
                                    <th>Heure</th>
                                    <th>Score</th>
                                    <th>Classification</th>
                                    <th>Détails</th>
                                    <th>Type IA</th>
                                    <th>Appareil</th>
                                    <th>Filigrane</th>
                                    <th>Liens OSINT</th>
                                </tr>
                            </thead>
                            <tbody>
                """.format(chunk_index=chunk_index, total_chunks=total_chunks)
                
                for video in videos:
                    if video.get('classification') == 'SUSPICIOUS':
                        class_color = "#ff5252"
                        class_label = "🤖 IA PROBABLE"
                    elif video.get('classification') == 'UNCERTAIN':
                        class_color = "#ff9800"
                        class_label = " Retouchée"
                    else:
                        class_color = "#4CAF50"
                        class_label = "✅ Réelle"
                    
                    wm_icon = "✓" if video.get('watermark') else "—"
                    
                    # Liens OSINT
                    page_url = video.get('page_url', '')
                    if page_url and page_url.startswith('http'):
                        encoded_url = quote_plus(page_url)
                        domain = urlparse(page_url).netloc
                        osint_links = f"""
                            <a href="{page_url}" target="_blank" class="osint-btn" title="Source">🌐</a>
                            <a href="https://yandex.com/images/search?rpt=imageview&url={encoded_url}" target="_blank" class="osint-btn" title="Yandex">🔍</a>
                            <a href="https://www.whois.com/whois/{domain}" target="_blank" class="osint-btn" title="Whois">🔗</a>
                        """
                    else:
                        osint_links = '<span style="color: #666;">N/A</span>'
                    
                    videos_table_html += f"""
                        <tr>
                            <td>{video.get('timestamp', 'N/A')}</td>
                            <td style="font-weight: bold; color: {class_color};">{video.get('score', 0)}/100</td>
                            <td style="color: {class_color}; font-weight: bold;">{class_label}</td>
                            <td style="font-size: 0.85em; color: #ccc;">{video.get('details', 'N/A')}</td>
                            <td>{video.get('ai_type', 'N/A')}</td>
                            <td>{video.get('camera_type', 'N/A')}</td>
                            <td>{wm_icon}</td>
                            <td>{osint_links}</td>
                        </tr>
                    """
                
                videos_table_html += """
                            </tbody>
                        </table>
                    </div>
                </div>
                """
            
            # HTML complet
            html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kerberos Video Analyzer - Rapport {chunk_index}/{total_chunks}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #161a2e 100%);
            color: #fff;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #00ffcc 0%, #00cc99 100%);
            color: #1e1e2e;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        }}
        .risk-banner {{
            background: {risk_color};
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
            font-size: 1.3em;
            font-weight: bold;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #2d2d3d;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
        }}
        .stat-card.total {{ border-top: 4px solid #00ffcc; }}
        .stat-card.real {{ border-top: 4px solid #4CAF50; }}
        .stat-card.suspicious {{ border-top: 4px solid #ff5252; }}
        .stat-card.uncertain {{ border-top: 4px solid #ff9800; }}
        .stat-value {{ font-size: 3em; font-weight: bold; margin: 10px 0; }}
        .section {{
            background: #2d2d3d;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #00ffcc;
            border-bottom: 2px solid #00ffcc;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .videos-table {{
            width: 100%;
            border-collapse: collapse;
            background: #1e1e2e;
            border-radius: 8px;
            overflow: hidden;
        }}
        .videos-table th {{
            background: linear-gradient(135deg, #00ffcc 0%, #00cc99 100%);
            color: #1e1e2e;
            padding: 15px 12px;
            text-align: left;
            font-weight: bold;
        }}
        .videos-table td {{
            padding: 12px;
            border-bottom: 1px solid #3d3d4d;
            font-size: 0.9em;
        }}
        .videos-table tr:hover {{ background: #2d2d3d; }}
        .osint-btn {{
            display: inline-block;
            padding: 5px 10px;
            margin: 2px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            background: #00ffcc;
            color: #1e1e2e;
        }}
        .osint-btn:hover {{ opacity: 0.8; }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            margin-top: 40px;
        }}
        .chunk-info {{
            background: #1e1e2e;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            color: #00ffcc;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ KERBEROS VIDEO ANALYZER</h1>
            <p>Rapport Fractionné — Chunk {chunk_index}/{total_chunks}</p>
            <p style="margin-top: 10px; font-size: 0.9em;">📅 {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
        </div>
        
        <div class="chunk-info">
             Chunk {chunk_index} sur {total_chunks} — {total} vidéos analysées
        </div>
        
        <div class="risk-banner">
            🛡️ Niveau de Risque: {risk_level}
        </div>
        
        <div class="stats-grid">
            <div class="stat-card total">
                <div>Total du Chunk</div>
                <div class="stat-value" style="color: #00ffcc;">{total}</div>
            </div>
            <div class="stat-card real">
                <div>✅ Réelles</div>
                <div class="stat-value" style="color: #4CAF50;">{real}</div>
                <div>{pct_real:.1f}%</div>
            </div>
            <div class="stat-card suspicious">
                <div>🤖 IA Probable</div>
                <div class="stat-value" style="color: #ff5252;">{suspicious}</div>
                <div>{pct_susp:.1f}%</div>
            </div>
            <div class="stat-card uncertain">
                <div>🎨 Retouchées</div>
                <div class="stat-value" style="color: #ff9800;">{uncertain}</div>
                <div>{pct_unc:.1f}%</div>
            </div>
        </div>
        
        {videos_table_html}
        
        <div class="footer">
            <p><strong>Kerberos Video Analyzer v7.2</strong></p>
            <p>Licence GPLv3 • Victor Pozen • github.com/victorpozen</p>
            <p style="margin-top: 10px; font-size: 0.85em; color: #ff9800;">
                ⚠️ Rapport fractionné automatiquement par ReportSplitterGuard
            </p>
        </div>
    </div>
</body>
</html>
            """
            
            # Sauvegarde
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = REPORTS_DIR / f"video_report_chunk_{chunk_index}_of_{total_chunks}_{timestamp}.html"
            report_file.write_text(html_content, encoding='utf-8')
            
            self.stats["last_report_path"] = str(report_file)
            logger.info(f"📊 Rapport chunk {chunk_index}/{total_chunks} généré: {report_file}")
            
            return str(report_file)
        
        except Exception as e:
            logger.error(f"❌ Erreur génération rapport chunk: {e}")
            return None
    
    def start(self):
        self.is_running = True
        logger.info("📊 ReportSplitterGuard démarré")
    
    def stop(self):
        self.is_running = False
        logger.info(" ReportSplitterGuard arrêté")
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()


# Fonctions globales pour le GuardManager
_guard_instance = None

def start_guard(kerberos_app=None):
    global _guard_instance
    _guard_instance = ReportSplitterGuard(kerberos_app)
    return _guard_instance

def stop_guard():
    global _guard_instance
    if _guard_instance:
        _guard_instance.stop()

def get_stats():
    global _guard_instance
    return _guard_instance.get_stats() if _guard_instance else {}