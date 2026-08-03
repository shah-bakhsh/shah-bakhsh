"""
Auto-Star Trending AI Repositories Script for GitHub
---------------------------------------------------
This script discovers and stars top trending open-source AI, LLM, 
Agentic AI, and RAG repositories on GitHub.

Usage:
1. Set environment variable: $env:GITHUB_TOKEN="ghp_your_token_here"
2. Run script: python auto_star_ai_repos.py --limit 10
"""

import os
import sys
import time
import json
import random
import urllib.request
import urllib.parse
import urllib.error

HISTORY_FILE = "starred_repos.json"

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

def search_trending_ai_repos(token, limit=10):
    queries = [
        "topic:agentic-ai stars:>100",
        "topic:llm topic:rag stars:>200",
        "topic:langgraph stars:>50",
        "topic:multi-agent stars:>50",
        "topic:computer-vision stars:>300"
    ]
    query = random.choice(queries)
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page=30"
    
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("User-Agent", "ShahBakhsh-AIStarrer/1.0")
    req.add_header("Accept", "application/vnd.github.v3+json")
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("items", [])
            repos = [repo["full_name"] for repo in items]
            print(f"🔍 Found {len(repos)} trending AI repositories matching '{query}'")
            return repos
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []

def star_repo(token, repo_full_name):
    url = f"https://api.github.com/user/starred/{repo_full_name}"
    req = urllib.request.Request(url, method="PUT")
    req.add_header("Authorization", f"token {token}")
    req.add_header("User-Agent", "ShahBakhsh-AIStarrer/1.0")
    req.add_header("Content-Length", "0")
    
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (204, 200):
                print(f"⭐ Successfully starred repository: {repo_full_name}")
                return True
    except Exception as e:
        print(f"⚠️ Error starring {repo_full_name}: {e}")
    return False

def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set!")
        sys.exit(1)

    print("🤖 Starting AI Repository Auto-Starrer...")
    history = load_history()
    candidates = search_trending_ai_repos(token, limit=10)
    
    starred_count = 0
    for repo_name in candidates:
        if starred_count >= 10:
            break
            
        if repo_name in history:
            continue

        print(f"⭐ Starring {repo_name}...")
        success = star_repo(token, repo_name)
        if success:
            history.add(repo_name)
            save_history(history)
            starred_count += 1
            time.sleep(random.uniform(4.0, 8.0))

    print(f"\n✨ Operation Complete: Starred {starred_count} new AI repositories!")

if __name__ == "__main__":
    main()
