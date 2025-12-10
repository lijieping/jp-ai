.PHONY: up down build logs clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

clean:
	docker compose down -v
	sudo rm -rf volumes/*

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d