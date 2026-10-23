"""Droit à l'effacement : les attributs personnels disparaissent de toutes les couches,
les contrats sont conservés, et l'effacement survit à un rechargement du CRM."""

import os
import shutil

import duckdb
import pytest

from pipeline import effacer_client, ingest
from pipeline.config import DOSSIER_SOURCES
from tests.test_ingestion import dbt_build

pytestmark = pytest.mark.skipif(not DOSSIER_SOURCES.is_dir(), reason="sources absentes (make sources)")

CLIENT = 33  # client conservé dont la fiche doublon 15 0xx partage l'empreinte d'e-mail


@pytest.fixture
def env(tmp_path):
    sources = tmp_path / "sources"
    shutil.copytree(DOSSIER_SOURCES, sources, ignore=shutil.ignore_patterns(".DS_Store"))
    entrepot = tmp_path / "boreal.duckdb"
    ingest.executer(entrepot, sources)
    return sources, entrepot


def test_effacement_dans_toutes_les_couches(env):
    sources, entrepot = env
    with duckdb.connect(str(entrepot), read_only=True) as con:
        email = con.execute("SELECT email_hash FROM raw.clients WHERE client_id = ?", [str(CLIENT)]).fetchone()[0]
        nb_fiches = con.execute("SELECT count(*) FROM raw.clients WHERE email_hash = ?", [email]).fetchone()[0]
    assert nb_fiches == 2

    ids = effacer_client.effacer(CLIENT, chemin_entrepot=entrepot)
    assert CLIENT in ids and len(ids) == 2
    # Un rechargement forcé du CRM ne doit pas faire réapparaître les données
    ingest.executer(entrepot, sources, sources=["clients"], forcer={"crm/clients.csv"})
    dbt_build(entrepot)

    with duckdb.connect(str(entrepot), read_only=True) as con:
        assert con.execute("SELECT count(*) FROM raw.clients WHERE email_hash = ?", [email]).fetchone()[0] == 0
        brut = con.execute(
            "SELECT date_naissance, region, csp, email_hash FROM raw.clients WHERE client_id = ?", [str(CLIENT)]
        ).fetchone()
        assert brut == ("", "", "", "")
        dim = con.execute(
            "SELECT date_naissance, region, csp, email_hash, est_efface FROM core.dim_client WHERE client_id = ?", [CLIENT]
        ).fetchone()
        assert dim == (None, None, None, None, True)
        # Contrats conservés (obligation légale) et doublon toujours rattaché au client conservé
        assert con.execute("SELECT count(*) FROM core.dim_contrat WHERE client_id = ?", [CLIENT]).fetchone()[0] > 0
        assert con.execute("SELECT count(*) FROM core.dim_client").fetchone()[0] == 15000
        assert con.execute("SELECT count(*) FROM snapshots.snap_clients WHERE client_id = ? AND email_hash IS NOT NULL",
                           [CLIENT]).fetchone()[0] == 0
