# 🎯 CELLULE À COPIER-COLLER DANS GOOGLE COLAB
# ===============================================
#
# Instructions:
# 1. Ouvrez Google Colab (colab.research.google.com)
# 2. Créez un nouveau notebook
# 3. Copiez-collez TOUT le contenu de ce fichier dans une cellule
# 4. Remplacez 'VOTRE_USERNAME' et 'VOTRE_REPO' par vos vrais noms
# 5. Remplacez l'URL de la Google Sheet ci-dessous
# 6. Exécutez la cellule (Shift + Enter)
#
# ===============================================

# 📄 CONFIGURATION - Remplacez par l'URL de votre Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/VOTRE_SHEET_ID/edit"

# 📥 Clonage du projet
print("🚀 Démarrage de l'installation...\n")
!git clone https://github.com/VOTRE_USERNAME/VOTRE_REPO.git
%cd VOTRE_REPO

# 📚 Installation des dépendances
print("📦 Installation des dépendances...")
!pip install --quiet -r requirements.txt
print("✅ Installation terminée!\n")

# 🎯 Lancement de l'optimisation
print("🎯 Lancement de l'optimisation...\n")
!python3 run_colab.py --sheet_url "{SHEET_URL}"

