# Data and counting rules

## GitHub metrics

The data comes from public GitHub REST endpoints, with a snapshot timestamp in `data/github.json`. The profile does not infer missing values as zero.

- Window: all available history up to the recorded UTC snapshot timestamp. `stats_days` is `null` in `config/profile.json`; a positive integer restores a rolling window of that many days.
- Commits: my linked GitHub author identity, across the history currently reachable from each selected repository's default branch. Merge commits and repeated SHAs within a repository are excluded. Unlinked author emails are not guessed.
- Line changes: additions and deletions in those commits, after path filters. Dioxyzine Frog is limited to `Working_Projects/Dioxyzine_Frog/` inside `Project`.
- Lockfiles, generated build folders, vendored dependencies, minified files and source maps are excluded by `config/profile.json`. Imported source that is not matched by an exclusion can still be counted. This is change volume, not a measure of original authorship, quality or skill.
- Re-adding or deleting a line counts as another change. A line change total is not the current codebase size.
- Stars: all-time stars across the selected code repositories. Stars belong to whole repositories, including the whole `Project` repository.
- PRs and issues: public items I opened across GitHub over all time, up to the snapshot timestamp. These are not limited to the four code repositories.

Per-commit counts are cached to reduce requests. Incomplete pagination, a failed request or a commit at GitHub's 3,000-file response boundary stops the authenticated workflow and preserves the previous published snapshot. The local bootstrap option can mark lines as pending; it never publishes a partial sum as a complete count.

## Programming languages

The chart sums GitHub's language-byte results for Portfolio, Frog Management, Retail Customer Insights and Football Analytics. The mixed `Project` repository is excluded because its repository-wide language totals also include unrelated coursework. These are repository code proportions, not personal proficiency or proof that I authored every line. GitHub's own language classification may exclude vendored or generated code.

## Contribution art

The custom catwalk uses the date and intensity levels exposed by my public GitHub contribution calendar, for the last 365 days. It does not manufacture contribution cells or treat a contribution as one commit. Publicly displayed private-activity counts, if enabled on my GitHub profile, may be reflected in the calendar; no private repository names or content are fetched.

The calendar renderer reads GitHub's public calendar markup, rather than a stable REST endpoint. It validates dates, levels and the number of days, and fails if that markup changes. The previous artwork remains available. The walking cat is decoration beneath the actual grid and respects reduced-motion preferences.

## References

- [GitHub commits API](https://docs.github.com/en/rest/commits/commits)
- [GitHub repository languages](https://docs.github.com/en/rest/repos/repos#list-repository-languages)
