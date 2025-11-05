import json
from module_utils.GitLab.query import GitLabAPI
from module_utils.GitLab.models import Repository


def collect_all_repositories(tree):
    """Rekursivt saml alle projekter fra træet."""
    repos = []

    # Tilføj projekterne fra denne gruppe
    repos.extend(tree.get("projects", []))

    # Gå gennem undergrupper
    for subgroup in tree.get("subgroups", []):
        repos.extend(collect_all_repositories(subgroup))

    return repos


def index_repositories(base_url: str, token: str, group_id: str, output_path: str):
    api = GitLabAPI(base_url, token)
    tree = api.get_group_tree(group_id)

    # Saml ALLE projekter fra hele gruppetræet
    all_repos = collect_all_repositories(tree)

    # Konverter til Repository-objekter
    repo_data = [
        Repository(
            id=repo["id"],
            name=repo["name"],
            description=repo.get("description"),
            visibility=repo.get("visibility"),
            last_activity_at=repo["last_activity_at"]
        ).__dict__
        for repo in all_repos
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(repo_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(repo_data)} repositories to {output_path}")