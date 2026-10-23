"""Orchestration : le pipeline ne se lance que sur un fichier nouveau, et un échec déclenche une alerte."""

import shutil
import sys

import pytest

from pipeline import ingest, surveiller
from pipeline.config import DOSSIER_SOURCES

pytestmark = pytest.mark.skipif(not DOSSIER_SOURCES.is_dir(), reason="sources absentes (make sources)")


@pytest.fixture
def env(tmp_path, monkeypatch):
    sources = tmp_path / "sources"
    shutil.copytree(DOSSIER_SOURCES, sources, ignore=shutil.ignore_patterns(".DS_Store"))
    entrepot = tmp_path / "boreal.duckdb"
    ingest.executer(entrepot, sources)
    monkeypatch.setattr(surveiller, "DOSSIER_SOURCES", sources)
    monkeypatch.setattr(surveiller, "CHEMIN_ENTREPOT", entrepot)
    monkeypatch.setattr(surveiller, "DOSSIER_LOGS", tmp_path / "logs")
    return sources, tmp_path


def test_sans_fichier_nouveau_rien_ne_se_lance(env):
    commande = [sys.executable, "-c", "raise SystemExit('ne doit pas être lancé')"]
    assert surveiller.surveiller(commande=commande) == 0


def test_nouveau_mois_declenche_le_pipeline(env):
    sources, _ = env
    (sources / "reglements" / "reglements_2025_08.csv").write_text("paiement_id,sinistre_id,date_paiement,montant\n")
    assert surveiller.fichiers_a_traiter() == ["reglements/reglements_2025_08.csv"]
    assert surveiller.surveiller(commande=[sys.executable, "-c", "print('pipeline ok')"]) == 0


def test_echec_du_pipeline_declenche_une_alerte(env, monkeypatch):
    sources, tmp = env
    monkeypatch.setattr(surveiller.platform, "system", lambda: "test")  # pas de notification pendant les tests
    (sources / "reglements" / "reglements_2025_08.csv").write_text("paiement_id,sinistre_id,date_paiement,montant\n")
    code = surveiller.surveiller(commande=[sys.executable, "-c", "print('ERROR test bloquant'); raise SystemExit(2)"])
    assert code == 2
    assert "ALERTE échec du pipeline" in (tmp / "logs" / "alertes.log").read_text()
