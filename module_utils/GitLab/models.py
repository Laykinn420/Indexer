from dataclasses import dataclass
from typing import Optional

@dataclass
class Repository:
    id: int
    name: str
    description: Optional[str]
    visibility: str
    last_activity_at: str