"""Tests des fonctions d'analyse : la décomposition doit être exacte."""

import numpy as np
import pandas as pd

from analyse.indicateurs import contributions_segments, decomposer_sp, ic_poisson


def donnees():
    return pd.DataFrame({
        "annee": [2021, 2022, 2023],
        "annees_police": [100.0, 150.0, 160.0],
        "nb_sinistres": [5, 9, 7],
        "charge": [20_000.0, 45_000.0, 60_000.0],
        "prime_acquise": [40_000.0, 61_000.0, 66_000.0],
    })


def test_decomposition_somme_exactement_la_variation():
    d = decomposer_sp(donnees())
    somme = d[["effet_frequence", "effet_cout_moyen", "effet_prime_moyenne", "effet_volume"]].sum(axis=1)
    assert np.allclose(somme, d["variation_sp"])


def test_contributions_segments_somment_la_variation_globale():
    df = pd.DataFrame({
        "annee": [2022, 2022, 2023, 2023],
        "segment": ["A", "B", "A", "B"],
        "charge": [10.0, 30.0, 25.0, 20.0],
        "prime_acquise": [50.0, 50.0, 60.0, 40.0],
    })
    c = contributions_segments(df, ["segment"], 2023)
    assert np.isclose(c["contribution_variation"].sum(), 45 / 100 - 40 / 100)


def test_ic_poisson_encadre_le_taux():
    bas, haut = ic_poisson(40, 1000)
    assert bas < 0.04 < haut
