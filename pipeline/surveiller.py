"""Orchestration : lance le pipeline quand un fichier source nouveau ou modifié arrive.

Appelé par la planification (launchd sur macOS, cron ailleurs : voir orchestration/) :
- à chaque modification du dossier des règlements (arrivée du fichier mensuel) ;
- et chaque jour à 7 h, en filet de sécurité.
Sans fichier nouveau, il ne fait rien. Sinon il exécute `make run` (ingestion, transformations,
tests bloquants). En cas d'échec, il émet une alerte : journal logs/alertes.log, notification
macOS et, si BOREAL_WEBHOOK_ALERTE est défini, un message JSON vers ce webhook (Slack, Teams…).
"""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import duckdb

from pipeline.config import CHEMIN_ENTREPOT, DOSSIER_SOURCES, RACINE, SOURCES

DOSSIER_LOGS = RACINE / "logs"


def fichiers_a_traiter(dossier_sources: Path | None = None, chemin_entrepot: Path | None = None) -> list[str]:
    """Fichiers sources absents du journal ou dont le contenu a changé depuis leur chargement."""
    dossier_sources = dossier_sources or DOSSIER_SOURCES
    chemin_entrepot = chemin_entrepot or CHEMIN_ENTREPOT
    connus: dict[str, str] = {}
    if chemin_entrepot.exists():
        with duckdb.connect(str(chemin_entrepot), read_only=True) as con:
            existe = con.execute("SELECT count(*) FROM information_schema.tables "
                                 "WHERE table_schema = 'meta' AND table_name = 'journal_ingestion'").fetchone()[0]
            if existe:
                connus = dict(con.execute(
                    """SELECT fichier, sha256 FROM meta.journal_ingestion WHERE statut IN ('CHARGE', 'RECHARGE')
                       QUALIFY row_number() OVER (PARTITION BY fichier ORDER BY debut DESC) = 1""").fetchall())
    a_traiter = []
    for source in SOURCES:
        for chemin in sorted(dossier_sources.glob(source.motif)):
            fichier = chemin.relative_to(dossier_sources).as_posix()
            if connus.get(fichier) != hashlib.sha256(chemin.read_bytes()).hexdigest():
                a_traiter.append(fichier)
    return a_traiter


def journaliser(message: str, fichier: str = "surveillance.log") -> None:
    DOSSIER_LOGS.mkdir(exist_ok=True)
    with open(DOSSIER_LOGS / fichier, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {message}\n")
    print(message)


def alerter(titre: str, detail: str) -> None:
    journaliser(f"ALERTE {titre} : {detail}", "alertes.log")
    if platform.system() == "Darwin":
        texte = detail[:200].replace('"', "'")
        subprocess.run(["osascript", "-e", f'display notification "{texte}" with title "Boréal : {titre}"'],
                       check=False, capture_output=True)
    webhook = os.environ.get("BOREAL_WEBHOOK_ALERTE")
    if webhook:
        donnees = json.dumps({"text": f"Boréal : {titre}\n{detail}"}).encode()
        requete = urllib.request.Request(webhook, data=donnees, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(requete, timeout=10)
        except OSError as erreur:
            journaliser(f"webhook injoignable : {erreur}", "alertes.log")


def surveiller(forcer: bool = False, commande: list[str] | None = None) -> int:
    commande = commande or ["make", "run"]
    nouveaux = fichiers_a_traiter()
    if not nouveaux and not forcer:
        journaliser("Aucun fichier nouveau : rien à faire.")
        return 0
    journaliser(f"{len(nouveaux)} fichier(s) nouveau(x) ou modifié(s) : {', '.join(nouveaux[:10])} → lancement du pipeline")
    resultat = subprocess.run(commande, cwd=RACINE, capture_output=True, text=True)
    sortie = (resultat.stdout + resultat.stderr)[-4000:]
    (DOSSIER_LOGS / f"execution_{datetime.now():%Y%m%dT%H%M%S}.log").write_text(sortie, encoding="utf-8")
    if resultat.returncode != 0:
        lignes_erreur = [l for l in sortie.splitlines() if "ERROR" in l or "FAIL" in l or "ÉCHEC" in l]
        alerter("échec du pipeline", "; ".join(lignes_erreur[-3:]) or f"code de retour {resultat.returncode}")
        return resultat.returncode
    journaliser("Pipeline terminé avec succès.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Lance le pipeline si un fichier source nouveau ou modifié est arrivé.")
    parser.add_argument("--forcer", action="store_true", help="lancer même sans fichier nouveau")
    args = parser.parse_args(argv)
    return surveiller(forcer=args.forcer)


if __name__ == "__main__":
    sys.exit(main())
