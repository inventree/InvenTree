#!make
#include default_env
#export $(shell sed 's/.*//' default_env)
include .env
export $(shell sed 's/.*//' .env)

.EXPORT_ALL_VARIABLES:


db-setup: 
	docker-compose up -d --no-deps inventree-db
	docker exec -it inventree-db /bin/bash -c 'while ! pg_isready -U ${POSTGRES_USER} -d ${INVENTREE_DB_NAME};do sleep 1; done;'
	docker exec -it inventree-db createdb -O ${POSTGRES_USER} -U ${POSTGRES_USER} ${INVENTREE_DB_NAME} || true
	docker-compose down 

inventree-setup:
	#docker-compose run inventree-server invoke migrate #&& invoke static && invoke superuser
	docker-compose run inventree-server invoke static
	docker-compose run inventree-server invoke superuser


up:
	docker-compose up
