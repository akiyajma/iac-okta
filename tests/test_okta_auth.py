import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

import okta_auth


@pytest.fixture
def rsa_private_key_pem():
    """
    Fixture to generate a temporary RSA private key in PEM format
    for testing purposes.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    return pem.decode('utf-8')


def test_load_private_key_valid(rsa_private_key_pem):
    """
    Test that a valid PEM string is correctly parsed into a private key object.
    """
    key = okta_auth.load_private_key(rsa_private_key_pem)
    assert key is not None


def test_generate_jwt(rsa_private_key_pem):
    """
    Test the JWT generation function and verify claims without signature validation.
    """
    client_id = "dummy_client"
    audience = "https://example.okta.com/oauth2/v1/token"
    token = okta_auth.generate_jwt(client_id, audience, rsa_private_key_pem)

    # Decode the JWT without verifying the signature to inspect payload
    decoded = jwt.decode(token, options={"verify_signature": False})

    assert decoded["iss"] == client_id
    assert decoded["sub"] == client_id
    assert decoded["aud"] == audience
    assert decoded["iat"] < decoded["exp"]


# Dummy response simulating a successful token response from Okta
def dummy_requests_post_success(url, headers, data):
    class DummyResponse:
        status_code = 200

        def json(self):
            return {"access_token": "dummy_access_token"}
    return DummyResponse()


# Dummy response simulating a failed token response from Okta
def dummy_requests_post_failure(url, headers, data):
    class DummyResponse:
        status_code = 400
        text = "Bad Request"
    return DummyResponse()


def test_get_okta_access_token_success(monkeypatch, rsa_private_key_pem):
    """
    Test successful retrieval of an access token using a dummy HTTP response.
    """
    client_id = "dummy_client"
    okta_domain = "https://example.okta.com"
    scope = "okta.groups.read okta.users.read"

    monkeypatch.setattr(okta_auth.requests, "post",
                        dummy_requests_post_success)

    token = okta_auth.get_okta_access_token(
        client_id, okta_domain, rsa_private_key_pem, scope
    )

    assert token == "dummy_access_token"


def test_get_okta_access_token_failure(monkeypatch, rsa_private_key_pem):
    """
    Test failure case when token request returns a non-200 response.
    """
    client_id = "dummy_client"
    okta_domain = "https://example.okta.com"
    scope = "okta.groups.read okta.users.read"

    monkeypatch.setattr(okta_auth.requests, "post",
                        dummy_requests_post_failure)

    with pytest.raises(RuntimeError) as excinfo:
        okta_auth.get_okta_access_token(
            client_id, okta_domain, rsa_private_key_pem, scope
        )

    assert "Failed to get token" in str(excinfo.value)
