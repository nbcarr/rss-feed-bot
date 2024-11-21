# TechTrendsBot
https://x.com/TechTrendsBot

A Python-based Twitter bot that posts updates from RSS feeds to Twitter. Runs on an AWS EC2 instance.


## Features

- **Automated Tweet Posting**: Fetches RSS feed updates and posts them to Twitter
- **Error Handling**: Retries failed tweets with exponential backoff
- **Daily Limits**: Restricts the number of tweets per day to prevent spam
- **Link Shortening**: Automatically shortens URLs using TinyURL
- **Feed Management**: Tracks state to avoid reposting the same links
