import praw

import configparser

# Config
config = configparser.ConfigParser()
config.read('config.ini')

# Test credentials
CLIENT_ID = config['reddit']['client_id']
CLIENT_SECRET = config['reddit']['client_secret']
USER_AGENT = config['reddit']['user_agent']
REDDIT_USERNAME = config['reddit']['username']
REDDIT_PASSWORD = config['reddit']['password']

try:
    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD,
    )

    # Test authentication by getting the current user
    user = reddit.user.me()
    print(f"Successfully authenticated as: {user}")
    print(f"Username: {user.name if user else 'None'}")

except Exception as e:
    print(f"Authentication failed: {e}")
    print(f"Error type: {type(e).__name__}")
