"""Ingestion des sources dans la couche brute (schéma raw) de l'entrepôt DuckDB.

Principes :
- copie fidèle : toutes les valeurs sont stockées en texte, telles que lues ;
  seuls l'encodage, le séparateur et le nom des colonnes sont harmonisés ;
- traçabilité : chaque ligne porte son fichier d'origine, son numéro de ligne,
  l'identifiant et la date du chargement ;
- idempotence : un fichier est identifié par son chemin et son empreinte SHA-256.
  Un fichier déjà chargé à l'identique est ignoré ; un fichier modifié remplace
  intégralement sa version précédente (suppression puis insertion dans une
  même transaction) ; un contenu déjà chargé sous un autre nom est refusé ;
- les lignes illisibles vont dans raw.rejets_ingestion avec leur motif ;
- chaque fichier traité laisse une ligne dans meta.journal_ingestion.

Usage :
    python -m pipeline.ingest                         # charge les fichiers nouveaux ou modifiés
    python -m pipeline.ingest --recharger-mois 2024_03  # force le rechargement d'un mois de règlements
"""

import argparse
import csv
import hashlib
import io
import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

from pipeline.config import CHEMIN_ENTREPOT, DOSSIER_SOURCES, SOURCES, SOURCES_PAR_NOM, Source

COLONNES_TECHNIQUES = ("_fichier_source", "_numero_ligne", "_id_chargement", "_date_chargement")
STATUTS_CHARGES = ("CHARGE", "RECHARGE")


class ErreurStructure(Exception):
    """Le fichier ne respecte pas la structure attendue : il n'est pas chargé."""


