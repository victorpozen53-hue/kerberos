@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================================
::  TEST HONEYPOT TRAP — Validation du Guard Script Kiddie Trap
::  Copyright (C) 2025 Victor Pozen — GPLv3
:: ============================================================================

echo.
echo ================================================
echo   TEST HONEYPOT TRAP — Kerberos Pentest Suite
echo ================================================
echo.

:: ── CONFIGURATION ────────────────────────────────────────────────────────
set "HONEYPOT_DIR=F:\kerberos-security\lymph\honeypot\script_kiddie_bait"
set "LOGS_DIR=F:\kerberos-security\logs.full.option\logs_guards\guard_script_kiddie_trap"
set "HONEYPOT_FILE=%HONEYPOT_DIR%\passwords.txt"

:: ── ETAPE 1 : VERIFIER QUE KERBEROS TOURNE ──────────────────────────────
echo [1/5] Verification que Kerberos est en cours d'execution...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | findstr /I "python.exe" >nul
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  ATTENTION : Python ne semble pas en cours d'execution
    echo    → Lance d'abord kerberos.py
    pause
    goto :END
)
echo ✅ Python detecte
echo.

:: ── ETAPE 2 : AFFICHER LE FICHIER HONEYPOT ──────────────────────────────
echo [2/5] Acces au fichier honeypot (passwords.txt)...
if not exist "%HONEYPOT_FILE%" (
    echo ❌ ERREUR : Fichier honeypot introuvable !
    echo    Chemin : %HONEYPOT_FILE%
    pause
    goto :END
)

type "%HONEYPOT_FILE%"
echo ✅ Fichier lu — l'acces devrait être loggé
echo.

:: ── ETAPE 3 : ATTENDRE 30 SECONDES ─────────────────────────────────────
echo [3/5] Attente de 30 secondes...
timeout /t 30 /nobreak >nul
echo ✅ 30 secondes ecoulees
echo.

:: ── ETAPE 4 : VERIFIER LES RAPPORTS ────────────────────────────────────
echo [4/5] Verification des rapports...
if not exist "%LOGS_DIR%" (
    echo ❌ ERREUR : Dossier de logs introuvable !
    pause
    goto :END
)

dir /B "%LOGS_DIR%\*.html"
echo.

:: ── ETAPE 5 : OUVRIR LE RAPPORT ────────────────────────────────────────
echo [5/5] Ouverture du rapport HTML...

:: Trouver le fichier HTML le plus recent
set "FOUND_FILE="
for /f "delims=" %%i in ('dir /B /O-D "%LOGS_DIR%\*.html" 2^>nul') do (
    if not defined FOUND_FILE set "FOUND_FILE=%%i"
)

if defined FOUND_FILE (
    echo ✅ Rapport trouve : %FOUND_FILE%
    
    :: ← CORRECTION : Utiliser explorer.exe au lieu de start
    explorer.exe "%LOGS_DIR%\%FOUND_FILE%"
    echo 🌐 Rapport ouvert dans l'explorateur
) else (
    echo ⚠️  Aucun rapport HTML trouve
    echo    → Verifie que guard_script_kiddie_trap est actif
)

echo.
echo ================================================
echo   TEST TERMINE
echo ================================================
echo.
pause

:END