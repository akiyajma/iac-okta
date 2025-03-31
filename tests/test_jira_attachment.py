import builtins
import os

from jira_attachment import attach_zip_and_comment


class DummyResponse:
    """
    A mock HTTP response object to simulate requests.post responses.
    """

    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


def dummy_temp_upload_success(url, headers, files):
    """
    Simulate successful temporary attachment upload to Service Desk.
    """
    return DummyResponse(201, {
        "temporaryAttachments": [{
            "temporaryAttachmentId": "temp-12345",
            "fileName": "dummy.zip"
        }]
    })


def dummy_attachment_success(url, headers, json):
    """
    Simulate successful permanent attachment and public comment.
    """
    return DummyResponse(201)


def dummy_temp_upload_failure(url, headers, files):
    """
    Simulate failed temporary attachment upload.
    """
    return DummyResponse(400, text="Bad Request")


def dummy_file_open(filepath, mode):
    """
    Simulate opening a zip file.
    """
    class DummyFile:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b"dummy content"
    return DummyFile()


def test_attach_zip_success(monkeypatch, tmp_path):
    """
    Test that attach_zip_and_comment() completes successfully when both steps succeed.
    """
    os.environ["JIRA_DOMAIN"] = "jira.example.com"
    os.environ["JIRA_USER_EMAIL"] = "user@example.com"
    os.environ["JIRA_PAT"] = "dummy_pat"
    os.environ["JIRA_ISSUE_KEY"] = "TEST-1"
    os.environ["SERVICE_DESK_ID"] = "2"

    monkeypatch.setattr("jira_attachment.requests.post", lambda url, headers, **kwargs: (
        dummy_temp_upload_success(url, headers, kwargs.get("files"))
        if "attachTemporaryFile" in url
        else dummy_attachment_success(url, headers, kwargs.get("json"))
    ))
    monkeypatch.setattr(builtins, "open", dummy_file_open)

    dummy_zip_path = str(tmp_path / "dummy.zip")
    attach_zip_and_comment(dummy_zip_path)


def test_attach_zip_temp_upload_failure(monkeypatch, tmp_path, capsys):
    """
    Test that attach_zip_and_comment() raises error when temp upload fails.
    """
    os.environ["JIRA_DOMAIN"] = "jira.example.com"
    os.environ["JIRA_USER_EMAIL"] = "user@example.com"
    os.environ["JIRA_PAT"] = "dummy_pat"
    os.environ["JIRA_ISSUE_KEY"] = "TEST-1"
    os.environ["SERVICE_DESK_ID"] = "2"

    monkeypatch.setattr("jira_attachment.requests.post",
                        dummy_temp_upload_failure)
    monkeypatch.setattr(builtins, "open", dummy_file_open)

    dummy_zip_path = str(tmp_path / "dummy.zip")

    try:
        attach_zip_and_comment(dummy_zip_path)
        assert False, "Expected RuntimeError due to failed temp upload"
    except RuntimeError as e:
        assert "Temporary file upload failed" in str(e)
