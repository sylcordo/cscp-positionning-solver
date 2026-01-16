"""Traitement et préparation des données pour l'optimisation."""

import pandas as pd
import math
from .config import PREFERENCE_MAPPING, NUMERIC_PREFS, TOLERANCE


class DataProcessor:
    """Classe pour traiter et préparer les données."""

    def __init__(self, df_choristes, df_params):
        """
        Initialise le processeur de données.

        Args:
            df_choristes: DataFrame des choristes
            df_params: DataFrame des paramètres
        """
        self.df = df_choristes
        self.params = df_params
        self.music_cols = self._detect_music_columns()
        self.rangs, self.capacites = self._extract_ranks_capacities()
        self.pupitres = self.df["Pupitre"].dropna().unique().tolist()
        self.total_by_pup = self.df["Pupitre"].value_counts().to_dict()

    def _detect_music_columns(self):
        """Détecte les colonnes de musiques (commencent par 'M')."""
        music_cols = [c for c in self.df.columns if str(c).upper().startswith("M")]
        return sorted(
            music_cols, key=lambda s: int("".join(filter(str.isdigit, str(s))) or 0)
        )

    def _extract_ranks_capacities(self):
        """Extrait les rangs et capacités depuis les paramètres."""
        if "Rang" not in self.params.columns:
            raise Exception("L'onglet Params doit contenir la colonne 'Rang'.")

        cap_col = None
        for col in ["Capacite", "Capacité"]:
            if col in self.params.columns:
                cap_col = col
                break

        if cap_col is None:
            raise Exception(
                "L'onglet Params doit contenir la colonne 'Capacite' ou 'Capacité'."
            )

        rangs = self.params["Rang"].astype(str).str.lower().tolist()
        capacites = dict(
            zip(
                self.params["Rang"].astype(str).str.lower(),
                self.params[cap_col].astype(int),
            )
        )

        return rangs, capacites

    def normalize_preference(self, raw_value):
        """
        Normalise une préférence brute en 'devant', 'derriere' ou 'peu importe'.

        Args:
            raw_value: Valeur brute de la préférence

        Returns:
            Préférence normalisée
        """
        if pd.isna(raw_value):
            return "peu importe"

        s = str(raw_value).strip().lower()

        # Vérifier les valeurs numériques spéciales
        if s in NUMERIC_PREFS:
            return NUMERIC_PREFS[s]

        # Vérifier les mappings de préférences
        for pref_normalized, variants in PREFERENCE_MAPPING.items():
            if s in variants:
                return pref_normalized

        # Vérifications par sous-chaînes
        if "dev" in s:
            return "devant"
        elif "der" in s or "arri" in s:
            return "derriere"
        else:
            return "peu importe"

    def get_preferences_per_music(self):
        """
        Retourne les préférences normalisées pour chaque musique.

        Returns:
            Liste de listes de préférences [musique][personne]
        """
        pref_list_per_music = []
        for mus in self.music_cols:
            pref_list = []
            for i in range(len(self.df)):
                raw = self.df.loc[i, mus]
                pref = self.normalize_preference(raw)
                pref_list.append(pref)
            pref_list_per_music.append(pref_list)
        return pref_list_per_music

    def pupitre_bounds_for_rank(self, rank, tolerance=TOLERANCE):
        """
        Calcule les bornes min/max par pupitre pour un rang donné.

        Args:
            rank: Le rang concerné
            tolerance: Tolérance pour les bornes

        Returns:
            Dict {pupitre: (min, max)}
        """
        cap = self.capacites.get(rank, 0)
        n_total = len(self.df)
        bounds = {}

        for p, tot in self.total_by_pup.items():
            ideal = tot / n_total * cap if n_total > 0 else 0
            mn = max(0, math.floor(ideal - tolerance))
            mx = min(cap, math.ceil(ideal + tolerance))
            bounds[p] = (mn, mx)

        return bounds

    def prepare_results_dataframe(self, assignments_per_music):
        """
        Prépare le DataFrame de résultats avec les comptages par rang.

        Args:
            assignments_per_music: Dict {musique: [rangs assignés par personne]}

        Returns:
            DataFrame des résultats
        """
        results_df = self.df.copy()

        # Remplacer les colonnes musique par les rangs assignés
        for mus, assignments in assignments_per_music.items():
            results_df[mus] = assignments

        # Supprimer la colonne ID si présente
        if "ID" in results_df.columns:
            results_df = results_df.drop(columns=["ID"])

        # Ajouter les colonnes de comptage
        results_df["count_devant"] = 0
        results_df["count_milieu"] = 0
        results_df["count_derriere"] = 0

        for idx in range(len(results_df)):
            vals = results_df.loc[idx, self.music_cols].astype(str).str.lower()
            results_df.at[idx, "count_devant"] = int((vals == "devant").sum())
            results_df.at[idx, "count_milieu"] = int((vals == "milieu").sum())
            results_df.at[idx, "count_derriere"] = int((vals == "derrière").sum())

        return results_df

    def prepare_stats_dataframe(self, assign_results):
        """
        Prépare le DataFrame de statistiques pivotées.

        Args:
            assign_results: Liste de dicts avec les assignations

        Returns:
            DataFrame des statistiques
        """
        sub = pd.DataFrame(assign_results)
        stats_dict = {}

        for mus in self.music_cols:
            sub_m = sub[sub["Musique"] == mus]

            # Totaux par rang
            for r in self.rangs:
                key = f"total_{r}"
                stats_dict.setdefault(key, {})[mus] = int((sub_m["Rang"] == r).sum())

            # Totaux par rang x pupitre
            for r in self.rangs:
                for p in self.pupitres:
                    key = f"count_{r}_{p}"
                    stats_dict.setdefault(key, {})[mus] = int(
                        ((sub_m["Rang"] == r) & (sub_m["Pupitre"] == p)).sum()
                    )

            # Unassigned
            stats_dict.setdefault("unassigned", {})[mus] = int(
                (sub_m["Rang"] == "UNASSIGNED").sum()
            )

        # Construction du DataFrame pivoté
        stats_df = pd.DataFrame.from_dict(stats_dict, orient="index")
        stats_df.insert(0, "Indicateur", stats_df.index)
        stats_df.reset_index(drop=True, inplace=True)

        return stats_df

    def prepare_violations_dataframe(self, assignments_per_music):
        """
        Prépare le DataFrame de violations au format similaire aux résultats.

        Pour chaque choriste et chaque musique, calcule l'écart par rapport à son souhait:
        - 0: souhait respecté ou "peu importe"
        - 1: écart de 1 rang (ex: milieu au lieu de devant, ou derrière au lieu de milieu)
        - 2: écart de 2 rangs (ex: derrière au lieu de devant, ou devant au lieu de derrière)

        Args:
            assignments_per_music: Dict {musique: [rangs assignés par personne]}

        Returns:
            DataFrame des violations (1 ligne par choriste, 1 colonne par musique)
        """
        # Mapping des écarts entre les rangs
        rank_distance = {
            ("devant", "devant"): 0,
            ("devant", "milieu"): 1,
            ("devant", "derriere"): 2,
            ("milieu", "milieu"): 0,
            ("milieu", "devant"): 1,
            ("milieu", "derriere"): 1,
            ("derriere", "derriere"): 0,
            ("derriere", "milieu"): 1,
            ("derriere", "devant"): 2,
        }

        # Créer le DataFrame de base avec Nom et Pupitre
        violations_df = self.df[["Nom", "Pupitre"]].copy()

        # Pour chaque musique, calculer les violations
        for mus in self.music_cols:
            assignments = assignments_per_music.get(mus, [])
            violations_col = []

            for idx in range(len(self.df)):
                # Récupérer la préférence du choriste
                raw_pref = self.df.loc[idx, mus]
                pref = self.normalize_preference(raw_pref)

                # Récupérer l'assignation
                assigned = assignments[idx] if idx < len(assignments) else "UNASSIGNED"
                assigned = str(assigned).lower()

                # Calculer l'écart
                if pref == "peu importe":
                    # Si "peu importe", toujours 0 (pas de violation)
                    violation = 0
                elif assigned == "unassigned" or assigned not in [
                    "devant",
                    "milieu",
                    "derriere",
                ]:
                    violation = 0  # Pas d'écart si pas assigné
                else:
                    # Calculer la distance entre la préférence et l'assignation
                    key = (pref, assigned)
                    violation = rank_distance.get(key, 0)

                violations_col.append(violation)

            violations_df[mus] = violations_col

        return violations_df
