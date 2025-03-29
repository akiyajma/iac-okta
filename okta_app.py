import csv
import logging
import os

import requests

from config import APP_CSV_FIELDS, APP_GROUP_CSV_FIELDS

logger = logging.getLogger(__name__)


def get_okta_all_apps(access_token, okta_domain):
    """
    Retrieve all applications registered in the Okta organization and export them to a CSV file.

    This function sends paginated GET requests to the Okta `/api/v1/apps` endpoint using the
    provided access token. It collects all application data, aggregates them, and writes the
    results to `output/apps.csv`.

    Args:
        access_token (str): A valid OAuth 2.0 access token for the Okta API.
        okta_domain (str): The base URL of the Okta organization (e.g., https://example.okta.com).

    Returns:
        list or None: A list of application objects if successful, otherwise None.
    """
    url = f"{okta_domain}/api/v1/apps"
    headers = {"Authorization": f"Bearer {access_token}"}
    all_apps = []

    while url:
        response = requests.get(url, headers=headers)
        logger.info("Apps URL: %s", url)
        logger.info("Status: %s", response.status_code)

        if response.status_code != 200:
            logger.error(
                "Failed to retrieve application data: %s", response.text)
            return None

        apps = response.json()
        all_apps.extend(apps)

        # Handle pagination if 'next' link is present
        url = None
        links = response.headers.get("Link")
        if links:
            for link in links.split(","):
                if 'rel="next"' in link:
                    url = link[link.find("<") + 1:link.find(">")]

    write_apps_to_csv(all_apps)
    return all_apps


def write_apps_to_csv(apps: list, filename: str = "apps.csv"):
    """
    Write a list of Okta application objects to a CSV file in the `output` directory.

    Each row in the CSV corresponds to a single application. The fields are defined
    in `APP_CSV_FIELDS` from the config.

    Args:
        apps (list): List of application dictionaries retrieved from the Okta API.
        filename (str): The name of the CSV file to generate.
    """
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filepath = os.path.join(output_folder, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[field for field, _ in APP_CSV_FIELDS],
            quoting=csv.QUOTE_ALL  # Quote all fields for safety
        )
        writer.writeheader()
        for app in apps:
            row = {field: getter(app) for field, getter in APP_CSV_FIELDS}
            writer.writerow(row)

    logger.info("Application list CSV exported: %s", filepath)


def get_okta_app_detail(access_token, okta_domain, app_id):
    """
    Retrieve detailed information for a specific Okta application and export it to a CSV file.

    This function sends a GET request to `/api/v1/apps/{app_id}` and writes
    the application metadata to a CSV file named `app_detail_{app_id}.csv`.

    Args:
        access_token (str): A valid Okta API token.
        okta_domain (str): The base URL of the Okta org.
        app_id (str): The ID of the application to retrieve.

    Returns:
        dict or None: The application detail if successful, otherwise None.
    """
    url = f"{okta_domain}/api/v1/apps/{app_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    logger.info("App Detail URL: %s", url)
    logger.info("Status: %s", response.status_code)

    if response.status_code != 200:
        logger.error(
            "Failed to retrieve application detail: %s", response.text)
        return None

    app = response.json()
    detail = {field: getter(app) for field, getter in APP_CSV_FIELDS}

    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filepath = os.path.join(output_folder, f"app_detail_{app_id}.csv")
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[field for field, _ in APP_CSV_FIELDS],
            quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerow(detail)

    logger.info("Application detail CSV exported: %s", filepath)
    return detail


def get_okta_app_groups(access_token, okta_domain, app_id):
    """
    Retrieve all Okta groups assigned to a specific application and export them to a CSV file.

    This function sends a GET request to `/api/v1/apps/{app_id}/groups` to fetch group
    assignments and exports them to `app_groups_{app_id}.csv`.

    Args:
        access_token (str): A valid Okta API token.
        okta_domain (str): The base URL of the Okta org.
        app_id (str): The ID of the application.

    Returns:
        list or None: A list of assigned group objects, or None if the request fails.
    """
    url = f"{okta_domain}/api/v1/apps/{app_id}/groups"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    logger.info("App Groups URL: %s", url)
    logger.info("Status: %s", response.status_code)

    if response.status_code != 200:
        logger.error(
            "Failed to retrieve application group data: %s", response.text)
        return None

    groups = response.json()
    if groups:
        output_folder = "output"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        filepath = os.path.join(output_folder, f"app_groups_{app_id}.csv")
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[field for field, _ in APP_GROUP_CSV_FIELDS],
                quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            for group in groups:
                row = {field: getter(group)
                       for field, getter in APP_GROUP_CSV_FIELDS}
                writer.writerow(row)

        logger.info("Application group CSV exported: %s", filepath)
    else:
        logger.warning("Application group data is empty.")

    return groups
