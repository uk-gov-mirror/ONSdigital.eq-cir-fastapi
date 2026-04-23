import json
from unittest.mock import patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.models.responses import CiMetadata
from app.services.ci_schema_location_service import CiSchemaLocationService
from tests.test_data.ci_test_data import (
    mock_classifier_type,
    mock_classifier_value,
    mock_id,
    mock_next_version_id,
    mock_post_ci_schema,
    mock_ci_metadata_v3,
    mock_next_version_ci_metadata_v3,
)

client = TestClient(app)
test_500_client = TestClient(app, raise_server_exceptions=False)
settings = Settings()

CONTENT_TYPE = "application/json"


@patch("app.services.create_guid_service.CreateGuidService.create_guid")
@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_latest_ci_metadata")
@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.perform_new_ci_transaction")
class TestHttpPostCiV3:
    """
    Tests for the `http_post_ci_v3` endpoint
    """

    url = "/v3/publish_collection_instrument"

    def test_endpoint_returns_200_if_ci_created_successfully(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_create_guid,
        pubsub_mock,
    ):
        """
        Endpoint should return `HTTP_200_OK` and serialized ci metadata as part of the response if new ci is created
        successfully. Assert mocked functions are called with the correct arguments.
        """
        # Update mocked function to return `None` indicating no previous version of metadata is found
        mocked_get_latest_ci_metadata.return_value = None
        # Update mocked function to return a valid guid
        mocked_create_guid.return_value = mock_id

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 2},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_ci_metadata_v3.model_dump()
        mocked_get_latest_ci_metadata.assert_called_once_with(
            mock_post_ci_schema.survey_id,
            mock_classifier_type,
            mock_classifier_value,
            mock_post_ci_schema.language,
        )
        mocked_perform_new_ci_transaction.assert_called_once_with(
            mock_id,
            mock_ci_metadata_v3,
            mock_post_ci_schema.model_dump(),
            CiSchemaLocationService.get_ci_schema_location(mock_ci_metadata_v3),
        )
        pubsub_mock.publish_message.assert_called_once_with(CiMetadata(**mock_ci_metadata_v3.model_dump()))

    def test_endpoint_returns_200_if_ci_next_version_created_successfully(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_create_guid,
        pubsub_mock,
    ):
        """
        Endpoint should return `HTTP_200_OK` and serialized ci metadata with updated version
        as part of the response if new version of ci is created.
        Assert mocked functions are called with the correct arguments.
        """
        # Update mocked function to return ci metadata indicating a previous version of metadata is found
        mocked_get_latest_ci_metadata.return_value = mock_ci_metadata_v3
        # Update mocked function to return a valid guid
        mocked_create_guid.return_value = mock_next_version_id

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1", "guid": mock_next_version_id, "ci_version": 100},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_next_version_ci_metadata_v3.model_dump()
        mocked_get_latest_ci_metadata.assert_called_once_with(
            mock_post_ci_schema.survey_id,
            mock_classifier_type,
            mock_classifier_value,
            mock_post_ci_schema.language,
        )
        mocked_perform_new_ci_transaction.assert_called_once_with(
            mock_next_version_id,
            mock_next_version_ci_metadata_v3,
            mock_post_ci_schema.model_dump(),
            CiSchemaLocationService.get_ci_schema_location(mock_next_version_ci_metadata_v3),
        )
        pubsub_mock.publish_message.assert_called_once_with(CiMetadata(**mock_next_version_ci_metadata_v3.model_dump()))

    def test_endpoint_returns_400_if_no_post_data(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if empty or incomplete post data is posted
        as part of the request
        """
        # Make request to base url without any post data
        response = client.post(self.url,
                               params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 100},
                               headers={"ContentType": CONTENT_TYPE})

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
    def test_endpoint_returns_400_if_required_field_none(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_create_guid,
        input_param,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if any required field in post data is `None`
        """
        # update `post_data` to contain `None` value for `input_param` field
        edited_mock_post_ci_schema = mock_post_ci_schema.model_copy()
        setattr(edited_mock_post_ci_schema, input_param, None)

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1", "ci_version": 100},
            headers={"ContentType": CONTENT_TYPE},
            json=edited_mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Validation has failed"

    def test_endpoint_returns_400_if_classifier_invalid(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_200_OK` and serialized ci metadata as part of the response if new ci is created
        successfully. Assert mocked functions are called with the correct arguments.
        """
        # Update mocked function to return `None` indicating no previous version of metadata is found
        mocked_get_latest_ci_metadata.return_value = None
        # Update mocked function to return a valid guid
        mocked_create_guid.return_value = mock_id

        with open("tests/test_data/classifier_invalid_input.json") as json_file:
            test_data = json.load(json_file)

        response = client.post(self.url,
                               params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 100},
                               headers={"ContentType": CONTENT_TYPE},
                               json=test_data)

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
    def test_endpoint_returns_400_if_required_field_empty_string(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_create_guid,
        input_param,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if any required field in post data is an
        empty string
        """
        # update `post_data` to contain empty string value for `input_param` field
        edited_mock_post_ci_schema = mock_post_ci_schema.model_copy()
        setattr(edited_mock_post_ci_schema, input_param, "")

        response = client.post(
            self.url,
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
        mocked_create_guid,
        input_param,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` if any required field in post data is
        whitespace
        """
        # update `post_data` to contain whitespace value for `input_param` field
        edited_mock_post_ci_schema = mock_post_ci_schema.model_copy()
        setattr(edited_mock_post_ci_schema, input_param, " ")

        response = client.post(
            self.url,
            params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 100},
            headers={"ContentType": CONTENT_TYPE},
            json=edited_mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Validation has failed"

    def test_endpoint_returns_500_if_exception_occurs_in_transaction(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_create_guid,
    ):
        """
        Endpoint should return `HTTP_500_INTERNAL_SERVER_ERROR` as part of the response if ci metadata is created
        but not processed due to an error in transaction
        """
        # Update mocked function to return `None` indicating no previous version of metadata is found
        mocked_get_latest_ci_metadata.return_value = None
        # Update mocked function to return a valid guid
        mocked_create_guid.return_value = mock_id
        # Raise an exception to simulate an error in transaction
        mocked_perform_new_ci_transaction.side_effect = Exception()

        response = test_500_client.post(
            self.url,
            params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 100},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["message"] == "Unable to process request"

    def test_endpoint_returns_500_if_exception_occurs_in_publish_message(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_create_guid,
        pubsub_mock,
    ):
        """
        Endpoint should return `HTTP_500_INTERNAL_SERVER_ERROR` as part of the response if ci metadata is created
        but not processed due to an error in publish message
        """
        # Update mocked function to return `None` indicating no previous version of metadata is found
        mocked_get_latest_ci_metadata.return_value = None
        # Update mocked function to return a valid guid
        mocked_create_guid.return_value = mock_id
        # Raise an exception to simulate an error in publish message
        pubsub_mock.publish_message.side_effect = Exception()

        response = test_500_client.post(
            self.url,
            params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 100},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["message"] == "Unable to process request"