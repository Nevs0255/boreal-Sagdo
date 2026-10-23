"""Publie les résultats du dernier `dbt build` dans meta.resultats_tests (page Exploitation).

Lancé après chaque dbt build, même en cas d'échec, pour que le dashboard montre les tests en échec.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import duckdb

from pipeline.config import CHEMIN_ENTREPOT, RACINE
from pipeline.ingest import initialiser


def publier(run_results: Path = RACINE / "dbt" / "target" / "run_results.json",
            chemin_entrepot: Path = CHEMIN_ENTREPOT) -> int:
    if not run_results.exists():
        print(f"Aucun résultat dbt à publier ({run_results})", file=sys.stderr)
        return 0
    resultats = json.loads(run_results.read_text())
    id_execution = resultats["metadata"]["invocation_id"]
    genere_le = datetime.fromisoformat(resultats["metadata"]["generated_at"].replace("Z", "+00:00")).replace(tzinfo=None)
    lignes = []
    for r in resultats["results"]:
        uid = r["unique_id"]
        if not uid.startswith("test."):
            continue
        nom = uid.split(".")[2]
        lignes.append((id_execution, genere_le, "dbt", nom, uid, r["status"].upper(),
                       r.get("failures"), r.get("execution_time"), (r.get("message") or "")[:500]))
    with duckdb.connect(str(chemin_entrepot)) as con:
        initialiser(con)
        con.execute("DELETE FROM meta.resultats_tests WHERE id_execution = ?", [id_execution])
        con.executemany("INSERT INTO meta.resultats_tests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", lignes)
    echecs = sum(1 for l in lignes if l[5] not in ("PASS", "WARN"))
    print(f"{len(lignes)} résultats de tests publiés, {echecs} en échec")
    return echecs


if __name__ == "__main__":
    publier()
