import os
import json
from dotenv import load_dotenv
from module_utils.GitLab.query import GitLabAPI


def test_gitlab_group_repositories():
    load_dotenv()

    token = os.getenv("GITLAB_TOKEN")
    assert token, "Missing GITLAB_TOKEN in .env file"

    base_url = "https://gitlab.com"
    group_id = "116891110"

    api = GitLabAPI(base_url, token)
    repos = api.get_repositories(group_id)

    print(f"Found {len(repos)} repositories in group {group_id}")

    for repo in repos:
        print(f"- {repo.get('name')} (ID: {repo.get('id')})")
        print(f"  URL: {repo.get('web_url')}")
        print(f"  Last activity: {repo.get('last_activity_at')}")
        print("-" * 60)

    if repos:
        print("\n🔍 First repository (raw JSON):")
        print(json.dumps(repos[0], indent=2))

    # Test assertions
    assert isinstance(repos, list), "API should return a list of repositories"
    if repos:
        assert "name" in repos[0], "Each repository should have a name"
        assert "id" in repos[0], "Each repository should have an ID"