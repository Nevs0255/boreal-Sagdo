"""Configuration de l'ingestion : emplacement des données et description des sources."""

import os
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_SOURCES = Path(os.environ.get("BOREAL_SOURCES", RACINE / "data" / "sources"))
CHEMIN_ENTREPOT = Path(os.environ.get("BOREAL_DB", RACINE / "data" / "warehouse" / "boreal.duckdb"))


@dataclass(frozen=True)
class Source:
    """Une source de l'archive et la table brute qui la reçoit."""

    nom: str
    motif: str  # motif glob relatif au dossier des sources
    table: str  # table de la couche brute (schéma raw)
    format: str  # "csv" ou "jsonl"
    colonnes: tuple[str, ...]  # colonnes attendues, dans l'ordre de la table brute
    # Noms de colonnes alternatifs rencontrés dans les livraisons -> nom attendu.
    # Seul l'en-tête est aligné : les valeurs restent intactes.
    alias: dict[str, str] = field(default_factory=dict)


SOURCES: tuple[Source, ...] = (
    Source(
        nom="clients",
        motif="crm/clients*.csv",
        table="clients",
        format="csv",
        colonnes=("client_id", "date_naissance", "region", "csp", "consent_marketing", "email_hash"),
    ),
    Source(
        nom="contrats",
        motif="contrats/contrats*.csv",
        table="contrats",
        format="csv",
        colonnes=(
            "contrat_id", "client_id", "produit", "date_effet", "date_resiliation", "formule",
            "canal_distribution", "zone_risque", "franchise", "bonus_malus", "puissance_cv",
            "surface_m2", "prime_annuelle",
        ),
    ),
    Source(
        nom="sinistres",
        motif="sinistres/sinistres*.jsonl",
        table="sinistres",
        format="jsonl",
        colonnes=(
            "sinistre_id", "contrat_id", "date_survenance", "date_declaration", "garantie",
            "statut", "reserve_initiale",
        ),
    ),
    Source(
        nom="reglements",
        motif="reglements/reglements_*.csv",
        table="reglements",
        format="csv",
        colonnes=("paiement_id", "sinistre_id", "date_paiement", "montant"),
        alias={"montant_eur": "montant"},
    ),
    Source(
        nom="audits",
        motif="antifraude/audits*.csv",
        table="audits",
        format="csv",
        colonnes=("sinistre_id", "date_audit", "fraude_confirmee"),
    ),
)

SOURCES_PAR_NOM = {s.nom: s for s in SOURCES}
