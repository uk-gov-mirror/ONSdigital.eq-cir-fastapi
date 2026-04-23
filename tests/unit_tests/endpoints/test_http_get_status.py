from unittest.mock import patch

from fastapi import status


class TestHttpGetStatus:
    base_url = "/status"

    @patch("app.routers.status_router.settings")
    def test_endpoint_returns_200_and_right_message_if_deployment_successful(self, mocked_settings, test_client):
        """
        Endpoint should return the right response if the deployment is successful
        """
        mocked_settings.CIR_APPLICATION_VERSION = "dev-048783a4"
        response = test_client.get(self.base_url)
        expected_message = '{"version":"dev-048783a4","status":"OK"}'
        assert expected_message in response.content.decode("utf-8")
        assert response.status_code == status.HTTP_200_OK

    @patch("app.routers.status_router.settings")
    def test_endpoint_returns_500_if_deployment_unsuccessful(self, mocked_settings, test_client_no_server_exception):
        """
        Endpoint should return `HTTP_500_INTERNAL_SERVER_ERROR` if the env var is
        None due to an unsuccessful deployment
        """
        mocked_settings.CIR_APPLICATION_VERSION = None
        response = test_client_no_server_exception.get(self.base_url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
