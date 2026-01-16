"""
Script d'exécution pour Google Colab.
Ce script demande l'URL de la Google Sheet et lance l'optimisation.
"""

import argparse

# Importer les modules nécessaires pour Google Colab
from google.colab import auth
from google.auth import default

# Importer le solveur
from lib.solver import main


def print_banner():
    """Affiche une bannière stylée."""
    print("=" * 60)
    print("   🎵 SOLVEUR DE POSITIONNEMENT DES CHORISTES 🎭")
    print("=" * 60)
    print()


def run_optimization(sheet_url=None):
    """Fonction principale pour Google Colab.

    Args:
        sheet_url: URL de la Google Sheet (optionnel, sinon demandé à l'utilisateur)
    """

    print_banner()

    # 1) Authentification Google
    print("🔐 Authentification Google en cours...")
    auth.authenticate_user()
    creds, project = default()
    print("✅ Authentification réussie!\n")

    # 2) Récupérer ou demander l'URL de la Google Sheet
    if not sheet_url:
        print("📋 Veuillez fournir l'URL de votre Google Sheet")
        print("   (Exemple: https://docs.google.com/spreadsheets/d/...)")
        print()
        sheet_url = input("🔗 URL de la Google Sheet: ").strip()

    if not sheet_url:
        print("❌ Erreur: URL vide")
        return False

    if "docs.google.com/spreadsheets" not in sheet_url:
        print("⚠️  Attention: L'URL ne semble pas être une Google Sheet valide")
        confirm = input("   Continuer quand même? (o/n): ").strip().lower()
        if confirm != "o":
            print("❌ Annulé par l'utilisateur")
            return False

    print()
    print("=" * 60)
    print()

    # 3) Lancer l'optimisation
    success = main(sheet_url, creds)

    print()
    if success:
        print("🎉 Tout s'est bien passé!")
        print(f"🔗 Consultez vos résultats: {sheet_url}")
    else:
        print("⚠️  L'optimisation a rencontré des problèmes")
        print("   Vérifiez les messages d'erreur ci-dessus")

    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Solveur de positionnement des choristes"
    )
    parser.add_argument("--sheet_url", type=str, help="URL de la Google Sheet")
    args = parser.parse_args()

    run_optimization(sheet_url=args.sheet_url)
