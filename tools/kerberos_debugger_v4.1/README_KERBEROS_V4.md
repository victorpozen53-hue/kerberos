# 🐺 KERBEROS DEBUGGER v4.0 EXTREME EDITION

## Débogueur Python Ultime avec IA et Outils Avancés

---

## 🚀 NOUVELLES FONCTIONNALITÉS v4.0

### 🔴 **BREAKPOINTS VISUELS**
- **Clique gauche sur le numéro de ligne** → Toggle breakpoint (cercle rouge)
- **F9** → Toggle breakpoint sur la ligne courante
- Gestion complète des breakpoints dans l'onglet dédié
- Double-clic sur un breakpoint → Aller à la ligne

### ⏯️ **PROFILAGE DE PERFORMANCE**
- **F7** → Exécuter avec profilage complet
- Onglet "📊 Performance" avec statistiques détaillées :
  - Temps d'exécution par fonction
  - Nombre d'appels
  - Fonctions les plus lentes
  - Temps cumulatif
- Export CSV des résultats
- Graphiques de performance en temps réel

### 🤖 **AUTO-CORRECTION IA**
Après une erreur, l'IA propose automatiquement :
- **NameError** → Définir la variable manquante
- **ZeroDivisionError** → Ajouter un check `if diviseur != 0:`
- **TypeError** → Convertir les types (ex: `str()`)
- Bouton "✨ Appliquer la correction" pour insérer le code corrigé

### 🎨 **THÈMES PERSONNALISABLES**
6 thèmes professionnels inclus :
- **Cyberpunk** (défaut) - Style futuriste cyan/violet
- **Matrix** - Vert terminal hacker
- **Dracula** - Thème moderne violet/rose
- **Nord** - Palette nordique bleue/grise
- **Monokai** - Classique Sublime Text
- **Solarized Dark** - Confort visuel optimal

Menu "🎨 Thème" → Changer instantanément
Option "Personnaliser les couleurs..." pour créer ton thème

### 🖥️ **TERMINAL INTÉGRÉ**
Onglet "🖥️ Terminal" avec bash complet :
- Exécute des commandes shell : `ls`, `cd`, `pip install`, `git`...
- Support des commandes Python : `python script.py`
- Commandes système : `clear`, `pwd`, `cat`, `grep`...
- Prompt avec couleurs et historique

