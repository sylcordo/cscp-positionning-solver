#!/bin/bash
# Script de setup pour environnement de développement local

set -e  # Arrêter en cas d'erreur

echo "🔧 Setup de l'environnement de développement local"
echo ""

# Créer le venv s'il n'existe pas
if [ ! -d ".venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv .venv
    echo "✅ Environnement virtuel créé"
else
    echo "✅ Environnement virtuel déjà présent"
fi

echo ""
echo "🔌 Activation de l'environnement virtuel..."
source .venv/bin/activate

echo ""
echo "📥 Installation des dépendances..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet google-auth-oauthlib google-auth-httplib2

echo ""
echo "✅ Setup terminé!"
echo ""
echo "Pour activer l'environnement virtuel:"
echo "  source .venv/bin/activate"
echo ""
echo "Pour tester l'optimisation:"
echo "  python test_local.py"
