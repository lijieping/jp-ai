.PHONY: up down build logs clean

updev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
upprod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
downdev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down
downprod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down
builddev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml build
buildprod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build
redev:
	docker compose \
		-f docker-compose.yml \
		-f docker-compose.dev.yml \
		down --rmi all
	docker compose \
		-f docker-compose.yml \
		-f docker-compose.dev.yml \
		build --no-cache
	docker compose \
		-f docker-compose.yml \
		-f docker-compose.dev.yml \
		up -d
reprod:
	docker compose \
		-f docker-compose.yml \
		-f docker-compose.prod.yml \
		down --rmi all
	docker compose \
		-f docker-compose.yml \
		-f docker-compose.prod.yml \
		build --no-cache
	docker compose \
		-f docker-compose.yml \
		-f docker-compose.prod.yml \
		up -d