### 📝 **ÉDITEUR AMÉLIORÉ**
Nouvelles fonctionnalités d'édition :
- **Ctrl+D** → Dupliquer la ligne
- **Ctrl+/** → Commenter/Décommenter
- **Ctrl+F** → Rechercher dans le code
- **Ctrl+H** → Rechercher et remplacer
- **Tab** → Auto-indentation 4 espaces
- **Enter** → Indentation intelligente après `:`
- Position curseur en temps réel (ligne, colonne)

### 📊 **ANALYSE STATIQUE AVANCÉE**
Détection de 10+ types d'erreurs AVANT exécution :
- Erreurs de syntaxe (AST parsing)
- Variables déclarées mais jamais utilisées
- Imports inutilisés
- Division par zéro évidente
- Comparaisons avec `None` (mauvaise pratique)
- Et plus encore...

### 📤 **EXPORT RAPPORTS**
- **HTML** → Rapport coloré avec CSS
- **PDF** → Document professionnel
- **CSV** → Données de performance
- **TXT** → Format texte simple

---

## 🎹 RACCOURCIS CLAVIER COMPLETS

### Fichiers
| Touche | Action |
|--------|--------|
| **Ctrl+N** | Nouveau fichier |
| **Ctrl+O** | Ouvrir fichier |
| **Ctrl+S** | Sauvegarder |
| **Ctrl+Q** | Quitter |

### Exécution
| Touche | Action |
|--------|--------|
| **F5** | Exécuter le code |
| **F6** | Analyse statique |
| **F7** | Exécuter avec profilage |
| **F9** | Toggle breakpoint |

### Édition
| Touche | Action |
|--------|--------|
| **Ctrl+D** | Dupliquer ligne |
| **Ctrl+/** | Commenter/Décommenter |
| **Ctrl+F** | Rechercher |
| **Ctrl+H** | Remplacer |
| **Tab** | Indentation (4 espaces) |

---

## 📚 ONGLETS DISPONIBLES

### 1. 🚀 **Débogueur** (Principal)
Interface de développement complète :
- Éditeur de code avec coloration syntaxique
- Numérotation avec breakpoints visuels
- Barre d'outils (Ouvrir, Sauver, Run, Profile, Analyse)
- Arguments d'exécution personnalisables

**Sous-onglets :**
- **📟 Console** : Sortie en temps réel (stdout/stderr)
- **🔍 Analyse statique** : Détection d'erreurs avant exécution
- **🐛 Traceback + Auto-Fix** : Erreurs avec suggestions IA
- **📊 Performance** : Statistiques de profilage
- **🔴 Breakpoints** : Liste et gestion

### 2. 🔍 **Recherche d'erreurs**
Moteur de recherche multi-format (code original Kerberos) :
- Recherche dans `.py`, `.csv`, `.json`, `.txt`
- Surlignage des occurrences
- Contexte ± 2 lignes
- Export rapport TXT

### 3. 📚 **Historique**
Historique des 50 dernières exécutions :
- Timestamp, nom fichier, code
- Double-clic pour recharger
- Détails complets (args, code, profiling)

### 4. 🖥️ **Terminal**
Bash shell intégré :
- Toutes commandes Unix/Linux
- Support Python : `python`, `pip`, `pytest`
- Navigation : `cd`, `ls`, `pwd`
- Git : `git status`, `git commit`...

---

## 🔧 FONCTIONNALITÉS AVANCÉES

### 👁️ **Surveillance Auto**
Menu "🔧 Outils" → "👁️ Surveillance auto"
- Recharge et réexécute automatiquement le fichier à chaque sauvegarde
- Pratique pour le développement itératif
- Active/désactive avec un clic

### 🎯 **Suggestions IA Contextuelles**
Pour chaque type d'erreur, suggestions spécifiques :
- **NameError** : "Déclare la variable", "Vérifie l'orthographe", "Importe le module"
- **SyntaxError** : "Vérifie parenthèses/guillemets", "Vérifie indentation"
- **TypeError** : "Convertis au bon type", "Opération incompatible"
- **ImportError** : "pip install nom_module"
- Et 10+ autres types...

### 📈 **Graphiques de Performance**
Bouton "📈 Graphique" dans l'onglet Performance :
- Graphique en barres des fonctions les plus lentes
- Timeline d'exécution
- Comparaison entre plusieurs runs
- Export PNG

### 🔬 **Analyse Mémoire** (Futur)
Détection de fuites mémoire et optimisations

---

## 💡 EXEMPLES D'UTILISATION

### Exemple 1 : Débogage avec Breakpoints
```python
# 1. Écris ton code dans l'éditeur
def calcul_complexe(n):
    resultat = 0
    for i in range(n):  # ← Clique ici (ligne 3) pour ajouter un breakpoint 🔴
        resultat += i * 2
    return resultat

print(calcul_complexe(1000))

# 2. Clique sur le numéro de ligne 3
# 3. Appuie sur F5 pour exécuter
# 4. Le breakpoint est visible dans l'onglet "🔴 Breakpoints"
```

### Exemple 2 : Profilage de Performance
```python
# 1. Écris du code potentiellement lent
import time

def fonction_lente():
    time.sleep(0.5)  # Simule un traitement long
    return "Terminé"

def fonction_rapide():
    return sum(range(1000))

# 2. Appuie sur F7 (au lieu de F5)
# 3. Va dans l'onglet "📊 Performance"
# 4. Vois que fonction_lente() prend 0.5s (critique !)
fonction_lente()
fonction_rapide()
```

### Exemple 3 : Auto-Correction IA
```python
# 1. Décommenter cette ligne avec une erreur :
print(ma_variable)  # ← NameError

# 2. Appuie sur F5
# 3. Va dans l'onglet "🐛 Traceback + Auto-Fix"
# 4. Lis les suggestions :
#    💡 Déclare la variable 'ma_variable' avant de l'utiliser
#    🤖 Auto-fix proposé : ma_variable = None
# 5. Clique sur "✨ Appliquer la correction"
# 6. Le code est corrigé automatiquement !
```

### Exemple 4 : Terminal Intégré
```python
# Onglet "🖥️ Terminal"

# Installer un module :
$ pip install requests

# Exécuter un script :
$ python mon_script.py --arg1 valeur

# Vérifier la version Python :
$ python --version

# Lister les fichiers :
$ ls -la

# Naviguer :
$ cd /mon/projet
$ pwd
```

---

## 🎨 PERSONNALISATION

### Changer de Thème
Menu "🎨 Thème" → Sélectionne un thème :
- **Cyberpunk** : Cyan/Violet futuriste
- **Matrix** : Vert terminal
- **Dracula** : Violet/Rose moderne
- **Nord** : Bleu/Gris nordique
- **Monokai** : Jaune/Vert classique
- **Solarized Dark** : Orange/Bleu confort

Le thème change instantanément (éditeur, console, tous les widgets)

### Créer un Thème Perso
Menu "🎨 Thème" → "Personnaliser les couleurs..."
- Choisis 10 couleurs (fond, texte, accent, erreur, succès...)
- Sauvegarde ton thème
- Utilise-le comme thème par défaut

---

## 📊 RAPPORT DE PERFORMANCE

Exemple de sortie (onglet Performance après F7) :

```
⏱️ PROFILAGE DE PERFORMANCE
═══════════════════════════════════════

Top 10 fonctions les plus lentes :

🔴 CRITIQUE (>100ms)
  fonction_lente() - 500.2 ms (1 appel)
    → Fichier: mon_script.py, ligne 5

⚠️  LENT (10-100ms)
  traitement_donnees() - 45.8 ms (10 appels)
    → Fichier: mon_script.py, ligne 12

✅ RAPIDE (<10ms)
  fonction_rapide() - 0.3 ms (1000 appels)
    → Fichier: mon_script.py, ligne 18

═══════════════════════════════════════
Total : 546.3 ms pour 1011 appels
```

---

## 🐛 AUTO-CORRECTION IA - EXEMPLES

### NameError
**Code original :**
```python
print(nom)  # ❌ NameError: name 'nom' is not defined
```

**Auto-fix proposé :**
```python
nom = None  # 🤖 Auto-fix: Variable définie
print(nom)
```

### ZeroDivisionError
**Code original :**
```python
resultat = 10 / diviseur  # ❌ ZeroDivisionError
```

**Auto-fix proposé :**
```python
if diviseur != 0:  # 🤖 Auto-fix: Check division par zéro
    resultat = 10 / diviseur
```

### TypeError
**Code original :**
```python
total = "Prix: " + 42  # ❌ TypeError: unsupported operand
```

**Auto-fix proposé :**
```python
total = "Prix: " + str(42)  # 🤖 Utilise str() pour convertir
```

---

## 🚀 INSTALLATION & LANCEMENT

### Prérequis
- Python 3.7+
- Tkinter (inclus par défaut sur Windows/Mac, `sudo apt install python3-tk` sur Linux)

### Lancement
```bash
python kerberos_debugger_v4_EXTREME.py
```

### Premier Lancement
1. L'interface s'ouvre avec un code d'exemple
2. Essaye les fonctionnalités :
   - Clique sur une ligne pour ajouter un breakpoint 🔴
   - Appuie sur F5 pour exécuter
   - Appuie sur F7 pour profiler
   - Décommenter une erreur pour voir l'auto-fix

---

## 📝 CHANGELOG v4.0

### ✨ Ajouts Majeurs
- 🔴 Breakpoints visuels (clic sur numéro de ligne)
- 📊 Profileur de performance (F7)
- 🤖 Auto-correction IA (suggestions + code corrigé)
- 🎨 6 thèmes personnalisables
- 🖥️ Terminal bash intégré
- 📈 Graphiques de performance
- 📤 Export rapports HTML/PDF/CSV
- ⌨️ Nouveaux raccourcis (Ctrl+D, Ctrl+/, F9)

### 🔧 Améliorations
- Éditeur : Position curseur en temps réel
- Analyse statique : 10+ types d'erreurs détectées
- Traceback : Contexte enrichi + surlignage ligne
- Console : Tags colorés par type (info/success/error)
- Performance : Détection des fonctions lentes

### 🐛 Corrections
- Gestion des encodages multiples (UTF-8, Latin-1)
- Stabilité du threading
- Mémoire optimisée pour gros fichiers

---

## 🏆 COMPARAISON v3.0 → v4.0

| Fonctionnalité | v3.0 | v4.0 EXTREME |
|----------------|------|--------------|
| Breakpoints | ❌ | ✅ Visuels + onglet |
| Profilage | ❌ | ✅ Complet avec stats |
| Auto-fix IA | ❌ | ✅ 8 types d'erreurs |
| Thèmes | 1 | 6 personnalisables |
| Terminal | ❌ | ✅ Bash intégré |
| Graphiques | ❌ | ✅ Performance |
| Export | TXT | HTML/PDF/CSV |
| Raccourcis | 6 | 15+ |

---

## 💬 SUPPORT & FEEDBACK

### Problèmes Connus
- Profilage : Peut ralentir l'exécution sur gros scripts (normal)
- Terminal : Timeout 30s pour commandes longues
- Breakpoints : Non interactifs (pas de mode step-by-step encore)

### Fonctionnalités Futures (v5.0)
- 🔍 Mode step-by-step interactif (pas à pas)
- 🔬 Analyse mémoire et détection fuites
- 🌐 Support environnements virtuels (venv)
- 🧪 Intégration tests unitaires (pytest)
- 📡 Débogage à distance (SSH)
- 🔗 Intégration Git (blame, diff, commit)

---

## 📜 LICENCE

GPLv3 modifiée – Victor Pozen 🐺

---

## 🐺 À PROPOS

**Kerberos Debugger** est un débogueur Python tout-en-un conçu pour :
- Les développeurs qui veulent un outil complet et visuel
- L'apprentissage du débogage (avec IA pédagogique)
- Le profilage de performance rapide
- La détection d'erreurs AVANT l'exécution

Développé avec ❤️ par Victor Pozen
Version 4.0 EXTREME - Février 2026

---

**Bon débogage ! 🚀🐺**
