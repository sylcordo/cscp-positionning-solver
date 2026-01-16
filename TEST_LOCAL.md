# 🧪 Test Local - Guide Rapide

Pour tester le projet en local depuis VSCode (sans Google Colab).

## 🚀 Quick Start (Exactement comme Colab !)

### 1. Setup automatique

```bash
# Crée le .venv et installe tout
bash bin/setup.sh

# Active l'environnement
source .venv/bin/activate
```

### 2. Lancer le test

```bash
# Méthode 1: Mode interactif (demande l'URL)
python test_local.py

# Méthode 2: Avec l'URL en argument
python test_local.py "https://docs.google.com/spreadsheets/d/VOTRE_SHEET_ID/edit"
```

## ✅ C'est tout !

**À la première exécution** :
- 🌐 Une fenêtre de navigateur s'ouvrira
- 🔐 Connectez-vous avec votre compte Google (celui qui a accès à la Sheet)
- ⚠️ Google affichera "Cette application n'est pas vérifiée" → cliquez sur **"Avancé"** puis **"Accéder à ..."**
- ✅ Autorisez l'accès aux Google Sheets
- 💾 Le token est sauvegardé pour les prochaines fois

**Ensuite** : Plus besoin de se reconnecter ! Le token est sauvegardé dans `~/.config/gspread/token.pickle`

**Exactement comme Google Colab** : Utilise les mêmes credentials OAuth publics que gspread !

Le script `test_local.py` simule exactement ce qui se passe dans Google Colab :
- ✅ Authentification Google (interactive, zéro config !)
- ✅ Lecture de la Google Sheet
- ✅ Optimisation
- ✅ Écriture des résultats

## 🐛 Problèmes courants

**Erreur: "gspread-oauth not found"**
→ Relancez `bash bin/setup.sh`

**Erreur: "Permission denied" ou "403"**
→ Vérifiez que vous êtes propriétaire de la Google Sheet (ou qu'elle est partagée avec vous en édition)

**Fenêtre de navigateur ne s'ouvre pas**
→ Vérifiez votre connexion internet

---

Pour plus de détails, voir le [README.md](README.md) principal.
