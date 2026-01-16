# CELL #1
# 📄 CONFIGURATION - Remplacez par l'URL de votre Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/VOTRE_SHEET_ID/edit"

# CELL #2
import os
import subprocess
from pathlib import Path

REPO_NAME = "cscp-positionning-solver"
REPO_URL = "https://github.com/sylcordo/cscp-positionning-solver.git"

print("🚀 Démarrage de l'installation...\n")

cwd = Path.cwd()
repo_path = cwd / REPO_NAME

# 1️⃣ Cas : on est déjà dans le repo
if cwd.name == REPO_NAME:
    print(f"→ Déjà dans {REPO_NAME}, git pull")
    subprocess.run(["git", "pull"], check=True)

# 2️⃣ Cas : repo présent au même niveau
elif repo_path.exists() and (repo_path / ".git").is_dir():
    print(f"→ {REPO_NAME} trouvé, git pull")
    subprocess.run(["git", "-C", str(repo_path), "pull"], check=True)
    os.chdir(repo_path)

# 3️⃣ Cas : repo absent → clone
else:
    print(f"→ Clonage du repo")
    subprocess.run(["git", "clone", REPO_URL], check=True)
    os.chdir(repo_path)

# 4️⃣ Sécurité : afficher le dossier courant
print(f"\n📂 Répertoire courant : {Path.cwd()}\n")

# 📦 Dépendances
print("📦 Installation des dépendances...")
subprocess.run(["pip", "install", "--quiet", "-r", "requirements.txt"], check=True)
print("✅ Installation terminée!\n")

# 🎯 Lancement
print("🎯 Lancement de l'optimisation...\n")
from run_colab import run_optimization

run_optimization(sheet_url=SHEET_URL)
