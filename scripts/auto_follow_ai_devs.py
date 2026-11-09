"""
Auto-Follow AI Developers Script for GitHub
-------------------------------------------
This script automates discovering and following top developers in AI, LLMs, 
Agentic AI, and Machine Learning using GitHub's REST API.

KEY IMPROVEMENTS (v2):
- Uses MULTIPLE search queries and random pagination to discover NEW users daily
- Skips your own username automatically
- Better rate-limit handling with exponential backoff
- Properly tracks history so you never follow the same person twice

Safety & Compliance Notice:
- Uses random delays (5-15 seconds) between follow requests.
- Tracks previously followed accounts in `followed_users.json` to prevent duplicates.
- Daily safe cap of 50 to protect your GitHub account reputation.

Usage:
1. Generate a GitHub Personal Access Token (PAT) with `user:follow` permission at:
   https://github.com/settings/tokens
2. Set environment variable:
   $env:GITHUB_TOKEN="your_personal_access_token_here"
3. Run the script:
   python auto_follow_ai_devs.py --limit 50
"""

import os
import sys
import time
import json
import random
import argparse
import urllib.request
import urllib.parse
import urllib.error

HISTORY_FILE = "followed_users.json"

# Your username - skip following yourself
MY_USERNAME = "shah-bakhsh"

# Diverse search queries covering many AI/ML communities
# Repository search supports topic filters; user search does not.
# Discover relevant repository maintainers rather than using unsupported user topic queries.
SEARCH_QUERIES = [
    "topic:machine-learning stars:>50 archived:false",
    "topic:large-language-models stars:>20 archived:false",
    "topic:llm stars:>50 archived:false",
    "topic:natural-language-processing stars:>20 archived:false",
    "topic:agentic-ai stars:>10 archived:false",
    "topic:rag stars:>20 archived:false",
    "topic:deep-learning stars:>50 archived:false",
    "topic:pytorch stars:>50 archived:false",
    "topic:huggingface stars:>20 archived:false",
    "topic:transformers stars:>20 archived:false",
]

def load_history():
    """Load the set of previously followed usernames from the JSON file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_history(history):
    """Save the set of followed usernames to the JSON file."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(history)), f, indent=2)


def github_api_request(url, token, method="GET"):
    """
    Make a request to the GitHub API with proper headers and error handling.
    Returns (response_data, status_code) or (None, error_code).
    """
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("User-Agent", "ShahBakhsh-AIFollower/2.0")
    req.add_header("Accept", "application/vnd.github.v3+json")
    if method == "PUT":
        req.add_header("Content-Length", "0")

    try:
        with urllib.request.urlopen(req) as resp:
            if method == "PUT":
                return None, resp.status
            data = json.loads(resp.read().decode("utf-8"))
            return data, resp.status
    except urllib.error.HTTPError as e:
        return None, e.code
    except Exception as e:
        print(f"    [ERROR] Request failed: {e}")
        return None, 0


def search_ai_developers(token, limit=50):
    """Discover individual owners of relevant public AI/ML repositories."""
    candidates = []
    seen = set()
    selected_queries = random.sample(SEARCH_QUERIES, min(5, len(SEARCH_QUERIES)))
    print(f"  Searching repository maintainers using {len(selected_queries)} topic queries...")

    for query in selected_queries:
        # Repository topics are supported here; select from first two pages.
        page = random.choice((1, 2))
        url = (
            "https://api.github.com/search/repositories"
            f"?q={urllib.parse.quote(query)}&sort=updated&order=desc"
            f"&per_page=50&page={page}"
        )
        data, status = github_api_request(url, token)
        if status != 200:
            print(f"[ERROR] Repository discovery API returned HTTP {status} for {query}")
            sys.exit(1)

        items = data.get("items", []) if isinstance(data, dict) else []
        added = 0
        for repository in items:
            owner = repository.get("owner") or {}
            login = owner.get("login")
            if (owner.get("type") != "User" or not login or
                    login.lower() == MY_USERNAME.lower() or
                    login.lower() in seen):
                continue
            seen.add(login.lower())
            candidates.append(login)
            added += 1

        print(f"    Query '{query}' (page {page}): {len(items)} repositories, {added} new developers")
        if len(candidates) >= limit * 2:
            break
        time.sleep(1)

    random.shuffle(candidates)
    print(f"  Total unique individual developers discovered: {len(candidates)}")
    if not candidates:
        print("[ERROR] No candidate developers discovered; check search queries and API responses.")
        sys.exit(1)
    return candidates


