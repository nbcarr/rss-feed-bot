from dataclasses import dataclass


@dataclass
class Feed:
    name: str
    url: str
    total_entries: int = 0
    skipped_entries: int = 0
    processed_entries: int = 0
    posted_entries: int = 0
