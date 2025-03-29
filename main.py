import base64
import json
import logging
import os
import sys
import zipfile

from jira_attachment import attach_zip_to_jira
from okta_app import (get_okta_all_apps, get_okta_app_detail,
                      get_okta_app_groups)
from okta_auth import get_okta_access_token
from okta_device import get_okta_all_devices, get_okta_device_detail
from okta_group import (get_okta_all_group, get_okta_group_apps,
                        get_okta_group_detail, get_okta_group_users)
from okta_user import get_okta_all_user

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_input():
    """
    Loads the input data required for the script execution.
    This function attempts to retrieve JSON input either from the
    'INPUT_JSON' environment variable or from a local 'input.json' file.

    Returns:
        dict: Parsed input data.

    Raises:
        SystemExit: If loading or parsing the JSON fails.
    """
    input_data = None
    input_json = os.environ.get("INPUT_JSON")
    if input_json:
        try:
            input_data = json.loads(input_json)
        except Exception as error:
            logger.error("Error parsing INPUT_JSON: %s", error)
            sys.exit(1)
    elif os.path.exists("input.json"):
        try:
            with open("input.json", "r", encoding="utf-8") as f:
                input_data = json.load(f)
        except Exception as error:
            logger.error("Error reading input.json: %s", error)
            sys.exit(1)
    else:
        logger.error("Input data not found.")
        sys.exit(1)
    return input_data


def load_okta_credentials():
    """
    Loads the credentials required for Okta API authentication from environment variables.

    Environment Variables:
        OKTA_DOMAIN, OKTA_CLIENT_ID, OKTA_KEY_PEM_BASE64 (base64-encoded)

    Returns:
        tuple: (okta_domain, client_id, private_key)

    Raises:
        SystemExit: If any required environment variable is missing or if decoding fails.
    """
    okta_domain = os.environ.get("OKTA_DOMAIN")
    client_id = os.environ.get("OKTA_CLIENT_ID")
    private_key_base64 = os.environ.get("OKTA_KEY_PEM_BASE64")

    missing = []
    if not okta_domain:
        missing.append("OKTA_DOMAIN")
    if not client_id:
        missing.append("OKTA_CLIENT_ID")
    if not private_key_base64:
        missing.append("OKTA_KEY_PEM_BASE64")

    if missing:
        logger.error("Missing required Okta credentials: %s",
                     ', '.join(missing))
        sys.exit(1)

    try:
        # Decode the base64 encoded private key to get the original PEM string.
        private_key = base64.b64decode(private_key_base64).decode('utf-8')
    except Exception as error:
        logger.error("Failed to decode OKTA_KEY_PEM_BASE64: %s", error)
        sys.exit(1)

    return okta_domain, client_id, private_key


def execute_action(action, input_data, access_token, okta_domain):
    """
    Executes the specified action using the provided Okta access token and domain.

    This function supports several actions such as retrieving all users,
    all groups, detailed information for a specific group or app, and devices.
    It also writes CSV files to the 'output/' directory.

    Args:
        action (str): The name of the action to perform.
        input_data (dict): Input parameters such as app_id, group_id, or device_id.
        access_token (str): Valid Okta access token.
        okta_domain (str): Base URL for the Okta API.

    Returns:
        dict or list: The resulting data or a message dictionary.

    Raises:
        SystemExit: If required fields are missing or an unsupported action is provided.
    """
    if action == "all_users":
        return get_okta_all_user(access_token, okta_domain)
    elif action == "all_groups":
        return get_okta_all_group(access_token, okta_domain)
    elif action == "detail_groups":
        group_id = input_data.get("group_id")
        if not group_id:
            logger.error("Action 'detail_groups' requires a group_id.")
            sys.exit(1)
        get_okta_group_detail(access_token, okta_domain, group_id)
        get_okta_group_apps(access_token, okta_domain, group_id)
        get_okta_group_users(access_token, okta_domain, group_id)
        return {"message": "Group details, apps, and user data exported to CSV."}
    elif action == "all_apps":
        return get_okta_all_apps(access_token, okta_domain)
    elif action == "detail_app":
        app_id = input_data.get("app_id")
        if not app_id:
            logger.error("Action 'detail_app' requires an app_id.")
            sys.exit(1)
        get_okta_app_detail(access_token, okta_domain, app_id)
        get_okta_app_groups(access_token, okta_domain, app_id)
        return {"message": "Application details and associated group information exported to CSV."}
    elif action == "all_devices":
        return get_okta_all_devices(access_token, okta_domain)
    elif action == "detail_device":
        device_id = input_data.get("device_id")
        if not device_id:
            logger.error("Action 'detail_device' requires a device_id.")
            sys.exit(1)
        get_okta_device_detail(access_token, okta_domain, device_id)
        return {"message": f"Device details for {device_id} exported to CSV."}
    else:
        logger.error("Unsupported action: %s", action)
        sys.exit(1)


def create_output_zip(output_folder='output', zip_filename='okta_data.zip'):
    """
    Archives all files in the specified output folder into a single ZIP file.

    Args:
        output_folder (str, optional): The folder containing output files. Default is 'output'.
        zip_filename (str, optional): The name of the generated ZIP file. Default is 'okta_data.zip'.

    Returns:
        str or None: The path to the created ZIP file, or None if the folder is empty.
    """
    if not os.path.exists(output_folder):
        logger.info(
            "Output folder '%s' does not exist. Creating it.", output_folder)
        os.makedirs(output_folder)

    has_files = any(files for _, _, files in os.walk(output_folder))
    if not has_files:
        logger.info(
            "No files found in '%s'. Skipping zip creation.", output_folder)
        return None

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_folder):
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, arcname=file)

    logger.info("Created ZIP file: %s", zip_filename)
    return zip_filename


def main():
    """
    Orchestrates the overall flow of retrieving data from Okta and attaching the results to a Jira ticket.

    Steps:
        1. Load input data from environment variables or a file.
           → JSON input should include 'action' and, if needed, 'app_id', 'group_id', or 'device_id'.
        2. Load required Okta API credentials from environment variables.
           (OKTA_DOMAIN, OKTA_CLIENT_ID, OKTA_KEY_PEM_BASE64)
        3. Obtain an access token.
        4. Execute the specified Okta action.
        5. Export the results to CSV files in the 'output/' directory.
        6. Create a ZIP archive of the results.
        7. Attach the ZIP file to a Jira ticket.

    The script exits with code 1 if any required step is missing.
    """
    input_data = load_input()

    action = input_data.get("action")
    if not action:
        logger.error("The 'action' key is missing from the input JSON.")
        sys.exit(1)

    okta_domain, client_id, private_key = load_okta_credentials()

    # Read Okta scope from environment variable; default if not set.
    scope = os.environ.get(
        "OKTA_SCOPE", "okta.groups.read okta.users.read okta.apps.read")

    try:
        access_token = get_okta_access_token(
            client_id=client_id,
            okta_domain=okta_domain,
            private_key_pem=private_key,
            scope=scope
        )
    except Exception as error:
        logger.error("Failed to obtain access token: %s", error)
        sys.exit(1)

    execute_action(action, input_data, access_token, okta_domain)

    zip_filepath = create_output_zip()
    if zip_filepath:
        try:
            attach_zip_to_jira(zip_filepath)
        except Exception as error:
            logger.warning("Warning: Failed to attach zip to Jira: %s", error)
    else:
        logger.info("No output files found to attach.")


if __name__ == "__main__":
    main()