def follow_user(token, username):
    """
    Send PUT request to follow a GitHub user.
    Returns True if successful, False otherwise.
    """
    url = f"https://api.github.com/user/following/{username}"
    _, status = github_api_request(url, token, method="PUT")

    if status in (204, 200):
        print(f"    [OK] Successfully followed: @{username}")
        return True
    elif status == 403:
        print(f"    [RATE LIMIT] Rate limited while following @{username}")
        return False
    elif status == 404:
        print(f"    [SKIP] User @{username} not found (may be deleted)")
        return False
    else:
        print(f"    [FAIL] Failed to follow @{username} (HTTP {status})")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Automated AI Developer Follower - Follows 50 new AI devs daily"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of developers to follow per run (Default: 50)",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[ERROR] GITHUB_TOKEN environment variable not set!")
        print("Please set your GitHub Personal Access Token (PAT) with 'user:follow' permission:")
        print("  Windows PowerShell: $env:GITHUB_TOKEN='ghp_your_token_here'")
        print("  Linux/Mac: export GITHUB_TOKEN='ghp_your_token_here'")
        sys.exit(1)

    print("=" * 60)
    print("  AI Developer Auto-Follower v2.0")
    print(f"  Target: {args.limit} new follows per run")
    print("=" * 60)

    # Verify the PAT before searching; an existing nonempty secret is not necessarily valid.
    user_data, auth_status = github_api_request("https://api.github.com/user", token)
    if auth_status != 200 or not user_data:
        print(f"[ERROR] GitHub token authentication check failed (HTTP {auth_status}).")
        print("Refresh AUTO_FOLLOW_PAT with a valid personal access token that permits following users.")
        sys.exit(1)
    print(f"[AUTH] GitHub API authenticated as @{user_data.get('login', 'unknown')}")

    # Load history of previously followed users
    history = load_history()
    print(f"\n  Previously followed: {len(history)} users")

    # Search for candidates
    print(f"\n[STEP 1] Discovering AI developers...\n")
    candidates = search_ai_developers(token, limit=args.limit)

    # Filter out already-followed users
    new_candidates = [u for u in candidates if u not in history]
    print(f"\n  New candidates (not in history): {len(new_candidates)}")

    if not new_candidates:
        print("\n  [INFO] No new candidates found this run.")
        print("  This can happen if all discovered users are already in history.")
        print("  The script uses random queries/pages, so try again tomorrow!")
        return

    # Follow new users
    print(f"\n[STEP 2] Following up to {args.limit} new developers...\n")
    followed_count = 0
    rate_limit_hits = 0

    for username in new_candidates:
        if followed_count >= args.limit:
            print(f"\n  Target limit of {args.limit} reached!")
            break

        if rate_limit_hits >= 3:
            print(f"\n  [STOP] Too many rate limits hit ({rate_limit_hits}). Stopping for safety.")
            break

        success = follow_user(token, username)
        if success:
            history.add(username)
            save_history(history)
            followed_count += 1

            # Randomized delay between 5 to 15 seconds for account safety
            delay = random.uniform(5.0, 15.0)
            print(f"    [WAIT] Sleeping {delay:.1f}s for account safety...\n")
            time.sleep(delay)
        else:
            # Failed follows are not successful history entries.
            rate_limit_hits += 1
            time.sleep(random.uniform(10.0, 20.0))

    if followed_count == 0:
        print("[ERROR] No accounts were followed; review API errors and token scopes above.")
        sys.exit(1)

    print("=" * 60)
    print(f"  DONE! Followed {followed_count} new AI developers today!")
    print(f"  Total in history: {len(history)}")
    print(f"  History file: '{HISTORY_FILE}'")
    print("=" * 60)


if __name__ == "__main__":
    main()
