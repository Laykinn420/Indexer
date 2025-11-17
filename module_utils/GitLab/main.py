import json
import os
import sys
from dotenv import load_dotenv
from module_utils.GitLab.query import GitLabAPI
from module_utils.GitLab.models import Repository

def save_repository(repo, folder_path):
    try:
        os.makedirs(folder_path, exist_ok=True)

        repo_object = Repository.from_api(repo)
        repo_data = repo_object.__dict__

        print(json.dumps(repo, indent=2, ensure_ascii=False))

        file_path = os.path.join(folder_path, f"{repo_object.name}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(repo_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved {repo_object.name} → {file_path}")
        return True

    except Exception as e:
        print(f"  ❌ Failed to save {repo.get('name', 'unknown')}: {e}")
        return False


def save_group_tree(group_data, parent_path="data"):
    group_folder = os.path.join(parent_path, group_data["name"])

    try:
        os.makedirs(group_folder, exist_ok=True)

        # Gem alle repositories i denne gruppe
        for repo in group_data["projects"]:
            save_repository(repo, group_folder)

        # Gå igennem undergrupper
        for subgroup in group_data.get("subgroups", []):
            save_group_tree(subgroup, group_folder)
    
    except Exception as e:
        print(f"❌ Failed to process group {group_data.get('name', 'unknown')}: {e}")


def main():
    load_dotenv()
    token = os.getenv("GITLAB_TOKEN")
    base_url = os.getenv("GITLAB_BASE_URL")
    group_id = os.getenv("GITLAB_GROUP_ID")
    
    # Validering
    if not token:
        print("❌ Missing GITLAB_TOKEN in .env file")
        sys.exit(1)
    
    if not base_url:
        print("❌ Missing GITLAB_BASE_URL in .env file")
        sys.exit(1)
        
    if not group_id:
        print("❌ Missing GITLAB_GROUP_ID in .env file")
        sys.exit(1)

    api = GitLabAPI(base_url, token)

    print("⏳ Fetching full GitLab group tree...")
    tree = api.get_group_tree(group_id, max_depth=3)

    if not tree:
        print("❌ Failed to fetch group tree")
        sys.exit(1)

    print("📁 Saving repositories as individual JSON files...")
    save_group_tree(tree)

    print("\n✅ All repositories saved under the 'data/' folder.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")