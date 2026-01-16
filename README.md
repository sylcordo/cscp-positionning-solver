# 🎵 Solveur de Positionnement des Choristes

Ce projet permet d'optimiser automatiquement le positionnement des choristes sur scène pour plusieurs musiques, en tenant compte de leurs préférences et des contraintes de capacité.

## 📋 Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Structure du projet](#structure-du-projet)
- [Utilisation depuis Google Colab](#utilisation-depuis-google-colab)
- [Configuration de la Google Sheet](#configuration-de-la-google-sheet)
- [Architecture technique](#architecture-technique)

## ✨ Fonctionnalités

- 🎯 **Optimisation multi-musiques** : Assigne automatiquement les rangs (devant/milieu/derrière) pour chaque musique
- 👥 **Équité** : Distribue équitablement les positions entre tous les choristes
- ❤️ **Préférences** : Prend en compte les préférences individuelles de positionnement
- 📊 **Équilibre des pupitres** : Maintient une répartition équilibrée des voix (soprano, alto, ténor, basse)
- 📈 **Statistiques détaillées** : Génère des rapports complets sur les assignations

## 📁 Structure du projet

```
cscp-positionning-solver/
│
├── lib/                      # 📚 Bibliothèque principale
│   ├── __init__.py
│   ├── solver.py             # 🧮 Point d'entrée de l'optimisation
│   └── components/           # 🔧 Composants internes
│       ├── __init__.py
│       ├── config.py         # Configuration et constantes
│       ├── sheets_handler.py # Gestion de Google Sheets
│       ├── data_processor.py # Traitement des données
│       └── optimizer.py      # Logique d'optimisation
│
├── run_colab.py              # 🚀 Interface pour Google Colab
├── COLAB_TEMPLATE.py         # 📋 Template à copier-coller
├── requirements.txt          # 📦 Dépendances Python
└── README.md                 # 📖 Documentation
```

## 🚀 Utilisation depuis Google Colab

### Méthode simple (recommandée pour utilisateurs non-techniques)

1. **Ouvrez Google Colab** : [colab.research.google.com](https://colab.research.google.com)

2. **Créez un nouveau notebook**

3. **Copiez-collez le code suivant dans une cellule** :

```python
# 🎯 INSTALLATION ET LANCEMENT AUTOMATIQUE
# Remplacez VOTRE_USERNAME, VOTRE_REPO et VOTRE_SHEET_ID

SHEET_URL = "https://docs.google.com/spreadsheets/d/VOTRE_SHEET_ID/edit"

print("🚀 Démarrage de l'installation...\n")
!git clone https://github.com/VOTRE_USERNAME/cscp-positionning-solver.git
%cd cscp-positionning-solver

# Installation des dépendances
!pip install --quiet -r requirements.txt

# Lancement de l'optimisation
!python3 run_colab.py --sheet_url "{SHEET_URL}"
```

4. **Modifiez** :
   - `VOTRE_USERNAME` et `VOTRE_REPO` avec vos informations GitHub
   - `VOTRE_SHEET_ID` avec l'ID de votre Google Sheet

5. **Exécutez la cellule** (Shift + Enter)

6. **Suivez les instructions** à l'écran :
   - Autorisez l'accès à votre compte Google
   - Collez l'URL de votre Google Sheet
   - Attendez que l'optimisation se termine

7. **Consultez les résultats** dans votre Google Sheet !

### Ce qui se passe automatiquement

✅ Clone le projet depuis GitHub  
✅ Installe toutes les dépendances nécessaires  
✅ Vous demande l'URL de votre Google Sheet  
✅ Lance l'optimisation  
✅ Écrit les résultats dans votre Google Sheet  
Le script `setup.sh` fait tout automatiquement :

✅ Installe toutes les dépendances nécessaires  
✅ Lance le script d'optimisation  
✅ Vous demande l'URL de votre Google Sheet  
✅ EffectuGoogle Sheet doit contenir **2 onglets obligatoires** :

### 1. Onglet "Choristes"

Colonnes requises :
- `Nom` : Nom du choriste
- `Pupitre` : Soprano, Alto, Ténor, Basse (ou S, A, T, B)
- `M1`, `M2`, `M3`, ... : Une colonne par musique avec les préférences

Valeurs acceptées pour les préférences :
- `devant` / `avant` / `front`
- `derriere` / `arrière` / `back`
- `peu importe` / vide (pas de préférence)

### 2. Onglet "Paramètres"

Colonnes requises :
- `Rang` : devant, milieu, derriere
- `Capacite` (ou `Capacité`) : Nombre de places disponibles pour chaque rang

Exemple :
```
| Rang     | Capacité |
| -------- | -------- |
| devant   | 15       |
| milieu   | 20       |
| derriere | 18       |
```

### Résultats générés

Le script créera automatiquement **3 nouveaux onglets** :

1. **Resultats** : Assignations détaillées par choriste avec compteurs
2. **Stats** : Statistiques globales par musique et par pupitre
3. **Violations** : Contraintes qui n'ont pas pu être respectées (idéalement vide)

## 🛠 Architecture technique

### Modules

- **config.py** : Paramètres d'optimisation (poids, tolérance, etc.)
- **sheets_handler.py** : Interface avec l'API Google Sheets
- **data_processor.py** : Normalisation des données et préparation pour l'optimisation
Le code est organisé dans le dossier `lib/` :

- **lib/config.py** : Paramètres d'optimisation (poids, tolérance, etc.)
- **lib/sheets_handler.py** : Interface avec l'API Google Sheets
- **lib/data_processor.py** : Normalisation des données et préparation pour l'optimisation
- **lib/optimizer.py** : Moteur d'optimisation utilisant OR-Tools CP-SAT

Scripts d'exécution :

- **run_colab.py** : Interface utilisateur pour Google Colab
Le solveur utilise la programmation par contraintes (CP-SAT de Google OR-Tools) pour :

1. **Minimiser les violations** de capacité (priorité maximale)
2. **Équilibrer** la distribution des rangs entre choristes
3. **Respecter** les préférences individuelles (priorité moindre)
4. **Maintenir** l'équilibre entre les pupitres

Les poids par défaut peuvent être modifiés dans [lib/components/config.py](lib/components/config.py).

## 📝 Développement local

Si vous souhaitez modifier le code localement :

```bash
# Cloner le projet
git clone https://github.com/VOTRE_USERNAME/cscp-positionning-solver.git
cd cscp-positionning-solver

# Installer les dépendances
pip install -r requirements.txt

# Note: L'exécution locale nécessite une configuration 
# spécifique de l'authentification Google
```

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

Ce projet est open source et disponible sous licence MIT.

---

**Bon positionnement ! 🎵🎭**