def initialiser(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("CREATE SCHEMA IF NOT EXISTS meta")
    for source in SOURCES:
        colonnes = ", ".join(f"{c} VARCHAR" for c in source.colonnes)
        con.execute(
            f"""CREATE TABLE IF NOT EXISTS raw.{source.table} (
                {colonnes},
                _fichier_source VARCHAR NOT NULL,
                _numero_ligne INTEGER NOT NULL,
                _id_chargement VARCHAR NOT NULL,
                _date_chargement TIMESTAMP NOT NULL
            )"""
        )
    con.execute(
        """CREATE TABLE IF NOT EXISTS raw.rejets_ingestion (
            fichier VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            numero_ligne INTEGER NOT NULL,
            contenu VARCHAR,
            motif VARCHAR NOT NULL,
            _id_chargement VARCHAR NOT NULL,
            _date_chargement TIMESTAMP NOT NULL
        )"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS meta.journal_ingestion (
            id_execution VARCHAR NOT NULL,
            id_chargement VARCHAR NOT NULL,
            fichier VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            sha256 VARCHAR,
            encodage VARCHAR,
            separateur VARCHAR,
            lignes_lues INTEGER,
            lignes_chargees INTEGER,
            lignes_rejetees INTEGER,
            debut TIMESTAMP NOT NULL,
            duree_s DOUBLE,
            statut VARCHAR NOT NULL,
            message VARCHAR
        )"""
    )


# --- Lecture des fichiers ---------------------------------------------------------------


def decoder(contenu: bytes) -> tuple[str, str]:
    """Décode en UTF-8 si possible, sinon en latin-1 (qui accepte tout octet)."""
    try:
        return contenu.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return contenu.decode("latin-1"), "latin-1"


def detecter_separateur(texte: str) -> str:
    entete = texte.splitlines()[0] if texte else ""
    try:
        return csv.Sniffer().sniff(entete, delimiters=",;\t|").delimiter
    except csv.Error:
        return max(",;\t|", key=entete.count)


def aligner_entete(source: Source, entete: list[str]) -> list[str]:
    """Normalise les noms de colonnes et vérifie qu'ils correspondent au contrat de la source."""
    noms = [source.alias.get(c.strip().lower(), c.strip().lower()) for c in entete]
    manquantes = set(source.colonnes) - set(noms)
    inattendues = set(noms) - set(source.colonnes)
    if manquantes or inattendues or len(noms) != len(set(noms)):
        raise ErreurStructure(
            f"en-tête non conforme : manquantes={sorted(manquantes)}, "
            f"inattendues={sorted(inattendues)}, lu={entete}"
        )
    return noms


def lire_csv(source: Source, texte: str) -> tuple[list[dict], list[tuple[int, str, str]], str, int]:
    separateur = detecter_separateur(texte)
    lignes_texte = texte.splitlines()
    lecteur = csv.reader(io.StringIO(texte), delimiter=separateur)
    try:
        entete = aligner_entete(source, next(lecteur))
    except StopIteration:
        raise ErreurStructure("fichier vide") from None

    lignes, rejets, lues = [], [], 0
    for champs in lecteur:
        numero = lecteur.line_num
        lues += 1
        brut = lignes_texte[numero - 1] if numero - 1 < len(lignes_texte) else separateur.join(champs)
        if not any(c.strip() for c in champs):
            rejets.append((numero, brut, "ligne vide"))
        elif len(champs) != len(entete):
            rejets.append((numero, brut, f"{len(champs)} champs au lieu de {len(entete)}"))
        else:
            ligne = dict(zip(entete, champs))
            ligne["_numero_ligne"] = numero
            lignes.append(ligne)
    return lignes, rejets, separateur, lues


def valeur_json_en_texte(valeur) -> str | None:
    if valeur is None:
        return None
    if isinstance(valeur, str):
        return valeur
    return json.dumps(valeur, ensure_ascii=False)


def lire_jsonl(source: Source, texte: str) -> tuple[list[dict], list[tuple[int, str, str]], str, int]:
    lignes, rejets, lues = [], [], 0
    for numero, brut in enumerate(texte.splitlines(), start=1):
        lues += 1
        if not brut.strip():
            rejets.append((numero, brut, "ligne vide"))
            continue
        try:
            objet = json.loads(brut)
        except json.JSONDecodeError as erreur:
            rejets.append((numero, brut, f"JSON invalide : {erreur.msg}"))
            continue
        if not isinstance(objet, dict):
            rejets.append((numero, brut, "la ligne n'est pas un objet JSON"))
            continue
        cles = {source.alias.get(k.lower(), k.lower()): v for k, v in objet.items()}
        inattendues = set(cles) - set(source.colonnes)
        if inattendues:
            rejets.append((numero, brut, f"clés inattendues : {sorted(inattendues)}"))
            continue
        ligne = {c: valeur_json_en_texte(cles.get(c)) for c in source.colonnes}
        ligne["_numero_ligne"] = numero
        lignes.append(ligne)
    return lignes, rejets, "", lues


# --- Chargement -----------------------------------------------------------------------------


def etat_fichiers(con: duckdb.DuckDBPyConnection) -> dict[str, str]:
    """Empreinte de la version actuellement chargée de chaque fichier."""
    lignes = con.execute(
        f"""SELECT fichier, sha256 FROM meta.journal_ingestion
            WHERE statut IN {STATUTS_CHARGES}
            QUALIFY row_number() OVER (PARTITION BY fichier ORDER BY debut DESC) = 1"""
    ).fetchall()
    return dict(lignes)


def journaliser(con, **champs) -> None:
    colonnes = ", ".join(champs)
    marqueurs = ", ".join("?" for _ in champs)
    con.execute(f"INSERT INTO meta.journal_ingestion ({colonnes}) VALUES ({marqueurs})", list(champs.values()))


def charger_fichier(
    con: duckdb.DuckDBPyConnection,
    source: Source,
    chemin: Path,
    dossier_sources: Path,
    id_execution: str,
    date_chargement: datetime,
    forcer: bool = False,
) -> dict:
    fichier = chemin.relative_to(dossier_sources).as_posix()
    id_chargement = uuid.uuid4().hex[:12]
    debut = time.perf_counter()
    contenu = chemin.read_bytes()
    empreinte = hashlib.sha256(contenu).hexdigest()
    base = dict(
        id_execution=id_execution, id_chargement=id_chargement, fichier=fichier,
        source=source.nom, sha256=empreinte, debut=date_chargement,
    )

    etat = etat_fichiers(con)
    if not forcer and etat.get(fichier) == empreinte:
        resultat = dict(base, statut="IGNORE", message="déjà chargé à l'identique")
        journaliser(con, **resultat, duree_s=time.perf_counter() - debut)
        return resultat
    homonymes = [f for f, h in etat.items() if h == empreinte and f != fichier]
    if homonymes and not forcer:
        resultat = dict(base, statut="DOUBLON_LIVRAISON", message=f"contenu identique à {homonymes[0]}")
        journaliser(con, **resultat, duree_s=time.perf_counter() - debut)
        return resultat

    texte, encodage = decoder(contenu)
    try:
        lire = lire_jsonl if source.format == "jsonl" else lire_csv
        lignes, rejets, separateur, lues = lire(source, texte)
    except ErreurStructure as erreur:
        resultat = dict(base, encodage=encodage, statut="ECHEC", message=str(erreur))
        journaliser(con, **resultat, duree_s=time.perf_counter() - debut)
        return resultat

    statut = "RECHARGE" if fichier in etat else "CHARGE"
    colonnes = list(source.colonnes) + ["_numero_ligne"]
    donnees = pd.DataFrame(lignes, columns=colonnes, dtype=object)
    donnees["_fichier_source"] = fichier
    donnees["_id_chargement"] = id_chargement
    donnees["_date_chargement"] = date_chargement
    donnees = donnees[list(source.colonnes) + list(COLONNES_TECHNIQUES)]
    df_rejets = pd.DataFrame(rejets, columns=["numero_ligne", "contenu", "motif"], dtype=object)

    con.execute("BEGIN TRANSACTION")
    try:
        # Remplacement intégral de la version précédente du fichier : rejouer un fichier
        # ne peut donc jamais dupliquer ses lignes.
        con.execute(f"DELETE FROM raw.{source.table} WHERE _fichier_source = ?", [fichier])
        con.execute("DELETE FROM raw.rejets_ingestion WHERE fichier = ?", [fichier])
        con.register("lot", donnees)
        con.execute(f"INSERT INTO raw.{source.table} SELECT * FROM lot")
        con.unregister("lot")
        if len(df_rejets):
            con.register("lot_rejets", df_rejets)
            con.execute(
                """INSERT INTO raw.rejets_ingestion
                   SELECT ?, ?, numero_ligne, contenu, motif, ?, ? FROM lot_rejets""",
                [fichier, source.nom, id_chargement, date_chargement],
            )
            con.unregister("lot_rejets")
        resultat = dict(
            base, encodage=encodage, separateur=separateur, lignes_lues=lues,
            lignes_chargees=len(donnees), lignes_rejetees=len(df_rejets), statut=statut,
            message="rechargement forcé" if forcer else None,
        )
        journaliser(con, **resultat, duree_s=time.perf_counter() - debut)
        con.execute("COMMIT")
    except Exception as erreur:
        con.execute("ROLLBACK")
        resultat = dict(base, encodage=encodage, statut="ECHEC", message=f"{type(erreur).__name__}: {erreur}")
        journaliser(con, **resultat, duree_s=time.perf_counter() - debut)
    return resultat


def lister_fichiers(sources: list[Source], dossier_sources: Path) -> list[tuple[Source, Path]]:
    return [(s, chemin) for s in sources for chemin in sorted(dossier_sources.glob(s.motif))]


def executer(
    chemin_entrepot: Path = CHEMIN_ENTREPOT,
    dossier_sources: Path = DOSSIER_SOURCES,
    sources: list[str] | None = None,
    forcer: set[str] | None = None,
) -> list[dict]:
    """Charge les fichiers des sources demandées ; `forcer` liste les fichiers à recharger quoi qu'il arrive."""
    if not dossier_sources.is_dir():
        raise FileNotFoundError(f"dossier des sources introuvable : {dossier_sources}")
    chemin_entrepot.parent.mkdir(parents=True, exist_ok=True)
    forcer = forcer or set()
    selection = [SOURCES_PAR_NOM[n] for n in sources] if sources else list(SOURCES)
    id_execution = datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6]
    date_chargement = datetime.now()

    with duckdb.connect(str(chemin_entrepot)) as con:
        initialiser(con)
        return [
            charger_fichier(
                con, source, chemin, dossier_sources, id_execution, date_chargement,
                forcer=chemin.relative_to(dossier_sources).as_posix() in forcer,
            )
            for source, chemin in lister_fichiers(selection, dossier_sources)
        ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingestion des sources Boréal dans la couche brute.")
    parser.add_argument("--source", action="append", choices=list(SOURCES_PAR_NOM), help="limiter à une source")
    parser.add_argument("--recharger-mois", metavar="AAAA_MM", help="forcer le rechargement d'un mois de règlements")
    parser.add_argument("--recharger", metavar="FICHIER", action="append", default=[],
                        help="forcer le rechargement d'un fichier (chemin relatif au dossier des sources)")
    args = parser.parse_args(argv)

    forcer = set(args.recharger)
    sources = args.source
    if args.recharger_mois:
        fichier = f"reglements/reglements_{args.recharger_mois}.csv"
        if not (DOSSIER_SOURCES / fichier).exists():
            print(f"Fichier introuvable : {fichier}", file=sys.stderr)
            return 1
        forcer.add(fichier)
        sources = sources or ["reglements"]

    resultats = executer(sources=sources, forcer=forcer)

    compte: dict[str, int] = {}
    for r in resultats:
        compte[r["statut"]] = compte.get(r["statut"], 0) + 1
        if r["statut"] != "IGNORE":
            detail = f"{r.get('lignes_chargees', '-')} chargées, {r.get('lignes_rejetees', '-')} rejetées"
            print(f"  {r['statut']:<18} {r['fichier']:<40} {detail}  {r.get('message') or ''}")
    print("Bilan : " + ", ".join(f"{n} {s}" for s, n in sorted(compte.items())))
    echecs = [r for r in resultats if r["statut"] == "ECHEC"]
    if echecs:
        print(f"ÉCHEC : {len(echecs)} fichier(s) non chargé(s), voir meta.journal_ingestion", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
