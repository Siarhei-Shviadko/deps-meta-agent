-include .env
-include vendors/deps-pipelines/shared/Makefile
-include Makefile.local

CURRENT_UID := $(shell id -u):$(shell id -g)
HASH := $(shell git rev-parse HEAD)
DATE := $(shell date)
TAG := $(shell git describe || echo "latest")

APP_NAME = api
NO_DEV_DOCKER_IMAGE = meta-agent
DEV_DOCKER_IMAGE = meta-agent-dev

.PHONY: config
## Show current docker compose config
config:
	docker compose -f docker-compose.yml config

.PHONY: config-test
## Show docker compose test config
config-test:
	docker compose -f docker-compose.yml -f docker-compose.test.yml config

.PHONY: install
## Install default environment settings
install:
	cp .env.example .env

.PHONY: login
## Login in docker registry
login:
	docker login $(repository)

.PHONY: prereq
prereq:
	test -f .env || echo >> .env
	docker network create deps-network || true

.PHONY: prereq-tests
prereq-tests: | prereq
	docker compose -f docker-compose.yml -f docker-compose.test.yml down -v

.PHONY: run
## Run service
run: | prereq
	docker compose up -d

.PHONY: logs
## Open service logs
logs:
	docker compose logs -f

.PHONY: status
## Get running status information
status:
	docker compose ps

.PHONY: stop
## Stop runned services
stop:
	docker compose stop

.PHONY: build
## Build containers
build:
	docker compose build \
	--build-arg BUILD_HASH=$(HASH) \
	--build-arg BUILD_TAG=$(TAG) \
	--build-arg BUILD_DATE="$(DATE)"

.PHONY: migrate
## Apply database migrations
migrate:
	docker compose run --rm migrator update

.PHONY: shell-app
## Open shell in Unifier API container
shell-app:
	docker compose exec -u root $(APP_NAME) /bin/sh

.PHONY: shell-db
## Open db shell
shell-db:
	docker compose exec -u "$(CURRENT_UID)" database psql -U deps-postgres deps

.PHONY: format
## Apply black & isort code formatting
format:
	docker compose run --rm --no-deps -u "$(CURRENT_UID)" $(APP_NAME) black --config pyproject.toml .
	docker compose run --rm --no-deps -u "$(CURRENT_UID)" $(APP_NAME) isort --settings-path setup.cfg .

.PHONY: format-check
## Check for correct code format
format-check:
	docker compose run --rm --no-deps -u "$(CURRENT_UID)" $(APP_NAME) black --config pyproject.toml --check .
	docker compose run --rm --no-deps -u "$(CURRENT_UID)" $(APP_NAME) isort --settings-path pyproject.toml --check-only .

.PHONY: lint
## Check code using linters
lint:
	docker compose run --rm --no-deps $(APP_NAME) flake8 .

.PHONY: mypy
## Check code using mypy
mypy:
	docker compose run --rm --no-deps $(APP_NAME) mypy .

.PHONY: tests-unit
## Run unit tests
tests-unit:
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --user="root" --rm --no-deps $(APP_NAME) coverage run -a -m pytest -vv -x tests/unit

.PHONY: tests-integration
## Run integration tests
tests-integration:
	docker compose -f docker-compose.yml -f docker-compose.test.yml rm -f
	docker compose -f docker-compose.yml -f docker-compose.test.yml up -d test-database test-rabbitmq
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm migrator update
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --user="root" --rm $(APP_NAME) coverage run -a -m pytest -vv -x tests/integration
	docker compose -f docker-compose.yml -f docker-compose.test.yml rm -f

.PHONY: tests
## Run unit & integration tests
tests: tests-unit tests-integration

.PHONY: coverage
## Get code coverage report
coverage:
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm $(APP_NAME) coverage report -i --rcfile=/app/setup.cfg

.PHONY: coverage-xml
## Generate xml coverage report
coverage-xml:
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm $(APP_NAME) coverage xml -i --rcfile=/app/setup.cfg

