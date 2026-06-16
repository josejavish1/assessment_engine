# golden-path: ignore
import logging

from google.api_core import exceptions
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class SecretNotFoundError(Exception):
    """Raised when a secret is not found."""

    pass


class SecretPermissionError(Exception):
    """Raised when there is a permission issue accessing a secret."""

    pass


def get_secret(secret_version_id: str) -> str:
    """
    Retrieves a secret from Google Secret Manager.

    Args:
        secret_version_id: The full version ID of the secret.
                           e.g., "projects/my-project/secrets/my-secret/versions/latest"

    Returns:
        The secret value as a string.

    Raises:
        SecretNotFoundError: If the secret is not found.
        SecretPermissionError: If there is a permission issue.
        google.api_core.exceptions.GoogleAPICallError: For other API errors.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=secret_version_id)
        payload = response.payload.data.decode("UTF-8")
        return payload
    except exceptions.NotFound:
        logger.debug(f"Secret not found: {secret_version_id}")
        raise SecretNotFoundError(f"Secret not found: {secret_version_id}")
    except exceptions.PermissionDenied:
        logger.debug(f"Permission denied for secret: {secret_version_id}")
        raise SecretPermissionError(
            f"Permission denied for secret: {secret_version_id}"
        )
    except exceptions.GoogleAPICallError as e:
        logger.debug(f"API error accessing secret {secret_version_id}: {e}")
        raise
