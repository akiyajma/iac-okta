import base64
import builtins
import json
import os
import zipfile

import pytest

import main
from main import (create_output_zip, execute_action, load_input,
                  load_okta_credentials)

# -----------------------
# Tests for load_input()
# -----------------------


def test_load_input_env(monkeypatch):
    """
    Test loading input from the INPUT_JSON environment variable.
    """
    sample_input = {
        "action": "all_users",
        "app_id": "dummy_app",
        "group_id": "dummy_group"
    }
    monkeypatch.setenv("INPUT_JSON", json.dumps(sample_input))
    data = load_input()
    assert data == sample_input


def test_load_input_from_file(monkeypatch, tmp_path):
    """
    Test loading input from the input.json file.
    """
    monkeypatch.delenv("INPUT_JSON", raising=False)
    test_file = tmp_path / "input.json"
    sample_data = {
        "action": "all_apps",
        "app_id": "dummy_app"
    }
    test_file.write_text(json.dumps(sample_data))

    monkeypatch.setattr(os.path, "exists",
                        lambda path: True if path == "input.json" else False)
    original_open = builtins.open
    monkeypatch.setattr(
        "builtins.open",
        lambda filename, mode="r", encoding="utf-8": original_open(
            test_file, mode, encoding=encoding)
    )

    result = load_input()
    assert result["action"] == "all_apps"


def test_load_input_no_env_no_file(monkeypatch):
    """
    Test failure when neither env var nor file is present.
    """
    monkeypatch.delenv("INPUT_JSON", raising=False)
    monkeypatch.setattr(os.path, "exists", lambda path: False)
    with pytest.raises(SystemExit):
        load_input()


# -------------------------------
# Tests for load_okta_credentials()
# -------------------------------

def test_load_okta_credentials_valid(monkeypatch):
    """
    Test loading Okta credentials when all required env variables are present.
    OKTA_KEY_PEM_BASE64 is provided as a base64-encoded string.
    """
    monkeypatch.setenv("OKTA_DOMAIN", "https://example.okta.com")
    monkeypatch.setenv("OKTA_CLIENT_ID", "dummy_client")
    encoded_key = base64.b64encode("dummy_key".encode("utf-8")).decode("utf-8")
    monkeypatch.setenv("OKTA_KEY_PEM_BASE64", encoded_key)
    okta_domain, client_id, private_key = load_okta_credentials()
    assert okta_domain == "https://example.okta.com"
    assert client_id == "dummy_client"
    assert private_key == "dummy_key"


def test_load_okta_credentials_missing(monkeypatch):
    """
    Test failure when some Okta credentials env variables are missing.
    """
    monkeypatch.setenv("OKTA_DOMAIN", "https://example.okta.com")
    monkeypatch.delenv("OKTA_CLIENT_ID", raising=False)
    monkeypatch.delenv("OKTA_KEY_PEM_BASE64", raising=False)
    with pytest.raises(SystemExit):
        load_okta_credentials()


# ---------------------
# Tests for execute_action()
# ---------------------

# Dummy functions for mocking
def dummy_get_okta_all_user(access_token, okta_domain):
    return "dummy_users"


def dummy_get_okta_all_group(access_token, okta_domain):
    return "dummy_groups"


def dummy_get_okta_group_detail(access_token, okta_domain, group_id):
    return {"id": group_id, "detail": "group detail"}


def dummy_get_okta_group_apps(access_token, okta_domain, group_id):
    return [{"id": "app1"}]


def dummy_get_okta_group_users(access_token, okta_domain, group_id):
    return [{"id": "user1"}]


def dummy_get_okta_all_apps(access_token, okta_domain):
    return [{"id": "app1"}]


def dummy_get_okta_app_detail(access_token, okta_domain, app_id):
    return {"id": app_id, "name": "Test App"}


def dummy_get_okta_app_groups(access_token, okta_domain, app_id):
    return [{"id": "group1"}]


def test_execute_action_all_users(monkeypatch):
    """
    Test executing 'all_users' action.
    """
    monkeypatch.setattr(main, "get_okta_all_user", dummy_get_okta_all_user)
    input_data = {"action": "all_users"}
    result = execute_action("all_users", input_data,
                            "dummy_token", "https://example.okta.com")
    assert result == "dummy_users"


def test_execute_action_all_groups(monkeypatch):
    """
    Test executing 'all_groups' action.
    """
    monkeypatch.setattr(main, "get_okta_all_group", dummy_get_okta_all_group)
    input_data = {"action": "all_groups"}
    result = execute_action("all_groups", input_data,
                            "dummy_token", "https://example.okta.com")
    assert result == "dummy_groups"


def test_execute_action_detail_groups(monkeypatch):
    """
    Test executing 'detail_groups' action.
    """
    monkeypatch.setattr(main, "get_okta_group_detail",
                        dummy_get_okta_group_detail)
    monkeypatch.setattr(main, "get_okta_group_apps", dummy_get_okta_group_apps)
    monkeypatch.setattr(main, "get_okta_group_users",
                        dummy_get_okta_group_users)
    input_data = {"action": "detail_groups", "group_id": "group123"}
    result = execute_action("detail_groups", input_data,
                            "dummy_token", "https://example.okta.com")
    assert "Group details" in result["message"]


