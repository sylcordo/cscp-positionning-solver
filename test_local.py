#!/usr/bin/env python3
"""
Script de test local - Simule l'exécution de COLAB_TEMPLATE.py en local.
Utilisez ce script pour tester depuis VSCode sans avoir besoin de Google Colab.
"""

import sys
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle


def get_credentials():

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = None
    # Chemin vers ton jeton d'accès (généré après la première connexion)
    token_file = "token.pickle"
    # Chemin vers le fichier téléchargé depuis la console Google Cloud
    client_secrets_file = "credentials.json"

    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # On utilise le fichier JSON local au lieu du dictionnaire en dur
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, SCOPES
            )
            # run_local_server est la méthode recommandée pour le local
            creds = flow.run_local_server(port=0)
        with open(token_file, "wb") as token:
            pickle.dump(creds, token)

    return creds


def main():
    """Fonction principale de test local."""

    print("=" * 60)
    print("   🧪 TEST LOCAL - Solveur de Positionnement")
    print("=" * 60)
    print()

    # 1. Obtenir les credentials
    creds = get_credentials()

    # 2. Demander l'URL ou la prendre en argument
    if len(sys.argv) > 1:
        sheet_url = sys.argv[1]
        print(f"📋 URL fournie: {sheet_url}\n")
    else:
        print("📋 Configuration de la Google Sheet")
        sheet_url = input("🔗 URL de la Google Sheet: ").strip()
        print()

    if not sheet_url:
        print("❌ URL vide")
        return False

    print("=" * 60)
    print()

    # 3. Importer et lancer l'optimisation
    from lib.solver import main as solve

    success = solve(sheet_url, creds)

    print()
    if success:
        print("🎉 Test local réussi!")
        print(f"🔗 Consultez vos résultats: {sheet_url}")
    else:
        print("⚠️  Le test a rencontré des problèmes")

    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
