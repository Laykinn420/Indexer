from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Repository:
    id: int
    name: str
    description: Optional[str]
    visibility: str
    last_activity_at: str
    web_url: str

    @classmethod
    def from_api(cls, data: dict):
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            visibility=data.get("visibility"),
            last_activity_at=data["last_activity_at"],
            web_url=data["web_url"]
        )
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Group:
    id: int
    name: str
    full_path: str
    project_count: int
    subgroup_count: int
    
    @classmethod
    def from_tree(cls, tree_data: dict) -> 'Group':
        return cls(
            id=tree_data["id"],
            name=tree_data["name"],
            full_path=tree_data.get("full_path", tree_data["name"]),
            project_count=len(tree_data.get("projects", [])),
            subgroup_count=len(tree_data.get("subgroups", []))
        )
    
    def to_dict(self) -> dict:
        return asdict(self)