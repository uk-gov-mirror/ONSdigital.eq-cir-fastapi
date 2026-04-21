from unittest.mock import patch

from fastapi import status

from app.models.responses import CiMetadata
from app.services.ci_schema_location_service import CiSchemaLocationService
from tests.test_data.ci_test_data import (
    mock_classifier_type,
    mock_classifier_value,
    mock_id,
    mock_next_version_id,
    mock_post_ci_schema,
    mock_ci_metadata_v3,
    mock_next_version_ci_metadata_v3, mock_ci_metadata_v3_auto_version, mock_next_version_ci_metadata_v3_auto_version,
)

CONTENT_TYPE = "application/json"


@patch("app.services.create_guid_service.CreateGuidService.create_guid")
@patch("app.events.publisher.Publisher.publish_message")
@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_latest_ci_metadata")
@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.perform_new_ci_transaction")
class TestHttpPostCiV3:
    """
    Tests for the `http_post_ci_v3` endpoint
    """

    url = "/v3/collection-instruments"

    def test_endpoint_returns_200_if_ci_created_successfully(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
        test_client,
    ):
        """
        Endpoint should return `HTTP_200_OK` and serialized ci metadata as part of the response if new ci is created
        successfully. Assert mocked functions are called with the correct arguments.
        """
        # Update mocked function to return `None` indicating no previous version of metadata is found
        mocked_get_latest_ci_metadata.return_value = None

        response = test_client.post(
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
        mocked_publish_message.assert_called_once_with(CiMetadata(**mock_ci_metadata_v3.model_dump()))


    def test_endpoint_returns_200_if_ci_next_version_created_successfully(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
        test_client,
    ):
        """
        Endpoint should return `HTTP_200_OK` and serialized ci metadata with updated version
        as part of the response if new version of ci is created.
        Assert mocked functions are called with the correct arguments.
        """
        # Update mocked function to return ci metadata indicating a previous version of metadata is found
        mocked_get_latest_ci_metadata.return_value = mock_ci_metadata_v3

        response = test_client.post(
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
        mocked_publish_message.assert_called_once_with(CiMetadata(**mock_next_version_ci_metadata_v3.model_dump()))

    def test_endpoint_returns_200_if_ci_created_successfully_without_version(
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

        response = test_client.post(
            self.url,
            params={"validator_version": "0.0.1", "guid": mock_id,},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_ci_metadata_v3_auto_version.model_dump()
        mocked_get_latest_ci_metadata.assert_called_once_with(
            mock_post_ci_schema.survey_id,
            mock_classifier_type,
            mock_classifier_value,
            mock_post_ci_schema.language,
        )
        mocked_perform_new_ci_transaction.assert_called_once_with(
            mock_id,
            mock_ci_metadata_v3_auto_version,
            mock_post_ci_schema.model_dump(),
            CiSchemaLocationService.get_ci_schema_location(mock_ci_metadata_v3_auto_version),
        )
        mocked_publish_message.assert_called_once_with(CiMetadata(**mock_ci_metadata_v3_auto_version.model_dump()))

    def test_endpoint_returns_200_if_ci_next_version_created_successfully_without_version(
        self,
        mocked_perform_new_ci_transaction,
        mocked_get_latest_ci_metadata,
        mocked_publish_message,
        mocked_create_guid,
        test_client,
    ):
        """
        Endpoint should return `HTTP_200_OK` and serialized ci metadata with updated version
        as part of the response if new version of ci is created.
        Assert mocked functions are called with the correct arguments.
        """
        # Update mocked function to return ci metadata indicating a previous version of metadata is found
        mocked_get_latest_ci_metadata.return_value = mock_ci_metadata_v3

        response = test_client.post(
            self.url,
            params={"validator_version": "0.0.1", "guid": mock_next_version_id},
            headers={"ContentType": CONTENT_TYPE},
            json=mock_post_ci_schema.model_dump(),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_next_version_ci_metadata_v3_auto_version.model_dump()
        mocked_get_latest_ci_metadata.assert_called_once_with(
            mock_post_ci_schema.survey_id,
            mock_classifier_type,
            mock_classifier_value,
            mock_post_ci_schema.language,
        )
        mocked_perform_new_ci_transaction.assert_called_once_with(
            mock_next_version_id,
            mock_next_version_ci_metadata_v3_auto_version,
            mock_post_ci_schema.model_dump(),
            CiSchemaLocationService.get_ci_schema_location(mock_next_version_ci_metadata_v3_auto_version),
        )
        mocked_publish_message.assert_called_once_with(CiMetadata(**mock_next_version_ci_metadata_v3_auto_version.model_dump()))
