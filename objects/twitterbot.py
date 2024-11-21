import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional, Tuple
from constants import IGNORED_TERMS, IGNORED_DOMAINS

import feedparser
import pyshorteners
import tweepy
from dotenv import load_dotenv

from objects.feed import Feed
from objects.state import State


class TwitterBot:
    MAX_DAILY_TWEETS = 50
    MAX_ATTEMPTS = 3
    BASE_DELAY = 4

    def __init__(
        self,
        state_file: str,
        feeds_file: str,
        logger: logging.Logger,
        dryrun: bool = False,
    ):
        load_dotenv()
        self.client = self._authenticate_twitter()
        self.state = State.load(state_file)
        self.feeds = self._load_feeds(feeds_file)
        self.logger = logger
        self.shortener = pyshorteners.Shortener()
        self.dryrun = dryrun

    def _authenticate_twitter(self) -> tweepy.Client:
        return tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_KEY_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        )

    def _load_feeds(self, feeds_file: str) -> List[Feed]:
        with open(feeds_file, "r") as f:
            feeds_data = json.load(f)
        return [Feed(name, url) for name, url in feeds_data.items()]

    def post_tweet(self, title: str, url: str) -> bool:
        shortened_url = self.shortener.tinyurl.short(url)
        tweet_text = f"{title}\n\n{shortened_url}"

        self.logger.info(f"Posting tweet: {tweet_text}...")

        for attempt in range(self.MAX_ATTEMPTS):
            try:
                if self.dryrun:
                    self.logger.info(f"Running in dryrun mode. Skipping posting.")
                    return True

                self.client.create_tweet(text=tweet_text)
                self.logger.info(f"Successfully posted tweet.")
                delay = random.randint(30, 120)
                self.logger.info(f"Waiting for {delay} seconds before the next action.")
                time.sleep(delay)
                return True
            except tweepy.TweepyException as e:
                self.logger.warning(
                    f"Error posting tweet (Attempt {attempt + 1}/{self.MAX_ATTEMPTS}): {e}"
                )
                if attempt < self.MAX_ATTEMPTS - 1:
                    sleep_time = self.BASE_DELAY * (2**attempt)
                    self.logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)

        self.logger.error("Failed to post tweet after multiple attempts")
        return False

    def should_process_link(self, feed: Feed, entry) -> Tuple[bool, Optional[str]]:
        last_check_time = self.state.last_check_time[feed.name]
        published_time = parsedate_to_datetime(entry.published)

        if any(domain in entry.link.lower() for domain in IGNORED_DOMAINS):
            return False, "Link contains an ignored domain"

        if any(term in entry.title.lower() for term in IGNORED_TERMS):
            return False, "Title contains an ignored term"

        if published_time <= last_check_time:
            return (
                False,
                f"Published before last check (published: {published_time}, last check: {last_check_time}, delta: {published_time - last_check_time})",
            )

        if entry.link in self.state.posted_links:
            return False, "Already posted"

        if self.state.daily_tweet_count >= self.MAX_DAILY_TWEETS:
            return False, "Daily limit reached"

        return True, None

    def process_feed(self, feed: Feed):
        try:
            parsed_feed = feedparser.parse(feed.url)
        except Exception as e:
            self.logger.error(f"Error fetching RSS feed {feed.name}: {e}")
            return

        self.state.ensure_feed_in_state(feed.name)

        for entry in parsed_feed.entries:
            feed.total_entries += 1
            should_process, skip_reason = self.should_process_link(feed, entry)

            if not should_process:
                self.logger.info(
                    f"Skipping link from {feed.name}: {entry.title[:20]} - Reason: {skip_reason}"
                )
                feed.skipped_entries += 1
                continue

            feed.processed_entries += 1
            self.logger.info(f"New post found in {feed.name}: {entry.title}")

            if self.post_tweet(entry.title, entry.link):
                feed.posted_entries += 1
                self.state.update_after_tweet(entry.link)

            if self.state.daily_tweet_count >= self.MAX_DAILY_TWEETS:
                self.logger.info("Daily limit reached. Stopping.")
                break

        self.state.last_check_time[feed.name] = datetime.now(timezone.utc)

    def log_run_stats(self):
        total_entries = sum(feed.total_entries for feed in self.feeds)
        total_processed = sum(feed.processed_entries for feed in self.feeds)
        total_skipped = sum(feed.skipped_entries for feed in self.feeds)

        stats = {
            "total_entries": total_entries,
            "total_processed": total_processed,
            "total_skipped": total_skipped,
            "feeds_processed": len(self.feeds),
        }

        self.logger.info(f"Run Statistics: {json.dumps(stats, indent=2)}")

        for feed in self.feeds:
            feed_stats = {
                "name": feed.name,
                "entries": feed.total_entries,
                "processed": feed.processed_entries,
                "skipped": feed.skipped_entries,
                "posted": feed.posted_entries,
                "failed_to_post": feed.processed_entries - feed.posted_entries,
            }
            self.logger.info(f"Feed Statistics: {json.dumps(feed_stats, indent=2)}")

    def run(self):
        start_time = time.time()
        self.logger.info(f"Starting bot run at {datetime.now(timezone.utc)}")
        self.state.reset_daily_count_if_needed()

        if self.state.daily_tweet_count >= self.MAX_DAILY_TWEETS:
            self.logger.info("Daily limit reached. Exiting.")
            return

        for feed in self.feeds:
            self.logger.info(f"Processing feed: {feed.name}")
            self.process_feed(feed)
            if self.state.daily_tweet_count >= self.MAX_DAILY_TWEETS:
                break

        self.log_run_stats()

        if not self.dryrun:
            self.state.prune_posted_links()
            self.state.save()

        end_time = time.time()
        self.logger.info(
            f"Finished bot run at {datetime.now(timezone.utc)}. Total time: {end_time - start_time:.2f} seconds."
        )