.PHONY: ci
## Run CI checks
ci: | prereq-tests format-check lint mypy tests coverage prereq-tests
	@if [ "$(version)" == "ci" ]; then \
		make coverage-xml;\
	else \
	  	make requirements-lock; \
	fi

.PHONY: build-prod
## Build images for production
build-prod:
	$(call build_service,meta-agent-dev,./etc/meta-agent/Dockerfile,,develop)
	$(call build_service,meta-agent,./etc/meta-agent/Dockerfile,,,meta-agent-dev)
	$(call build_service,meta-agent-migrator,./etc/migrator/Dockerfile)

.PHONY: push
## Push images to registry
push:
	$(call push_service,meta-agent)
	$(call push_service,meta-agent-dev)
	$(call push_service,meta-agent-migrator)

.PHONY: deliver
## Build prod images and push to registry
deliver: | build-prod push

.PHONY: tag
## Retag built services
tag:
	$(call tag_service,meta-agent)
	$(call tag_service,meta-agent-dev)
	$(call tag_service,meta-agent-migrator)

.PHONY: pull
## Pull service images from docker registry
pull:
	$(call pull_service,meta-agent)
	$(call pull_service,meta-agent-dev)
	$(call pull_service,meta-agent-migrator)

.PHONY: helm-upgrade-service
helm-upgrade-service:
	helm upgrade --install $(CI_PROJECT_NAME) .helm/services \
        --values .helm/services/values.yaml $(ADDITIONAL_VALUES) \
        --set registry=$(REPOSITORY_URL) \
        --set meta_agent.image.tag=$(CI_COMMIT_SHORT_SHA) \
        --set meta_agent_consumer.image.tag=$(CI_COMMIT_SHORT_SHA) \
        --set meta_agent_settings.DATABASE_REQUIRE_SECURE_TRANSPORT=$(DATABASE_REQUIRE_SECURE_TRANSPORT) \
        --set meta_agent_settings.EXTERNAL_URL=$(SERVICE_EXTERNAL_URL) \
        --set vault_settings.enabled=$(VAULT_ENABLE) \
        --timeout 300s \
        --atomic \
        --wait \
        --debug \
        --namespace $(NAMESPACE)

.PHONY: helm-apply-migrations
helm-apply-migrations:
	helm upgrade --install $(CI_PROJECT_NAME)-migrator .helm/migrator \
        --values .helm/migrator/values.yaml $(ADDITIONAL_VALUES) \
        --set registry=$(REPOSITORY_URL) \
        --set migrator.image.tag=$(CI_COMMIT_SHORT_SHA) \
        --set migrator.args="$(migration_command)" \
        --set migration_settings.DATABASE_REQUIRE_SECURE_TRANSPORT=$(DATABASE_REQUIRE_SECURE_TRANSPORT) \
        --set vault_settings.enabled=$(VAULT_ENABLE) \
        --timeout 300s \
        --atomic \
        --wait \
        --debug \
        --namespace $(NAMESPACE)

.PHONY: helm-migration-rollback
helm-migration-rollback:
	make migration_command="rollback $(CI_COMMIT_SHORT_SHA)" helm-apply-migrations

.PHONY: helm-deployment-rollback
helm-deployment-rollback:
	helm rollback --namespace $(NAMESPACE) $(CI_PROJECT_NAME) 0

.PHONY: helm-rollback
helm-rollback:
	make helm-migration-rollback
	make helm-deployment-rollback

.PHONY: helm-upgrade
helm-upgrade:
	make migration_command="tag $(CI_COMMIT_SHORT_SHA)" helm-apply-migrations
	make helm-apply-migrations
	make helm-upgrade-service

testdkube := $(shell kubectl config current-context)
ifeq ($(testdkube), rancher-desktop)
.PHONY: skaffold
skaffold:
	cd skaffold && skaffold run -f skaffold.yaml
endif

.PHONY: build-no-dev
build-no-dev:
	$(call build_service,$(NO_DEV_DOCKER_IMAGE),./etc/meta-agent/Dockerfile,,build,$(DEV_DOCKER_IMAGE))
