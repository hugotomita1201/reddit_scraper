import praw
import csv
import datetime
import time
import random
import webbrowser
import socket
import sys
from urllib.parse import urlparse, parse_qs
import os

import configparser

# Config
config = configparser.ConfigParser()
config.read('config.ini')

# Reddit App Credentials (from Reddit app settings)
CLIENT_ID = config['reddit']['client_id']
CLIENT_SECRET = config['reddit']['client_secret']
USER_AGENT = config['reddit']['user_agent']

# Files
input_csv = "/Users/hugo/tshirt/data/reddit leads - filtered_grunge_attendees (2).csv"
log_csv = "messaging_log.csv"

# Daily message limit
MESSAGE_LIMIT = 10


def get_oauth_token(account_number):
    """Get OAuth token using authorization code flow"""

    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
        redirect_uri="http://localhost:8080",
    )

    # Generate authorization URL
    scopes = ["identity", "read", "privatemessages", "submit"]
    auth_url = reddit.auth.url(scopes, "unique_state", "permanent")

    print(
        f"Please visit this URL to authorize the application for account {account_number}: {auth_url}"
    )
    webbrowser.open(auth_url)

    # Set up a simple server to receive the callback
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 8080))
    server_socket.listen(1)

    print("Waiting for authorization...")

    client_socket, addr = server_socket.accept()
    request = client_socket.recv(1024).decode("utf-8")

    # Parse the authorization code from the request
    lines = request.split("\n")
    get_line = lines[0]
    path = get_line.split(" ")[1]
    parsed_url = urlparse(f"http://localhost:8080{path}")
    params = parse_qs(parsed_url.query)

    if "code" in params:
        code = params["code"][0]

        # Exchange code for access token
        refresh_token = reddit.auth.authorize(code)

        # Save refresh token to file for future use
        token_file = f"reddit_refresh_token_{account_number}.txt"
        with open(token_file, "w") as f:
            f.write(refresh_token)

        print(f"Successfully authorized! Refresh token saved to {token_file}")

        # Send response to browser
        response = """HTTP/1.1 200 OK
Content-Type: text/html

<html>
<head><title>Reddit Authorization Successful</title></head>
<body>
<h1>Authorization Successful!</h1>
<p>You can now close this window and return to the application.</p>
</body>
</html>"""
        client_socket.send(response.encode())

        client_socket.close()
        server_socket.close()

        return refresh_token
    else:
        print("Authorization failed - no code received")
        client_socket.close()
        server_socket.close()
        return None


def create_reddit_instance(account_number):
    """Create Reddit instance using OAuth"""

    token_file = f"reddit_refresh_token_{account_number}.txt"
    # Try to load refresh token from file
    try:
        with open(token_file, "r") as f:
            refresh_token = f.read().strip()
    except FileNotFoundError:
        print(
            f"No refresh token found for account {account_number}. Running OAuth flow..."
        )
        refresh_token = get_oauth_token(account_number)
        if not refresh_token:
            return None

    try:
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
            refresh_token=refresh_token,
        )

        # Test authentication
        user = reddit.user.me()
        if user:
            print(
                f"Successfully authenticated as: {user.name} (Account {account_number})"
            )
            return reddit
        else:
            print(f"Authentication failed for account {account_number}")
            return None

    except Exception as e:
        print(f"Authentication error for account {account_number}: {e}")
        return None


def send_message(reddit, username, message):
    """Send a message to a specific user"""
    try:
        reddit.redditor(username).message(subject="band t shirts", message=message)
        today = datetime.date.today().isoformat()

        with open(log_csv, "a", newline="") as logfile:
            writer = csv.writer(logfile)
            writer.writerow([username, today, message, "no", "", ""])

        print(f"Successfully sent message to {username}")
        return True

    except Exception as e:
        print(f"Error sending message to {username}: {e}")
        return False


def update_sent_status(file_path, index):
    """Updates the 'Sent' status of a row in the CSV file."""
    rows = []
    with open(file_path, "r", encoding="utf-8") as infile:
        reader = csv.reader(infile)
        rows = list(reader)

    rows[index][rows[0].index("Sent")] = "True"

    with open(file_path, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)


def main():
    """Main function to run the auto messenger"""

    # Add 'Sent' column if it doesn't exist
    rows = []
    try:
        with open(input_csv, "r", encoding="utf-8") as infile:
            reader = csv.reader(infile)
            header = next(reader)
            if "Sent" not in header:
                header.append("Sent")
                rows.append(header)
                for row in reader:
                    row.append("False")
                    rows.append(row)
            else:
                rows.append(header)
                for row in reader:
                    rows.append(row)

        with open(input_csv, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.writer(outfile)
            writer.writerows(rows)

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_csv}")
        return

    # Check for command-line argument for account selection
    if len(sys.argv) > 1:
        try:
            account_number = int(sys.argv[1])
            if account_number not in [1, 2]:
                print("Invalid account number. Please use 1 or 2.")
                return
            reddit = create_reddit_instance(account_number)
            if not reddit:
                print(f"Failed to authenticate account {account_number}.")
                return
            reddit_instances = [reddit]
        except ValueError:
            print("Invalid account number. Please provide a number (1 or 2).")
            return
    else:
        # Create Reddit instances for both accounts for alternating
        reddit_instances = []
        for i in range(1, 3):
            reddit = create_reddit_instance(i)
            if reddit:
                reddit_instances.append(reddit)

    if not reddit_instances:
        print("Failed to authenticate any Reddit accounts.")
        return

    messages_sent = 0
    with open(input_csv, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)
        for i, row in enumerate(rows):
            if messages_sent >= MESSAGE_LIMIT:
                print(f"Reached daily message limit of {MESSAGE_LIMIT}. Exiting.")
                break

            if row["Sent"] == "False":
                username = row["Username"]
                message = row["Personalized Message"]

                # Alternate between accounts if multiple are loaded
                reddit = reddit_instances[messages_sent % len(reddit_instances)]
                if send_message(reddit, username, message):
                    update_sent_status(input_csv, i + 1)  # +1 for header
                    messages_sent += 1
                    print(f"Sent from account: {reddit.user.me().name}")
                    print(f"Messages sent: {messages_sent}/{MESSAGE_LIMIT}")
                    delay = random.randint(
                        120, 300
                    )  # Random delay between 2 and 5 minutes
                    print(f"Waiting {delay} seconds before next message...")
                    time.sleep(delay)
                else:
                    print(f"Failed to send message to {username}. Will retry later.")
            else:
                print(f"Already sent message to {row['Username']}, skipping...")


if __name__ == "__main__":
    main()
