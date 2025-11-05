import requests
import os

class GitLabAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {"PRIVATE-TOKEN": token}

    def get_repositories(self, group_id):
        url = f"{self.base_url}/api/v4/groups/{group_id}/projects?per_page=100"
        repos = []
        while url:
            r = requests.get(url, headers=self.headers)
            r.raise_for_status()
            repos.extend(r.json())
            url = r.links.get("next", {}).get("url")
        return repos

    def get_subgroups(self, group_id):
        url = f"{self.base_url}/api/v4/groups/{group_id}/subgroups?per_page=100"
        subgroups = []
        while url:
            r = requests.get(url, headers=self.headers)
            r.raise_for_status()
            subgroups.extend(r.json())
            url = r.links.get("next", {}).get("url")
        return subgroups

    def get_group_tree(self, group_id):
        # Henter gruppens basisdata
        group_url = f"{self.base_url}/api/v4/groups/{group_id}"
        group_res = requests.get(group_url, headers=self.headers)
        group_res.raise_for_status()
        group_data = group_res.json()

        # Henter gruppens projekter
        projects = self.get_repositories(group_id)

        # Henter undergrupper
        subgroups = self.get_subgroups(group_id)
        subgroup_trees = [self.get_group_tree(sg["id"]) for sg in subgroups]

        # Returnerer som hierarkisk struktur
        return {
            "id": group_data["id"],
            "name": group_data["name"],
            "path": group_data["full_path"],
            "projects": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "web_url": p["web_url"],
                    "last_activity_at": p["last_activity_at"],
                }
                for p in projects
            ],
            "subgroups": subgroup_trees,
        }