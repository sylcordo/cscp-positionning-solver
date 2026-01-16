"""Configuration et constantes pour le solveur de positionnement."""

# Tolérance pour bornes pupitre (modifiable)
TOLERANCE = 1

# Poids pour l'objectif d'optimisation
SLACK_WEIGHT = 1000  # Priorité sur la minimisation des slack
PREF_WEIGHT = 1      # Poids léger pour les préférences
FAIR_WEIGHT = 50     # Poids pour l'équité entre choristes

# Paramètres du solveur
MAX_TIME_IN_SECONDS = 120.0
NUM_SEARCH_WORKERS = 1  # Pour le déterminisme
RANDOM_SEED = 42        # Pour la reproductibilité

# Normalisation des préférences
PREFERENCE_MAPPING = {
    'devant': ['devant', 'avant', 'front', 'frontale', 'frontier'],
    'derriere': ['derriere', 'arriere', 'arrière', 'back', 'behind'],
    'peu importe': ['peu importe', 'peuimporte', 'any', 'indifferent', 'indifférent', '0', 'none', 'n/a', 'na', '']
}

# Valeurs numériques spéciales pour préférences
NUMERIC_PREFS = {
    '1': 'derriere',
    '0': 'peu importe'
}
