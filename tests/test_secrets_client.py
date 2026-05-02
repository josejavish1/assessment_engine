
import pytest
from unittest.mock import patch, MagicMock
from google.api_core import exceptions
from assessment_engine.lib.secrets_client import get_secret, SecretNotFoundError, SecretPermissionError

@patch('assessment_engine.lib.secrets_client.secretmanager.SecretManagerServiceClient')
def test_get_secret_success(mock_client_constructor):
    """
    Tests successful retrieval of a secret.
    """
    mock_client = MagicMock()
    mock_client_constructor.return_value = mock_client

    secret_payload = "my-super-secret-value"
    mock_response = MagicMock()
    mock_response.payload.data = secret_payload.encode("UTF-8")
    mock_client.access_secret_version.return_value = mock_response

    secret_id = "projects/my-project/secrets/my-secret/versions/latest"
    result = get_secret(secret_id)

    assert result == secret_payload
    mock_client.access_secret_version.assert_called_once_with(name=secret_id)

@patch('assessment_engine.lib.secrets_client.secretmanager.SecretManagerServiceClient')
def test_get_secret_not_found(mock_client_constructor):
    """
    Tests handling of a secret that is not found.
    """
    mock_client = MagicMock()
    mock_client_constructor.return_value = mock_client
    mock_client.access_secret_version.side_effect = exceptions.NotFound("Secret not found")

    secret_id = "projects/my-project/secrets/non-existent-secret/versions/latest"
    with pytest.raises(SecretNotFoundError):
        get_secret(secret_id)

    mock_client.access_secret_version.assert_called_once_with(name=secret_id)

@patch('assessment_engine.lib.secrets_client.secretmanager.SecretManagerServiceClient')
def test_get_secret_permission_denied(mock_client_constructor):
    """
    Tests handling of permission denied errors.
    """
    mock_client = MagicMock()
    mock_client_constructor.return_value = mock_client
    mock_client.access_secret_version.side_effect = exceptions.PermissionDenied("Permission denied")

    secret_id = "projects/my-project/secrets/protected-secret/versions/latest"
    with pytest.raises(SecretPermissionError):
        get_secret(secret_id)

    mock_client.access_secret_version.assert_called_once_with(name=secret_id)

@patch('assessment_engine.lib.secrets_client.secretmanager.SecretManagerServiceClient')
def test_get_secret_other_api_error(mock_client_constructor):
    """
    Tests handling of other Google API errors.
    """
    mock_client = MagicMock()
    mock_client_constructor.return_value = mock_client
    mock_client.access_secret_version.side_effect = exceptions.InternalServerError("Internal server error")

    secret_id = "projects/my-project/secrets/error-secret/versions/latest"
    with pytest.raises(exceptions.InternalServerError):
        get_secret(secret_id)

    mock_client.access_secret_version.assert_called_once_with(name=secret_id)
