"""Indicateurs techniques, décomposition du ratio S/P et outils statistiques.

Fonctions partagées par les notebooks (dossier) et le dashboard : un indicateur a
une seule définition dans tout le projet.

Définitions (sur les marts, mesures additives) :
    fréquence      = sinistres avec suite / années-police
    coût moyen     = charge (payé + réserve restante) / sinistres avec suite
    prime moyenne  = primes acquises / années-police
    S/P            = charge / primes acquises  (= fréquence × coût moyen / prime moyenne)
    taux de résiliation = résiliations / années-police
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

from pipeline.config import CHEMIN_ENTREPOT

MESURES = [
    "nb_contrats_exposes", "annees_police", "prime_acquise", "nb_resiliations", "nb_sinistres_declares",
    "nb_sinistres", "nb_sinistres_sans_suite", "nb_sinistres_atypiques", "montant_paye", "reserve_restante",
    "charge", "charge_hors_atypique",
]


def connexion(chemin: Path = CHEMIN_ENTREPOT) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(chemin), read_only=True)


def lire(sql: str, chemin: Path = CHEMIN_ENTREPOT) -> pd.DataFrame:
    with connexion(chemin) as con:
        return con.sql(sql).df()


def ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les indicateurs à un tableau de mesures additives agrégées."""
    d = df.copy()
    d["frequence"] = d["nb_sinistres"] / d["annees_police"]
    d["cout_moyen"] = d["charge"] / d["nb_sinistres"].replace(0, np.nan)
    d["prime_moyenne"] = d["prime_acquise"] / d["annees_police"]
    d["sp"] = d["charge"] / d["prime_acquise"]
    d["sp_hors_atypique"] = d["charge_hors_atypique"] / d["prime_acquise"]
    d["taux_resiliation"] = d["nb_resiliations"] / d["annees_police"]
    d["part_sans_suite"] = d["nb_sinistres_sans_suite"] / d["nb_sinistres_declares"].replace(0, np.nan)
    d["part_reserve"] = d["reserve_restante"] / d["charge"].replace(0, np.nan)
    return d


def indicateurs(df: pd.DataFrame, axes: list[str]) -> pd.DataFrame:
    """Agrège les mesures selon les axes puis calcule les indicateurs."""
    mesures = [m for m in MESURES if m in df.columns]
    agrege = df.groupby(axes, as_index=False)[mesures].sum() if axes else df[mesures].sum().to_frame().T
    return ratios(agrege)


# --- Décomposition de l'évolution du S/P --------------------------------------------------------


def _moyenne_log(a: float, b: float) -> float:
    """Moyenne logarithmique, poids exacts de la décomposition LMDI."""
    if a == b:
        return a
    return (a - b) / (np.log(a) - np.log(b))


def decomposer_sp(par_annee: pd.DataFrame, charge: str = "charge") -> pd.DataFrame:
    """Décompose la variation annuelle du S/P en effets fréquence, coût moyen et prime moyenne.

    S/P = F × C / P, donc Δln(S/P) = Δln F + Δln C − Δln P exactement. Chaque effet est converti
    en points de S/P par la méthode LMDI (poids = moyenne logarithmique des S/P), ce qui rend la
    somme des effets strictement égale à la variation observée. Le volume d'années-police
    multiplie à la fois la charge et les primes : son effet sur le S/P est nul par construction ;
    on le mesure sur la charge (colonne effet_volume_sur_charge).
    """
    d = par_annee.sort_values("annee").reset_index(drop=True)
    F = d["nb_sinistres"] / d["annees_police"]
    C = d[charge] / d["nb_sinistres"]
    P = d["prime_acquise"] / d["annees_police"]
    SP = d[charge] / d["prime_acquise"]
    lignes = []
    for i in range(1, len(d)):
        poids = _moyenne_log(SP[i], SP[i - 1])
        poids_charge = _moyenne_log(d[charge][i], d[charge][i - 1])
        lignes.append({
            "annee": int(d["annee"][i]),
            "sp_precedent": SP[i - 1],
            "sp": SP[i],
            "variation_sp": SP[i] - SP[i - 1],
            "effet_frequence": poids * np.log(F[i] / F[i - 1]),
            "effet_cout_moyen": poids * np.log(C[i] / C[i - 1]),
            "effet_prime_moyenne": -poids * np.log(P[i] / P[i - 1]),
            "effet_volume": 0.0,
            "variation_charge": d[charge][i] - d[charge][i - 1],
            "effet_volume_sur_charge": poids_charge * np.log(d["annees_police"][i] / d["annees_police"][i - 1]),
        })
    return pd.DataFrame(lignes)


def contributions_segments(df: pd.DataFrame, segment: list[str], annee: int, charge: str = "charge") -> pd.DataFrame:
    """Contribution de chaque segment à la variation du S/P global entre annee-1 et annee.

    S/P = Σ charge_s / Σ primes : la contribution d'un segment est charge_s,t / P_t − charge_s,t-1 / P_t-1.
    Les contributions somment exactement la variation du S/P global.
    """
    primes = df.groupby("annee")["prime_acquise"].sum()
    seg = df[df["annee"].isin([annee - 1, annee])].groupby(segment + ["annee"])[charge].sum().unstack("annee").fillna(0)
    resultat = pd.DataFrame({
        "sp_contribution_precedente": seg[annee - 1] / primes[annee - 1],
        "sp_contribution": seg[annee] / primes[annee],
    })
    resultat["contribution_variation"] = resultat["sp_contribution"] - resultat["sp_contribution_precedente"]
    return resultat.sort_values("contribution_variation").reset_index()


# --- Incertitude -----------------------------------------------------------------------------------


def ic_poisson(nombre: float, exposition: float, niveau: float = 0.95) -> tuple[float, float]:
    """Intervalle exact (Garwood) d'un taux = nombre d'événements / exposition."""
    alpha = 1 - niveau
    bas = stats.chi2.ppf(alpha / 2, 2 * nombre) / 2 if nombre > 0 else 0.0
    haut = stats.chi2.ppf(1 - alpha / 2, 2 * nombre + 2) / 2
    return bas / exposition, haut / exposition


def ic_bootstrap_ratio(numerateur: np.ndarray, denominateur: np.ndarray, n: int = 5000,
                       niveau: float = 0.95, graine: int = 2025) -> tuple[float, float]:
    """Intervalle percentile d'un ratio de sommes Σnum / Σden, par rééchantillonnage des unités.

    L'unité rééchantillonnée est le contrat (ou le sinistre pour un coût moyen) : on respecte
    la corrélation entre les années d'un même contrat et la queue épaisse des coûts.
    """
    rng = np.random.default_rng(graine)
    num, den = np.asarray(numerateur, float), np.asarray(denominateur, float)
    idx = rng.integers(0, len(num), size=(n, len(num)))
    tirages = num[idx].sum(axis=1) / den[idx].sum(axis=1)
    alpha = 1 - niveau
    return float(np.quantile(tirages, alpha / 2)), float(np.quantile(tirages, 1 - alpha / 2))


def test_taux_poisson(n1: float, e1: float, n2: float, e2: float) -> dict:
    """Compare deux taux de Poisson (n événements sur e années-police) : test E de Krishnamoorthy-Thomson."""
    resultat = stats.poisson_means_test(int(n1), e1, int(n2), e2)
    return {"taux_1": n1 / e1, "taux_2": n2 / e2, "rapport": (n1 / e1) / (n2 / e2),
            "statistique": resultat.statistic, "p_valeur": resultat.pvalue}
