import os
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional


class GitLabUploader:
    def __init__(self, base_url: str, token: str, project_id: str, branch: str = "main"):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.project_id = project_id
        self.branch = branch
        self.headers = {
            "PRIVATE-TOKEN": token,
            "Content-Type": "application/json"
        }
    
    def _encode_file_path(self, file_path: str) -> str:
        return file_path.replace("/", "%2F").replace("\\", "%2F")
    
    def file_exists(self, file_path: str) -> bool:
        encoded_path = self._encode_file_path(file_path)
        url = f"{self.base_url}/api/v4/projects/{self.project_id}/repository/files/{encoded_path}"
        params = {"ref": self.branch}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def create_file(self, file_path: str, content: str, commit_message: Optional[str] = None) -> bool:
        if not commit_message:
            commit_message = f"Add {file_path}"
        
        encoded_path = self._encode_file_path(file_path)
        url = f"{self.base_url}/api/v4/projects/{self.project_id}/repository/files/{encoded_path}"
        
        # Encode content til base64 for at håndtere special characters
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
        
        payload = {
            "branch": self.branch,
            "content": content_base64,
            "commit_message": commit_message,
            "encoding": "base64"
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 201:
                print(f"  ✅ Created: {file_path}")
                return True
            elif response.status_code == 400 and "already exists" in response.text.lower():
                print(f"  ⚠️  Already exists: {file_path}")
                return False
            else:
                print(f"  ❌ Failed to create {file_path}: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"  ❌ Error creating {file_path}: {e}")
            return False
    
    def update_file(self, file_path: str, content: str, commit_message: Optional[str] = None) -> bool:
        if not commit_message:
            commit_message = f"Update {file_path}"
        
        encoded_path = self._encode_file_path(file_path)
        url = f"{self.base_url}/api/v4/projects/{self.project_id}/repository/files/{encoded_path}"
        
        # Encode content til base64
        content_base64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
        
        payload = {
            "branch": self.branch,
            "content": content_base64,
            "commit_message": commit_message,
            "encoding": "base64"
        }
        
        try:
            response = requests.put(url, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                print(f"  ✅ Updated: {file_path}")
                return True
            else:
                print(f"  ❌ Failed to update {file_path}: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"  ❌ Error updating {file_path}: {e}")
            return False
    
    def upload_or_update_file(self, file_path: str, content: str, commit_message: Optional[str] = None) -> bool:
        if self.file_exists(file_path):
            return self.update_file(file_path, content, commit_message)
        else:
            return self.create_file(file_path, content, commit_message)


def upload_local_directory_structure(local_base_path: str, uploader: GitLabUploader, gitlab_base_path: str = "data"):
    local_path = Path(local_base_path)
    
    if not local_path.exists():
        print(f"❌ Local path does not exist: {local_base_path}")
        return
    
    stats = {
        "created": 0,
        "updated": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # Find alle JSON filer rekursivt
    json_files = list(local_path.rglob("*.json"))
    
    print(f"📁 Found {len(json_files)} JSON files to upload\n")
    
    for local_file in json_files:
        # Beregn relativ sti
        relative_path = local_file.relative_to(local_path)
        gitlab_path = f"{gitlab_base_path}/{relative_path}".replace("\\", "/")
        
        try:
            # Læs fil indhold
            with open(local_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Upload eller opdater
            exists = uploader.file_exists(gitlab_path)
            
            if exists:
                success = uploader.update_file(gitlab_path, content)
                if success:
                    stats["updated"] += 1
                else:
                    stats["failed"] += 1
            else:
                success = uploader.create_file(gitlab_path, content)
                if success:
                    stats["created"] += 1
                else:
                    stats["failed"] += 1
                    
        except Exception as e:
            print(f"  ❌ Error processing {local_file}: {e}")
            stats["failed"] += 1
    
    # Print statistik
    print("\n" + "="*50)
    print("📊 UPLOAD STATISTICS")
    print("="*50)
    print(f"✅ Created: {stats['created']}")
    print(f"🔄 Updated: {stats['updated']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"⏭️  Skipped: {stats['skipped']}")
    print(f"\n📂 Total files processed: {sum(stats.values())}")