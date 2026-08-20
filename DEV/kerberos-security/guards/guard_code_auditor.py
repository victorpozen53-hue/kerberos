# ============================================================================
# === FONCTIONS UI — ONGLETS SPÉCIFIQUES =====================================
# ============================================================================

def get_ui_buttons() -> dict:
    """
    Retourne les boutons pour l'interface Kerberos.
    À appeler depuis guards_panel.py pour afficher les boutons d'action.
    """
    return {
        "🔍 Scanner un fichier": {
            "command": scan_file_dialog,
            "bg": "#2d5a7b",
            "fg": "white",
            "tooltip": "Choisir un fichier Python à auditer"
        },
        "📊 Scanner tous les guards": {
            "command": audit_all_guards,
            "bg": "#2d7b5a",
            "fg": "white",
            "tooltip": "Auditer tous les guards du dossier /guards"
        },
        "📁 Scanner un dossier": {
            "command": scan_directory_dialog,
            "bg": "#7b5a2d",
            "fg": "white",
            "tooltip": "Choisir un dossier à scanner récursivement"
        },
        "📄 Voir derniers rapports": {
            "command": open_reports_folder,
            "bg": "#5a2d7b",
            "fg": "white",
            "tooltip": "Ouvrir le dossier des rapports d'audit"
        }
    }

def scan_file_dialog():
    """Ouvre une boîte de dialogue pour choisir un fichier à scanner"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Créer une fenêtre temporaire
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre
        root.attributes('-topmost', True)  # Mettre au premier plan
        
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier Python à auditer",
            filetypes=[
                ("Fichiers Python", "*.py"),
                ("Tous les fichiers", "*.*")
            ],
            initialdir=GUARDS_DIR
        )
        
        root.destroy()
        
        if file_path:
            _log(f"Audit demandé : {file_path}", "INFO")
            result = audit_one(Path(file_path))
            _show_audit_result(result)
            return result
        else:
            _log("Aucun fichier sélectionné", "INFO")
            return None
            
    except Exception as e:
        _log(f"Erreur boîte de dialogue : {e}", "ERROR")
        return None

def scan_directory_dialog():
    """Ouvre une boîte de dialogue pour choisir un dossier à scanner"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        directory = filedialog.askdirectory(
            title="Sélectionner un dossier à scanner",
            initialdir=GUARDS_DIR
        )
        
        root.destroy()
        
        if directory:
            _log(f"Scan dossier demandé : {directory}", "INFO")
            results = audit_directory(Path(directory))
            _show_directory_results(results)
            return results
        else:
            _log("Aucun dossier sélectionné", "INFO")
            return None
            
    except Exception as e:
        _log(f"Erreur boîte de dialogue : {e}", "ERROR")
        return None

def audit_directory(directory: Path) -> list:
    """
    Scanne tous les fichiers .py d'un dossier récursivement.
    """
    _log(f"Scan récursif du dossier : {directory}", "START")
    results = []
    
    if not directory.exists():
        _log(f"Dossier introuvable : {directory}", "ERROR")
        return results
    
    # Trouver tous les .py
    py_files = list(directory.rglob("*.py"))
    _log(f"{len(py_files)} fichier(s) Python trouvé(s)", "INFO")
    
    for i, f in enumerate(py_files, 1):
        _log(f"[{i}/{len(py_files)}] {f.relative_to(directory)}", "SCAN")
        try:
            result = audit_file(f)
            results.append(result)
            _save_report_json(result)
            _save_report_html(result)
            
            # Afficher résumé
            grade = result.get('grade', '?')
            score = result.get('score', 0)
            issues = result.get('total_issues', 0)
            status_color = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
            _log(f"  {status_color} Grade {grade} | Score {score}/100 | {issues} faille(s)", "RESULT")
            
        except Exception as e:
            _log(f"  ❌ Erreur audit {f.name}: {e}", "ERROR")
            results.append({
                "file": str(f),
                "file_name": f.name,
                "error": str(e),
                "score": 0
            })
    
    # Résumé global
    if results:
        avg_score = sum(r.get('score', 0) for r in results if 'score' in r) / len([r for r in results if 'score' in r])
        total_issues = sum(r.get('total_issues', 0) for r in results)
        critical_files = [r for r in results if r.get('critical', 0) > 0]
        
        _log("=" * 60, "SUMMARY")
        _log(f"Dossier scanné : {directory}", "SUMMARY")
        _log(f"Fichiers analysés : {len(results)}", "SUMMARY")
        _log(f"Score moyen : {avg_score:.1f}/100", "SUMMARY")
        _log(f"Total failles : {total_issues}", "SUMMARY")
        if critical_files:
            _log(f"Fichiers critiques : {len(critical_files)}", "WARN")
            for cf in critical_files[:5]:
                _log(f"  • {cf['file_name']} ({cf['critical']} critiques)", "WARN")
        _log("=" * 60, "SUMMARY")
    
    return results

