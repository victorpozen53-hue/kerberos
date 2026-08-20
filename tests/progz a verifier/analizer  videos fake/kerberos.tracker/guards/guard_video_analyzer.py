#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ GUARD VIDEO ANALYZER v6.0 — DÉTECTION IA AVANCÉE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Version: 6.0.0 "Challenge Accepted"
Author: Victor Pozen
License: GPLv3

CORRECTIONS & AMÉLIORATIONS v6.0:
- ✅ FIX Nom: "video_analyzer" (minuscules)
- ✅ FIX Seuil: 65 par défaut (réaliste)
- ✅ FIX Scoring: Système de vote pondéré (3 niveaux)
- ✅ FIX Fermeture navigateur: len(contexts) == 0
- ✅ FIX Mémoire: Rotation auto (max 500 vidéos)
- ✅ NOUVEAU: Détection "perfection suspecte" (IA modernes)
- ✅ NOUVEAU: Détection "objets flottants" (ombres manquantes)
- ✅ NOUVEAU: Analyse bruit sub-pixel (signature capteur)
- ✅ NOUVEAU: Intégration EnsembleVoterGuard (chef d'orchestre)
- ✅ NOUVEAU: Mode scroll Auto/Manuel
"""
import os
import sys
import time
import json
import threading
import random
import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    logging.warning("Playwright non installé. pip install playwright && playwright install chromium")

try:
    import cv2
    import numpy as np
    HAS_CV = True
except ImportError:
    HAS_CV = False
    logging.warning("OpenCV non installé. pip install opencv-python numpy")

try:
    from guards.guard_interface import GuardInterface
except ImportError:
    class GuardInterface:
        def __init__(self, name):
            self.name = name
            self.is_running = False
            self.stats = {}
        def start(self): pass
        def stop(self): pass
        def get_stats(self): return self.stats

logger = logging.getLogger(__name__)

# ============================================================================
# SONDE JAVASCRIPT GÉNÉRALISTE (injectée dans chaque page)
# ============================================================================
KERBEROS_SONDE_JS = """
(function() {
    if (window.__kerberos_sonde__) return;

    // Badges officiels "contenu généré par IA" affichés par les plateformes
    // elles-mêmes (TikTok, YouTube, Instagram...). Multi-langue (FR/EN),
    // basé sur des expressions régulières pour tolérer les variations
    // exactes de wording d'une plateforme/langue à l'autre.
    const AI_BADGE_PATTERNS = [
        /contient des m[ée]dias g[ée]n[ée]r[ée]s par (l')?ia/i,
        /g[ée]n[ée]r[ée] (par|avec) (l')?ia/i,
        /cr[ée][ée] avec (l')?ia/i,
        /contenu modifi[ée] ou synth[ée]tique/i,
        /ai-generated/i,
        /generated (with|by) ai/i,
        /made with ai/i,
        /altered or synthetic content/i,
        /synthetic media/i,
    ];

    window.__kerberos_sonde__ = {
        activeVideo: null,
        canvas: document.createElement('canvas'),
        ctx: null,
        lastVideoUrl: '',
        init: function() {
            this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
            this.scanForVideo();
            setInterval(() => this.scanForVideo(), 2000);
        },
        scanForVideo: function() {
            let videos = Array.from(document.querySelectorAll('video'));
            document.querySelectorAll('*').forEach(el => {
                if (el.shadowRoot) {
                    videos = videos.concat(Array.from(el.shadowRoot.querySelectorAll('video')));
                }
            });
            const visible = videos.filter(v => {
                const r = v.getBoundingClientRect();
                return r.width > 100 && r.height > 100 && v.readyState >= 2;
            });
            if (visible.length > 0) {
                const current = visible[0];
                const currentSrc = current.src || current.currentSrc || '';
                if (this.activeVideo !== current || this.lastVideoUrl !== currentSrc) {
                    this.activeVideo = current;
                    this.lastVideoUrl = currentSrc;
                }
            }
        },
        // Cherche un badge "généré par IA" affiché par la plateforme, à
        // proximité de la vidéo active plutôt que sur toute la page (pour
        // éviter les faux positifs venant de pubs/articles sans rapport).
        detectPlatformAiBadge: function() {
            try {
                let scope = document.body;
                if (this.activeVideo) {
                    // Remonte jusqu'à un conteneur raisonnable (max 8 niveaux)
                    // autour de la vidéo pour limiter le scan au bon contexte.
                    let el = this.activeVideo;
                    for (let i = 0; i < 8 && el.parentElement; i++) el = el.parentElement;
                    scope = el;
                }
                const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT);
                let node;
                while ((node = walker.nextNode())) {
                    const text = node.textContent.trim();
                    if (!text || text.length > 200) continue;
                    for (const pattern of AI_BADGE_PATTERNS) {
                        if (pattern.test(text)) return text;
                    }
                }
            } catch (e) { /* ignore */ }
            return null;
        },
        getVideoInfo: function() {
            if (!this.activeVideo || this.activeVideo.readyState < 2) return null;
            let videoSrc = this.lastVideoUrl;
            if (!videoSrc && this.activeVideo.children.length > 0) {
                videoSrc = this.activeVideo.children[0].src || '';
            }
            if (this.canvas.width !== this.activeVideo.videoWidth) {
                this.canvas.width = this.activeVideo.videoWidth;
                this.canvas.height = this.activeVideo.videoHeight;
            }
            let frameData = null;
            try {
                this.ctx.drawImage(this.activeVideo, 0, 0);
                frameData = this.canvas.toDataURL('image/jpeg', 0.4);
            } catch (e) { frameData = "TAINTED"; }
            return {
                frame: frameData,
                videoSrc: videoSrc,
                pageUrl: window.location.href,
                pageTitle: document.title,
                platformAiLabel: this.detectPlatformAiBadge(),
                timestamp: new Date().toISOString()
            };
        }
    };
    if (document.readyState === 'complete') window.__kerberos_sonde__.init();
    else window.addEventListener('load', () => window.__kerberos_sonde__.init());
})();
"""


class VideoAnalyzerGuard(GuardInterface):
    """
    Guard principal d'analyse vidéo avec détection IA avancée.
    Utilise 3 niveaux de détection + EnsembleVoterGuard si disponible.
    """
    
    def __init__(self, kerberos_app: Optional[Any] = None) -> None:
        # ✅ FIX 1: Nom en minuscules pour correspondre au GuardManager
        super().__init__("video_analyzer")
        self.kerberos = kerberos_app
        self.is_running = False
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.analysis_thread: Optional[threading.Thread] = None
        self._is_paused = False
        self._lock = threading.Lock()
        self._frame_count_lock = threading.Lock()
        
        # Stats
        self.video_stats: Dict[str, int] = {
            "total": 0, "real": 0, "suspicious": 0, "uncertain": 0
        }
        self.detailed_stats: Dict[str, Any] = {
            "watermarks_detected": 0,
            "ai_types": {"GAN": 0, "Diffusion": 0, "FaceSwap": 0, "Unknown": 0},
            "camera_types": {"Smartphone": 0, "Webcam": 0, "Professional": 0, "Unknown": 0}
        }
        self.analyzed_videos: List[Dict[str, Any]] = []
        
        # ✅ FIX 2: Seuil réaliste et limite mémoire
        self.detection_threshold: int = 65
        self.MAX_VIDEOS_IN_MEMORY = 500
        self.frame_count = 0
        
        # ✅ NOUVEAU: Mode scroll Auto/Manuel
        self.auto_scroll_enabled = True
        self.scroll_speed = 2  # 1=lent, 2=moyen, 3=rapide
        self.scroll_interval = 3  # secondes
        self.scroll_amount = 800  # pixels
        
        # ✅ NOUVEAU: Seuil de bruit de capteur (sub-pixel)
        self.noise_floor_threshold = 3.5
        
        # Haar Cascade pour détection de visages
        self.face_cascade = None
        if HAS_CV:
            try:
                self.face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
            except Exception as e:
                logger.error(f"Erreur Haar Cascade: {e}")
        
        logger.info("🛡️ VideoAnalyzerGuard v6.0 initialisé (Challenge Accepted)")
    
    # =========================================================================
    # CONFIGURATION
    # =========================================================================
    
    def set_threshold(self, value: float) -> None:
        self.detection_threshold = int(value)
        logger.info(f"🎚️ Seuil mis à jour: {self.detection_threshold}")
    
    def set_scroll_speed(self, speed: int) -> None:
        self.scroll_speed = max(1, min(3, int(speed)))
        speeds = {1: (5, 400), 2: (3, 800), 3: (1.5, 1200)}
        self.scroll_interval, self.scroll_amount = speeds[self.scroll_speed]
        logger.info(f"🔄 Vitesse scroll: {self.scroll_speed} (intervalle: {self.scroll_interval}s)")
    
    def toggle_auto_scroll(self) -> bool:
        self.auto_scroll_enabled = not self.auto_scroll_enabled
        logger.info(f"🔄 Scroll: {'AUTO' if self.auto_scroll_enabled else 'MANUEL'}")
        return self.auto_scroll_enabled
    
    def get_analyzed_videos(self) -> List[Dict[str, Any]]:
        with self._lock:
            return self.analyzed_videos.copy()
    
    # =========================================================================
    # NIVEAU 1: DÉTECTION CLASSIQUE (IA anciennes - mauvaise qualité)
    # =========================================================================
    
    def _analyze_classic_artifacts(self, face_roi: np.ndarray, frame: np.ndarray, 
                                    x: int, y: int, w: int, h: int) -> Tuple[int, List[str]]:
        """
        Niveau 1: Détecte les artefacts classiques des IA anciennes
        (flou, compression, saturation faible)
        """
        votes = 0
        details = []
        
        # 1. Flou anormal
        try:
            blur = cv2.Laplacian(face_roi, cv2.CV_64F).var()
            if blur < 100:  # Seuil augmenté (80 → 100)
                votes += 1
                details.append(f"Flou anormal ({blur:.1f})")
        except: pass
        
        # 2. Artefacts DCT (compression)
        try:
            dct = cv2.dct(face_roi.astype(np.float32))
            fh, fw = face_roi.shape
            hf = np.mean(np.abs(dct[fh//2:(fh//2)+10, fw//2:(fw//2)+10]))
            if hf < 15:  # Seuil augmenté (10 → 15)
                votes += 1
                details.append(f"Artefacts DCT ({hf:.1f})")
        except: pass
        
        # 3. Saturation faible
        try:
            hsv = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2HSV)
            sat = np.std(hsv[:,:,1])
            if sat < 30:  # Seuil augmenté (25 → 30)
                votes += 1
                details.append(f"Saturation faible ({sat:.1f})")
        except: pass
        
        return votes, details
    
    # =========================================================================
    # NIVEAU 2: DÉTECTION "PERFECTION SUSPECTE" (IA modernes)
    # =========================================================================
    
    def _analyze_perfection_suspecte(self, face_roi: np.ndarray, frame: np.ndarray,
                                      x: int, y: int, w: int, h: int) -> Tuple[int, List[str]]:
        """
        Niveau 2: Détecte les IA modernes (Midjourney v6, DALL-E 3)
        qui sont "trop parfaites" (peau lisse, netteté excessive, etc.)
        """
        votes = 0
        details = []
        
        # 4. Netteté excessive (IA hyper-réaliste)
        try:
            sharpness = cv2.Laplacian(face_roi, cv2.CV_64F).var()
            if sharpness > 800:  # Seuil abaissé (1000 → 800)
                votes += 1
                details.append(f"Netteté excessive ({sharpness:.1f})")
        except: pass
        
        # 5. Saturation trop uniforme (couleurs trop parfaites)
        try:
            hsv_full = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2HSV)
            sat_uniformity = np.std(hsv_full[:,:,1])
            if sat_uniformity < 20:  # Seuil augmenté (10 → 20)
                votes += 1
                details.append(f"Saturation trop uniforme ({sat_uniformity:.1f})")
        except: pass
        
        # 6. Contraste excessif
        try:
            contrast = np.std(face_roi)
            if contrast > 80:
                votes += 1
                details.append(f"Contraste excessif ({contrast:.1f})")
        except: pass
        
        # 7. Peau trop lisse (variance faible dans zones claires)
        try:
            skin_variance = np.var(face_roi[face_roi > 100])
            if skin_variance < 200:
                votes += 1
                details.append(f"Peau trop lisse ({skin_variance:.1f})")
        except: pass
        
        return votes, details
    
    # =========================================================================
    # NIVEAU 3: DÉTECTION PHYSIQUE (ombres, bruit de capteur)
    # =========================================================================
    
    def _analyze_physical_anomalies(self, gray: np.ndarray, frame: np.ndarray) -> Tuple[int, List[str]]:
        """
        Niveau 3: Détecte les anomalies physiques
        (objets flottants sans ombre, absence de bruit de capteur)
        """
        votes = 0
        details = []
        h, w = gray.shape
        
        # 8. Détection d'objets flottants (pas d'ombre de contact)
        try:
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                main_contour = max(contours, key=cv2.contourArea)
                cx, cy, cw, ch = cv2.boundingRect(main_contour)
                
                # Vérifier la zone juste en dessous de l'objet
                check_y_start = cy + ch
                check_y_end = min(h, check_y_start + 20)
                
                if check_y_end < h and cw > 50 and ch > 50:
                    region_below = gray[check_y_start:check_y_end, cx:cx+cw]
                    object_region = gray[cy:cy+ch, cx:cx+cw]
                    
                    avg_below = np.mean(region_below)
                    avg_object = np.mean(object_region)
                    
                    # Si la zone en dessous n'est PAS plus sombre = objet flottant
                    if avg_below > avg_object - 15:
                        votes += 1
                        details.append("Objet flottant (pas d'ombre de contact)")
        except: pass
        
        # 9. Analyse du bruit de capteur (sub-pixel)
        try:
            flat_mask = cv2.inRange(gray, 100, 150)
            if np.sum(flat_mask > 0) > 1000:
                noise_floor = np.std(gray[flat_mask > 0])
            else:
                noise_floor = np.std(gray)
            
            # Si image haute résolution mais bruit trop faible = IA
            if (h * w) > 1_000_000 and noise_floor < self.noise_floor_threshold:
                votes += 1
                details.append(f"Bruit capteur absent ({noise_floor:.2f})")
        except: pass
        
        return votes, details
    
    # =========================================================================
    # MÉTHODE PRINCIPALE D'ANALYSE CV
    # =========================================================================
    
    def _analyze_frame_cv2(self, frame: np.ndarray) -> Tuple[int, List[str]]:
        """
        Analyse complète avec 3 niveaux de détection.
        Retourne un score de vote (0-100) et les détails.
        """
        if not HAS_CV or frame is None:
            return 50, ["OpenCV non disponible"]
        
        details = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Détection de visages
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        ) if self.face_cascade else []
        
        total_votes = 0
        suspicious_votes = 0
        
        if len(faces) > 0:
            # Prendre le plus grand visage
            x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
            w, h = w - (w % 2), h - (h % 2)
            face_roi = gray[y:y+h, x:x+w]
            details.append("Visage détecté")
            
            # NIVEAU 1: Artefacts classiques
            v1, d1 = self._analyze_classic_artifacts(face_roi, frame, x, y, w, h)
            suspicious_votes += v1
            total_votes += 3
            details.extend(d1)
            
            # NIVEAU 2: Perfection suspecte
            v2, d2 = self._analyze_perfection_suspecte(face_roi, frame, x, y, w, h)
            suspicious_votes += v2
            total_votes += 4
            details.extend(d2)
            
            # NIVEAU 3: Anomalies physiques
            v3, d3 = self._analyze_physical_anomalies(gray, frame)
            suspicious_votes += v3
            total_votes += 2
            details.extend(d3)
        else:
            details.append("Aucun visage")
            # Analyse globale sans visage
            v3, d3 = self._analyze_physical_anomalies(gray, frame)
            suspicious_votes += v3
            total_votes += 2
            details.extend(d3)
        
        # Calcul du score final (pourcentage de votes suspects)
        if total_votes > 0:
            vote_score = int((suspicious_votes / total_votes) * 100)
        else:
            vote_score = 50
        
        details.append(f"Vote: {suspicious_votes}/{total_votes} critères suspects")
        
        return vote_score, details
    
    # =========================================================================
    # MÉTHODE PRINCIPALE D'ANALYSE (avec EnsembleVoter)
    # =========================================================================
    
    def analyze_frame(self, video_info: Optional[Dict[str, Any]]) -> Tuple[int, str]:
        """
        Analyse complète d'une frame.
        Utilise EnsembleVoterGuard si disponible, sinon fallback local.
        """
        if not video_info or not video_info.get('frame') or video_info['frame'] == "TAINTED":
            return 50, "UNCERTAIN"
        
        frame_data = video_info['frame']
        page_url = video_info.get('pageUrl', '')
        video_src = video_info.get('videoSrc', '')
        
        if not HAS_CV:
            return 50, "UNCERTAIN"
        
        try:
            # Décodage de l'image
            if ',' in frame_data:
                frame_data_cv = frame_data.split(',')[1]
            else:
                frame_data_cv = frame_data
            img_bytes = base64.b64decode(frame_data_cv)
            frame = cv2.imdecode(np.frombuffer(img_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            if frame is None:
                raise ValueError("Decode error")
            
            # ✅ SIGNAL PRIORITAIRE : badge officiel "généré par IA" de la
            # plateforme elle-même (TikTok, YouTube, Instagram...). Ce signal
            # est beaucoup plus fiable que nos heuristiques pixel/bruit de
            # capteur, donc il écrase le verdict heuristique quand présent —
            # mais le score heuristique est quand même calculé et conservé
            # dans les détails, pour garder une trace de ce que l'analyse
            # visuelle aurait dit toute seule.
            platform_ai_label = video_info.get('platformAiLabel')

            # ✅ UTILISATION DU ENSEMBLE VOTER (Chef d'Orchestre)
            ensemble_guard = None
            if self.kerberos and hasattr(self.kerberos, 'guard_manager'):
                ensemble_guard = self.kerberos.guard_manager.get_guard("ensemble_voter")
            
            if ensemble_guard and hasattr(ensemble_guard, 'vote'):
                # Le chef d'orchestre prend le contrôle
                final_score, classification, all_details = ensemble_guard.vote({
                    'frame': frame,
                    'page_url': page_url,
                    'video_src': video_src
                })
            else:
                # Fallback: analyse locale avec les 3 niveaux
                vote_score, details = self._analyze_frame_cv2(frame)
                
                # Classification
                if vote_score > self.detection_threshold:
                    final_score = vote_score
                    classification = "SUSPICIOUS"
                elif vote_score > (self.detection_threshold - 30):
                    final_score = vote_score
                    classification = "UNCERTAIN"
                else:
                    final_score = vote_score
                    classification = "REAL"
                all_details = details

            if platform_ai_label:
                all_details = (all_details if isinstance(all_details, list) else [str(all_details)])
                all_details = [f"🏷️ Badge plateforme détecté: \"{platform_ai_label}\"",
                                f"(score heuristique avant écrasement: {final_score})"] + all_details
                final_score = 100
                classification = "SUSPICIOUS"

            # ✅ NOUVEAU: Sauvegarde de la frame "preuve" sur disque quand la
            # vidéo est jugée SUSPICIOUS. Une image vaut mieux qu'un score —
            # ça permet de vérifier visuellement/manuellement, et de joindre
            # une preuve concrète dans un rapport d'investigation.
            # Dossier dédié (evidence_frames) pour ne pas entrer en conflit
            # avec les guards frame_saver / screenshot_capture existants.
            evidence_frame_path = None
            if classification == "SUSPICIOUS":
                try:
                    evidence_dir = Path("reports") / "evidence_frames"
                    evidence_dir.mkdir(parents=True, exist_ok=True)
                    fname = f"suspicious_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                    fpath = evidence_dir / fname
                    cv2.imwrite(str(fpath), frame)
                    evidence_frame_path = str(fpath)
                except Exception as e:
                    logger.debug(f"⚠️ Impossible de sauvegarder la frame preuve: {e}")
            
            # Sauvegarde du record vidéo
            video_record = {
                "page_url": page_url,
                "video_src": video_src,
                "score": final_score,
                "classification": classification,
                "details": " | ".join(all_details) if isinstance(all_details, list) else str(all_details),
                "evidence_frame_path": evidence_frame_path,
                "timestamp": datetime.now().strftime('%H:%M:%S')
            }
            
            with self._lock:
                self.analyzed_videos.append(video_record)
                self.video_stats["total"] += 1
                if classification == "SUSPICIOUS":
                    self.video_stats["suspicious"] += 1
                elif classification == "UNCERTAIN":
                    self.video_stats["uncertain"] += 1
                else:
                    self.video_stats["real"] += 1
                
                # ✅ FIX 4: Rotation mémoire
                if len(self.analyzed_videos) > self.MAX_VIDEOS_IN_MEMORY:
                    self.analyzed_videos = self.analyzed_videos[-(self.MAX_VIDEOS_IN_MEMORY // 2):]
                    logger.info(f" Rotation mémoire (max {self.MAX_VIDEOS_IN_MEMORY})")
            
            # Mise à jour UI
            detail_str = " | ".join(all_details) if isinstance(all_details, list) else str(all_details)
            self._update_stats_and_ui(final_score, classification, detail_str)
            
            return final_score, classification
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse: {e}")
            return 50, "UNCERTAIN"
    
    # =========================================================================
    # UTILITAIRES
    # =========================================================================
    
    def detect_watermark(self, gray: np.ndarray) -> bool:
        try:
            h, w = gray.shape
            zones = [
                gray[0:h//10, 0:w//10],
                gray[0:h//10, 9*w//10:w],
                gray[9*h//10:h, 0:w//10],
                gray[9*h//10:h, 9*w//10:w]
            ]
            score = sum(
                1 for z in zones
                if np.sum(cv2.Canny(z, 50, 150) > 0) / (z.shape[0] * z.shape[1]) > 0.05
            )
            return score >= 2
        except:
            return False
    
    def estimate_camera_type(self, frame: np.ndarray, gray: np.ndarray) -> str:
        try:
            h, w = frame.shape[:2]
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            if h * w < 720 * 1280:
                return "Smartphone"
            elif h * w < 1080 * 1920:
                return "Webcam" if blur < 100 else "Smartphone"
            else:
                return "Professional" if blur > 500 else "Smartphone"
        except:
            return "Unknown"
    
    def classify_ai_type(self, gray: np.ndarray, details: List[str]) -> str:
        try:
            blur = cv2.Laplacian(gray, cv2.CV_64F).var()
            dct = cv2.dct(gray.astype(np.float32))
            fh, fw = gray.shape
            comp_artifacts = np.mean(np.abs(dct[fh//2:(fh//2)+10, fw//2:(fw//2)+10])) < 10
            
            if blur < 80 and "Flou anormal" in details:
                return "FaceSwap"
            elif comp_artifacts and "Artefacts DCT" in details:
                return "Diffusion"
            elif blur < 80:
                return "GAN"
            return "Unknown"
        except:
            return "Unknown"
    
    def _classify_score(self, score: int) -> str:
        threshold = self.detection_threshold
        uncertain_zone = threshold - 30
        if score > threshold:
            return "SUSPICIOUS"
        elif score > uncertain_zone:
            return "UNCERTAIN"
        else:
            return "REAL"
    
    def _update_stats_and_ui(self, score: int, classification: str, detail: str) -> None:
        if self.kerberos and hasattr(self.kerberos, 'root'):
            msg = f"🎥 Score: {score}/100 | {classification} ({detail})\n"
            try:
                self.kerberos.root.after(0, lambda m=msg: self.kerberos.append_to_chat(m))
            except:
                pass
    
    def get_detailed_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "video_stats": self.video_stats.copy(),
                "detailed_stats": {
                    "watermarks_detected": self.detailed_stats["watermarks_detected"],
                    "ai_types": self.detailed_stats["ai_types"].copy(),
                    "camera_types": self.detailed_stats["camera_types"].copy()
                }
            }
    
    # =========================================================================
    # BOUCLE PLAYWRIGHT (avec fix fermeture navigateur)
    # =========================================================================
    
    def _run_playwright_loop(self) -> None:
        """Boucle Playwright avec détection correcte de fermeture navigateur"""
        try:
            logger.info("🔧 Initialisation Playwright (Windows 10)...")
            with sync_playwright() as p:
                brave_paths = [
                    os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
                    os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
                ]
                exec_path = next((path for path in brave_paths if os.path.exists(path)), None)
                
                if exec_path:
                    logger.info(f"✅ Brave trouvé: {exec_path}")
                else:
                    logger.warning("⚠️ Brave introuvable. Chromium par défaut.")
                
                self.browser = p.chromium.launch(
                    headless=False,
                    executable_path=exec_path,
                    args=["--disable-gpu", "--no-sandbox", "--disable-infobars"]
                )
                
                self.context = self.browser.new_context(
                    viewport={"width": 1280, "height": 900},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                self.context.add_init_script(KERBEROS_SONDE_JS)
                self.page = self.context.new_page()
                
                self.page.goto("about:blank", wait_until="domcontentloaded")
                time.sleep(1)
                
                logger.info("✅ Navigateur prêt")
                logger.info(f"🔄 Scroll: {'AUTO' if self.auto_scroll_enabled else 'MANUEL'}")
                
                while self.is_running:
                    # ✅ FIX 5: Détection correcte de la fermeture du navigateur
                    if not self.browser or len(self.browser.contexts) == 0:
                        logger.warning("🚫 Navigateur fermé par l'utilisateur")
                        break
                    
                    if self._is_paused:
                        time.sleep(1)
                        continue
                    
                    try:
                        video_info = None
                        try:
                            video_info = self.page.evaluate(
                                "window.__kerberos_sonde__ ? window.__kerberos_sonde__.getVideoInfo() : null"
                            )
                        except Exception as e:
                            error_msg = str(e)
                            if "Target closed" in error_msg or "Browser closed" in error_msg:
                                logger.info("🚫 Navigateur fermé, arrêt de l'analyse")
                                break
                            elif "Execution context was destroyed" in error_msg:
                                # On attend que la navigation/preview soit VRAIMENT terminée
                                # avant de réinjecter, sinon on boucle à chaque frappe clavier
                                # dans la barre d'adresse (suggestions Brave qui détruisent
                                # le contexte JS en continu).
                                try:
                                    current_url = self.page.url
                                except Exception:
                                    current_url = "?"
                                logger.debug(f"🔄 Contexte détruit, url actuelle='{current_url}' — attente de stabilisation...")
                                try:
                                    self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                                except Exception:
                                    # Toujours pas stable (ex: toujours en train de taper) :
                                    # on patiente un peu plus longtemps avant de reboucler
                                    logger.debug("🔄 Toujours instable après 5s de timeout, on repatiente 1.5s")
                                    time.sleep(1.5)
                                    continue
                                try:
                                    self.page.evaluate(KERBEROS_SONDE_JS)
                                    logger.debug("🔄 Sonde réinjectée avec succès")
                                except Exception as e2:
                                    logger.debug(f"🔄 Échec réinjection sonde: {e2}")
                                continue
                            else:
                                logger.debug(f"⚠️ Erreur evaluate non gérée: {error_msg}")
                                time.sleep(1)
                                continue
                        
                        if video_info and video_info.get('frame'):
                            self.analyze_frame(video_info)
                            time.sleep(2)
                        else:
                            # ✅ LOGIQUE DE SCROLL AUTO/MANUEL
                            # On ne scrolle QUE s'il y a une vraie page chargée.
                            # Sur about:blank (ou une page vide/en cours de chargement),
                            # scroller ne sert à rien et donne l'impression d'une boucle
                            # (action répétée sans effet visible toutes les secondes).
                            try:
                                current_url = self.page.url
                            except Exception:
                                current_url = ""

                            # Liste blanche : on ne scrolle QUE sur de vraies pages
                            # web (exclut about:blank, chrome://new-tab-page/,
                            # brave://newtab/, edge://..., etc.)
                            is_real_page = current_url.startswith(("http://", "https://"))

                            # En plus : on exclut les pages de résultats de moteurs
                            # de recherche (Brave Search, Google, Bing, DuckDuckGo...).
                            # Scroller une page de résultats n'a pas de sens ici —
                            # il n'y a pas de vidéo à trouver en scrollant une SERP,
                            # l'utilisateur est encore en train de chercher/taper.
                            SEARCH_ENGINE_DOMAINS = (
                                "search.brave.com",
                                "google.", "www.google.",
                                "bing.com", "www.bing.com",
                                "duckduckgo.com",
                                "yahoo.com", "search.yahoo.com",
                                "ecosia.org",
                                "qwant.com",
                            )
                            is_search_page = any(domain in current_url for domain in SEARCH_ENGINE_DOMAINS)

                            should_scroll = is_real_page and not is_search_page

                            if self.auto_scroll_enabled and should_scroll:
                                try:
                                    self.page.evaluate(f"window.scrollBy(0, {self.scroll_amount})")
                                except: pass
                            elif is_search_page:
                                logger.debug(f"⏸️ Page de recherche détectée ('{current_url}'), scroll suspendu")
                                time.sleep(1.5)
                                continue
                            elif not is_real_page:
                                # Pas de spam de logs : un seul message si on vient
                                # de passer sur une page vide, puis on patiente plus
                                # longtemps tant que rien de réel n'est chargé.
                                logger.debug(f"⏸️ Page vide/about:blank ('{current_url}'), scroll suspendu")
                                time.sleep(1.5)
                                continue

                            time.sleep(1)
                    
                    except Exception as e:
                        logger.error(f"❌ Erreur boucle: {e}")
                        time.sleep(1)
                
                logger.info("⏹️ Arrêt boucle...")
        
        except Exception as e:
            logger.error(f"❌ Erreur Playwright: {e}")
        finally:
            self._cleanup()
    
    def _cleanup(self) -> None:
        self.is_running = False
        if self.page:
            try: self.page.close()
            except: pass
        if self.browser:
            try: self.browser.close()
            except: pass
        self.page = self.browser = self.playwright = None
        logger.info("🧹 Ressources nettoyées")
    
    # =========================================================================
    # INTERFACE PUBLIQUE
    # =========================================================================
    
    def start(self) -> None: self.start_analysis()
    def stop(self) -> None: self.stop_analysis()
    
    def get_stats(self) -> Dict[str, int]:
        with self._lock: return self.video_stats.copy()
    
    def start_analysis(self) -> None:
        if self.is_running:
            logger.warning("⚠️ Déjà en cours")
            return
        if not HAS_PLAYWRIGHT:
            logger.error("❌ Playwright non installé")
            return
        self.is_running = True
        self._is_paused = False
        self.analysis_thread = threading.Thread(target=self._run_playwright_loop, daemon=True)
        self.analysis_thread.start()
        logger.info("▶️ Analyse démarrée")
    
    def stop_analysis(self) -> None:
        logger.info("⏹️ Arrêt demandé...")
        self.is_running = False
        self._is_paused = False
    
    def pause(self):
        self._is_paused = True
        logger.info("⏸️ Analyse en pause")
    
    def resume(self):
        self._is_paused = False
        logger.info("▶️ Analyse reprise")
    
    def navigate_to_url(self, url: str):
        if self.page:
            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                logger.info(f"🌐 Navigation vers: {url}")
                time.sleep(2)
                self.page.evaluate(KERBEROS_SONDE_JS)
            except Exception as e:
                logger.error(f" Erreur navigation: {e}")


# ============================================================================
# FONCTIONS GLOBALES
# ============================================================================
_guard_instance: Optional[VideoAnalyzerGuard] = None

def start_guard(kerberos_app: Optional[Any] = None) -> Optional[VideoAnalyzerGuard]:
    global _guard_instance
    _guard_instance = VideoAnalyzerGuard(kerberos_app)
    logger.info("🛡️ VideoAnalyzerGuard démarré")
    return _guard_instance

def stop_guard() -> None:
    global _guard_instance
    if _guard_instance:
        _guard_instance.stop_analysis()
        _guard_instance = None

def get_stats() -> Dict[str, int]:
    global _guard_instance
    return _guard_instance.get_stats() if _guard_instance else {
        "total": 0, "real": 0, "suspicious": 0, "uncertain": 0
    }

def get_detailed_stats() -> Dict[str, Any]:
    global _guard_instance
    return _guard_instance.get_detailed_stats() if _guard_instance else {
        "video_stats": {"total": 0, "real": 0, "suspicious": 0, "uncertain": 0},
        "detailed_stats": {"watermarks_detected": 0, "ai_types": {}, "camera_types": {}}
    }

def get_analyzed_videos() -> List[Dict[str, Any]]:
    global _guard_instance
    return _guard_instance.get_analyzed_videos() if _guard_instance else []