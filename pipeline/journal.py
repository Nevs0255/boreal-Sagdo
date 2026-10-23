"""Résumé du journal d'ingestion : dernière exécution et état de chaque source."""

import duckdb

from pipeline.config import CHEMIN_ENTREPOT


def main() -> None:
    with duckdb.connect(str(CHEMIN_ENTREPOT), read_only=True) as con:
        print("Dernière exécution :")
        con.sql(
            """SELECT statut, count(*) AS fichiers, sum(lignes_chargees) AS lignes_chargees,
                      sum(lignes_rejetees) AS lignes_rejetees, round(sum(duree_s), 2) AS duree_s
               FROM meta.journal_ingestion
               WHERE id_execution = (SELECT id_execution FROM meta.journal_ingestion ORDER BY debut DESC LIMIT 1)
               GROUP BY statut ORDER BY statut"""
        ).show()
        print("État par source (version actuellement chargée) :")
        con.sql(
            """WITH actuel AS (
                   SELECT * FROM meta.journal_ingestion
                   WHERE statut IN ('CHARGE', 'RECHARGE')
                   QUALIFY row_number() OVER (PARTITION BY fichier ORDER BY debut DESC) = 1
               )
               SELECT source, count(*) AS fichiers, sum(lignes_chargees) AS lignes,
                      sum(lignes_rejetees) AS rejets, max(debut) AS dernier_chargement
               FROM actuel GROUP BY source ORDER BY source"""
        ).show()


if __name__ == "__main__":
    main()
