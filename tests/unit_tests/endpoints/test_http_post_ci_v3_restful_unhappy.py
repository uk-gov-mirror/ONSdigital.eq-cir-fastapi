import json
from unittest.mock import patch

import pytest
from fastapi import status

from tests.test_data.ci_test_data import mock_ci_metadata_v3, mock_next_version_id, mock_post_ci_schema, mock_id

CONTENT_TYPE = "application/json"
URL = "/v3/collection-instruments"


@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_latest_ci_metadata")
def test_endpoint_returns_400_if_version_smaller_than_latest(
        mocked_get_latest_ci_metadata,
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
        URL,
        params={"validator_version": "0.0.1", "guid": mock_next_version_id, "ci_version": 1},
        headers={"ContentType": CONTENT_TYPE},
        json=mock_post_ci_schema.model_dump(),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "Invalid ci_version provided"


@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.get_ci_metadata_with_id")
def test_endpoint_returns_400_if_guid_already_exists(
        mocked_get_ci_metadata_with_id,
        test_client,
):
    """
    Endpoint should return `HTTP_200_OK` and serialized ci metadata with updated version
    as part of the response if new version of ci is created.
    Assert mocked functions are called with the correct arguments.
    """
    mocked_get_ci_metadata_with_id.return_value = mock_ci_metadata_v3

    response = test_client.post(
        URL,
        params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 100},
        headers={"ContentType": CONTENT_TYPE},
        json=mock_post_ci_schema.model_dump(),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "Invalid GUID provided"


def test_endpoint_returns_400_if_no_post_data(
        test_client,
):
    """
    Endpoint should return `HTTP_400_BAD_REQUEST` if empty or incomplete post data is posted
    as part of the request
    """
    # Make request to base url without any post data
    response = test_client.post(
        URL,
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
        input_param,
        test_client,
):
    """
    Endpoint should return `HTTP_400_BAD_REQUEST` if any required field in post data is `None`
    """
    # update `post_data` to contain `None` value for `input_param` field
    edited_mock_post_ci_schema = mock_post_ci_schema.model_copy()
    setattr(edited_mock_post_ci_schema, input_param, None)

    response = test_client.post(
        URL,
        params={"validator_version": "0.0.1", "ci_version": 100},
        headers={"ContentType": CONTENT_TYPE},
        json=edited_mock_post_ci_schema.model_dump(),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "Validation has failed"


def test_endpoint_returns_400_if_classifier_invalid(
        test_client,
):
    """
    Endpoint should return `HTTP_200_OK` and serialized ci metadata as part of the response if new ci is created
    successfully. Assert mocked functions are called with the correct arguments.
    """
    with open("tests/test_data/classifier_invalid_input.json") as json_file:
        test_data = json.load(json_file)

    response = test_client.post(URL,
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
        input_param,
        test_client,
):
    """
    Endpoint should return `HTTP_400_BAD_REQUEST` if any required field in post data is an
    empty string
    """
    # update `post_data` to contain empty string value for `input_param` field
    edited_mock_post_ci_schema = mock_post_ci_schema.model_copy()
    setattr(edited_mock_post_ci_schema, input_param, "")

    response = test_client.post(
        URL,
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
        input_param,
        test_client,
):
    """
    Endpoint should return `HTTP_400_BAD_REQUEST` if any required field in post data is
    whitespace
    """
    # update `post_data` to contain whitespace value for `input_param` field
    edited_mock_post_ci_schema = mock_post_ci_schema.model_copy()
    setattr(edited_mock_post_ci_schema, input_param, " ")

    response = test_client.post(
        URL,
        params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 100},
        headers={"ContentType": CONTENT_TYPE},
        json=edited_mock_post_ci_schema.model_dump(),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"] == "Validation has failed"


@patch("app.repositories.firebase.ci_firebase_repository.CiFirebaseRepository.perform_new_ci_transaction")
def test_endpoint_returns_500_if_exception_occurs_in_transaction(
        mocked_perform_new_ci_transaction,
        test_client_no_server_exception,
):
    """
    Endpoint should return `HTTP_500_INTERNAL_SERVER_ERROR` as part of the response if ci metadata is created
    but not processed due to an error in transaction
    """
    # Raise an exception to simulate an error in transaction
    mocked_perform_new_ci_transaction.side_effect = Exception()

    response = test_client_no_server_exception.post(
        URL,
        params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 100},
        headers={"ContentType": CONTENT_TYPE},
        json=mock_post_ci_schema.model_dump(),
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["message"] == "Unable to process request"


@patch("app.events.publisher.Publisher.publish_message")
def test_endpoint_returns_500_if_exception_occurs_in_publish_message(
        mocked_publish_message,
        test_client_no_server_exception,
):
    """
    Endpoint should return `HTTP_500_INTERNAL_SERVER_ERROR` as part of the response if ci metadata is created
    but not processed due to an error in publish message
    """
    # Raise an exception to simulate an error in publish message
    mocked_publish_message.side_effect = Exception()

    response = test_client_no_server_exception.post(
        URL,
        params={"validator_version": "0.0.1", "guid": mock_id, "ci_version": 100},
        headers={"ContentType": CONTENT_TYPE},
        json=mock_post_ci_schema.model_dump(),
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["message"] == "Unable to process request"