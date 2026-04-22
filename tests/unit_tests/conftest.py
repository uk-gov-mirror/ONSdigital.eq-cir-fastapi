import datetime
import os
from unittest.mock import Mock

import pytest
from gcp_storage_emulator.server import create_server
from google.cloud import pubsub_v1
from mockfirestore import MockFirestore
from fastapi.testclient import TestClient

from app.config import Settings, logging
from app.dependencies import get_bucket_loader, get_publisher_service, get_firebase_loader
from app.events.publisher import Publisher
from app.repositories.buckets.bucket_loader import BucketLoader
from app.repositories.firebase.firebase_loader import FirebaseLoader

logger = logging.getLogger(__name__)
mock_publish_date = datetime.datetime(2023, 4, 20, 12, 0, 0, 0)
settings = Settings()


'''@pytest.fixture(scope="session")
def setup_mock_firestore():
    logger.debug("***setup_mock_firestore")
    firestore_client = MockFirestore()

    return firestore_client


@pytest.fixture(autouse=True)
def mock_firestore_collection(mocker, setup_mock_firestore):
    logger.debug("***mock_firestore_collection")
    # mock firebase client
    mocker.patch(
        "app.repositories.firebase.firebase_loader.firebase_loader.get_client",
        return_value=setup_mock_firestore,
    )
    # mock firestore ci collection
    collection = setup_mock_firestore.collection(settings.CI_FIRESTORE_COLLECTION_NAME)
    mocker.patch(
        "app.repositories.firebase.firebase_loader.firebase_loader.get_ci_collection",
        return_value=collection,
    )
    # use ci collection
    yield collection
    setup_mock_firestore.reset()


@pytest.fixture(scope="session")
def setup_mock_storage():
    logger.debug("local storage starting")
    server = create_server(
        "localhost",
        9023,
        in_memory=True,
        default_bucket="ons-cir-schemas",
    )
    os.environ.setdefault("STORAGE_EMULATOR_HOST", "http://localhost:9023")
    server.start()
    logger.info("local storage started")
    yield server
    logger.debug("local storage stopping")
    server.stop()
    logger.info("local storage stopped")'''


@pytest.fixture(autouse=True)
def mock_datetime(mocker):
    mocker.patch(
        "app.services.datetime_service.DatetimeService.get_current_date_and_time",
        return_value=mock_publish_date,
    )


'''@pytest.fixture(scope="session")
def setup_pubsub_emulator():
    # Set the environment variable for the Pub/Sub emulator host and port
    os.environ.setdefault("PUBSUB_EMULATOR_HOST", "http://localhost:8085")

    # Create a Pub/Sub publisher client
    publisher = pubsub_v1.PublisherClient()

    # Create the topic if it doesn't exist
    topic_id = "post-ci"  # Replace with your topic ID
    topic_path = f"projects/{publisher.project}/topics/{topic_id}"

    try:
        publisher.create_topic(request={"name": topic_path})
    except Exception as e:
        pytest.fail(f"Failed to create Pub/Sub topic: {e}")

    yield'''


@pytest.fixture(autouse=True)
def bucket_mock(test_client):
    app = test_client.app
    mock_bucket_loader = Mock(spec=BucketLoader)
    app.dependency_overrides[get_bucket_loader] = lambda: mock_bucket_loader

    yield mock_bucket_loader


@pytest.fixture(autouse=True)
def firestore_mock(test_client):
    app = test_client.app
    mock_firestore = Mock(spec=FirebaseLoader)
    mock_firestore.client = MockFirestore()
    app.dependency_overrides[get_firebase_loader] = lambda: mock_firestore

    yield mock_firestore


@pytest.fixture(autouse=True)
def mock_firestore_collection(firestore_mock):
    collection = firestore_mock.client.collection(settings.CI_FIRESTORE_COLLECTION_NAME)
    firestore_mock.get_ci_collection.return_value = collection

    yield collection

    firestore_mock.client.reset()


@pytest.fixture(autouse=True)
def pubsub_mock(test_client):
    """
    Mocks the google pubsub credentials.
    """
    app = test_client.app
    mock_pubsub = Mock(spec=Publisher)
    app.dependency_overrides[get_publisher_service] = lambda: mock_pubsub

    yield mock_pubsub


@pytest.fixture
def test_client():
    """
    General client for hitting endpoints in tests, also mocking firebase credentials.
    """
    from app.main import app

    client = TestClient(app)
    yield client


@pytest.fixture
def test_client_no_server_exception():
    """
    This client is only used to test the 500 server error exception handler,
    therefore server exception for this client is suppressed
    """
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)
    yield client
