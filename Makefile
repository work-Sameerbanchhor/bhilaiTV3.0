# ==============================================================================
# BHILAI_TV // Developer & Deployment Automation Makefile
# Live URL: https://bhilaitv-23241707890.us-central1.run.app
# ==============================================================================

SERVICE_NAME ?= bhilaitv
REGION ?= us-central1
PYTHON ?= /Users/sameerbanchhor/g_venv/venv/bin/python

.PHONY: help deploy update logs status test stress dev setup

help:
	@echo "=========================================================="
	@echo "  BHILAI_TV // COMMAND AUTOMATION MENU"
	@echo "=========================================================="
	@echo "  make deploy   - Fast 1-step Cloud Run redeployment"
	@echo "  make update   - Alias for 'make deploy'"
	@echo "  make logs     - Tail live production logs from Cloud Run"
	@echo "  make status   - Show live Cloud Run service status & URL"
	@echo "  make test     - Run full automated regression test suite"
	@echo "  make stress   - Run production concurrency & stress suite"
	@echo "  make dev      - Start local development server on :8000"
	@echo "  make setup    - Enable Google Cloud APIs (one-time setup)"
	@echo "=========================================================="

deploy:
	@./deploy-cloudrun.sh

update: deploy

logs:
	@echo ">> Streaming live production logs for $(SERVICE_NAME)..."
	@gcloud run services logs tail $(SERVICE_NAME) --region $(REGION)

status:
	@echo ">> Checking Cloud Run service status..."
	@gcloud run services describe $(SERVICE_NAME) --region $(REGION) --format="table(status.url,status.conditions[0].status:label=READY,status.latestReadyRevisionName)"

test:
	@$(PYTHON) scripts/test_runner.py

stress:
	@$(PYTHON) scripts/production_stress_test.py

dev:
	@$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

setup:
	@./deploy-cloudrun.sh --setup
