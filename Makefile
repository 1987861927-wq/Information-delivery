.PHONY: backend-dev backend-test pipeline

backend-dev:
	cd backend && uvicorn app.main:app --reload

backend-test:
	cd backend && pytest

pipeline:
	cd backend && python -m app.tasks.daily_pipeline
