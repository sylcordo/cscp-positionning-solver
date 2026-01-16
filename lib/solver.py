"""
Script principal pour optimiser le positionnement des choristes.
Utilise Google Sheets comme source et destination des données.
"""

import sys
import traceback
from .components import SheetsHandler, DataProcessor, PositionOptimizer


def main(sheet_url, credentials):
    """
    Fonction principale d'optimisation.

    Args:
        sheet_url: URL de la Google Sheet
        credentials: Credentials Google authentifiés
    """
    try:
        print("🔗 Connexion à Google Sheets...")
        sheets = SheetsHandler(sheet_url, credentials)

        print("📊 Lecture des données...")
        df_choristes = sheets.read_choristes()
        df_params = sheets.read_params()

        print(f"✅ {len(df_choristes)} choristes chargés")

        print("🔧 Préparation des données...")
        data_processor = DataProcessor(df_choristes, df_params)
        print(
            f"✅ {len(data_processor.music_cols)} musiques détectées: {', '.join(data_processor.music_cols)}"
        )

        print("🧮 Lancement de l'optimisation...")
        optimizer = PositionOptimizer(data_processor)
        success, assignments_per_music, assign_results, violations = optimizer.solve()

        if success:
            print("✅ Optimisation réussie!")
        else:
            print("⚠️  Solution sous-optimale trouvée")

        print("📝 Préparation des résultats...")
        results_df = data_processor.prepare_results_dataframe(assignments_per_music)
        stats_df = data_processor.prepare_stats_dataframe(assign_results)
        violations_df = data_processor.prepare_violations_dataframe(
            assignments_per_music
        )

        print("💾 Écriture des résultats dans Google Sheets...")
        sheets.write_results(results_df, stats_df, violations_df)

        print("\n" + "=" * 50)
        print("✅ Terminé avec succès!")
        print("=" * 50)
        print("📊 Consultez les onglets suivants dans votre Google Sheet:")
        print("   • Resultats   : Assignations par choriste")
        print("   • Stats       : Statistiques globales")
        print("   • Violations  : Contraintes violées")

        return True

    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ ERREUR lors de l'exécution")
        print("=" * 50)
        print(f"Message: {str(e)}")
        print("\nDétails:")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Ce bloc est pour exécution locale uniquement
    # Pour Google Colab, utilisez run_colab.py
    print("⚠️  Ce script doit être exécuté depuis Google Colab")
    print("Utilisez le fichier run_colab.py ou le notebook template")
    sys.exit(1)
