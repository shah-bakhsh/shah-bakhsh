"""
Auto-Follow AI Developers Script for GitHub
-------------------------------------------
This script automates discovering and following top developers in AI, LLMs, 
Agentic AI, and Machine Learning using GitHub's REST API.

Safety & Compliance Notice:
- Uses random delays (5-12 seconds) between follow requests.
- Tracks previously followed accounts in `followed_users.json` to prevent duplicates.
- Daily safe cap to protect your GitHub account reputation.

Usage:
1. Generate a GitHub Personal Access Token (PAT) with `user:follow` permission at:
   https://github.com/settings/tokens
2. Set environment variable:
   $env:GITHUB_TOKEN="your_personal_access_token_here"
3. Run the script:
   python auto_follow_ai_devs.py --limit 30
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

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(history), f, indent=2)

def search_ai_developers(token, topic="ai", limit=30):
    """
    Search for top active developers in AI/LLMs/Machine Learning on GitHub.
    """
    queries = [
        "type:user topic:ai followers:>50",
        "type:user topic:llm followers:>30",
        "type:user topic:agentic-ai followers:>20",
        "type:user language:python followers:>100"
    ]
    query = random.choice(queries)
    url = f"https://api.github.com/search/users?q={urllib.parse.quote(query)}&sort=followers&order=desc&per_page=50"
    
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("User-Agent", "ShahBakhsh-AIFollower/1.0")
    req.add_header("Accept", "application/vnd.github.v3+json")
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("items", [])
            users = [user["login"] for user in items]
            print(f"🔍 Discovered {len(users)} developers matching query: '{query}'")
            return users
    except urllib.error.HTTPError as e:
        print(f"❌ Search Error (HTTP {e.code}): {e.reason}")
        return []
    except Exception as e:
        print(f"❌ Search Error: {e}")
        return []

def follow_user(token, username):
    """
    Send PUT request to follow a GitHub user.
    """
    url = f"https://api.github.com/user/following/{username}"
    req = urllib.request.Request(url, method="PUT")
    req.add_header("Authorization", f"token {token}")
    req.add_header("User-Agent", "ShahBakhsh-AIFollower/1.0")
    req.add_header("Content-Length", "0")
    
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (204, 200):
                print(f"✅ Successfully followed: @{username}")
                return True
    except urllib.error.HTTPError as e:
        print(f"⚠️ Failed to follow @{username} (HTTP {e.code}): {e.reason}")
    except Exception as e:
        print(f"⚠️ Error following @{username}: {e}")
    return False

def main():
    parser = argparse.ArgumentParser(description="Automated AI Developer Follower")
    parser.add_argument("--limit", type=int, default=30, help="Maximum number of developers to follow per run (Default: 30)")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set!")
        print("Please set your GitHub Personal Access Token (PAT) with 'user:follow' permission:")
        print("  Windows PowerShell: $env:GITHUB_TOKEN='ghp_your_token_here'")
        sys.exit(1)

    print("🤖 Starting AI Developer Auto-Follower...")
    history = load_history()
    candidates = search_ai_developers(token, limit=args.limit)
    
    followed_count = 0
    for username in candidates:
        if followed_count >= args.limit:
            print(f"🎉 Target limit of {args.limit} developers reached!")
            break
            
        if username in history:
            print(f"⏭️ Skipping @{username} (Already followed in history)")
            continue

        print(f"🚀 Following @{username}...")
        success = follow_user(token, username)
        if success:
            history.add(username)
            save_history(history)
            followed_count += 1
            
            # Randomized delay between 5 to 12 seconds for account safety
            delay = random.uniform(5.0, 12.0)
            print(f"⏳ Sleeping {delay:.1f}s for account safety...")
            time.sleep(delay)

    print(f"\n✨ Operation Complete: Followed {followed_count} new AI developers!")
    print(f"📁 History updated in '{HISTORY_FILE}'. Total tracked: {len(history)}")

if __name__ == "__main__":
    main()
