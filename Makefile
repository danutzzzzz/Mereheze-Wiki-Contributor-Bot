# Project Configuration
PROJECT_NAME := mereheze-wiki-bot
VERSION := $(shell python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version']")

# Docker Configuration
DOCKER_IMAGE := ghcr.io/danutzzzzz/$(PROJECT_NAME):$(VERSION)

.PHONY: help install test lint build docker-build docker-run release

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install:  ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

test:  ## Run tests
	pytest tests/ -v --cov=src --cov-report=xml

lint:  ## Run linting and formatting checks
	pre-commit run --all-files

build:  ## Build Python package
	python -m build

docker-build:  ## Build Docker image
	docker build -t $(DOCKER_IMAGE) .

docker-run: docker-build  ## Run Docker container
	docker run --rm -it \
		-e CONFIG_PATH=/app/config/config.yaml \
		$(DOCKER_IMAGE)

release:  ## Interactive release workflow
	./scripts/prepare-release.sh

bump-patch:  ## Bump patch version
	bumpver update --patch

bump-minor:  ## Bump minor version
	bumpver update --minor

bump-major:  ## Bump major version
	bumpver update --major

changelog:  ## Generate changelog
	git-cliff --unreleased --output CHANGELOG.md