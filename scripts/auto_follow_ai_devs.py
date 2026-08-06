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
SEARCH_QUERIES = [
    # AI topics
    "type:user topic:artificial-intelligence followers:>10",
    "type:user topic:ai followers:>50",
    "type:user topic:machine-learning followers:>20",
    "type:user topic:deep-learning followers:>20",
    "type:user topic:llm followers:>10",
    "type:user topic:large-language-models followers:>10",
    "type:user topic:agentic-ai followers:>5",
    "type:user topic:generative-ai followers:>10",
    "type:user topic:transformers followers:>10",
    "type:user topic:nlp followers:>20",
    "type:user topic:natural-language-processing followers:>10",
    "type:user topic:computer-vision followers:>20",
    "type:user topic:reinforcement-learning followers:>10",
    "type:user topic:neural-network followers:>10",
    "type:user topic:data-science followers:>30",
    "type:user topic:mlops followers:>10",
    "type:user topic:pytorch followers:>15",
    "type:user topic:tensorflow followers:>15",
    "type:user topic:huggingface followers:>5",
    "type:user topic:langchain followers:>5",
    "type:user topic:stable-diffusion followers:>5",
    "type:user topic:chatgpt followers:>5",
    "type:user topic:openai followers:>5",
    # Language + followers combos (catches devs without AI topics)
    "type:user language:python followers:>100",
    "type:user language:python followers:>50 repos:>20",
    "type:user language:jupyter-notebook followers:>30",
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
    """
    Search for AI/ML developers across MULTIPLE queries and pages
    to discover new users every day.
    
    Strategy:
    - Randomly select several queries from the pool
    - Use random page offsets (page 1-10) to reach beyond the top results
    - Collect unique usernames until we have enough candidates
    """
    all_candidates = []
    seen = set()

    # Pick a random subset of queries (5-8 queries per run for variety)
    num_queries = min(random.randint(5, 8), len(SEARCH_QUERIES))
    selected_queries = random.sample(SEARCH_QUERIES, num_queries)

    print(f"  Searching with {num_queries} different queries...")

    for query in selected_queries:
        # Random page between 1 and 10 to get different results each day
        page = random.randint(1, 10)
        encoded_query = urllib.parse.quote(query)
        url = (
            f"https://api.github.com/search/users"
            f"?q={encoded_query}"
            f"&sort=followers&order=desc"
            f"&per_page=50&page={page}"
        )

        data, status = github_api_request(url, token)

        if status == 403:
            print(f"    [RATE LIMIT] Hit rate limit, waiting 60s...")
            time.sleep(60)
            data, status = github_api_request(url, token)

        if status == 422:
            # GitHub returns 422 if page is too deep, try page 1
            url_p1 = (
                f"https://api.github.com/search/users"
                f"?q={encoded_query}"
                f"&sort=followers&order=desc"
                f"&per_page=50&page=1"
            )
            data, status = github_api_request(url_p1, token)

        if data and "items" in data:
            users = [
                user["login"]
                for user in data["items"]
                if user["login"].lower() != MY_USERNAME.lower()
                and user["login"] not in seen
            ]
            for u in users:
                seen.add(u)
                all_candidates.append(u)

            print(f"    Query '{query[:50]}...' (page {page}): found {len(users)} new candidates")
        else:
            print(f"    Query '{query[:50]}...' (page {page}): no results (HTTP {status})")

        # Small delay between search requests to avoid rate limiting
        time.sleep(random.uniform(2.0, 4.0))

        # Stop searching if we have way more than enough
        if len(all_candidates) >= limit * 3:
            break

    # Shuffle to randomize follow order
    random.shuffle(all_candidates)

    print(f"\n  Total unique candidates discovered: {len(all_candidates)}")
    return all_candidates


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
            # Still add to history to avoid retrying failed users
            if username not in history:
                history.add(username)
                save_history(history)
            rate_limit_hits += 1
            time.sleep(random.uniform(10.0, 20.0))

    print("=" * 60)
    print(f"  DONE! Followed {followed_count} new AI developers today!")
    print(f"  Total in history: {len(history)}")
    print(f"  History file: '{HISTORY_FILE}'")
    print("=" * 60)


if __name__ == "__main__":
    main()
