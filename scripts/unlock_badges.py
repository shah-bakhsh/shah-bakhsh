"""
Automated GitHub Achievements Unlocker
-------------------------------------
Unlocks:
1. Quickdraw 🤠 - Closes an issue within 5 minutes
2. YOLO 🎲 - Merges a PR without review
3. Pair Extraordinaire 👯‍♀️ - Merges a PR with a Co-authored commit
4. Pull Shark 🦈 - Merges PRs into main branch
"""

import os
import sys
import time
import json
import base64
import urllib.request
import urllib.error

TOKEN = os.environ.get("GITHUB_TOKEN")
REPO = os.environ.get("GITHUB_REPOSITORY", "shah-bakhsh/shah-bakhsh")

if not TOKEN:
    print("❌ GITHUB_TOKEN not found!")
    sys.exit(1)

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "BadgeUnlocker/1.0"
}

def api_request(url, method="GET", body=None):
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, method=method, data=data, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (204, 200, 201):
                res_body = resp.read().decode("utf-8")
                return json.loads(res_body) if res_body else {}, resp.status
    except urllib.error.HTTPError as e:
        print(f"  ⚠️ HTTP Error {e.code}: {e.reason}")
        err_msg = e.read().decode("utf-8")
        print(f"  Details: {err_msg[:200]}")
        return None, e.code
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None, 0
    return None, 0

def unlock_quickdraw():
    print("\n🤠 [1/4] Unlocking 'Quickdraw' Badge...")
    # 1. Create Issue
    url = f"https://api.github.com/repos/{REPO}/issues"
    payload = {
        "title": "Quickdraw Badge Verification Issue",
        "body": "Automated issue to trigger Quickdraw achievement badge."
    }
    res, status = api_request(url, method="POST", body=payload)
    if status == 201 and res and "number" in res:
        issue_num = res["number"]
        print(f"  ✅ Created Issue #{issue_num}")
        time.sleep(2)
        # 2. Immediately close it (< 5 minutes)
        close_url = f"https://api.github.com/repos/{REPO}/issues/{issue_num}"
        _, c_status = api_request(close_url, method="PATCH", body={"state": "closed"})
        if c_status == 200:
            print(f"  🎉 Closed Issue #{issue_num} immediately! Quickdraw unlocked 🤠!")
        else:
            print("  ⚠️ Failed to close issue.")

def unlock_pr_badges():
    print("\n🦈 [2/4] Unlocking 'Pull Shark', 'YOLO', & 'Pair Extraordinaire' Badges...")
    
    # Get main branch SHA
    ref_url = f"https://api.github.com/repos/{REPO}/git/ref/heads/main"
    ref_data, _ = api_request(ref_url)
    if not ref_data or "object" not in ref_data:
        print("  ❌ Could not fetch main branch SHA")
        return
    main_sha = ref_data["object"]["sha"]

    for i in range(1, 3):
        branch_name = f"achievement-badge-unlock-{i}-{int(time.time())}"
        print(f"\n  ▶ Creating PR #{i} (Branch: {branch_name})...")
        
        # 1. Create Branch
        create_ref_url = f"https://api.github.com/repos/{REPO}/git/refs"
        api_request(create_ref_url, method="POST", body={
            "ref": f"refs/heads/{branch_name}",
            "sha": main_sha
        })
        time.sleep(1)

        # 2. Create/Update File with Co-Author for 'Pair Extraordinaire'
        file_url = f"https://api.github.com/repos/{REPO}/contents/docs/achievements_{i}.md"
        content_str = f"# Achievement Badge Tracking File #{i}\n\nAutomated PR to unlock GitHub Badges."
        b64_content = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
        
        commit_msg = (
            f"docs: update achievement log #{i}\n\n"
            f"Co-authored-by: github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>"
        )
        
        api_request(file_url, method="PUT", body={
            "message": commit_msg,
            "content": b64_content,
            "branch": branch_name
        })
        time.sleep(1)

        # 3. Create PR
        pr_url = f"https://api.github.com/repos/{REPO}/pulls"
        pr_data, p_status = api_request(pr_url, method="POST", body={
            "title": f"chore: unlock github achievements #{i}",
            "head": branch_name,
            "base": "main",
            "body": "Automated Pull Request to unlock Pull Shark, YOLO, and Pair Extraordinaire achievements."
        })

        if p_status == 201 and pr_data and "number" in pr_data:
            pr_num = pr_data["number"]
            print(f"  ✅ Created Pull Request #{pr_num}")
            time.sleep(2)

            # 4. Merge PR (Unlocks YOLO & Pull Shark & Pair Extraordinaire)
            merge_url = f"https://api.github.com/repos/{REPO}/pulls/{pr_num}/merge"
            _, m_status = api_request(merge_url, method="PUT", body={
                "commit_title": f"Merge PR #{pr_num} for achievements",
                "merge_method": "squash"
            })
            if m_status == 200:
                print(f"  🎉 Merged PR #{pr_num}! Badges Unlocked: Pull Shark 🦈, YOLO 🎲, Pair Extraordinaire 👯‍♀️!")

def main():
    print("=" * 60)
    print("  🏆 GitHub Achievements Automated Unlocker")
    print(f"  Repository: {REPO}")
    print("=" * 60)

    unlock_quickdraw()
    unlock_pr_badges()

    print("\n" + "=" * 60)
    print("  ✨ ALL DONE! Check your GitHub profile for badges!")
    print("=" * 60)

if __name__ == "__main__":
    main()
