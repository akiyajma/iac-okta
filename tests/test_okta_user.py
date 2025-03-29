import okta_user


class DummyResponse:
    """
    A dummy response class to simulate the behavior of `requests.get`.
    """

    def __init__(self, json_data, status_code, headers=None):
        self._json = json_data
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._json


def dummy_requests_get(url, headers):
    """
    Simulate Okta API user response for a simple, single-page result.
    """
    if "limit=200" in url:
        return DummyResponse([{
            "id": "user1",
            "status": "ACTIVE",
            "created": "2020-01-01",
            "lastLogin": "2020-01-02",
            "profile": {
                "firstName": "Jane",
                "lastName": "Doe",
                "email": "jane@example.com",
                "login": "jane@example.com"
            }
        }], 200, headers={"Link": ""})
    return DummyResponse([], 200)


def test_get_okta_all_user(monkeypatch, tmp_path):
    """
    Test that all Okta users are retrieved and returned correctly.

    This test mocks the `requests.get` function and simulates a successful
    response with a single user. It also mocks the file system operations
    to prevent actual directory creation during CSV export.
    """
    # Patch HTTP GET
    monkeypatch.setattr(okta_user.requests, "get", dummy_requests_get)

    # Change working directory to tmp_path for isolated file output
    monkeypatch.chdir(tmp_path)

    # Ensure output folder exists
    (tmp_path / "output").mkdir()

    # Run function under test
    users = okta_user.get_okta_all_user(
        "dummy_token", "https://example.okta.com"
    )

    # Assertions
    assert isinstance(users, list)
    assert users[0]["id"] == "user1"

    # Validate that output CSV was created
    output_csv = tmp_path / "output" / "users.csv"
    assert output_csv.exists()
