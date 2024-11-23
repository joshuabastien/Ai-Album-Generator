import base64
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables from .env
load_dotenv()

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Personal Access Token with repo scope
GITHUB_REPO = os.getenv("GITHUB_REPO")  # Format: username/repo-name
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")  # Default to 'main'

# Netlify Configuration
NETLIFY_SITE_ID = os.getenv("NETLIFY_SITE_ID")
NETLIFY_TOKEN = os.getenv("NETLIFY_TOKEN")

def upload_to_github(file_path):
    """
    Uploads a file to a GitHub repository.
    """
    
    repo = GITHUB_REPO
    branch = GITHUB_BRANCH
    token = GITHUB_TOKEN

    # Read file content
    with open(file_path, "rb") as f:
        content = f.read()
    
    # Encode file content in Base64 (required by GitHub API)
    encoded_content = base64.b64encode(content).decode("utf-8")

    # Prepare API endpoint and headers
    filename = os.path.basename(file_path)
    github_api_url = f"https://api.github.com/repos/{repo}/contents/public/uploads/{filename}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Check if the file already exists in the repo
    response = requests.get(github_api_url, headers=headers)
    if response.status_code == 200:
        # File exists; retrieve the SHA to update it
        sha = response.json()["sha"]
        print(f"File {filename} already exists in the repo. Updating it...")
    else:
        # New file; no SHA needed
        sha = None
        print(f"Uploading new file {filename} to the repo...")

    # Construct the payload
    payload = {
        "message": f"Added file upload via script",
        "content": encoded_content,
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    # Upload the file
    response = requests.put(github_api_url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"File {filename} uploaded successfully.")
        return f"https://raw.githubusercontent.com/{repo}/{branch}/public/uploads/{filename}"
    else:
        print(f"Failed to upload file: {response.status_code}")
        print(response.text)
        return None

def trigger_netlify_build():
    """
    Triggers a Netlify build and returns the deploy ID for monitoring.
    """
    site_id = NETLIFY_SITE_ID
    token = NETLIFY_TOKEN

    url = f"https://api.netlify.com/api/v1/sites/{site_id}/builds"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(url, headers=headers)

    if response.status_code == 201 or response.status_code == 200:
        deploy_data = response.json()
        deploy_id = deploy_data.get("deploy_id")
        deploy_state = deploy_data.get("deploy_state")
        print(f"Netlify build triggered successfully. Deploy state: {deploy_state}")
        return deploy_id  # Return deploy ID for further monitoring
    else:
        print(f"Failed to trigger Netlify build: {response.status_code}")
        print(response.text)
        return None


# Ensure the uploaded image URL is accessible
def verify_image_url(url, retries=120, delay=60):
    for attempt in range(retries):
        print(f"Attempt {attempt + 1} of {retries} to verify URL: {url}")
        try:
            response = requests.get(url)
            print(f"Received status code: {response.status_code}")
            if response.status_code == 200:
                print("Image URL is accessible.")
                return True
            else:
                print(f"URL not accessible yet. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error during GET request: {e}")
        
        print(f"Retrying in {delay} seconds...")
        time.sleep(delay)
    
    print("Failed to verify the image URL after multiple attempts.")
    return False
