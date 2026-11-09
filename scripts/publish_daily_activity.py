#!/usr/bin/env python3
"""Publish a transparent daily digest based only on real public GitHub events.

No generative fabrication, synthetic contributions, automated engagement, or
impersonation. Uses standard library only. Public events can be delayed/limited.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

USER = os.environ.get("GH_USERNAME", "shah-bakhsh")
TOKEN = os.environ.get("GH_TOKEN", "")
ZONE = ZoneInfo(os.environ.get("TZ_NAME", "Asia/Karachi"))
PROFILE_REPO = f"{USER}/{USER}".lower()
API = f"https://api.github.com/users/{USER}/events/public"
MAX_PAGES = 3


def get_events(page):
    req = Request(
        f"{API}?per_page=100&page={page}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "GitHub-Activity-Publisher/1.0",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            return json.load(response)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"GitHub events API request failed: {exc}") from exc


def safe_markdown(value):
    return str(value).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]").replace("\n", " ").strip()


def event_line(event):
    kind = event.get("type", "")
    repo = (event.get("repo") or {}).get("name", "")
    payload = event.get("payload") or {}
    if not repo or repo.lower() == PROFILE_REPO:
        return None  # Avoid reporting automated commits in this profile repository.
    if kind == "PushEvent":
        commits = payload.get("commits") or []
        if not commits:
            return None  # Public events API can omit commit details.
        labels = "; ".join(safe_markdown(c.get("message", "").splitlines()[0])[:90]
                           for c in commits[:3] if c.get("message"))
        if not labels:
            return None
        return f"- **Code pushed** to [{safe_markdown(repo)}](https://github.com/{repo}): {labels}"
    if kind == "PullRequestEvent":
        action = payload.get("action", "")
        if action not in ("opened", "closed", "reopened", "synchronize"):
            return None
        pr = payload.get("pull_request") or {}
        url = pr.get("html_url") or f"https://github.com/{repo}/pulls"
        label = "merged" if pr.get("merged") else action
        return f"- **Pull request {label}:** [{safe_markdown(pr.get('title', 'Pull request'))}]({url})"
    if kind == "IssuesEvent" and payload.get("action") in ("opened", "closed"):
        issue = payload.get("issue") or {}
        url = issue.get("html_url") or f"https://github.com/{repo}/issues"
        return f"- **Issue {payload['action']}:** [{safe_markdown(issue.get('title', 'Issue'))}]({url})"
    if kind == "PullRequestReviewEvent" and payload.get("action") == "submitted":
        pr = payload.get("pull_request") or {}
        return f"- **Reviewed a pull request:** [{safe_markdown(pr.get('title', 'Pull request'))}]({pr.get('html_url', f'https://github.com/{repo}/pulls')})"
    return None


def main():
    now = datetime.now(ZONE)
    date = now.date()
    start = datetime.combine(date, datetime.min.time(), tzinfo=ZONE)
    end = start + timedelta(days=1)
    events = []
    for page in range(1, MAX_PAGES + 1):
        batch = get_events(page)
        if not isinstance(batch, list):
            raise RuntimeError("GitHub events API returned an unexpected response")
        events.extend(batch)
        if len(batch) < 100:
            break

    entries = []
    seen = set()
    for event in events:
        if (event.get("actor") or {}).get("login", "").lower() != USER.lower():
            continue
        created = event.get("created_at")
        if not created:
            continue
        at = datetime.fromisoformat(created.replace("Z", "+00:00")).astimezone(ZONE)
        if not (start <= at < end):
            continue
        line = event_line(event)
        if line and line not in seen:
            entries.append((at, line))
            seen.add(line)

    # Only publish facts actually visible in public GitHub activity.
    if not entries:
        print(f"No verified public development activity available for {date}; skipping publication.")
        return

    entries.sort(key=lambda entry: entry[0])
    out = Path("docs/activity") / f"{date.isoformat()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    body = (
        f"# GitHub Development Update — {date.isoformat()}\n\n"
        f"Public activity from [@{USER}](https://github.com/{USER}) "
        f"for {date.isoformat()} (Pakistan time).\n\n"
        + "\n".join(line for _, line in entries)
        + "\n\n---\n"
        + "_Automatically compiled from public GitHub events. "
        + "Posted by GitHub Actions, not manually written by the account owner. "
        + "GitHub public events may be delayed or incomplete._\n"
    )
    if out.exists() and out.read_text(encoding="utf-8") == body:
        print("Post already up to date.")
        return
    out.write_text(body, encoding="utf-8")
    print(f"Prepared {out} from {len(entries)} verified public events.")


if __name__ == "__main__":
    main()
