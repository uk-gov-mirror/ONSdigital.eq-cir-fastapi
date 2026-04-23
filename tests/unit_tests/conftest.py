import datetime
from unittest.mock import Mock

import pytest
from google.cloud.firestore import Transaction
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


@pytest.fixture(autouse=True)
def mock_datetime(mocker):
    mocker.patch(
        "app.services.datetime_service.DatetimeService.get_current_date_and_time",
        return_value=mock_publish_date,
    )


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

    mock_firestore.client.reset()


@pytest.fixture(autouse=True)
def transaction_mock(firestore_mock):
    """
    Mock a firestore transaction with default values mimicking google.cloud.firestore.Transaction.
    This is required as MockFirestore does not support transactions mocking, and this set up enables
    unit-test without patching the transaction functions
    """
    mock_transaction = Mock(spec=Transaction)
    mock_transaction._read_only = False
    mock_transaction._max_attempts = 1
    mock_transaction._id = None
    firestore_mock.set_transaction.return_value = mock_transaction

    yield mock_transaction


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
