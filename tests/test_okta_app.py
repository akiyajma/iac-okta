import okta_app


# Dummy response class to simulate requests.get behavior
class DummyResponse:
    def __init__(self, json_data, status_code, headers=None, text=None):
        self._json = json_data
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text if text is not None else str(json_data)

    def json(self):
        return self._json


def dummy_requests_get(url, headers):
    """
    Simulate Okta app and group data responses based on URL.
    """
    if "/apps/" in url and not url.endswith("/groups"):
        return DummyResponse({
            "id": "app123",
            "name": "Test App",
            "label": "TestLabel",
            "status": "ACTIVE",
            "created": "2020-01-01",
            "lastUpdated": "2020-01-02",
            "signOnMode": "BOOKMARK",
            "accessibility": {},
            "visibility": {},
            "features": [],
            "credentials": {},
            "settings": {}
        }, 200)
    elif url.endswith("/groups"):
        return DummyResponse([
            {
                "id": "group1",
                "profile": {"name": "Group 1", "description": "Test group"},
                "created": "2020-01-01",
                "lastUpdated": "2020-01-02"
            }
        ], 200)
    return DummyResponse([], 200)


def dummy_requests_get_all_apps(url, headers):
    """
    Return a single-page app list for testing.
    """
    return DummyResponse([{"id": "app1", "name": "App One"}], 200, headers={})


def dummy_requests_get_fail(url, headers):
    """
    Simulate failed request with HTTP 404.
    """
    return DummyResponse("Error", 404, text="Error")


def dummy_requests_get_empty_groups(url, headers):
    """
    Return empty group list for app group API.
    """
    return DummyResponse([], 200)


def test_get_okta_app_detail(monkeypatch, tmp_path):
    """
    Test successful retrieval of app detail and writing CSV.
    """
    monkeypatch.setattr(okta_app.requests, "get", dummy_requests_get)
    monkeypatch.chdir(tmp_path)  # Set current working directory to temp
    (tmp_path / "output").mkdir()  # Create output directory

    detail = okta_app.get_okta_app_detail(
        "dummy_token", "https://example.okta.com", "app123"
    )
    assert detail["id"] == "app123"
    assert detail["name"] == "Test App"
    assert (tmp_path / "output" / "app_detail_app123.csv").exists()


def test_get_okta_app_groups(monkeypatch, tmp_path):
    """
    Test successful retrieval of groups associated with an app.
    """
    monkeypatch.setattr(okta_app.requests, "get", dummy_requests_get)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()

    groups = okta_app.get_okta_app_groups(
        "dummy_token", "https://example.okta.com", "app123"
    )
    assert isinstance(groups, list)
    assert groups[0]["id"] == "group1"
    assert (tmp_path / "output" / "app_groups_app123.csv").exists()


def test_get_okta_app_groups_empty(monkeypatch, tmp_path):
    """
    Test case for an app with no associated groups.
    """
    monkeypatch.setattr(okta_app.requests, "get",
                        dummy_requests_get_empty_groups)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()

    groups = okta_app.get_okta_app_groups(
        "dummy_token", "https://example.okta.com", "app123"
    )
    assert groups == []


def test_get_okta_all_apps_success(monkeypatch):
    """
    Test successful retrieval of all apps and CSV export.
    """
    monkeypatch.setattr(okta_app.requests, "get", dummy_requests_get_all_apps)
    container = {}

    def dummy_write_apps_to_csv(apps, filename="apps.csv"):
        container["apps"] = apps

    monkeypatch.setattr(okta_app, "write_apps_to_csv", dummy_write_apps_to_csv)

    result = okta_app.get_okta_all_apps(
        "dummy_token", "https://example.okta.com"
    )
    assert result == [{"id": "app1", "name": "App One"}]
    assert container["apps"] == [{"id": "app1", "name": "App One"}]


def test_get_okta_all_apps_failure(monkeypatch):
    """
    Test failed request for retrieving all apps.
    """
    monkeypatch.setattr(okta_app.requests, "get", dummy_requests_get_fail)
    result = okta_app.get_okta_all_apps(
        "dummy_token", "https://example.okta.com"
    )
    assert result is None
