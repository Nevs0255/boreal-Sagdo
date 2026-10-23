"""Le dashboard s'exécute sans erreur sur l'entrepôt et s'affiche en moins de 5 secondes."""

import time

import pytest
from streamlit.testing.v1 import AppTest

from pipeline.config import CHEMIN_ENTREPOT, RACINE

pytestmark = pytest.mark.skipif(not CHEMIN_ENTREPOT.exists(), reason="entrepôt absent (make run)")


@pytest.mark.parametrize("page", ["page_portefeuille", "page_technique", "page_exploitation", "page_definitions"])
def test_page_sans_erreur_en_moins_de_5_secondes(page, monkeypatch):
    monkeypatch.setenv("BOREAL_PAGE_DEFAUT", page)
    debut = time.perf_counter()
    at = AppTest.from_file(str(RACINE / "dashboard" / "app.py"), default_timeout=30)
    at.run()
    duree = time.perf_counter() - debut
    assert not at.exception, at.exception
    assert at.title[0].value == {"page_portefeuille": "Portefeuille", "page_technique": "Technique et clients",
                                 "page_exploitation": "Exploitation", "page_definitions": "Définitions"}[page]
    assert duree < 5, f"{page} : {duree:.1f} s"
