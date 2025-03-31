import base64
import os

import requests


def attach_zip_and_comment(zip_filepath: str) -> None:
    """
    Uploads a ZIP file to a Jira Service Management issue so that the attachment is visible
    to the customer in the customer portal. This function follows the two-step upload process
    required by the Service Desk API:

    Step 1: Upload the file as a temporary attachment using the `attachTemporaryFile` endpoint.
    Step 2: Promote the temporary file to a permanent attachment on the issue using the `attachment`
            endpoint, while posting a public comment referencing the file.

    Environment Variables:
        - JIRA_DOMAIN: Your Jira Cloud domain (e.g., yourcompany.atlassian.net)
        - JIRA_USER_EMAIL: The email address associated with your Jira account
        - JIRA_PAT: A personal access token (PAT) for Jira authentication
        - JIRA_ISSUE_KEY: The key of the issue you want to attach the file to (e.g., PROJ-123)
        - SERVICE_DESK_ID: The numeric ID of the service desk project

    Args:
        zip_filepath (str): The full path to the ZIP file to upload.

    Raises:
        ValueError: If any required environment variable is missing.
        RuntimeError: If any of the API calls fail.
    """

    # Load required environment variables
    JIRA_DOMAIN = os.environ.get("JIRA_DOMAIN")
    JIRA_USER_EMAIL = os.environ.get("JIRA_USER_EMAIL")
    JIRA_PAT = os.environ.get("JIRA_PAT")
    JIRA_ISSUE_KEY = os.environ.get("JIRA_ISSUE_KEY")
    SERVICE_DESK_ID = os.environ.get(
        "SERVICE_DESK_ID") or "2"  # fallback if not set

    if not all([JIRA_DOMAIN, JIRA_USER_EMAIL, JIRA_PAT, JIRA_ISSUE_KEY, SERVICE_DESK_ID]):
        raise ValueError("Missing one or more required environment variables: "
                         "JIRA_DOMAIN, JIRA_USER_EMAIL, JIRA_PAT, JIRA_ISSUE_KEY, SERVICE_DESK_ID")

    # Prepare Basic Auth header
    token = f"{JIRA_USER_EMAIL}:{JIRA_PAT}"
    basic_token = base64.b64encode(token.encode()).decode()

    # Step 1: Upload file as a temporary attachment
    temp_upload_url = f"https://{JIRA_DOMAIN}/rest/servicedeskapi/servicedesk/{SERVICE_DESK_ID}/attachTemporaryFile"
    headers = {
        "Authorization": f"Basic {basic_token}",
        "X-Atlassian-Token": "no-check"
    }

    with open(zip_filepath, "rb") as f:
        files = {"file": (os.path.basename(zip_filepath),
                          f, "application/octet-stream")}
        temp_response = requests.post(
            temp_upload_url, headers=headers, files=files)
        print(
            f"Temporary file upload response: {temp_response.status_code} - {temp_response.text}")

    if temp_response.status_code not in [200, 201]:
        raise RuntimeError(
            f"Temporary file upload failed: {temp_response.status_code} - {temp_response.text}")

    # Step 1.5: Extract temporaryAttachmentIds from the response
    temp_data = temp_response.json()
    if "temporaryAttachments" in temp_data:
        temporary_attachment_ids = [
            item["temporaryAttachmentId"]
            for item in temp_data["temporaryAttachments"]
            if "temporaryAttachmentId" in item
        ]
    else:
        temporary_attachment_ids = None

    if not temporary_attachment_ids:
        raise RuntimeError(
            "No temporaryAttachmentIds found in temporary file upload response.")

    # Step 2: Promote the temporary file to a permanent attachment and post a public comment
    attach_url = f"https://{JIRA_DOMAIN}/rest/servicedeskapi/request/{JIRA_ISSUE_KEY}/attachment"
    attach_headers = {
        "Authorization": f"Basic {basic_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "temporaryAttachmentIds": temporary_attachment_ids,
        "public": True,
        "additionalComment": {
            "body": f"{os.path.basename(zip_filepath)} has been attached. Please review the file."
        }
    }

    attach_response = requests.post(
        attach_url, headers=attach_headers, json=payload)
    if attach_response.status_code not in [200, 201]:
        raise RuntimeError(
            f"Failed to attach temporary file: {attach_response.status_code} - {attach_response.text}")

    print(
        f"[✓] File attached and visible to customer: {os.path.basename(zip_filepath)}")
