"""Logique d'optimisation avec OR-Tools CP-SAT."""

from ortools.sat.python import cp_model
from .config import (
    SLACK_WEIGHT,
    PREF_WEIGHT,
    FAIR_WEIGHT,
    MAX_TIME_IN_SECONDS,
    NUM_SEARCH_WORKERS,
    RANDOM_SEED,
)


class PositionOptimizer:
    """Classe pour optimiser les positions des choristes."""

    def __init__(self, data_processor):
        """
        Initialise l'optimiseur.

        Args:
            data_processor: Instance de DataProcessor avec les données
        """
        self.dp = data_processor
        self.N = len(self.dp.df)
        self.M = len(self.dp.music_cols)
        self.rangs = self.dp.rangs
        self.capacites = self.dp.capacites

    def solve(self):
        """
        Résout le problème d'optimisation.

        Returns:
            Tuple (success, assignments_per_music, assign_results, violations)
            - success: True si optimal/faisable, False sinon
            - assignments_per_music: Dict {musique: [rangs par personne]}
            - assign_results: Liste de dicts pour les stats
            - violations: Liste de dicts avec les slacks par musique
        """
        if self.M == 0:
            raise ValueError("Aucune colonne musique détectée.")

        # Calculs préliminaires
        total_slots_per_rank = {
            r: self.capacites.get(r, 0) * self.M for r in self.rangs
        }
        target_per_person_rank = {}
        for r in self.rangs:
            target_per_person_rank[r] = int(
                round(total_slots_per_rank[r] / max(1, self.N))
            )

        # Construire le modèle
        model = cp_model.CpModel()

        # Variables x[(i,r,mi)] : personne i assignée au rang r pour musique mi
        x = {}
        for i in range(self.N):
            for r in self.rangs:
                for mi in range(self.M):
                    x[(i, r, mi)] = model.NewBoolVar(f"x_i{i}_r{r}_m{mi}")

        # Contrainte: chaque personne exactement un rang par musique
        for i in range(self.N):
            for mi in range(self.M):
                model.Add(sum(x[(i, r, mi)] for r in self.rangs) == 1)

        # Préférences par musique
        pref_list_per_music = self.dp.get_preferences_per_music()

        # Contraintes de capacité avec slacks
        capacity_slacks = []
        capacity_slack_map = {}
        for mi in range(self.M):
            for r in self.rangs:
                cap = self.capacites.get(r, 0)
                s_exceed = model.NewIntVar(
                    0, self.N * self.M, f"slack_cap_exceed_{r}_m{mi}"
                )
                capacity_slacks.append(s_exceed)
                capacity_slack_map[(r, mi)] = s_exceed
                model.Add(sum(x[(i, r, mi)] for i in range(self.N)) <= cap + s_exceed)

        # Contraintes d'équilibre des pupitres avec slacks
        pup_slacks = []
        for mi in range(self.M):
            for r in self.rangs:
                cap = self.capacites.get(r, 0)
                bounds = self.dp.pupitre_bounds_for_rank(r)
                for p in self.dp.pupitres:
                    idxs = [
                        i for i in range(self.N) if self.dp.df.loc[i, "Pupitre"] == p
                    ]
                    if len(idxs) == 0:
                        continue
                    mn, mx = bounds.get(p, (0, cap))
                    s_low = model.NewIntVar(
                        0, self.N * self.M, f"slack_low_{r}_{p}_m{mi}"
                    )
                    s_high = model.NewIntVar(
                        0, self.N * self.M, f"slack_high_{r}_{p}_m{mi}"
                    )
                    pup_slacks.extend([s_low, s_high])
                    model.Add(sum(x[(i, r, mi)] for i in idxs) + s_low >= mn)
                    model.Add(sum(x[(i, r, mi)] for i in idxs) - s_high <= mx)

        # Termes de coût pour les préférences
        pref_terms = []
        for mi in range(self.M):
            pref_list = pref_list_per_music[mi]
            for i in range(self.N):
                pref = pref_list[i]
                if pref == "devant":
                    desired_order = [
                        r for r in ["devant", "milieu", "derriere"] if r in self.rangs
                    ]
                elif pref == "derriere":
                    desired_order = [
                        r for r in ["derriere", "milieu", "devant"] if r in self.rangs
                    ]
                else:
                    desired_order = [
                        r for r in ["devant", "milieu", "derriere"] if r in self.rangs
                    ]

                for r in self.rangs:
                    if r in desired_order:
                        cost = desired_order.index(r)
                    else:
                        cost = len(desired_order)
                    if cost != 0:
                        pref_terms.append((PREF_WEIGHT * cost, x[(i, r, mi)]))

        # Équité : variables de déviation par personne par rang
        dev_vars = []
        for i in range(self.N):
            for r in self.rangs:
                count_ir = model.NewIntVar(0, self.M, f"count_{i}_{r}")
                model.Add(count_ir == sum(x[(i, r, mi)] for mi in range(self.M)))
                target = target_per_person_rank[r]
                dev = model.NewIntVar(0, self.M, f"dev_{i}_{r}")
                dev_vars.append(dev)
                model.Add(count_ir - target <= dev)
                model.Add(target - count_ir <= dev)

        # Objectif : somme pondérée
        all_slacks = list(capacity_slack_map.values()) + pup_slacks
        obj_terms = []
        for s in all_slacks:
            obj_terms.append((SLACK_WEIGHT, s))
        for d in dev_vars:
            obj_terms.append((FAIR_WEIGHT, d))
        for coef, var in pref_terms:
            obj_terms.append((coef, var))

        model.Minimize(sum(coef * var for coef, var in obj_terms))

        # Résoudre
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = MAX_TIME_IN_SECONDS
        solver.parameters.num_search_workers = NUM_SEARCH_WORKERS
        solver.parameters.random_seed = RANDOM_SEED

        status = solver.Solve(model)

        # Extraire les résultats
        success = status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

        assignments_per_music = {}
        assign_results = []
        violations = []

        if success:
            for mi, mus in enumerate(self.dp.music_cols):
                assigned_for_m = []
                for i in range(self.N):
                    assigned_rank = None
                    for r in self.rangs:
                        if solver.Value(x[(i, r, mi)]) == 1:
                            assigned_rank = r
                            break
                    if assigned_rank is None:
                        assigned_rank = "UNASSIGNED"

                    assign_results.append(
                        {
                            "Musique": mus,
                            "ID": self.dp.df.loc[i, "ID"],
                            "Nom": self.dp.df.loc[i, "Nom"],
                            "Pupitre": self.dp.df.loc[i, "Pupitre"],
                            "Rang": assigned_rank,
                        }
                    )
                    assigned_for_m.append(assigned_rank)

                assignments_per_music[mus] = assigned_for_m

            # Calcul des violations
            for mi, mus in enumerate(self.dp.music_cols):
                slack_sum = 0
                for r in self.rangs:
                    slack_sum += int(solver.Value(capacity_slack_map[(r, mi)]))
                violations.append({"Musique": mus, "Slack_total": int(slack_sum)})
        else:
            # Fallback: UNASSIGNED partout
            for mus in self.dp.music_cols:
                assignments_per_music[mus] = ["UNASSIGNED"] * self.N
                for i in range(self.N):
                    assign_results.append(
                        {
                            "Musique": mus,
                            "ID": self.dp.df.loc[i, "ID"],
                            "Nom": self.dp.df.loc[i, "Nom"],
                            "Pupitre": self.dp.df.loc[i, "Pupitre"],
                            "Rang": "UNASSIGNED",
                        }
                    )
                violations.append({"Musique": mus, "Slack_total": None})

        return success, assignments_per_music, assign_results, violations
