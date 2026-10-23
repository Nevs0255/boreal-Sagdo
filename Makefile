# Pipeline Boréal Assurances : sources -> brut -> préparation -> cœur -> marts
# Chaque cible s'arrête à la première erreur (code de retour non nul) : un test en échec bloque la suite.

PYTHON  := .venv/bin/python
DBT     := .venv/bin/dbt --no-use-colors
DBT_DIR := --project-dir dbt --profiles-dir dbt
SRC     ?= $(HOME)/Downloads/sources_boreal

.PHONY: install sources ingest build run reload test docs journal clean

install:            ## Crée l'environnement Python et installe les dépendances
	python3 -m venv .venv
	$(PYTHON) -m pip install -q --upgrade pip
	$(PYTHON) -m pip install -q -r requirements.txt

sources:            ## Copie l'archive extraite (SRC=...) dans data/sources
	mkdir -p data/sources
	rsync -a --exclude .DS_Store "$(SRC)/" data/sources/

ingest:             ## Charge les fichiers nouveaux ou modifiés dans la couche brute
	$(PYTHON) -m pipeline.ingest

build:              ## Construit préparation, cœur et marts, et exécute les tests dbt (bloquants)
	$(DBT) build $(DBT_DIR)

run: ingest build   ## Pipeline complet

reload:             ## Recharge un mois de règlements : make reload MOIS=2024_03
	@test -n "$(MOIS)" || (echo "Usage : make reload MOIS=AAAA_MM" && exit 1)
	$(PYTHON) -m pipeline.ingest --recharger-mois $(MOIS)
	$(DBT) build $(DBT_DIR)

test:               ## Tests d'ingestion (idempotence, rechargement) et tests dbt
	$(PYTHON) -m pytest -q
	$(DBT) test $(DBT_DIR)

docs:               ## Génère le catalogue de données et le lignage (dbt docs)
	$(DBT) docs generate $(DBT_DIR)
	@echo "Pour consulter : $(DBT) docs serve $(DBT_DIR)"

journal:            ## Affiche le dernier passage du journal d'ingestion
	$(PYTHON) -m pipeline.journal

clean:              ## Supprime l'entrepôt et les artefacts dbt (les sources sont conservées)
	rm -rf data/warehouse dbt/target dbt/logs
