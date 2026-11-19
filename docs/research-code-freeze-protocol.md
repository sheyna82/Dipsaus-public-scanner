# DIPSAUS research code-freeze pre-write protocol

Scope: isolated research branch only. **This is not GitHub branch protection.**

Before each GitHub write operation (create/update/delete file, commit, merge,
or workflow with write permissions), the operator must evaluate
`us_code_freeze.code_freeze_active()` using a current timezone-aware timestamp.
Do not batch a write that can cross the start of the freeze without rechecking.
For a local shell or a workflow that checks out this branch:

```sh
python us_code_freeze.py
# Only if exit status is 0 may the subsequent write proceed.
```

The CLI exits nonzero during **09:25 through 15:59:59 New York time,
Monday–Friday**, independent of Netherlands DST. This conservatively freezes
US market holidays as well. It does **not** cover early exchange closures,
unscheduled halts, exchange holiday exceptions or late pre-market changes.
Do not use it to authorize trading or market-data freshness.

For CI that writes, invoke this as the first step and immediately before
each write; use the same job so a failing exit aborts the write. Read-only
offline regression jobs may continue. GitHub's server-side rulesets or branch
protection are still needed to prevent direct pushes from bypassing a local
or workflow preflight; none are asserted to be installed by this document.

Never modify `main`, production or draft PR #65 in this research exercise.
No automated order placement or trade-ready flag is authorized.
