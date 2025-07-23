# Reddit Automation Project

This project contains scripts for automating Reddit tasks, such as scraping data and sending messages.

## Setup

1.  Clone the repository.
2.  Install the required Python libraries:
    ```
    pip install praw
    ```
3.  Create a `config.ini` file in the root directory of the project. You can use `config.ini.example` as a template. Fill in your Reddit API credentials in this file.
4.  Run the scripts from the `src` directory.

## Scripts

*   `reddit_scraper.py`: Scrapes subreddits for keywords.
*   `auto_messenger_final.py`: Sends messages to users from a CSV file.
*   `test_reddit_auth.py`: Tests your Reddit API credentials.

## Development

It is important to explicitly test every single feature before finalizing and implementing it.
