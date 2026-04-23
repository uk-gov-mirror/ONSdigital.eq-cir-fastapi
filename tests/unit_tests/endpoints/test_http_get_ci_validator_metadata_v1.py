from unittest.mock import patch
from fastapi import status

from tests.test_data.ci_test_data import mock_ci_metadata_list, mock_ci_validator_metadata_list

URL = "/v1/collection-instruments/validator-metadata"

@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_all_ci_metadata_collection")
def test_endpoint_returns_200_if_ci_validator_metadata_found(
        mocked_get_all_ci_metadata_collection,
        test_client
):
    """
    Endpoint should return `HTTP_200_OK` and a string as part of the response if ci validator metadata is found.
    """
    mocked_get_all_ci_metadata_collection.return_value = mock_ci_metadata_list

    response = test_client.get(URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [mock_ci_validator_metadata.model_dump() for mock_ci_validator_metadata in mock_ci_validator_metadata_list]
    mocked_get_all_ci_metadata_collection.assert_called_once()

def test_endpoint_returns_404_if_ci_validator_metadata_not_found(test_client):
    """
    Endpoint should return `HTTP_404_NOT_FOUND` as part of the response if ci validator metadata is not found.
    """
    response = test_client.get(URL)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["message"] == "No CI validator metadata found"
