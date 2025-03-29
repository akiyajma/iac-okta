import logging
from datetime import datetime, timedelta, timezone

import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)


def load_private_key(pem_key_str: str):
    """
    Load a private key object from a PEM-formatted string.

    This function is used to deserialize a PEM-encoded private key string
    (typically in RSA format) into a usable key object for signing JWTs.

    Args:
        pem_key_str (str): A string containing the PEM-encoded private key.

    Returns:
        Any: A private key object usable with cryptographic functions.

    Raises:
        Exception: If loading the key fails, the exception is logged and raised.
    """
    try:
        return serialization.load_pem_private_key(
            pem_key_str.encode(),
            password=None,
            backend=default_backend()
        )
    except Exception as error:
        logger.error("Failed to load private key: %s", error)
        raise


def generate_jwt(client_id: str, audience: str, private_key_pem: str):
    """
    Generate a JWT (JSON Web Token) signed with a private key for use in client assertion.

    This JWT is used in Okta's OAuth 2.0 Client Credentials flow to authenticate the client.

    Args:
        client_id (str): The client ID issued by Okta.
        audience (str): The intended audience for the JWT, usually the token endpoint URL.
        private_key_pem (str): PEM-encoded RSA private key as a string.

    Returns:
        str: A signed JWT as a string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "iss": client_id,  # Issuer (client)
        "sub": client_id,  # Subject (client)
        "aud": audience,   # Audience (token endpoint)
        "iat": int(now.timestamp()),  # Issued at (current time)
        # Expiration time (5 minutes)
        "exp": int((now + timedelta(minutes=5)).timestamp())
    }

    private_key = load_private_key(private_key_pem)
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token


def get_okta_access_token(client_id: str, okta_domain: str, private_key_pem: str, scope: str):
    """
    Obtain an access token from Okta using the OAuth 2.0 Client Credentials flow.

    This function uses a JWT as a client assertion to authenticate to Okta’s token endpoint
    and requests an access token for the specified scopes.

    Note:
        The `scope` argument must be provided by the caller. In our implementation,
        main.py obtains the scope from the environment variable OKTA_SCOPE (with a default value
        of "okta.groups.read okta.users.read okta.devices.read" if not set) and passes it in.
        Therefore, this function does not define a default value for scope.

    Args:
        client_id (str): The Okta-issued client ID.
        okta_domain (str): The base URL of the Okta domain (e.g., https://example.okta.com).
        private_key_pem (str): PEM-encoded RSA private key as a string.
        scope (str): Space-separated scopes to include in the token request.
                     (Typically "okta.groups.read okta.users.read okta.devices.read")

    Returns:
        str: The OAuth 2.0 access token issued by Okta.

    Raises:
        RuntimeError: If the token request fails, a RuntimeError is raised with details.
    """
    token_url = f"{okta_domain}/oauth2/v1/token"
    audience = token_url

    # Generate a signed JWT for client assertion
    jwt_token = generate_jwt(client_id, audience, private_key_pem)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": scope,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": jwt_token,
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        logger.error("Failed to get token: %s", response.text)
        raise RuntimeError(f"Failed to get token: {response.text}")
