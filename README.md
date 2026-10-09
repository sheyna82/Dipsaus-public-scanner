# DIPSAUS — public stock recovery scanner

**Migration status: preparation only.** The existing private scanner remains authoritative until a tested cutover. No automated trading or scheduled workflows are enabled here yet.

## Privacy and security
- This is a new clean-history repository; do not copy the private repository's `.git` history.
- Do not commit positions, cost basis, broker handoffs, personal notification state, API keys, notification channel IDs, or private reports.
- Store provider keys and alert destinations in GitHub Actions Secrets.
- Review and sanitize source files and workflows before enabling schedules.
- A `.gitignore` is not sufficient protection for files that have already been committed; inspect files before copying.

Research-only signals; no automatic buy or sell orders.
