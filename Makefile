# Pipeline Boréal Assurances : sources -> brut -> préparation -> cœur -> marts
# Chaque cible s'arrête à la première erreur (code de retour non nul) : un test en échec bloque la suite.

PYTHON  := .venv/bin/python
DBT     := .venv/bin/dbt --no-use-colors
DBT_DIR := --project-dir dbt --profiles-dir dbt
SRC     ?= $(HOME)/Downloads/sources_boreal

.PHONY: install sources ingest build run reload test notebooks dashboard docs journal surveiller planifier deplanifier effacer clean

install:            ## Crée l'environnement Python et installe les dépendances
	python3 -m venv .venv
	$(PYTHON) -m pip install -q --upgrade pip
	$(PYTHON) -m pip install -q -r requirements.txt

sources:            ## Copie l'archive extraite (SRC=...) dans data/sources
	mkdir -p data/sources
	rsync -a --exclude .DS_Store "$(SRC)/" data/sources/

ingest:             ## Charge les fichiers nouveaux ou modifiés dans la couche brute
	$(PYTHON) -m pipeline.ingest

build:              ## Construit préparation, cœur et marts, exécute les tests dbt (bloquants) et publie leurs résultats
	$(DBT) build $(DBT_DIR); statut=$$?; $(PYTHON) -m pipeline.publier_tests; exit $$statut

run: ingest build   ## Pipeline complet

reload:             ## Recharge un mois de règlements : make reload MOIS=2024_03
	@test -n "$(MOIS)" || (echo "Usage : make reload MOIS=AAAA_MM" && exit 1)
	$(PYTHON) -m pipeline.ingest --recharger-mois $(MOIS)
	$(MAKE) build

test:               ## Tests d'ingestion (idempotence, rechargement) et tests dbt
	$(PYTHON) -m pytest -q
	$(DBT) test $(DBT_DIR)

dashboard:          ## Lance le dashboard (http://localhost:8501)
	.venv/bin/streamlit run dashboard/app.py

notebooks:          ## Réexécute les notebooks d'analyse sur l'entrepôt (sorties et figures à jour)
	.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb

docs:               ## Génère le catalogue de données et le lignage (dbt docs)
	$(DBT) docs generate $(DBT_DIR)
	$(PYTHON) -m pipeline.catalogue
	@echo "Catalogue : docs/catalogue.md ; lignage interactif : $(DBT) docs serve $(DBT_DIR)"

surveiller:         ## Lance le pipeline seulement si un fichier source nouveau ou modifié est arrivé (alerte en cas d'échec)
	$(PYTHON) -m pipeline.surveiller

planifier:          ## Installe la planification macOS (launchd) : nouveau fichier ou chaque jour à 7 h
	mkdir -p logs $(HOME)/Library/LaunchAgents
	sed "s|__RACINE__|$(CURDIR)|g" orchestration/fr.boreal.pipeline.plist > $(HOME)/Library/LaunchAgents/fr.boreal.pipeline.plist
	launchctl unload $(HOME)/Library/LaunchAgents/fr.boreal.pipeline.plist 2>/dev/null || true
	launchctl load $(HOME)/Library/LaunchAgents/fr.boreal.pipeline.plist
	@echo "Planification active. Désinstallation : make deplanifier"

deplanifier:        ## Retire la planification macOS
	launchctl unload $(HOME)/Library/LaunchAgents/fr.boreal.pipeline.plist 2>/dev/null || true
	rm -f $(HOME)/Library/LaunchAgents/fr.boreal.pipeline.plist

effacer:            ## Droit à l'effacement RGPD : make effacer CLIENT=123
	@test -n "$(CLIENT)" || (echo "Usage : make effacer CLIENT=identifiant" && exit 1)
	$(PYTHON) -m pipeline.effacer_client $(CLIENT)
	$(MAKE) build

journal:            ## Affiche le dernier passage du journal d'ingestion
	$(PYTHON) -m pipeline.journal

clean:              ## Supprime l'entrepôt et les artefacts dbt (les sources sont conservées)
	rm -rf data/warehouse dbt/target dbt/logs
