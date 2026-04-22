# Global Variables
LOCAL_URL=localhost:3030
PROJECT_ID = $(shell gcloud config get project)
SANDBOX_IP_ADDRESS = $(shell gcloud compute addresses list --global  --filter=name:$(PROJECT_ID)-cir-static-lb-ip --format='value(address)' --limit=1 --project=$(PROJECT_ID))

# Please run gcloud auth application-default login before running the following commands that interact with GCP services
start-cloud-dev:
	export PROJECT_ID='$(PROJECT_ID)' && \
	export FIRESTORE_DB_NAME='$(PROJECT_ID)-cir' && \
	export CI_STORAGE_BUCKET_NAME='$(PROJECT_ID)-cir-europe-west2-schema' && \
	uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 3030

unit-tests:
	export CONF='unit' && \
	export CI_STORAGE_BUCKET_NAME='the-ci-schema-bucket' && \
	export PROJECT_ID='mock-project-id' && \
	export FIRESTORE_DB_NAME="the-firestore-db-name" && \
	uv run python -m pytest --cov=app --cov-fail-under=90 --cov-report term-missing --cov-config=.coveragerc_unit -vv ./tests/unit_tests/ -W ignore::DeprecationWarning

# Spinning up emulators in docker is required to run the local integration tests.
integration-tests-local:
	export CONF='local-int-tests' && \
	export PROJECT_ID='emulated-project-id' && \
	export CI_STORAGE_BUCKET_NAME='emulated-ci-bucket' && \
	export PUBLISH_CI_TOPIC_ID='emulated-cir-topic' && \
	export DEFAULT_HOSTNAME=${LOCAL_URL} && \
	export URL_SCHEME='http' && \
	export PYTHONPATH=app && \
	export PUBSUB_EMULATOR_HOST=localhost:8086 && \
	export FIRESTORE_EMULATOR_HOST=localhost:8200 && \
	export STORAGE_EMULATOR_HOST=http://localhost:9026 && \
	uv run python -m pytest tests/integration_tests -vv -W ignore::DeprecationWarning

# Please run gcloud auth application-default login before running the following commands that interact with GCP services
integration-tests-sandbox:
	export CONF='sandbox-int-tests' && \
	export PROJECT_ID='$(PROJECT_ID)' && \
	export FIRESTORE_DB_NAME='$(PROJECT_ID)-cir' && \
	export CI_STORAGE_BUCKET_NAME='$(PROJECT_ID)-cir-europe-west2-schema' && \
	export DEFAULT_HOSTNAME=${SANDBOX_IP_ADDRESS}.nip.io && \
	export URL_SCHEME='https' && \
	export SECRET_ID='iap-secret' && \
	export PYTHONPATH=app && \
	uv run python -m pytest tests/integration_tests -vv -W ignore::DeprecationWarning

#For use only by automated cloudbuild, is not intended to work locally.
integration-tests-cloudbuild:
	export CONF='cloudbuild-int-tests' && \
	export PROJECT_ID=${INT_PROJECT_ID} && \
	export FIRESTORE_DB_NAME=${INT_FIRESTORE_DB_NAME} && \
	export CI_STORAGE_BUCKET_NAME=${INT_CI_STORAGE_BUCKET_NAME} && \
	export DEFAULT_HOSTNAME=${INT_DEFAULT_HOSTNAME} && \
	export URL_SCHEME=${INT_URL_SCHEME} && \
	export PYTHONPATH=app && \
	uv run python -m pytest tests/integration_tests -vv -W ignore::DeprecationWarning

# Spinning up emulators in docker is required to run this command successfully.
generate-spec:
	export PROJECT_ID='emulated-project-id' && \
	export CI_STORAGE_BUCKET_NAME='emulated-ci-bucket' && \
	export FIRESTORE_EMULATOR_HOST=localhost:8200 && \
	export STORAGE_EMULATOR_HOST=http://localhost:9026 && \
	uv run python -m scripts.generate_openapi

lint:
	uv run python -m ruff check .

lint-check:
	uv run python -m ruff check .

lint-fix:
	uv run python -m ruff check --fix .

audit:
	uv run python -m pip_audit

publish-multiple-ci:
	uv run python -m scripts.publish_multiple_ci

setup:
	@command -v uv >/dev/null 2>&1 || { \
		echo "uv not found – installing..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	uv sync

.PHONY:  bump bump-patch bump-minor bump-major
bump:
	@echo "🔼 Bumping project version (patch)..."
	uv run --only-group version-check python .github/scripts/bump_version.py patch
	@echo "🔄 Generating new lock file..."
	uv lock

bump-patch:
	@echo "🔼 Bumping project version (patch)..."
	uv run --only-group version-check python .github/scripts/bump_version.py patch
	@echo "🔄 Generating new lock file..."
	uv lock

bump-minor:
	@echo "🔼 Bumping project version (minor)..."
	uv run --only-group version-check python .github/scripts/bump_version.py minor
	@echo "🔄 Generating new lock file..."
	uv lock

bump-major:
	@echo "🔼 Bumping project version (major)..."
	uv run --only-group version-check python .github/scripts/bump_version.py major
	@echo "🔄 Generating new lock file..."
	uv lock
