import csv
import logging
import os

import requests

from config import DEVICE_CSV_FIELDS

logger = logging.getLogger(__name__)


def get_okta_all_devices(access_token, okta_domain):
    """
    Retrieve all devices registered in the Okta organization and export them to a CSV file.

    This function sends paginated GET requests to the Okta `/api/v1/devices` endpoint using the
    provided access token. It collects all device data, aggregates them, and writes the
    results to `output/devices.csv`.

    Args:
        access_token (str): A valid OAuth 2.0 access token for the Okta API.
        okta_domain (str): The base URL of the Okta organization (e.g., https://example.okta.com).

    Returns:
        list or None: A list of device objects if successful, otherwise None.
    """
    url = f"{okta_domain}/api/v1/devices"
    headers = {"Authorization": f"Bearer {access_token}"}
    all_devices = []

    while url:
        response = requests.get(url, headers=headers)
        logger.info("Devices URL: %s", url)
        logger.info("Status: %s", response.status_code)

        if response.status_code != 200:
            logger.error("Failed to retrieve device data: %s", response.text)
            return None

        devices = response.json()
        all_devices.extend(devices)

        # Handle pagination if 'next' link is present
        url = None
        links = response.headers.get("Link")
        if links:
            for link in links.split(","):
                if 'rel="next"' in link:
                    url = link[link.find("<") + 1:link.find(">")]
                    break

    write_devices_to_csv(all_devices)
    return all_devices


def write_devices_to_csv(devices: list, filename: str = "devices.csv"):
    """
    Write a list of Okta device objects to a CSV file in the `output` directory.

    Each row in the CSV corresponds to a single device. The fields are defined
    in DEVICE_CSV_FIELDS from the config.

    Args:
        devices (list): List of device dictionaries retrieved from the Okta API.
        filename (str): The name of the CSV file to generate.
    """
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filepath = os.path.join(output_folder, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[field for field, _ in DEVICE_CSV_FIELDS],
            quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        for device in devices:
            row = {field: getter(device)
                   for field, getter in DEVICE_CSV_FIELDS}
            writer.writerow(row)

    logger.info("Device list CSV exported: %s", filepath)


def get_okta_device_detail(access_token, okta_domain, device_id):
    """
    Retrieve detailed information for a specific Okta device and export it to a CSV file.

    This function sends a GET request to `/api/v1/devices/{device_id}` and writes
    the device metadata to a CSV file named `device_detail_{device_id}.csv`.

    Args:
        access_token (str): A valid Okta API token.
        okta_domain (str): The base URL of the Okta organization.
        device_id (str): The ID of the device to retrieve.

    Returns:
        dict or None: The device detail if successful, otherwise None.
    """
    url = f"{okta_domain}/api/v1/devices/{device_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    logger.info("Device Detail URL: %s", url)
    logger.info("Status: %s", response.status_code)

    if response.status_code != 200:
        logger.error("Failed to retrieve device detail: %s", response.text)
        return None

    device = response.json()
    detail = {field: getter(device) for field, getter in DEVICE_CSV_FIELDS}

    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    filepath = os.path.join(output_folder, f"device_detail_{device_id}.csv")
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[field for field, _ in DEVICE_CSV_FIELDS],
            quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerow(detail)

    logger.info("Device detail CSV exported: %s", filepath)
    return detail