def test_execute_action_detail_groups_missing(monkeypatch):
    """
    Test 'detail_groups' action when group_id is missing.
    """
    input_data = {"action": "detail_groups"}
    with pytest.raises(SystemExit):
        execute_action("detail_groups", input_data,
                       "dummy_token", "https://example.okta.com")


def test_execute_action_all_apps(monkeypatch):
    """
    Test executing 'all_apps' action.
    """
    monkeypatch.setattr(main, "get_okta_all_apps", dummy_get_okta_all_apps)
    input_data = {"action": "all_apps"}
    result = execute_action("all_apps", input_data,
                            "dummy_token", "https://example.okta.com")
    assert result == [{"id": "app1"}]


def test_execute_action_detail_app(monkeypatch):
    """
    Test executing 'detail_app' action.
    """
    monkeypatch.setattr(main, "get_okta_app_detail", dummy_get_okta_app_detail)
    monkeypatch.setattr(main, "get_okta_app_groups", dummy_get_okta_app_groups)
    input_data = {"action": "detail_app", "app_id": "app123"}
    result = execute_action("detail_app", input_data,
                            "dummy_token", "https://example.okta.com")
    assert "Application details" in result["message"]


def test_execute_action_detail_app_missing(monkeypatch):
    """
    Test 'detail_app' action when app_id is missing.
    """
    input_data = {"action": "detail_app"}
    with pytest.raises(SystemExit):
        execute_action("detail_app", input_data, "dummy_token",
                       "https://example.okta.com")


def test_execute_action_unsupported():
    """
    Test an unsupported action results in failure.
    """
    input_data = {"action": "unsupported"}
    with pytest.raises(SystemExit):
        execute_action("unsupported", input_data, "dummy_token",
                       "https://example.okta.com")


def test_execute_action_detail_device(monkeypatch):
    """
    Test executing 'detail_device' action.
    """
    # モック関数は何かダミーの値を返すが、実際の戻り値は固定メッセージとなる
    monkeypatch.setattr(main, "get_okta_device_detail",
                        lambda token, domain, device_id: {"displayName": "Test Device Detail"})
    input_data = {"action": "detail_device", "device_id": "device123"}
    result = execute_action("detail_device", input_data,
                            "dummy_token", "https://example.okta.com")
    expected_msg = "Device details for device123 exported to CSV."
    assert result["message"] == expected_msg


# --------------------------
# Tests for create_output_zip()
# --------------------------

def test_create_output_zip(tmp_path):
    """
    Test that a ZIP archive is created correctly from the output directory.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    dummy_file = output_dir / "dummy.txt"
    dummy_file.write_text("dummy content")

    zip_path = tmp_path / "test_zip.zip"
    result = create_output_zip(str(output_dir), str(zip_path))

    assert result == str(zip_path)
    assert os.path.exists(result)
    assert zipfile.is_zipfile(result)

    with zipfile.ZipFile(result, 'r') as zipf:
        assert "dummy.txt" in zipf.namelist()


def test_create_output_zip_no_output(tmp_path):
    """
    Test that None is returned if the output directory does not exist.
    """
    nonexistent_folder = tmp_path / "nonexistent_folder"
    result = create_output_zip(str(nonexistent_folder), "dummy.zip")
    assert result is None


# ---------------------
# Integration test for main()
# ---------------------

def dummy_get_okta_access_token(client_id, okta_domain, private_key_pem, scope):
    return "dummy_token"


def dummy_attach_zip_to_jira(zip_filepath):
    pass


def test_main_success(monkeypatch, tmp_path):
    """
    Integration-style test for the main() function with mocked dependencies.
    """
    sample_input = {"action": "all_users"}
    monkeypatch.setenv("INPUT_JSON", json.dumps(sample_input))
    monkeypatch.setenv("OKTA_DOMAIN", "https://example.okta.com")
    monkeypatch.setenv("OKTA_CLIENT_ID", "dummy_client")
    encoded_key = base64.b64encode("dummy_key".encode("utf-8")).decode("utf-8")
    monkeypatch.setenv("OKTA_KEY_PEM_BASE64", encoded_key)
    monkeypatch.setattr(main, "get_okta_access_token",
                        dummy_get_okta_access_token)
    monkeypatch.setattr(main, "get_okta_all_user",
                        lambda token, domain: [{"id": "user1"}])
    monkeypatch.setattr(main, "attach_zip_and_comment",
                        dummy_attach_zip_to_jira)

    monkeypatch.setattr(main, "create_output_zip",
                        lambda *args, **kwargs: "dummy.zip")
    monkeypatch.setattr(main, "load_input", lambda: sample_input)

    # Should run without exceptions
    main.main()
