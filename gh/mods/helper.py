import os
import requests

def workflow_permissions_(owner, repo_name, permission_level):
    token = os.getenv('GITHUB_TOKEN')
    url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/permissions/workflow"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "default_workflow_permissions": permission_level
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code in (200, 204):
        print(f"Successfully set workflow permissions to {permission_level} for {repo_name}")
    else:
        print(f"Failed to set permissions: {response.status_code}, {response.text}")
