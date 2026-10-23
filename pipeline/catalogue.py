"""Catalogue des données : chaque table et chaque colonne de l'entrepôt avec sa définition.

Généré à partir des métadonnées dbt (`dbt docs generate` : manifest.json et catalog.json).
Une colonne sans description propre reprend la définition de la colonne de même nom documentée
ailleurs dans le projet (une définition unique par notion). Le script échoue si une colonne
reste sans définition : `make docs` garantit ainsi un catalogue complet.
"""

import json
import sys
from pathlib import Path

from pipeline.config import RACINE

ORDRE_SCHEMAS = ["raw", "meta", "prep", "quarantaine", "qualite", "core", "snapshots", "marts"]
ROLE_SCHEMAS = {
    "raw": "Couche brute : copie fidèle des sources, toutes valeurs en texte.",
    "meta": "Pilotage de la chaîne : journal d'ingestion, résultats des tests, registre des effacements.",
    "prep": "Préparation : typage (stg_*) et contrôles de qualité (int_*).",
    "quarantaine": "Lignes écartées avec leur motif.",
    "qualite": "Catalogue et bilan des règles de qualité.",
    "core": "Cœur : schéma en étoile.",
    "snapshots": "Historique (type 2) des dimensions.",
    "marts": "Tables d'indicateurs lues par le dashboard et les notebooks.",
}
DICTIONNAIRE = RACINE / "dbt" / "dictionnaire_colonnes.yml"


def lire_dictionnaire() -> dict[str, str]:
    """Dictionnaire simple « colonne: "définition" » (une entrée par ligne, sans dépendance YAML)."""
    definitions = {}
    for ligne in DICTIONNAIRE.read_text(encoding="utf-8").splitlines():
        if ligne.strip() and not ligne.lstrip().startswith("#") and ":" in ligne:
            cle, valeur = ligne.split(":", 1)
            definitions[cle.strip()] = valeur.strip().strip('"')
    return definitions


def charger(cible: Path):
    manifest = json.loads((cible / "manifest.json").read_text())
    catalog = json.loads((cible / "catalog.json").read_text())
    return manifest, catalog


def generer(cible: Path = RACINE / "dbt" / "target", sortie: Path = RACINE / "docs" / "catalogue.md") -> list[str]:
    manifest, catalog = charger(cible)
    noeuds = {**manifest["nodes"], **manifest["sources"]}
    definitions = lire_dictionnaire()
    for n in noeuds.values():
        for nom, col in n.get("columns", {}).items():
            if col.get("description"):
                definitions.setdefault(nom, col["description"])

    tables = []
    for uid, entree in {**catalog["nodes"], **catalog["sources"]}.items():
        noeud = noeuds.get(uid, {})
        meta = entree["metadata"]
        tables.append((meta["schema"], meta["name"], noeud.get("description", ""), noeud.get("columns", {}), entree["columns"]))
    tables.sort(key=lambda t: (ORDRE_SCHEMAS.index(t[0]) if t[0] in ORDRE_SCHEMAS else 99, t[1]))

    manquants = []
    lignes = ["# Catalogue des données", "",
              "Généré par `make docs` à partir des métadonnées dbt : chaque table et chaque colonne de l'entrepôt "
              "`data/warehouse/boreal.duckdb`, avec son type et sa définition. Une même notion porte une seule définition "
              "dans tout le projet.", ""]
    schema_courant = None
    for schema, nom, description, colonnes_doc, colonnes in tables:
        if schema != schema_courant:
            lignes += [f"## Schéma `{schema}`", "", ROLE_SCHEMAS.get(schema, ""), ""]
            schema_courant = schema
        if not description:
            manquants.append(f"{schema}.{nom} (table)")
        lignes += [f"### `{schema}.{nom}`", "", description or "_(sans description)_", "",
                   "| Colonne | Type | Définition |", "|---|---|---|"]
        for col in sorted(colonnes.values(), key=lambda c: c["index"]):
            nom_col = col["name"]
            definition = (colonnes_doc.get(nom_col, {}).get("description") or definitions.get(nom_col, "")).replace("|", "\\|")
            if not definition:
                manquants.append(f"{schema}.{nom}.{nom_col}")
            lignes.append(f"| `{nom_col}` | {col['type']} | {definition} |")
        lignes.append("")
    sortie.write_text("\n".join(lignes), encoding="utf-8")
    return manquants


if __name__ == "__main__":
    manquants = generer()
    if manquants:
        print(f"{len(manquants)} élément(s) sans définition :", *manquants, sep="\n  ", file=sys.stderr)
        sys.exit(1)
    print("Catalogue complet : docs/catalogue.md")
