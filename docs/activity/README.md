# Daily GitHub Activity Publisher

This automation creates a publicly readable Markdown development update in
`docs/activity/YYYY-MM-DD.md` when real public GitHub development events
are visible for the current Pakistan-local day.

- Runs daily near **9:00 PM Pakistan time** (GitHub may delay schedules).
- Can be run manually from **Actions → Publish Daily GitHub Activity**.
- Includes public pushes with visible commit details, PR events, issues and reviews.
- Omits the profile repository itself to avoid counting synthetic bot/streak commits.
- Publishes **nothing** on days without verified public activity.
- Commits as `github-actions[bot]`, and clearly identifies the post as automated.
- Does not follow, star, comment, submit PRs, or post to third-party repositories.
- Needs no personal access token or external AI service.

Limitations: GitHub's public events feed may be delayed, limited or omit some
commit details. Therefore a day with activity can occasionally have no post.

To show posts prominently on your profile, add a link to the `docs/activity/`
folder in `README.md` after merging the PR.
