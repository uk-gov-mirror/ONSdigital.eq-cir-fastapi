from unittest.mock import Mock
from unittest.mock import patch
from urllib.parse import urlencode

from fastapi import status

from app.config import Settings
from app.models.requests import UpdateValidatorVersionV1Params
from tests.test_data.ci_test_data import (
    mock_id, mock_ci_metadata_v2, mock_post_ci_schema, mock_updated_validator_version_v2,
    mock_updated_ci_metadata_v2,
)

settings = Settings()


@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_ci_metadata_with_id")
@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.update_ci_metadata")
@patch("app.repositories.buckets.ci_schema_bucket_repository.CiSchemaBucketRepository.store_ci_schema")
class TestHttpPutValidatorVersionV1:
    """Tests for the `http_put_ci_validator_version_v1` endpoint"""

    base_url = "/v1/collection-instruments/validator-version"

    query_params = UpdateValidatorVersionV1Params(
        guid=mock_id,
        validator_version=mock_updated_validator_version_v2
    )

    url = f"{base_url}?{urlencode(query_params.__dict__)}"

    missing_validator_version = f"{base_url}?guid={query_params.guid}"

    missing_guid = f"{base_url}?validator_version={query_params.validator_version}"

    def test_endpoint_returns_200(self,
                                  mocked_store_ci_schema: Mock,
                                  mocked_update_ci_metadata: Mock,
                                  mocked_get_ci_metadata_with_id: Mock,
                                  test_client,
                                  ):
        content_type = "application/json"
        # mocked function to return valid ci metadata, indicating ci metadata is found
        mocked_get_ci_metadata_with_id.return_value = mock_ci_metadata_v2

        response = test_client.put(self.url,
                              headers={"ContentType": content_type},
                              json=mock_post_ci_schema.model_dump())

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_updated_ci_metadata_v2.model_dump()

        mocked_store_ci_schema.assert_called_once_with(
            f"{mock_updated_ci_metadata_v2.guid}.json",
            mock_post_ci_schema.model_dump(),
        )
        mocked_update_ci_metadata.assert_called_once_with(
            mock_updated_ci_metadata_v2.guid,
            mock_updated_ci_metadata_v2
        )

    def test_endpoint_metadata_not_found(self,
                                         mocked_store_ci_schema: Mock,
                                         mocked_update_ci_metadata: Mock,
                                         mocked_get_ci_metadata_with_id: Mock,
                                         test_client,
                                         ):

        content_type = "application/json"
        mocked_get_ci_metadata_with_id.return_value = None

        # Make request to base url without any query params
        response = test_client.put(self.url,
                              headers={"ContentType": content_type},
                              json=mock_post_ci_schema.model_dump())

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["message"] == "No results found"

    def test_endpoint_returns_400_no_validator_version(self,
                                                       mocked_store_ci_schema: Mock,
                                                       mocked_update_ci_metadata: Mock,
                                                       mocked_get_ci_metadata_with_id: Mock,
                                                       test_client,
                                                       ):
        content_type = "application/json"
        response = test_client.put(self.missing_validator_version,
                              headers={"ContentType": content_type},
                              json=mock_post_ci_schema.model_dump()
                              )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Invalid search parameters provided"

    def test_endpoint_returns_400_no_guid(self,
                                          mocked_store_ci_schema: Mock,
                                          mocked_update_ci_metadata: Mock,
                                          mocked_get_ci_metadata_with_id: Mock,
                                          test_client,
                                          ):
        content_type = "application/json"
        response = test_client.put(self.missing_guid,
                              headers={"ContentType": content_type},
                              json=mock_post_ci_schema.model_dump())

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Invalid search parameters provided"
