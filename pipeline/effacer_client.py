"""Droit à l'effacement (RGPD, art. 17) : efface les attributs personnels d'un client.

Les contrats, sinistres et règlements sont conservés : ils relèvent d'obligations légales
(prescription, comptabilité, lutte antifraude ; art. 17.3.b et e du RGPD). Le client reste un
identifiant technique sans attribut personnel dans toutes les couches :
- brut : date de naissance, région, CSP, consentement et empreinte d'e-mail vidés, et réappliqués
  à chaque rechargement du CRM (meta.effacements) ;
- préparation, cœur, marts : reconstruits par dbt à partir du brut ;
- historique (snapshots.snap_clients) : versions du client supprimées.
Les fiches doublons partageant la même empreinte d'e-mail sont effacées avec lui.

Usage : python -m pipeline.effacer_client CLIENT_ID [--motif "..."]  puis  make build
"""

import argparse
import sys
from datetime import datetime

import duckdb

from pipeline.config import CHEMIN_ENTREPOT
from pipeline.ingest import appliquer_effacements, initialiser


def effacer(client_id: int, motif: str = "demande de la personne", chemin_entrepot=CHEMIN_ENTREPOT) -> list[int]:
    with duckdb.connect(str(chemin_entrepot)) as con:
        initialiser(con)
        ligne = con.execute(
            "SELECT email_hash FROM raw.clients WHERE client_id = ? LIMIT 1", [str(client_id)]
        ).fetchone()
        if ligne is None:
            raise ValueError(f"client {client_id} inconnu de la couche brute")
        email_hash = ligne[0] or None
        ids = [client_id]
        if email_hash:
            ids = [int(r[0]) for r in con.execute(
                "SELECT DISTINCT client_id FROM raw.clients WHERE email_hash = ?", [email_hash]).fetchall()]
        # Fiche conservée du groupe (même règle de survie que int_clients) : celle qui porte des
        # contrats, puis le plus petit identifiant. Le rapprochement survit ainsi à l'effacement.
        avec_contrats = {int(r[0]) for r in con.execute(
            f"SELECT DISTINCT client_id FROM raw.contrats WHERE client_id IN ({','.join('?' * len(ids))})",
            [str(i) for i in ids]).fetchall()}
        retenu = min(avec_contrats) if avec_contrats else min(ids)
        maintenant = datetime.now()
        con.execute("BEGIN TRANSACTION")
        for i in ids:
            if not con.execute("SELECT 1 FROM meta.effacements WHERE client_id = ?", [i]).fetchone():
                # L'empreinte n'est pas conservée : le registre ne contient que des identifiants techniques.
                con.execute("INSERT INTO meta.effacements VALUES (?, ?, ?, ?)", [i, retenu, maintenant, motif])
        appliquer_effacements(con)
        existe_snapshot = con.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'snapshots' AND table_name = 'snap_clients'"
        ).fetchone()[0]
        if existe_snapshot:
            con.execute(f"DELETE FROM snapshots.snap_clients WHERE client_id IN ({','.join('?' * len(ids))})", ids)
        con.execute("COMMIT")
    return ids


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Effacement RGPD d'un client")
    parser.add_argument("client_id", type=int)
    parser.add_argument("--motif", default="demande de la personne")
    args = parser.parse_args(argv)
    try:
        ids = effacer(args.client_id, args.motif)
    except ValueError as erreur:
        print(erreur, file=sys.stderr)
        return 1
    print(f"Attributs personnels effacés pour les fiches {ids}. Lancer `make build` pour propager aux couches dérivées.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