def open_reports_folder():
    """Ouvre le dossier des rapports d'audit"""
    try:
        import subprocess
        _REPORT_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(f'explorer "{_REPORT_DIR.absolute()}"', shell=True)
        _log(f"Dossier rapports ouvert : {_REPORT_DIR}", "INFO")
    except Exception as e:
        _log(f"Erreur ouverture dossier : {e}", "ERROR")

def _show_audit_result(result: dict):
    """Affiche le résultat d'un audit dans la console"""
    print("\n" + "=" * 70)
    print(f"🔬 RÉSULTAT AUDIT — {result.get('file_name', '?')}")
    print("=" * 70)
    
    score = result.get('score', 0)
    grade = result.get('grade', '?')
    status = result.get('status', 'unknown')
    
    # Badge score
    if score >= 80:
        badge = "✅ EXCELLENT"
        color = "#00ff88"
    elif score >= 60:
        badge = "⚠️  ACCEPTABLE"
        color = "#ffaa00"
    else:
        badge = "❌ CRITIQUE"
        color = "#ff4444"
    
    print(f"\n📊 Score : {score}/100 (Grade {grade})")
    print(f"🏷️  Statut : {badge}")
    print(f"\n📈 Détails :")
    print(f"   • Lignes de code : {result.get('lines_count', 0)}")
    print(f"   • Total failles  : {result.get('total_issues', 0)}")
    print(f"   • Critiques      : {result.get('critical', 0)}")
    print(f"   • Élevées        : {result.get('high', 0)}")
    print(f"   • Moyennes       : {result.get('medium', 0)}")
    print(f"   • Faibles        : {result.get('low', 0)}")
    
    # Afficher les failles
    findings = result.get('findings', [])
    if findings:
        print(f"\n🔍 Failles détectées (top 10) :")
        print("-" * 70)
        for i, f in enumerate(findings[:10], 1):
            sev = f.get('severity', 'INFO')
            layer = f.get('layer', '?')
            name = f.get('name', 'Unknown')
            line = f"L{f['line']}" if f.get('line') else "—"
            print(f"{i:2d}. [{sev:8s}] {layer:12s} {name} {line}")
            if f.get('fix'):
                print(f"    💡 {f['fix']}")
        
        if len(findings) > 10:
            print(f"\n   ... et {len(findings) - 10} autre(s) faille(s)")
    
    # Rapports générés
    print(f"\n📄 Rapports générés :")
    print(f"   • {_REPORT_DIR / f'audit_{Path(result.get(\"file\", \"\")).stem}_*.html'}")
    print("=" * 70 + "\n")

def _show_directory_results(results: list):
    """Affiche les résultats d'un scan de dossier"""
    if not results:
        _log("Aucun résultat à afficher", "INFO")
        return
    
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ GLOBAL DU SCAN DE DOSSIER")
    print("=" * 70)
    
    # Stats
    total_files = len(results)
    files_with_scores = [r for r in results if 'score' in r]
    avg_score = sum(r['score'] for r in files_with_scores) / len(files_with_scores) if files_with_scores else 0
    total_issues = sum(r.get('total_issues', 0) for r in results)
    critical_count = sum(r.get('critical', 0) for r in results)
    
    print(f"\n📁 Fichiers analysés : {total_files}")
    print(f"📊 Score moyen       : {avg_score:.1f}/100")
    print(f"⚠️  Total failles     : {total_issues}")
    print(f"🚨 Critiques         : {critical_count}")
    
    # Top 5 fichiers les plus problématiques
    if critical_count > 0:
        print(f"\n🔴 Top 5 fichiers les plus critiques :")
        sorted_results = sorted(results, key=lambda x: x.get('critical', 0), reverse=True)
        for i, r in enumerate(sorted_results[:5], 1):
            if r.get('critical', 0) > 0:
                print(f"  {i}. {r.get('file_name', '?')} — {r.get('critical')} critiques")
    
    print("=" * 70 + "\n")

# ============================================================================
# === INTÉGRATION DANS start_guard() =========================================
# ============================================================================

def start_guard():
    """Point d'entrée Kerberos — avec boutons UI"""
    config = _load_config()
    mode   = config.get("mode", "passif")
    
    _log(f"Guard démarré — mode {mode.upper()} — 12 couches — 70+ règles", "START")
    print(f"🔬 [Code Auditor v3] Mode {mode.upper()} | 12 couches | Taint inter-fonctions")
    
    # Publier métrique
    _publish_metric(0.05)
    
    # Mode auto ou continu
    if mode == "auto":
        def _auto():
            r = audit_all_guards()
            print(f"🔬 [Code Auditor] AUTO — {len(r)} fichiers analysés")
        threading.Thread(target=_auto, daemon=True, name="CodeAuditAuto").start()
    
    elif mode == "continu":
        start_watch()
        print(f"🔬 [Code Auditor] Watchdog actif — interval {config.get('watch_interval_sec',60)}s")
    
    else:
        print("🔬 [Code Auditor] PASSIF — utilisez les boutons UI pour auditer")
        # Afficher les boutons disponibles
        buttons = get_ui_buttons()
        print("\n📋 Boutons disponibles pour l'interface :")
        for btn_name, btn_config in buttons.items():
            print(f"   • {btn_name}")
    
    return None