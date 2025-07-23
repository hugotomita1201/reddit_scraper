import praw
import csv
import time

import configparser

# --- Configuration ---

# Config
config = configparser.ConfigParser()
config.read('config.ini')

# Your credentials
CLIENT_ID = config['reddit']['client_id']
CLIENT_SECRET = config['reddit']['client_secret']
USER_AGENT = config['reddit']['user_agent']

# Subreddits to search
subreddits = ["grunge", "Nirvana", "PearlJam", "AliceInChains", "Soundgarden", "90sAlternative", "Concerts", "LiveMusic", "90s", "90s_kid", "GenX"]

# Keywords for flagging
explicit_attendee_keywords = [
    "attended concert", "saw live", "i saw", "went to show", "caught them live",
    "saw nirvana", "pearl jam show", "soundgarden ticket", "got at the concert",
    "bought at the show"
]

potential_attendee_keywords = [
    "first concert", "best grunge concert", "live show experiences", "tour shirt",
    "owned merch", "alice in chains tee", "grunge t-shirt", "grunge tshirt",
    "grunge shirt", "grunge tee", "vintage grunge shirt", "vintage band shirt",
    "nirvana shirt", "nirvana tee", "pearl jam shirt", "pearl jam tee",
    "soundgarden shirt", "soundgarden tee", "alice in chains shirt",
    "alice in chains tee", "old band shirt", "original tour shirt",
    "concert t-shirt", "concert tee", "band t-shirt", "band tee",
    "still have my shirt", "still have my tee", "my old shirt", "my old tee",
    "saved my shirt", "saved my tee", "kept my shirt", "kept my tee",
    "wore my shirt", "wore my tee", "from the concert", "from the show",
    "from the tour", "tour merch", "tour t-shirt", "tour tee", "merch shirt",
    "merch tee", "gig shirt", "gig tee", "show shirt", "show tee", "born in 19"
]

# Combined list for searching
all_keywords = explicit_attendee_keywords + potential_attendee_keywords

# Output file
output_file = "grunge_attendees_v4.csv"

# --- Helper Functions ---

def get_flag(text):
    """Determines the flag based on keywords found in the text."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in explicit_attendee_keywords):
        return "Explicit Attendee"
    if any(kw in text_lower for kw in potential_attendee_keywords):
        return "Potential Attendee/Merch Owner"
    return None

# --- Main Script ---

# Initialize Reddit
reddit = praw.Reddit(
    client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT
)

# Sets to keep track of processed items to avoid duplicates
processed_submissions = set()
processed_comments = set()

print("Starting Reddit scraper...")

with open(output_file, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([
        "Subreddit", "Flag", "Keyword Found", "Post Title", "Author",
        "Text", "Post URL", "Comment URL"
    ])

    for sub_name in subreddits:
        subreddit = reddit.subreddit(sub_name)
        print(f"\n--- Searching in r/{sub_name} ---")
        for keyword in all_keywords:
            print(f"Searching for keyword: '{keyword}', sorted by new.")
            try:
                # Search for submissions with the keyword, sorted by new
                for submission in subreddit.search(keyword, sort="new", limit=100):
                    if submission.id in processed_submissions:
                        continue
                    processed_submissions.add(submission.id)

                    # Check submission title and selftext
                    submission_text = submission.title + " " + submission.selftext
                    flag = get_flag(submission_text)
                    if flag:
                        writer.writerow([
                            sub_name, flag, keyword, submission.title,
                            submission.author.name if submission.author else "[deleted]",
                            submission.selftext, f"https://reddit.com{submission.permalink}", ""
                        ])

                    # Process comments
                    submission.comments.replace_more(limit=None)
                    for comment in submission.comments.list():
                        if comment.id in processed_comments:
                            continue
                        processed_comments.add(comment.id)

                        flag = get_flag(comment.body)
                        if flag:
                            writer.writerow([
                                sub_name, flag, keyword, submission.title,
                                comment.author.name if comment.author else "[deleted]",
                                comment.body, f"https://reddit.com{submission.permalink}",
                                f"https://reddit.com{comment.permalink}"
                            ])
                    
                    time.sleep(0.5) # Be nice to Reddit's API

            except Exception as e:
                print(f"An error occurred while searching in r/{sub_name} for keyword '{keyword}': {e}")
            
            time.sleep(1) # Be nice to Reddit's API

print(f"\nScraping complete! Results saved to {output_file}")
