# golden-path: ignore
import logging

from google.api_core import exceptions
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class SecretNotFoundError(Exception):
    """Raised when a requested secret or secret version is not found.
    """

    pass


class SecretPermissionError(Exception):
    """Raised when a principal lacks the required IAM permissions for a secret.

        This typically indicates that the service account or user does not have the
        'Secret Manager Secret Accessor' (roles/secretmanager.secretAccessor) role on the
        secret or a parent resource.
    """

    pass


def get_secret(secret_version_id: str) -> str:
    """Fetches a secret's payload from Google Secret Manager.

        This function provides a simplified interface to the Google Cloud Secret
        Manager API. It instantiates a `SecretManagerServiceClient` on each call
        to access a specified secret version and decodes the payload to a UTF-8
        string.

        Args:
            secret_version_id (str): The fully qualified resource name of the secret
                version to access, formatted as
                `projects/*/secrets/*/versions/*`. The version can be a specific
                number or the alias 'latest'.

        Returns:
            str: The secret payload, decoded as a UTF-8 string.

        Raises:
            SecretNotFoundError: Raised when the underlying API returns a
                `google.api_core.exceptions.NotFound` error, indicating the secret
                version resource does not exist.
            SecretPermissionError: Raised when the underlying API returns a
                `google.api_core.exceptions.PermissionDenied` error, indicating the
                caller lacks the necessary IAM permissions (e.g.,
                `secretmanager.versions.access`).
            google.api_core.exceptions.GoogleAPICallError: For other exceptions
                raised by the underlying Google Cloud API client during the RPC
                call.
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
