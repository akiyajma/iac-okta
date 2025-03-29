import csv
import logging
import os

import requests

from config import (GROUP_APP_CSV_FIELDS, GROUP_DETAIL_CSV_FIELDS,
                    GROUP_LIST_CSV_FIELDS, GROUP_USER_CSV_FIELDS)

logger = logging.getLogger(__name__)


def get_okta_all_group(access_token, okta_domain):
    """
    Retrieve a list of all groups from the Okta API and export the result to a CSV file.

    Args:
        access_token (str): OAuth 2.0 access token.
        okta_domain (str): The base URL of the Okta domain.

    Returns:
        list: A list of group objects retrieved from Okta, or None if the request fails.
    """
    url = f"{okta_domain}/api/v1/groups?limit=200"
    headers = {"Authorization": f"Bearer {access_token}"}
    all_groups = []

    # Paginated request loop
    while url:
        response = requests.get(url, headers=headers)
        logger.info("URL: %s", url)
        logger.info("Status: %s", response.status_code)

        if response.status_code != 200:
            logger.error("Failed to retrieve group data: %s", response.text)
            return None

        groups = response.json()
        all_groups.extend(groups)

        # Check for next page in the response header
        url = None
        links = response.headers.get("Link")
        if links:
            for link in links.split(","):
                if 'rel="next"' in link:
                    url = link[link.find("<") + 1:link.find(">")]

    write_groups_to_csv(all_groups)
    return all_groups


def get_okta_group_detail(access_token, okta_domain, group_id):
    """
    Retrieve detailed information about a specific group and export it to a CSV file.

    Args:
        access_token (str): OAuth 2.0 access token.
        okta_domain (str): The base URL of the Okta domain.
        group_id (str): The ID of the group to retrieve.

    Returns:
        dict: A dictionary of the group's detailed information, or None if the request fails.
    """
    url = f"{okta_domain}/api/v1/groups/{group_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    logger.info("Group Detail URL: %s", url)
    logger.info("Status: %s", response.status_code)

    if response.status_code != 200:
        logger.error("Failed to retrieve group detail: %s", response.text)
        return None

    group = response.json()
    detail = {field: getter(group)
              for field, getter in GROUP_DETAIL_CSV_FIELDS}

    # Write detail to CSV
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    filepath = os.path.join(output_folder, f"group_detail_{group_id}.csv")

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=[field for field, _ in GROUP_DETAIL_CSV_FIELDS])
        writer.writeheader()
        writer.writerow(detail)

    logger.info("Group detail CSV exported: %s", filepath)
    return detail


def get_okta_group_apps(access_token, okta_domain, group_id):
    """
    Retrieve the list of applications assigned to a specific group and export it to a CSV file.

    Args:
        access_token (str): OAuth 2.0 access token.
        okta_domain (str): The base URL of the Okta domain.
        group_id (str): The ID of the group to query.

    Returns:
        list: A list of applications assigned to the group, or None if the request fails.
    """
    url = f"{okta_domain}/api/v1/groups/{group_id}/apps"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    logger.info("Group Apps URL: %s", url)
    logger.info("Status: %s", response.status_code)

    if response.status_code != 200:
        logger.error("Failed to retrieve group apps: %s", response.text)
        return None

    apps = response.json()
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    filepath = os.path.join(output_folder, f"group_apps_{group_id}.csv")

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        if apps:
            writer = csv.DictWriter(
                f, fieldnames=[field for field, _ in GROUP_APP_CSV_FIELDS])
            writer.writeheader()
            for app in apps:
                row = {field: getter(app)
                       for field, getter in GROUP_APP_CSV_FIELDS}
                writer.writerow(row)
        else:
            f.write("No apps found\n")

    logger.info("Group apps CSV exported: %s", filepath)
    return apps


def get_okta_group_users(access_token, okta_domain, group_id):
    """
    Retrieve the list of users in a specific group and export the result to a CSV file.

    Args:
        access_token (str): OAuth 2.0 access token.
        okta_domain (str): The base URL of the Okta domain.
        group_id (str): The ID of the group to query.

    Returns:
        list: A list of users in the group, or None if the request fails.
    """
    url = f"{okta_domain}/api/v1/groups/{group_id}/users"
    headers = {"Authorization": f"Bearer {access_token}"}
    all_users = []

    # Paginated request loop
    while url:
        response = requests.get(url, headers=headers)
        logger.info("Group Users URL: %s", url)
        logger.info("Status: %s", response.status_code)

        if response.status_code != 200:
            logger.error("Failed to retrieve group users: %s", response.text)
            return None

        users = response.json()
        all_users.extend(users)

        # Check for next page
        url = None
        links = response.headers.get("Link")
        if links:
            for link in links.split(","):
                if 'rel="next"' in link:
                    url = link[link.find("<") + 1:link.find(">")]

    if all_users:
        output_folder = "output"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        filepath = os.path.join(output_folder, f"group_users_{group_id}.csv")

        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=[field for field, _ in GROUP_USER_CSV_FIELDS])
            writer.writeheader()
            for user in all_users:
                row = {field: getter(user)
                       for field, getter in GROUP_USER_CSV_FIELDS}
                writer.writerow(row)

        logger.info("Group users CSV exported: %s", filepath)
    else:
        logger.warning("User data is empty.")

    return all_users


def write_groups_to_csv(groups: list, filename: str = "groups.csv"):
    """
    Write a list of group objects to a CSV file.

    Args:
        groups (list): List of group dictionaries to write.
        filename (str): The name of the output CSV file. Defaults to "groups.csv".
    """
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    filepath = os.path.join(output_folder, filename)

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=[field for field, _ in GROUP_LIST_CSV_FIELDS])
        writer.writeheader()
        for group in groups:
            row = {field: getter(group)
                   for field, getter in GROUP_LIST_CSV_FIELDS}
            writer.writerow(row)

    logger.info("Group list CSV exported: %s", filepath)
