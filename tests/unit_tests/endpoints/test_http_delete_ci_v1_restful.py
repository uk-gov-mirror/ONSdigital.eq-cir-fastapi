from unittest.mock import patch
from urllib.parse import urlencode

from fastapi import status

from app.config import Settings
from app.models.requests import DeleteCiV1Params
from tests.test_data.ci_test_data import mock_ci_metadata, mock_survey_id

settings = Settings()


@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_ci_metadata_collection_with_survey_id")
@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.perform_delete_ci_transaction")
class TestHttpDeleteCiV1Restful:
    """Tests for the `delete_collection_instrument` endpoint"""

    base_url = "/v1/collection-instruments"
    query_params = DeleteCiV1Params(survey_id=mock_survey_id)
    url = f"{base_url}?{urlencode(query_params.__dict__)}"

    def test_endpoint_returns_200_if_ci_deleted(
        self,
        mocked_perform_delete_ci_transaction,
        mocked_get_ci_metadata_collection_with_survey_id,
        test_client,
    ):
        """
        Endpoint should return `HTTP_200_OK` and a return confirmation string as part of the response
        if ci is found and deleted. Assert that the correct methods are called with the correct arguments
        """
        # Update mocked function to return a list of valid ci metadata
        mocked_get_ci_metadata_collection_with_survey_id.return_value = [mock_ci_metadata]

        response = test_client.delete(self.url)
        expected_message = f"CI metadata and schema successfully deleted for {self.query_params.survey_id}."

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_message
        mocked_get_ci_metadata_collection_with_survey_id.assert_called_once_with(mock_survey_id)
        mocked_perform_delete_ci_transaction.assert_called_once_with([mock_ci_metadata])

    def test_endpoint_returns_400_if_query_parameters_are_not_present(
        self,
        mocked_perform_delete_ci_transaction,
        mocked_get_ci_metadata_collection_with_survey_id,
        test_client,
    ):
        """
        Endpoint should return `HTTP_400_BAD_REQUEST` as part of the response if `
        `survey_id` are not part of the querystring parameters
        """
        # Make request to base url without any query params
        response = test_client.delete(self.base_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["message"] == "Invalid search parameters provided"

    def test_endpoint_returns_404_if_ci_not_found(
        self,
        mocked_perform_delete_ci_transaction,
        mocked_get_ci_metadata_collection_with_survey_id,
        test_client,
    ):
        """
        Endpoint should return `HTTP_404_NOT_FOUND` and a string indicating a bad request
        as part of the response if no ci is found to delete
        """
        # Update mocked function to return `None` showing ci metadata is not found
        mocked_get_ci_metadata_collection_with_survey_id.return_value = None

        response = test_client.delete(self.url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["message"] == "No CI to delete"

    def test_endpoint_returns_500_if_ci_not_deleted(
        self,
        mocked_perform_delete_ci_transaction,
        mocked_get_ci_metadata_collection_with_survey_id,
        test_client_no_server_exception,
    ):
        """
        Endpoint should return `HTTP_500_INTERNAL_SERVER_ERROR` as part of the response if ci is
        found but not deleted due to an error in transaction
        """
        # Update mocked function to return a list of valid ci metadata to indicate ci is found
        mocked_get_ci_metadata_collection_with_survey_id.return_value = [mock_ci_metadata]
        # Raise an exception to simulate an error in transaction
        mocked_perform_delete_ci_transaction.side_effect = Exception()

        response = test_client_no_server_exception.delete(self.url)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["message"] == "Unable to process request"
