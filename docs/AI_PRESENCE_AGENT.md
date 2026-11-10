# SHAH.OS AI Presence Agent

## Purpose

Automated technical publishing in the account owner's own GitHub repository;
read-only discovery of third-party open-source opportunities. It is not an
impersonation or mass-engagement bot.

## Balanced autonomy boundaries

- Automatically gather official GitHub software releases and arXiv paper metadata.
- Create one dated, source-linked AI research journal per day when verified sources exist.
- Generate richer articles using the optional free-tier Gemini API key; otherwise produce
  a transparent citation-backed reading brief (no fabricated research or experiments).
- Optionally cross-post to **this repository's** GitHub Discussions when supported.
- Search public open-source issues read-only, saving links for owner review.
- **Never** submit external comments, PRs, issues, reviews, follows or stars.

## Schedule and output

Workflow: `SHAH.OS AI Presence - Daily Publisher`
Cron: `17 16 * * *` (approximately **9:17 PM Pakistan time**).
GitHub can delay or skip scheduled runs.

Daily post: `docs/presence/posts/YYYY-MM-DD.md`
Audit log: `docs/presence/state/YYYY-MM-DD.json`
External opportunities: `docs/presence/opportunities/YYYY-MM-DD.md`

A date-specific state file prevents duplicate daily publications when rerun.

## Setup required

1. Keep workflow enabled and grant GitHub Actions **read/write repository contents**
   permission under Settings -> Actions -> General. Check branch protection rules.
2. The repository currently has **Discussions disabled**. For cross-posting,
   turn on Settings -> General -> Features -> Discussions and add a General
   category. This workflow uses `DISCUSSIONS_MODE=optional`; the Markdown post
   still publishes even when Discussions is unavailable. A GitHub App token with
   Discussion write permission may be needed; the built-in token may be insufficient.
3. Add Actions secret `GEMINI_API_KEY` from Google AI Studio for LLM-written analysis.\n   Set `GEMINI_MODEL=gemini-2.5-flash` (already configured). Free API quotas\n   and model access vary by region and project; do not enable billing if your\n   goal is strictly free use. Without the key or when quota is exceeded, the workflow still
   publishes grounded source descriptions, not generated essays.
4. After merge, run the publisher manually in Actions to verify the generated
   post and workflow logs. A successful workflow must show a pushed commit
   and a source audit file.
5. Monitor real outputs rather than relying only on a green Actions status.

## Research and editorial calendar

Monday: LLM engineering.
Tuesday: Agentic AI.
Wednesday: Low-resource NLP.
Thursday: RAG.
Friday: ML engineering.
Saturday: Open source AI.
Sunday: AI research review.

## Safety and limits

Posts are labeled automated/AI-assisted. No invented citations, benchmark
claims, research findings, or first-person engineering experiences. Source
metadata is a starting point and should not be mistaken for a full peer
review. The optional LLM has basic citation URL screening, but that alone
cannot prove factual accuracy. If research sources all fail, publishing fails
instead of fabricating content. The opportunity list is only for human review.

Publishing to GitHub Discussions may need additional feature configuration,
permissions, and manual verification. The implementation cannot guarantee
that GitHub executes every daily cron trigger or that external API services
remain accessible.

## Gemini activation (November 2026)

The workflow reads `GEMINI_API_KEY` and uses the official Gemini `generateContent` REST endpoint. API results undergo basic citation URL screening; invalid, blocked or quota-limited responses fall back to the source-linked reading brief. Generated content is labeled AI-assisted. No OpenAI API key is needed. Do not publish private data to the free-tier API. API success and daily actual publishing must be verified in Actions logs.
