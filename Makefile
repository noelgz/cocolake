.PHONY: run pipeline web api db build clean help

run:  ## Start all services! DB, pipeline, API, and web
	docker compose up db -d --wait
	docker compose run --rm pipeline
	docker compose up api web

pipeline:  ## Run only the news pipeline
	docker compose up db -d --wait
	docker compose run --rm pipeline

api:  ## Run only the API on localhost:8000
	docker compose up db api

web:  ## Run only the web app on localhost:3000
	docker compose up api web

db:  ## Run only PostgreSQL on localhost:5432
	docker compose up db

# Setup stuff

build:  ## Rebuild the images
	docker compose build

clean:  ## Remove containers, images, and volumes
	docker compose down --rmi local --volumes

help:  ## Show all available commands
	@awk 'BEGIN {FS = ":  ## "}; /^[a-zA-Z0-9_-]+:  ## / {printf "%-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
