"""Tests de l'ingestion : idempotence, rechargement d'un mois, livraisons anormales.

Chaque test travaille sur une copie des sources et un entrepôt temporaire :
l'entrepôt de travail (data/warehouse) n'est jamais touché.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

from pipeline import ingest
from pipeline.config import DOSSIER_SOURCES, RACINE

MOIS_TEST = "2024_03"  # mois dont l'en-tête diffère des autres (montant_eur en première colonne)

pytestmark = pytest.mark.skipif(not DOSSIER_SOURCES.is_dir(), reason="sources absentes (make sources)")


@pytest.fixture
def env(tmp_path):
    sources = tmp_path / "sources"
    shutil.copytree(DOSSIER_SOURCES, sources, ignore=shutil.ignore_patterns(".DS_Store"))
    return sources, tmp_path / "boreal.duckdb"


def dbt_build(entrepot: Path) -> None:
    resultat = subprocess.run(
        [str(Path(sys.executable).parent / "dbt"), "build", "--project-dir", "dbt", "--profiles-dir", "dbt",
         "--target-path", str(entrepot.parent / "dbt_target"), "--log-path", str(entrepot.parent / "dbt_logs")],
        cwd=RACINE, env={**os.environ, "BOREAL_DB": str(entrepot)}, capture_output=True, text=True,
    )
    assert resultat.returncode == 0, resultat.stdout[-3000:]


def photo(entrepot: Path) -> dict:
    """Empreinte du contenu métier de l'entrepôt (hors colonnes de date de chargement)."""
    with duckdb.connect(str(entrepot), read_only=True) as con:
        def q(sql):
            return con.execute(sql).fetchone()
        return {
            "raw.reglements": q(
                "SELECT count(*), sum(hash(paiement_id, sinistre_id, date_paiement, montant, _fichier_source, _numero_ligne))"
                " FROM raw.reglements"
            ),
            "raw.reglements du mois": q(
                f"SELECT count(*) FROM raw.reglements WHERE _fichier_source = 'reglements/reglements_{MOIS_TEST}.csv'"
            ),
            "core.fct_reglement": q(
                "SELECT count(*), count(DISTINCT paiement_id), sum(montant),"
                " sum(hash(paiement_id, sinistre_id, date_paiement, montant, _fichier_source, nb_livraisons))"
                " FROM core.fct_reglement"
            ),
        }


def statuts(resultats: list[dict]) -> dict[str, str]:
    return {r["fichier"]: r["statut"] for r in resultats}


def test_relancer_le_pipeline_ne_change_rien(env):
    sources, entrepot = env
    premier = ingest.executer(entrepot, sources)
    assert set(statuts(premier).values()) == {"CHARGE"}
    dbt_build(entrepot)
    avant = photo(entrepot)

    second = ingest.executer(entrepot, sources)
    assert set(statuts(second).values()) == {"IGNORE"}
    dbt_build(entrepot)
    assert photo(entrepot) == avant


def test_rejouer_un_mois_ne_cree_aucun_doublon(env):
    sources, entrepot = env
    ingest.executer(entrepot, sources)
    dbt_build(entrepot)
    avant = photo(entrepot)

    fichier = f"reglements/reglements_{MOIS_TEST}.csv"
    resultats = ingest.executer(entrepot, sources, sources=["reglements"], forcer={fichier})
    assert statuts(resultats)[fichier] == "RECHARGE"
    dbt_build(entrepot)

    assert photo(entrepot) == avant
    with duckdb.connect(str(entrepot), read_only=True) as con:
        nb, distincts = con.execute("SELECT count(*), count(DISTINCT paiement_id) FROM core.fct_reglement").fetchone()
    assert nb == distincts


def test_meme_mois_livre_deux_fois_sous_un_autre_nom_est_refuse(env):
    sources, entrepot = env
    ingest.executer(entrepot, sources)
    copie = sources / "reglements" / f"reglements_{MOIS_TEST}_bis.csv"
    shutil.copy(sources / "reglements" / f"reglements_{MOIS_TEST}.csv", copie)

    resultats = statuts(ingest.executer(entrepot, sources))
    assert resultats[f"reglements/{copie.name}"] == "DOUBLON_LIVRAISON"
    with duckdb.connect(str(entrepot), read_only=True) as con:
        assert con.execute("SELECT count(*) FROM raw.reglements WHERE _fichier_source LIKE '%_bis.csv'").fetchone()[0] == 0


def test_fichier_corrige_remplace_la_version_precedente(env):
    sources, entrepot = env
    ingest.executer(entrepot, sources)
    chemin = sources / "reglements" / f"reglements_{MOIS_TEST}.csv"
    lignes = chemin.read_text().splitlines()
    chemin.write_text("\n".join(lignes[:-1]) + "\n")  # la livraison corrigée a une ligne de moins

    resultats = statuts(ingest.executer(entrepot, sources))
    assert resultats[f"reglements/{chemin.name}"] == "RECHARGE"
    with duckdb.connect(str(entrepot), read_only=True) as con:
        nb = con.execute(
            "SELECT count(*) FROM raw.reglements WHERE _fichier_source = ?", [f"reglements/{chemin.name}"]
        ).fetchone()[0]
    assert nb == len(lignes) - 2  # en-tête et ligne retirée


def test_structure_inconnue_bloque_le_fichier_sans_rien_charger(env):
    sources, entrepot = env
    chemin = sources / "reglements" / "reglements_2099_01.csv"
    chemin.write_text("paiement_id;sinistre_id;date_paiement;montant;devise\n1;1;2099-01-01;10.0;EUR\n")

    resultats = statuts(ingest.executer(entrepot, sources))
    assert resultats["reglements/reglements_2099_01.csv"] == "ECHEC"
    with duckdb.connect(str(entrepot), read_only=True) as con:
        assert con.execute("SELECT count(*) FROM raw.reglements WHERE _fichier_source LIKE '%2099%'").fetchone()[0] == 0


def test_lignes_illisibles_vont_en_rejet_avec_motif(env):
    sources, entrepot = env
    chemin = sources / "reglements" / "reglements_2099_02.csv"
    chemin.write_text("paiement_id,sinistre_id,date_paiement,montant\n99001,1,2099-02-01,10.0\n99002,1\n\n")

    ingest.executer(entrepot, sources)
    with duckdb.connect(str(entrepot), read_only=True) as con:
        motifs = dict(con.execute(
            "SELECT numero_ligne, motif FROM raw.rejets_ingestion WHERE fichier = 'reglements/reglements_2099_02.csv'"
        ).fetchall())
        journal = con.execute(
            "SELECT lignes_lues, lignes_chargees, lignes_rejetees FROM meta.journal_ingestion"
            " WHERE fichier = 'reglements/reglements_2099_02.csv'"
        ).fetchone()
    assert motifs == {3: "2 champs au lieu de 4", 4: "ligne vide"}
    assert journal == (3, 1, 2)
