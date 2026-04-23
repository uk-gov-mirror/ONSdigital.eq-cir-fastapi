from unittest.mock import patch
from urllib.parse import urlencode

from fastapi import status

from app.config import Settings
from app.models.requests import GetCiMetadataV2Params
from tests.test_data.ci_test_data import (
    mock_ci_metadata_list,
    mock_classifier_type,
    mock_classifier_value,
    mock_language,
    mock_survey_id,
)

settings = Settings()


@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_ci_metadata_collection")
@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_all_ci_metadata_collection")
class TestHttpGetCiMetadataV2Restful:
    """Tests for the `get_collection_instruments_metadata_v2` endpoint"""

    base_url = "/v2/collection-instruments/metadata"

    query_params = GetCiMetadataV2Params(
        classifier_type=mock_classifier_type,
        classifier_value=mock_classifier_value,
        language=mock_language,
        survey_id=mock_survey_id,
    )
    url = f"{base_url}?{urlencode(query_params.__dict__)}"

    classifier_error = (
        f"{base_url}?classifier_type=bad_classifier&classifier_value={mock_classifier_value}"
        f"&language={mock_language}&survey_id={mock_survey_id}"
    )

    missing_one_query_param = f"{base_url}?classifier_type={mock_classifier_type}&&survey_id={mock_survey_id}"

    def test_endpoint_returns_200_when_all_params_are_none(
        self,
        mocked_get_all_ci_metadata_collection,
        mocked_get_ci_metadata_collection,
        test_client,
    ):
        mocked_get_all_ci_metadata_collection.return_value = mock_ci_metadata_list

        response = test_client.get(self.base_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [mock_ci_metadata.model_dump() for mock_ci_metadata in mock_ci_metadata_list]

    def test_endpoint_returns_400_when_one_param_is_missing(
        self,
        mocked_get_all_ci_metadata_collection,
        mocked_get_ci_metadata_collection,
        test_client,
    ):
        response = test_client.get(self.missing_one_query_param)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Invalid search parameters provided"

    def test_endpoint_returns_200_if_ci_metadata_found_with_query(
        self,
        mocked_get_all_ci_metadata_collection,
        mocked_get_ci_metadata_collection,
        test_client,
    ):
        """
        Endpoint should return `HTTP_200_OK` and ci metadata collection as part of the response if ci metadata is found if
        queried with params.
        Assert the mocked function is called with the correct params.
        """
        # Update mocked function to return a list of valid ci metadata
        mocked_get_ci_metadata_collection.return_value = mock_ci_metadata_list

        response = test_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [mock_ci_metadata.model_dump() for mock_ci_metadata in mock_ci_metadata_list]

        mocked_get_ci_metadata_collection.assert_called_once_with(
            mock_survey_id, mock_classifier_type, mock_classifier_value, mock_language
        )

    def test_endpoint_returns_404_if_ci_metadata_not_found(
        self,
        mocked_get_all_ci_metadata_collection,
        mocked_get_ci_metadata_collection,
        test_client,
    ):
        """
        Endpoint should return `HTTP_404_NOT_FOUND` and a string indicating a bad request
        as part of the response if ci metadata is not found
        """
        mocked_get_ci_metadata_collection.return_value = None

        response = test_client.get(self.url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["message"] == "No CI found"

    def test_endpoint_returns_404_if_ci_metadata_not_found_and_no_param_used(
        self,
        mocked_get_all_ci_metadata_collection,
        mocked_get_ci_metadata_collection,
        test_client,
    ):
        mocked_get_all_ci_metadata_collection.return_value = None

        response = test_client.get(self.base_url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["message"] == "No CI found"


    def test_endpoint_returns_400_if_invalid_classifier_is_used(
        self,
        mocked_get_all_ci_metadata_collection,
        mocked_get_ci_metadata_collection,
        test_client,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` as part of the response if `classifier_type`, `classifier_value`
        `language` and/or `survey_id` are not part of the query string parameters
        """
        # Make request to base url without any query params
        response = test_client.get(self.classifier_error)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Validation has failed"
