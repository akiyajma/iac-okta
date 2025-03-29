import csv

import okta_group


class DummyResponse:
    """
    Dummy response object to simulate `requests.get()` behavior for testing.
    """

    def __init__(self, json_data, status_code, headers=None, text=None):
        self._json = json_data
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text if text is not None else str(json_data)

    def json(self):
        return self._json


def dummy_requests_get(url, headers):
    """
    Mock `requests.get` handler for multiple Okta group-related endpoints.
    """
    if "/groups/" in url and not url.endswith("/apps") and not url.endswith("/users"):
        # Simulate group detail response
        return DummyResponse({
            "id": "group123",
            "name": "Test Group",
            "description": "A test group",
            "created": "2020-01-01",
            "lastUpdated": "2020-01-02",
            "objectClass": "group",
            "type": "OKTA_GROUP",
            "user_count_url": "",
            "apps_url": ""
        }, 200)
    elif url.endswith("/apps"):
        # Simulate apps assigned to a group
        return DummyResponse([
            {
                "id": "app1",
                "label": "App 1",
                "status": "ACTIVE",
                "name": "Application 1",
                "lastUpdated": "2020-01-02"
            }
        ], 200)
    elif url.endswith("/users"):
        # Simulate users in a group
        return DummyResponse([
            {
                "id": "user1",
                "status": "ACTIVE",
                "created": "2020-01-01",
                "lastLogin": "2020-01-02",
                "type": {"id": "type1"},
                "profile": {
                    "firstName": "John",
                    "lastName": "Doe",
                    "email": "john@example.com",
                    "login": "john@example.com"
                }
            }
        ], 200)
    else:
        return DummyResponse({}, 200)


def dummy_requests_get_all_groups(url, headers):
    """
    Return a single page of dummy group data for get_okta_all_group.
    """
    return DummyResponse([
        {
            "id": "group1",
            "profile": {"name": "Group 1", "description": "Desc 1"},
            "type": "OKTA_GROUP",
            "created": "2020-01-01",
            "lastUpdated": "2020-01-02",
            "lastMembershipUpdated": "2020-01-03"
        }
    ], 200)


def dummy_requests_get_fail_groups(url, headers):
    """
    Simulate a failed request when retrieving group data.
    """
    return DummyResponse("Error", 404, text="Error")


def test_get_okta_group_detail(monkeypatch, tmp_path):
    """
    Test that group detail is successfully retrieved and parsed.
    """
    monkeypatch.setattr(okta_group.requests, "get", dummy_requests_get)
    monkeypatch.chdir(tmp_path)  # change current working directory to tmp
    (tmp_path / "output").mkdir()  # ensure output folder exists

    detail = okta_group.get_okta_group_detail(
        "dummy_token", "https://example.okta.com", "group123")
    assert detail["id"] == "group123"
    assert detail["name"] == "Test Group"
    assert (tmp_path / "output" / "group_detail_group123.csv").exists()


def test_get_okta_group_apps(monkeypatch, tmp_path):
    """
    Test retrieval of applications assigned to a group.
    """
    monkeypatch.setattr(okta_group.requests, "get", dummy_requests_get)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()  # Ensure the output directory exists

    apps = okta_group.get_okta_group_apps(
        "dummy_token", "https://example.okta.com", "group123")
    assert isinstance(apps, list)
    assert apps[0]["id"] == "app1"
    assert (tmp_path / "output" / "group_apps_group123.csv").exists()


def test_get_okta_group_users(monkeypatch, tmp_path):
    """
    Test retrieval of users who belong to a group.
    """
    monkeypatch.setattr(okta_group.requests, "get", dummy_requests_get)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()  # Ensure the output directory exists

    users = okta_group.get_okta_group_users(
        "dummy_token", "https://example.okta.com", "group123")
    assert isinstance(users, list)
    assert users[0]["id"] == "user1"
    assert (tmp_path / "output" / "group_users_group123.csv").exists()


def test_write_groups_to_csv(monkeypatch, tmp_path):
    """
    Test writing group data to a CSV file using the configured output folder.
    """
    monkeypatch.chdir(tmp_path)
    from okta_group import write_groups_to_csv

    dummy_groups = [{
        "id": "group123",
        "profile": {"name": "Test Group", "description": "A test group"},
        "type": "OKTA_GROUP",
        "created": "2020-01-01",
        "lastUpdated": "2020-01-02",
        "lastMembershipUpdated": "2020-01-03"
    }]

    write_groups_to_csv(dummy_groups, "test_groups.csv")
    output_file = tmp_path / "output" / "test_groups.csv"
    assert output_file.exists()

    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) >= 2  # header + one row


def test_get_okta_all_group_success(monkeypatch, tmp_path):
    """
    Test successful retrieval of all groups and CSV export.
    """
    monkeypatch.setattr(okta_group.requests, "get",
                        dummy_requests_get_all_groups)
    container = {}

    def dummy_write_groups_to_csv(groups, filename="groups.csv"):
        container["groups"] = groups

    monkeypatch.setattr(okta_group, "write_groups_to_csv",
                        dummy_write_groups_to_csv)

    result = okta_group.get_okta_all_group(
        "dummy_token", "https://example.okta.com")

    expected = [{
        "id": "group1",
        "profile": {"name": "Group 1", "description": "Desc 1"},
        "type": "OKTA_GROUP",
        "created": "2020-01-01",
        "lastUpdated": "2020-01-02",
        "lastMembershipUpdated": "2020-01-03"
    }]

    assert result == expected
    assert container["groups"] == expected


def test_get_okta_all_group_failure(monkeypatch):
    """
    Test handling of an HTTP failure when retrieving all group data.
    """
    monkeypatch.setattr(okta_group.requests, "get",
                        dummy_requests_get_fail_groups)
    result = okta_group.get_okta_all_group(
        "dummy_token", "https://example.okta.com")
    assert result is None
