# MVidarr Enhanced - Makefile for Development and Deployment Automation

.PHONY: help install build test lint clean docker-build docker-run deploy-staging deploy-production backup restore

# Default target
help:
	@echo "MVidarr Enhanced - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  install           Install dependencies and set up development environment"
	@echo "  test              Run comprehensive test suite"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-manual       Run manual testing checklist"
	@echo "  lint              Run code quality checks"
	@echo "  format            Format code with black and isort"
	@echo "  security-scan     Run security vulnerability scan"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build      Build production Docker image"
	@echo "  docker-run        Run application with Docker Compose"
	@echo "  docker-dev        Run development environment with Docker"
	@echo "  docker-logs       View Docker container logs"
	@echo "  docker-stop       Stop all Docker containers"
	@echo "  docker-clean      Clean up Docker images and containers"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-local      Deploy locally for testing"
	@echo "  deploy-staging    Deploy to staging environment"
	@echo "  deploy-production Deploy to production environment"
	@echo "  rollback          Rollback to previous deployment"
	@echo ""
	@echo "Database:"
	@echo "  migrate           Run database migrations"
	@echo "  backup-db         Create database backup"
	@echo "  restore-db        Restore database from backup"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean             Clean up temporary files and caches"
	@echo "  health-check      Check application health"
	@echo "  update-deps       Update Python dependencies"

# Variables
PYTHON = python3
PIP = pip3
DOCKER_COMPOSE = docker-compose
COMPOSE_FILE = docker-compose.production.yml
COMPOSE_DEV_FILE = docker-compose.dev.yml
IMAGE_NAME = mvidarr-enhanced
APP_URL = http://localhost:5000

# Development Environment Setup
install:
	@echo "Setting up development environment..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Creating data directories..."
	mkdir -p data/logs data/downloads data/thumbnails data/cache
	@echo "Setup complete!"

# Testing
test:
	@echo "Running comprehensive test suite..."
	$(PYTHON) scripts/testing/run_comprehensive_tests.py

test-unit:
	@echo "Running unit tests..."
	$(PYTHON) -m pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	$(PYTHON) -m pytest tests/integration/ -v

test-manual:
	@echo "Starting manual testing checklist..."
	$(PYTHON) scripts/testing/manual_test_checklist.py

# Code Quality
lint:
	@echo "Running code quality checks..."
	flake8 src/ --max-line-length=120 --exclude=__pycache__ --statistics
	pylint src/ --exit-zero
	bandit -r src/ -x tests/

format:
	@echo "Formatting code..."
	black src/
	isort src/

security-scan:
	@echo "Running security scan..."
	safety check
	bandit -r src/ -x tests/

# Docker Operations
docker-build:
	@echo "Building production Docker image..."
	docker build -f Dockerfile.production -t $(IMAGE_NAME):latest .

docker-run:
	@echo "Starting application with Docker Compose..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) up -d

docker-dev:
	@echo "Starting development environment..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_DEV_FILE) up -d

docker-logs:
	@echo "Viewing Docker logs..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) logs -f

docker-stop:
	@echo "Stopping Docker containers..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) down

docker-clean:
	@echo "Cleaning up Docker resources..."
	docker image prune -f
	docker container prune -f
	docker volume prune -f

# Deployment
deploy-local:
	@echo "Deploying locally..."
	./scripts/deployment/deploy.sh local --force

deploy-staging:
	@echo "Deploying to staging..."
	./scripts/deployment/deploy.sh staging --backup-db

deploy-production:
	@echo "Deploying to production..."
	./scripts/deployment/deploy.sh production --backup-db --migrate-db

rollback:
	@echo "Rolling back deployment..."
	./scripts/deployment/deploy.sh production --rollback

# Database Operations
migrate:
	@echo "Running database migrations..."
	$(PYTHON) scripts/migrations/add_authentication_tables.py
	$(PYTHON) scripts/migrations/add_genre_columns.py

backup-db:
	@echo "Creating database backup..."
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) exec -T mariadb mysqldump -u root -p$${MYSQL_ROOT_PASSWORD} mvidarr_enhanced > backup_$$(date +%Y%m%d_%H%M%S).sql

restore-db:
	@echo "Restoring database..."
	@read -p "Enter backup file path: " backup_file; \
	$(DOCKER_COMPOSE) -f $(COMPOSE_FILE) exec -T mariadb mysql -u root -p$${MYSQL_ROOT_PASSWORD} mvidarr_enhanced < $$backup_file

# Health and Maintenance
health-check:
	@echo "Checking application health..."
	curl -f $(APP_URL)/api/health || echo "Health check failed"

clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf .coverage
	rm -rf htmlcov/

update-deps:
	@echo "Updating dependencies..."
	$(PIP) list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 $(PIP) install -U

# CI/CD Helpers
ci-test:
	@echo "Running CI test suite..."
	$(MAKE) lint
	$(MAKE) security-scan
	$(MAKE) test

# Release Preparation
prepare-release:
	@echo "Preparing release..."
	$(MAKE) clean
	$(MAKE) ci-test
	$(MAKE) docker-build
	@echo "Release preparation complete!"

# Quick Start
quick-start:
	@echo "Quick start setup..."
	$(MAKE) install
	$(MAKE) migrate
	$(PYTHON) app.py &
	@echo "Application started at $(APP_URL)"

# Development Server
dev-server:
	@echo "Starting development server..."
	FLASK_ENV=development $(PYTHON) app.py

# Production Setup
production-setup:
	@echo "Setting up production environment..."
	@if [ ! -f .env.production ]; then \
		cp .env.production.template .env.production; \
		echo "Created .env.production from template. Please edit with your values."; \
	fi
	$(MAKE) docker-build
	@echo "Production setup complete. Edit .env.production and run 'make deploy-production'"