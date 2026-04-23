from unittest.mock import patch
from urllib.parse import urlencode

from fastapi import status

from app.config import Settings
from app.models.requests import GetCiSchemaV2Params
from tests.test_data.ci_test_data import mock_ci_metadata, mock_id

settings = Settings()


@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_ci_metadata_with_id")
@patch("app.repositories.buckets.ci_schema_bucket_repository.CiSchemaBucketRepository.retrieve_ci_schema")
class TestHttpGetCiSchemaV2Restful:
    """Tests for the `get_collection_instrument_schema_by_guid_v2` endpoint"""

    base_url = "/v2/collection-instruments/schema"
    query_params = GetCiSchemaV2Params(guid=mock_id)
    url = f"{base_url}?{urlencode(query_params.__dict__)}"

    def test_endpoint_returns_200_if_ci_schema_found(self, mocked_retrieve_ci_schema, mocked_get_ci_metadata_with_id, test_client):
        """
        Endpoint should return `HTTP_200_OK` and ci schema as part of the response if ci metadata and schema are found.
        Assert the mocked function is called with the correct params.
        """
        # mocked function to return valid ci metadata, indicating ci metadata is found
        mocked_get_ci_metadata_with_id.return_value = mock_ci_metadata
        # mocked function to return valid ci schema, indicating ci schema is found from bucket
        mocked_retrieve_ci_schema.return_value = mock_ci_metadata.__dict__

        response = test_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_ci_metadata.__dict__
        mocked_get_ci_metadata_with_id.assert_called_once_with(mock_id)

    def test_endpoint_returns_404_if_metadata_not_found(self, mocked_retrieve_ci_schema, mocked_get_ci_metadata_with_id, test_client):
        """
        Endpoint should return `HTTP_404_NOT_FOUND` and a string as part of the response if metadata is not
        found
        """
        # Update mocked function to return `None`, indicating ci metadata is not found
        mocked_get_ci_metadata_with_id.return_value = None

        response = test_client.get(self.url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["message"] == "No results found"

    def test_endpoint_returns_404_if_schema_not_found(self, mocked_retrieve_ci_schema, mocked_get_ci_metadata_with_id, test_client):
        """
        Endpoint should return `HTTP_404_NOT_FOUND` and a string as part of the response if schema is not
        found
        """
        # mocked function to return valid ci metadata, indicating ci metadata is found
        mocked_get_ci_metadata_with_id.return_value = mock_ci_metadata
        # mocked function to return `None`, indicating ci schema is not found from bucket
        mocked_retrieve_ci_schema.return_value = None

        response = test_client.get(self.url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["message"] == "No CI found"

    def test_endpoint_returns_400_if_query_parameters_are_not_present(
        self, mocked_retrieve_ci_schema, mocked_get_ci_metadata_with_id, test_client
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` as part of the response if `id` is not
        part of the querystring parameters
        """
        # Make request to base url without any query params
        response = test_client.get(self.base_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Invalid search parameters provided"
