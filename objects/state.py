import os
import pickle
from datetime import datetime, timedelta, timezone
from typing import Dict, Set

from constants import STATE_FILE


class State:
    def __init__(self):
        self.last_check_time: Dict[str, datetime] = {}
        self.posted_links: Set[str] = set()
        self.daily_tweet_count: int = 0
        self.last_tweet_day: int = datetime.now().day
        self.state_file = STATE_FILE

    @classmethod
    def load(cls, state_file: str) -> "State":
        if os.path.exists(state_file):
            with open(state_file, "rb") as f:
                return pickle.load(f)
        else:
            return cls()

    def save(self):
        with open(self.state_file, "wb") as f:
            pickle.dump(self, f)

    def reset_daily_count_if_needed(self):
        current_day = datetime.now().day
        if current_day != self.last_tweet_day:
            self.daily_tweet_count = 0
            self.last_tweet_day = current_day

    def update_after_tweet(self, link: str):
        self.posted_links.add(link)
        self.daily_tweet_count += 1

    def prune_posted_links(self):
        if len(self.posted_links) > 1000:
            self.posted_links = set(list(self.posted_links)[-1000:])

    def ensure_feed_in_state(self, feed_name: str):
        if feed_name not in self.last_check_time:
            self.last_check_time[feed_name] = datetime.now(timezone.utc) - timedelta(
                hours=1
            )
