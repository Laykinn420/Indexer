import json
import os
from dotenv import load_dotenv
from module_utils.GitLab.query import GitLabAPI

def save_repository(repo, folder_path):
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, f"{repo['name']}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(repo, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved {repo['name']} → {file_path}")


def save_group_tree(group_data, parent_path="data"):
    """Rekursivt gem alle repositories i gruppen og dens undergrupper."""
    group_folder = os.path.join(parent_path, group_data["name"])
    os.makedirs(group_folder, exist_ok=True)

    # Gem alle repositories i denne gruppe
    for repo in group_data["projects"]:
        save_repository(repo, group_folder)

    # Gå igennem undergrupper
    for subgroup in group_data.get("subgroups", []):
        save_group_tree(subgroup, group_folder)


def main():
    load_dotenv()
    token = os.getenv("GITLAB_TOKEN")
    assert token, "⚠️  Missing GITLAB_TOKEN in .env file"

    base_url = os.getenv("GITLAB_BASE_URL")
    group_id = os.getenv("GITLAB_GROUP_ID")

    api = GitLabAPI(base_url, token)
    print("⏳ Fetching full GitLab group tree...")
    tree = api.get_group_tree(group_id)

    print("📁 Saving repositories as individual JSON files...")
    save_group_tree(tree)

    print("\n✅ All repositories saved under the 'data/' folder.")


if __name__ == "__main__":
    main()