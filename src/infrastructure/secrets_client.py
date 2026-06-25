# NOTE: This module is programmatically excluded from automated golden-path analysis due to its direct interaction with external infrastructure services.
import logging

from google.api_core import exceptions
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class SecretNotFoundError(Exception):
    """Indicate that a requested secret or secret version was not found in Secret Manager."""

    pass


class SecretPermissionError(Exception):
    """Error for insufficient IAM permissions on a Google Secret Manager secret.

    This exception is raised on an attempt to access a secret version when
    the authenticated principal (e.g., a service account) lacks the necessary
    IAM permissions. Typically, this indicates the principal is missing the
    `roles/secretmanager.secretAccessor` role on the secret or a parent
    resource.
    """

    pass


def get_secret(secret_version_id: str) -> str:
    """Retrieve a secret's payload from Google Cloud Secret Manager.

    This function wraps the `secretmanager.SecretManagerServiceClient` to provide
    a simplified interface for accessing a specific secret version. It handles
    common Google Cloud API exceptions by re-raising them as more specific,
    application-level exceptions.

    Args:
        secret_version_id: The fully qualified resource name of the secret
            version, formatted as
            `projects/{project_id}/secrets/{secret_id}/versions/{version_id}`.

    Returns:
        The UTF-8 decoded secret payload.

    Raises:
        SecretNotFoundError: If the specified secret version is not found.
        SecretPermissionError: If the authenticated principal lacks the
            `secretmanager.secretAccessor` IAM permission for the secret.
        google.api_core.exceptions.GoogleAPICallError: For other underlying
            Google Cloud API errors encountered during the request.
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
