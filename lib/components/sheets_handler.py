"""Gestion de la connexion et des opérations avec Google Sheets."""

import gspread
import pandas as pd


class SheetsHandler:
    """Classe pour gérer les interactions avec Google Sheets."""
    
    def __init__(self, sheet_url, credentials):
        """
        Initialise la connexion à Google Sheets.
        
        Args:
            sheet_url: URL de la Google Sheet
            credentials: Credentials Google authentifiés
        """
        self.gc = gspread.authorize(credentials)
        self.sheet = self.gc.open_by_url(sheet_url)
        
    def read_choristes(self):
        """Lit l'onglet 'Choristes' et retourne un DataFrame."""
        chor_sheet = self.sheet.worksheet("Choristes")
        df = pd.DataFrame(chor_sheet.get_all_records())
        
        # Ajoute un ID si absent
        if 'ID' not in df.columns:
            df['ID'] = df.index
            
        return df
    
    def read_params(self):
        """Lit l'onglet 'Paramètres' et retourne un DataFrame."""
        params_sheet = self.sheet.worksheet("Paramètres")
        params = pd.DataFrame(params_sheet.get_all_records())
        
        # Normalise les noms de colonnes
        params.columns = [c.strip() for c in params.columns]
        
        return params
    
    def write_results(self, results_df, stats_df, violations_df):
        """
        Écrit les résultats dans 3 onglets de la Google Sheet.
        
        Args:
            results_df: DataFrame des résultats par choriste
            stats_df: DataFrame des statistiques
            violations_df: DataFrame des violations
        """
        self._write_df_to_sheet('Resultats', results_df)
        self._write_df_to_sheet('Stats', stats_df)
        self._write_df_to_sheet('Violations', violations_df)
        
    def _write_df_to_sheet(self, sheet_name, df):
        """
        Helper pour (re)créer un onglet et y écrire un DataFrame.
        
        Args:
            sheet_name: Nom de l'onglet
            df: DataFrame à écrire
        """
        try:
            ws = self.sheet.worksheet(sheet_name)
            self.sheet.del_worksheet(ws)
        except Exception:
            pass
        
        ws = self.sheet.add_worksheet(
            title=sheet_name,
            rows=str(len(df) + 5),
            cols=str(len(df.columns) + 2)
        )
        ws.update([df.columns.values.tolist()] + df.values.tolist())
