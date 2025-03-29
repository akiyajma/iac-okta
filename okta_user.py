import csv
import logging
import os

import requests

from config import USER_CSV_FIELDS

logger = logging.getLogger(__name__)


def get_okta_all_user(access_token, okta_domain):
    """
    Retrieve all users from the Okta API and export the result to a CSV file.

    This function makes a paginated request to the Okta API to retrieve all users
    in the organization. The collected user data is then exported to a CSV file
    located in the "output" directory.

    Args:
        access_token (str): OAuth 2.0 access token for authentication.
        okta_domain (str): The base URL of your Okta organization (e.g., https://dev-12345.okta.com).

    Returns:
        list: A list of user objects retrieved from the Okta API, or None if the request fails.
    """
    url = f"{okta_domain}/api/v1/users?limit=200"
    headers = {"Authorization": f"Bearer {access_token}"}
    all_users = []

    # Loop through paginated responses
    while url:
        response = requests.get(url, headers=headers)
        logger.info("URL: %s", url)
        logger.info("Status: %s", response.status_code)

        if response.status_code != 200:
            logger.error("Failed to retrieve user data: %s", response.text)
            return None

        users = response.json()
        all_users.extend(users)

        # Check for pagination in response headers
        url = None
        links = response.headers.get("Link")
        if links:
            for link in links.split(","):
                if 'rel="next"' in link:
                    url = link[link.find("<") + 1:link.find(">")]

    write_users_to_csv(all_users)
    return all_users


def write_users_to_csv(users: list, filename: str = "users.csv"):
    """
    Write the provided list of user data to a CSV file.

    The function exports user attributes defined in `USER_CSV_FIELDS` to a CSV file
    stored in the "output" directory.

    Args:
        users (list): A list of user objects to export.
        filename (str): The filename to use for the CSV export. Default is "users.csv".
    """
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filepath = os.path.join(output_folder, filename)

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write CSV header
        writer.writerow([field_name for field_name, _ in USER_CSV_FIELDS])
        # Write each user row
        for user in users:
            row = [getter(user) for _, getter in USER_CSV_FIELDS]
            writer.writerow(row)

    logger.info("CSV file exported: %s", filepath)
