# Okta Resource Exporter with GitHub Actions Integration

This project provides a Python-based utility to retrieve resources from the Okta API, export them as CSV files, package them into a ZIP archive, and optionally attach the result to a Jira issue. It is designed to be run via GitHub Actions using a `workflow_dispatch` trigger for on-demand execution.

## Features

- Supports retrieval of the following Okta resources:
  - All Users
  - All Groups
  - Group Detail (apps and users)
  - All Applications
  - Application Detail (with assigned groups)
  - All Devices
  - Device Detail
- Outputs all data as CSV into an `output/` directory
- Archives the result as a ZIP file
- Automatically attaches the ZIP file to a Jira issue
- Securely uses GitHub Secrets and Environment Variables
- Compatible with `workflow_dispatch` inputs for flexible execution

## Prerequisites

- Python 3.12+
- A GitHub repository configured with the required secrets
- Okta OAuth 2.0 service app with JWT authentication
- Jira with API access

## GitHub Actions Workflow Example

```yaml
name: Execute Get Okta Resource

on:
  workflow_dispatch:
    inputs:
      input_json:
        description: 'JSON input containing action, group_id, app_id, and device_id'
        required: true
        type: string
        default: |
          {
            "action": "all_users",
            "group_id": "",
            "app_id": "",
            "device_id": ""
          }
      jira_issue_key:
        description: 'Jira issue key to link the results (e.g., "PROJ-123")'
        required: true
        type: string
```

## Supported Actions

The following values can be specified in the `action` field of the input JSON:

| Action           | Required Field(s) | Description                                                      |
|------------------|-------------------|------------------------------------------------------------------|
| `all_users`      | -                 | Retrieve and export all users in Okta                            |
| `all_groups`     | -                 | Retrieve and export all groups in Okta                           |
| `detail_groups`  | `group_id`        | Retrieve details of a specific group (info, apps, users)         |
| `all_apps`       | -                 | Retrieve and export all applications in Okta                     |
| `detail_app`     | `app_id`          | Retrieve detailed information and assigned groups for an app     |
| `all_devices`    | -                 | Retrieve and export all devices registered with Okta             |
| `detail_device`  | `device_id`       | Retrieve detailed information for a specific device              |

## Output

All retrieved resources are exported as `.csv` files to the `output/` directory.  
At the end of the job, these files are compressed into a `ZIP` archive (`okta_data.zip`) and can be optionally attached to a Jira ticket.

## Required Secrets

| Name                | Description                                   |
|---------------------|-----------------------------------------------|
| `OKTA_CLIENT_ID`    | OAuth 2.0 Client ID from Okta                 |
| `OKTA_KEY_PEM_BASE64` | Base64-encoded PEM-formatted private key     |
| `JIRA_PAT`          | Jira Personal Access Token                    |
| `JIRA_USER_EMAIL`   | Email address associated with the PAT         |

## Required Environment Variables

These can be defined in the workflow `env` section:

| Variable       | Description                                                    |
|----------------|----------------------------------------------------------------|
| `OKTA_DOMAIN`  | The full domain URL of your Okta instance (e.g. `https://your-okta.okta.com`) |
| `JIRA_DOMAIN`  | Jira domain (e.g. `yourorg.atlassian.net`)                    |
| `OKTA_SCOPE`   | (Optional) Space-separated list of scopes (default: `okta.groups.read okta.users.read okta.apps.read`) |

## Running the Workflow

You can trigger the workflow manually using GitHub Actions' **workflow_dispatch**.  
The following example input would retrieve all Okta users:

```json
{
  "action": "all_users",
  "group_id": "",
  "app_id": "",
  "device_id": ""
}
```

## Documentation
Documentation is generated and available in the docs/ directory. It includes detailed information about the modules and functions in the project.

To generate the documentation in Markdown format, run the following command:

pdoc --html --output-dir temp-docs --force .  
