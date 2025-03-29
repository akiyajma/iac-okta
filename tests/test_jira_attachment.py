import os

from jira_attachment import attach_zip_to_jira


class DummyResponse:
    """
    A mock HTTP response object to simulate requests.post responses.
    """

    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


def dummy_post_success(url, headers, files):
    """
    Simulate a successful HTTP POST request.
    """
    return DummyResponse(201)


def dummy_post_failure(url, headers, files):
    """
    Simulate a failed HTTP POST request with status 400.
    """
    return DummyResponse(400, "Bad Request")


def dummy_open_zip(filepath, mode):
    """
    Simulate opening a zip file for reading, returning a dummy file-like object.
    """
    class DummyFile:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            pass

        def read(self):
            return b"dummy zip content"

    return DummyFile()


def test_attach_zip_success(monkeypatch, tmp_path):
    """
    Test that attach_zip_to_jira() completes without error when the upload is successful.
    """
    # Set required environment variables for the Jira upload
    os.environ["JIRA_DOMAIN"] = "jira.example.com"
    os.environ["JIRA_USER_EMAIL"] = "user@example.com"
    os.environ["JIRA_PAT"] = "dummy_pat"
    os.environ["JIRA_ISSUE_KEY"] = "TEST-1"

    # Mock requests.post and open
    monkeypatch.setattr("jira_attachment.requests.post", dummy_post_success)
    monkeypatch.setattr("builtins.open", dummy_open_zip)

    # Simulate a dummy zip file path
    dummy_zip = str(tmp_path / "dummy.zip")

    # No exception should be raised during upload
    attach_zip_to_jira(dummy_zip)


def test_attach_zip_failure(monkeypatch, tmp_path, capsys):
    """
    Test that an error message is printed to stdout when the upload fails.
    """
    # Set required environment variables for the Jira upload
    os.environ["JIRA_DOMAIN"] = "jira.example.com"
    os.environ["JIRA_USER_EMAIL"] = "user@example.com"
    os.environ["JIRA_PAT"] = "dummy_pat"
    os.environ["JIRA_ISSUE_KEY"] = "TEST-1"

    # Mock failed upload and file opening
    monkeypatch.setattr("jira_attachment.requests.post", dummy_post_failure)
    monkeypatch.setattr("builtins.open", dummy_open_zip)

    # Simulate a dummy zip file path
    dummy_zip = str(tmp_path / "dummy.zip")

    # Attempt to upload, expecting failure
    attach_zip_to_jira(dummy_zip)

    # Capture stdout and verify error message is present
    captured = capsys.readouterr().out
    assert "Failed to attach ZIP file to Jira:" in captured
