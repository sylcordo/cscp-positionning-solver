"""
Bibliothèque pour le solveur de positionnement des choristes.
"""

from .components import (
    SheetsHandler,
    DataProcessor,
    PositionOptimizer,
    TOLERANCE,
    SLACK_WEIGHT,
    PREF_WEIGHT,
    FAIR_WEIGHT,
    MAX_TIME_IN_SECONDS,
    NUM_SEARCH_WORKERS,
    RANDOM_SEED,
)

from .solver import main

__all__ = [
    "main",
    "SheetsHandler",
    "DataProcessor",
    "PositionOptimizer",
    "TOLERANCE",
    "SLACK_WEIGHT",
    "PREF_WEIGHT",
    "FAIR_WEIGHT",
    "MAX_TIME_IN_SECONDS",
    "NUM_SEARCH_WORKERS",
    "RANDOM_SEED",
]
