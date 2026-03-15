# CloudDrive Skill

## Overview

This skill enables AI agents to interact with a CloudDrive personal cloud storage system. Users must configure the CloudDrive URL and API Key before use.

## Required Configuration

Before using this skill, users must provide:

1. **CLOUDDRIVE_URL**: The base URL of the CloudDrive instance
   - Example: `http://localhost:5051` or `https://your-clouddrive.example.com`
2. **CLOUDDRIVE_API_KEY**: The API Key for authentication
   - Get from user or generate via: `POST /api/login` then `POST /api/api-key`

**Ask user for these values if not provided.**

## Quick Start

```python
# User must configure these:
CLOUDDRIVE_URL = "http://localhost:5051"  # Ask user
CLOUDDRIVE_API_KEY = "your-api-key"      # Ask user
```

## Core Functions

### 1. Get User Info

```python
import requests

def get_user_info(url, api_key):
    headers = {"X-API-Key": api_key}
    response = requests.get(f"{url}/api/user", headers=headers)
    return response.json()

# Example response:
# {"user_id": 1, "username": "john", "storage_used": 1048576}
```

### 2. List Files

```python
def list_files(url, api_key, folder_id=None):
    headers = {"X-API-Key": api_key}
    params = {"folder_id": folder_id} if folder_id else {}
    response = requests.get(f"{url}/api/files", headers=headers, params=params)
    return response.json()

# Example response:
# {
#     "files": [
#         {"id": 1, "filename": "report.pdf", "filesize": 2048000, "created_at": "2024-01-15"}
#     ],
#     "folders": [
#         {"id": 2, "name": "Documents", "created_at": "2024-01-10"}
#     ]
# }
```

### 3. Download File

```python
def download_file(url, api_key, filename, save_path=None):
    headers = {"X-API-Key": api_key}
    response = requests.get(f"{url}/api/download/{filename}", headers=headers)
    
    if response.status_code == 200:
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(response.content)
        return {"success": True, "content": response.content}
    return {"success": False, "error": response.text}
```

### 4. Upload File

```python
def upload_file(url, api_key, file_path):
    headers = {"X-API-Key": api_key}
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{url}/api/upload", files=files, headers=headers)
    return response.json()

# Example response:
# {"message": "File uploaded successfully", "filename": "test.txt", "filesize": 1024}
```

### 5. Create Folder

```python
def create_folder(url, api_key, name, parent_id=None):
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    data = {"name": name, "parent_id": parent_id}
    response = requests.post(f"{url}/api/folders", json=data, headers=headers)
    return response.json()

# Example response:
# {"message": "Folder created", "folder_id": 5}
```

### 6. Delete File

```python
def delete_file(url, api_key, filename):
    headers = {"X-API-Key": api_key}
    response = requests.delete(f"{url}/api/delete/{filename}", headers=headers)
    return response.json()

# Example response:
# {"message": "File deleted successfully"}
```

### 7. Delete Folder

```python
def delete_folder(url, api_key, folder_id):
    headers = {"X-API-Key": api_key}
    response = requests.delete(f"{url}/api/folders/{folder_id}", headers=headers)
    return response.json()

# Example response:
# {"message": "Folder deleted successfully"}
```

## Complete Workflow Example

```python
import requests

# === CONFIGURATION (Ask user for these) ===
CLOUDDRIVE_URL = "http://localhost:5051"  # REQUIRED: Ask user
CLOUDDRIVE_API_KEY = "your-api-key"       # REQUIRED: Ask user
# ===========================================

def clouddrive_request(method, endpoint, **kwargs):
    """Make authenticated request to CloudDrive."""
    headers = {"X-API-Key": CLOUDDRIVE_API_KEY}
    headers.update(kwargs.pop("headers", {}))
    url = f"{CLOUDDRIVE_URL}{endpoint}"
    response = requests.request(method, url, headers=headers, **kwargs)
    return response

# Get user info
user = clouddrive_request("GET", "/api/user")
print(f"User: {user.json()['username']}")

# List files
files = clouddrive_request("GET", "/api/files")
print(f"Files: {files.json()}")

# Upload a file
with open("document.pdf", "rb") as f:
    result = clouddrive_request("POST", "/api/upload", files={"file": f})
print(f"Upload: {result.json()}")
```

## Important Notes

- All API calls require authentication via `X-API-Key` header
- Files are stored in user-specific directories (managed internally)
- Folders can be nested (use `parent_id` parameter)
- Upload size is limited by available disk space
- All timestamps are in UTC

## Error Handling

Common error responses:

| Status | Error | Solution |
|--------|-------|----------|
| 401 | Unauthorized | Check API Key is valid |
| 404 | Not Found | Check filename/folder_id exists |
| 400 | Bad Request | Check request format |
