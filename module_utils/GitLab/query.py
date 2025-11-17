import requests
import os

class GitLabAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {"PRIVATE-TOKEN": token}

    def get_repositories(self, group_id):
        url = f"{self.base_url}/api/v4/groups/{group_id}/projects?per_page=100"
        return self._get_paginated(url)

    def _get_paginated(self, url):
        items = []

        while url:
            try:    
                r = requests.get(url, headers=self.headers)
                r.raise_for_status()
                items.extend(r.json())
                url = r.links.get("next", {}).get("url")
            except requests.RequestException as e:
                print(f"❌ API request failed: {e}")
                break
        return items

    def get_subgroups(self, group_id):
        url = f"{self.base_url}/api/v4/groups/{group_id}/subgroups?per_page=100"
        subgroups = []
        while url:
            r = requests.get(url, headers=self.headers)
            r.raise_for_status()
            subgroups.extend(r.json())
            url = r.links.get("next", {}).get("url")
        return subgroups

    def get_group_tree(self, group_id, current_depth = 0, max_depth = 3):
        if current_depth >= max_depth:
            print(f"⚠️  Max depth {max_depth} reached at group {group_id}")
            return None
        try:
            # Henter gruppens basisdata
            group_url = f"{self.base_url}/api/v4/groups/{group_id}"
            group_res = requests.get(group_url, headers=self.headers)
            group_res.raise_for_status()
            group_data = group_res.json()

            # Henter gruppens projekter
            projects = self.get_repositories(group_id)

            # Henter undergrupper
            subgroups = self.get_subgroups(group_id)
            
            # Rekursivt hent undergruppe-træer
            subgroup_trees = []
            for sg in subgroups:
                tree = self.get_group_tree(
                    sg["id"], 
                    max_depth=max_depth, 
                    current_depth=current_depth + 1
                )
                if tree:
                    subgroup_trees.append(tree)

            # Returnerer som hierarkisk struktur
            return {
                "id": group_data["id"],
                "name": group_data["name"],
                "full_path": group_data.get("full_path"),
                "projects": [
                    {
                        "id": p["id"],
                        "name": p["name"],
                        "web_url": p["web_url"],
                        "last_activity_at": p["last_activity_at"],
                        "description": p.get("description"),
                        "visibility": p.get("visibility"),
                    }
                    for p in projects
                ],
                "subgroups": subgroup_trees,
            }
        except requests.RequestException as e:
            print(f"❌ Failed to fetch group {group_id}: {e}")
            return None
        except KeyError as e:
            print(f"❌ Missing expected field in API response: {e}")
            return None