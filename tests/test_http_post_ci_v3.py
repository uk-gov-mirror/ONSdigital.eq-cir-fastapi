import json
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from app.config import Settings
from app.events.publisher import Publisher
from app.main import app
from app.models.responses import CiMetadata
from app.repositories.firebase.ci_firebase_repository import CiFirebaseRepository
from app.services.ci_schema_location_service import CiSchemaLocationService
from tests.test_data.ci_test_data import (
    mock_classifier_type,
    mock_classifier_value,
    mock_id,
    mock_next_version_id,
    mock_post_ci_schema,
    mock_next_version_ci_metadata_v3,
    mock_ci_metadata_v3,
    mock_ci_metadata_v3_with_ci_version,
)

settings = Settings()

CONTENT_TYPE = "application/json"


@patch("app.services.create_guid_service.CreateGuidService.create_guid")
@patch("app.events.publisher.Publisher.publish_message")
@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_latest_ci_metadata")
@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.perform_new_ci_transaction")
class TestHttpPostCiV3:

    url = "/v3/publish_collection_instrument"

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_endpoint_returns_200_if_ci_created_successfully_with_validator_version_only(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
        test_client,
    ):
        """
        Endpoint should return `HTTP_200_OK` and serialized CI metadata when called with
        `validator_version` only (no `ci_version`), and no previous version exists.
        Assert mocked functions are called with the correct arguments.
        """
        # Return `None` to indicate no previous version of metadata exists
        mocked_get_latest_ci_metadata.return_value = None
        mocked_create_guid.return_value = mock_id

        response = test_client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_ci_metadata_v3.model_dump()
        CiFirebaseRepository.get_latest_ci_metadata.assert_called_once_with(
            mock_post_ci_schema.survey_id,
            mock_classifier_type,
            mock_classifier_value,
            mock_post_ci_schema.language,
        )
        CiFirebaseRepository.perform_new_ci_transaction.assert_called_once_with(
            mock_id,
            mock_ci_metadata_v3,
            mock_post_ci_schema.model_dump(),
            CiSchemaLocationService.get_ci_schema_location(mock_ci_metadata_v3),
        )
        Publisher.publish_message.assert_called_once_with(CiMetadata(**mock_ci_metadata_v3.model_dump()))

    def test_endpoint_returns_200_if_ci_created_successfully_with_validator_version_and_ci_version(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_200_OK` and serialized CI metadata when called with both
        `validator_version` and `ci_version`, and no previous version exists.
        Assert mocked functions are called with the correct arguments.
        """
        # Return `None` to indicate no previous version of metadata exists
        mocked_get_latest_ci_metadata.return_value = None
        mocked_create_guid.return_value = mock_id

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1", "ci_version": "1"},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_ci_metadata_v3_with_ci_version.model_dump()
        CiFirebaseRepository.get_latest_ci_metadata.assert_called_once_with(
            mock_post_ci_schema.survey_id,
            mock_classifier_type,
            mock_classifier_value,
            mock_post_ci_schema.language,
        )
        CiFirebaseRepository.perform_new_ci_transaction.assert_called_once_with(
            mock_id,
            mock_ci_metadata_v3_with_ci_version,
            mock_post_ci_schema.model_dump(),
            CiSchemaLocationService.get_ci_schema_location(mock_ci_metadata_v3_with_ci_version),
        )
        Publisher.publish_message.assert_called_once_with(
            CiMetadata(**mock_ci_metadata_v3_with_ci_version.model_dump())
        )

    def test_endpoint_returns_200_if_ci_next_version_created_successfully(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_200_OK` and serialized CI metadata with an incremented version
        when a previous version of the CI already exists in the repository.
        Assert mocked functions are called with the correct arguments.
        """
        # Return existing metadata to indicate a previous version exists
        mocked_get_latest_ci_metadata.return_value = mock_ci_metadata_v3
        mocked_create_guid.return_value = mock_next_version_id

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_next_version_ci_metadata_v3.model_dump()
        CiFirebaseRepository.get_latest_ci_metadata.assert_called_once_with(
            mock_post_ci_schema.survey_id,
            mock_classifier_type,
            mock_classifier_value,
            mock_post_ci_schema.language,
        )
        CiFirebaseRepository.perform_new_ci_transaction.assert_called_once_with(
            mock_next_version_id,
            mock_next_version_ci_metadata_v3,
            mock_post_ci_schema.model_dump(),
            CiSchemaLocationService.get_ci_schema_location(mock_next_version_ci_metadata_v3),
        )
        Publisher.publish_message.assert_called_once_with(
            CiMetadata(**mock_next_version_ci_metadata_v3.model_dump())
        )

    def test_endpoint_response_contains_required_metadata_fields(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint response body should contain all required CI metadata fields.
        Validates AC-6: response body structure and required fields.
        """
        mocked_get_latest_ci_metadata.return_value = None
        mocked_create_guid.return_value = mock_id

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_200_OK
        response_body = response.json()
        required_fields = [
            "id",
            "survey_id",
            "language",
            "title",
            "data_version",
            "schema_version",
            "sds_published_at",
        ]
        for field in required_fields:
            assert field in response_body, f"Expected field '{field}' missing from response body"

    # ------------------------------------------------------------------
    # —  Missing or invalid parameters
    # ------------------------------------------------------------------

    def test_endpoint_returns_400_if_no_post_data(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if no post data is supplied with the request.
        """
        response = client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Validation has failed"

    def test_endpoint_returns_400_if_validator_version_missing(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if `validator_version` query parameter
        is not provided.
        """
        mocked_get_latest_ci_metadata.return_value = None
        mocked_create_guid.return_value = mock_id

        response = client.post(
            self.url,
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "No validator version provided"

    def test_endpoint_returns_400_if_classifier_invalid(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if the classifier in the request body
        is invalid or does not meet expected structure.
        """
        mocked_get_latest_ci_metadata.return_value = None
        mocked_create_guid.return_value = mock_id

        with open("tests/test_data/classifier_invalid_input.json") as json_file:
            test_data = json.load(json_file)

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=test_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Invalid classifier"

    @pytest.mark.parametrize(
        "input_param",
        [
            "data_version",
            "language",
            "survey_id",
            "title",
        ],
    )
    def test_endpoint_returns_400_if_required_field_none(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
        input_param,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if any required field in the post data
        is `None`.
        """
        edited_mock_post_ci_schema = mock_post_ci_schema.model_copy()
        setattr(edited_mock_post_ci_schema, input_param, None)

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=edited_mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Validation has failed"

    @pytest.mark.parametrize(
        "input_param",
        [
            "data_version",
            "language",
            "survey_id",
            "title",
        ],
    )
    def test_endpoint_returns_400_if_required_field_empty_string(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
        input_param,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if any required field in the post data
        is an empty string.
        """
        edited_mock_post_ci_schema = mock_post_ci_schema.model_copy()
        setattr(edited_mock_post_ci_schema, input_param, "")

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=edited_mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Validation has failed"

    @pytest.mark.parametrize(
        "input_param",
        [
            "data_version",
            "language",
            "survey_id",
            "title",
        ],
    )
    def test_endpoint_returns_400_if_required_field_whitespace(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
        input_param,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if any required field in the post data
        contains only whitespace.
        """
        edited_mock_post_ci_schema = mock_post_ci_schema.model_copy()
        setattr(edited_mock_post_ci_schema, input_param, " ")

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=edited_mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Validation has failed"

    # ------------------------------------------------------------------
    # AC-5  —  Authorisation
    # ------------------------------------------------------------------

    def test_endpoint_returns_401_if_request_is_unauthenticated(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_401_UNAUTHORIZED` if the request is made without
        authentication credentials.
        """
        unauthenticated_client = TestClient(app, headers={})

        response = unauthenticated_client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_endpoint_returns_403_if_request_is_unauthorised(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_403_FORBIDDEN` if the request is made with credentials
        that do not have permission to publish a CI schema.
        """
        unauthorised_client = TestClient(app, headers={"Authorization": "Bearer invalid_token"})

        response = unauthorised_client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    # ------------------------------------------------------------------
    # Server errors
    # ------------------------------------------------------------------

    def test_endpoint_returns_500_if_exception_occurs_in_transaction(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_500_INTERNAL_SERVER_ERROR` if an unhandled exception
        is raised during the Firebase transaction.
        """
        mocked_get_latest_ci_metadata.return_value = None
        mocked_create_guid.return_value = mock_id
        mocked_perform_new_ci_transaction.side_effect = Exception()

        response = test_500_client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["message"] == "Unable to process request"

    def test_endpoint_returns_500_if_exception_occurs_in_publish_message(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_500_INTERNAL_SERVER_ERROR` if an unhandled exception
        is raised during the Pub/Sub publish step.
        """
        mocked_get_latest_ci_metadata.return_value = None
        mocked_create_guid.return_value = mock_id
        mocked_publish_message.side_effect = Exception()

        response = test_500_client.post(
            self.url,
            params={"validator_version": "0.0.1"},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["message"] == "Unable to process request"