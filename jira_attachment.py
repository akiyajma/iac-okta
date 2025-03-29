import base64
import os

import requests


def attach_zip_to_jira(zip_filepath):
    """
    Attach a ZIP file to a specified Jira issue using a Personal Access Token (PAT).

    This function sends a POST request to the Jira REST API's attachments endpoint.
    Authentication is handled via Basic Auth using the format: email:PAT.

    Environment Variables Required:
        - JIRA_DOMAIN: The Jira domain (e.g., yourcompany.atlassian.net)
        - JIRA_USER_EMAIL: The email address associated with the Jira account
        - JIRA_PAT: The Personal Access Token for Jira authentication
        - JIRA_ISSUE_KEY: The key of the issue to which the file should be attached (e.g., PROJ-123)

    Args:
        zip_filepath (str): Path to the ZIP file to be attached.

    Raises:
        ValueError: If any required environment variable is missing.

    Prints:
        A success message if the upload is successful,
        otherwise prints an error message with the HTTP response.
    """
    # Load required environment variables
    JIRA_DOMAIN = os.environ.get("JIRA_DOMAIN")
    JIRA_USER_EMAIL = os.environ.get("JIRA_USER_EMAIL")
    JIRA_PAT = os.environ.get("JIRA_PAT")
    JIRA_ISSUE_KEY = os.environ.get("JIRA_ISSUE_KEY")

    # Validate all required variables are present
    if not all([JIRA_DOMAIN, JIRA_USER_EMAIL, JIRA_PAT, JIRA_ISSUE_KEY]):
        raise ValueError(
            "JIRA_DOMAIN, JIRA_USER_EMAIL, JIRA_PAT, and JIRA_ISSUE_KEY must all be set as environment variables."
        )

    # Create Basic Auth token (email:PAT encoded in Base64)
    token = f"{JIRA_USER_EMAIL}:{JIRA_PAT}"
    basic_token = base64.b64encode(token.encode()).decode()

    # Define the Jira REST API endpoint for attachments
    url = f"https://{JIRA_DOMAIN}/rest/api/2/issue/{JIRA_ISSUE_KEY}/attachments"
    headers = {
        "Authorization": f"Basic {basic_token}",
        "X-Atlassian-Token": "no-check"  # Required to disable CSRF check
    }

    # Prepare file payload and make the request
    with open(zip_filepath, "rb") as f:
        files = {
            'file': (os.path.basename(zip_filepath), f, 'application/zip')
        }
        response = requests.post(url, headers=headers, files=files)

    # Handle the response
    if response.status_code in [200, 201]:
        print("Successfully attached ZIP file to Jira.")
    else:
        print("Failed to attach ZIP file to Jira:",
              response.status_code, response.text)
