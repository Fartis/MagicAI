#!/usr/bin/env bash

set -Eeuo pipefail

command -v gh >/dev/null || {
    echo "Error: GitHub CLI (gh) is required."
    exit 1
}

command -v jq >/dev/null || {
    echo "Error: jq is required."
    exit 1
}

command -v python3 >/dev/null || {
    echo "Error: python3 is required."
    exit 1
}

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "Error: run this script inside the Git repository."
    exit 1
}

gh auth status >/dev/null 2>&1 || {
    echo "Error: authenticate first with: gh auth login"
    exit 1
}

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
OUT="github-analysis-${TIMESTAMP}"

mkdir -p \
    "$OUT/api/stats" \
    "$OUT/api/traffic" \
    "$OUT/api/pr_details" \
    "$OUT/git" \
    "$OUT/csv"

ERROR_LOG="$OUT/api_errors.log"
touch "$ERROR_LOG"

echo "Exporting repository analysis to: $OUT"

api_object() {
    local endpoint="$1"
    local output="$2"

    if ! gh api "$endpoint" > "$output" 2>>"$ERROR_LOG"; then
        echo '{"available":false,"reason":"API request failed or permission unavailable"}' > "$output"
    fi
}

api_array() {
    local endpoint="$1"
    local output="$2"

    if ! gh api --paginate "$endpoint" --jq '.[]' 2>>"$ERROR_LOG" |
        jq -s '.' > "$output"; then
        echo '[]' > "$output"
    fi
}

stat_api() {
    local endpoint="$1"
    local output="$2"
    local temporary="${output}.tmp"

    for attempt in 1 2 3 4 5; do
        rm -f "$temporary"

        gh api "$endpoint" > "$temporary" 2>>"$ERROR_LOG" || true

        if [[ -s "$temporary" ]]; then
            mv "$temporary" "$output"
            return 0
        fi

        sleep 3
    done

    rm -f "$temporary"

    cat > "$output" <<EOF
{
  "available": false,
  "reason": "GitHub had not finished compiling this statistic. Run the exporter again later."
}
EOF
}

# ---------------------------------------------------------------------------
# General repository information
# ---------------------------------------------------------------------------

api_object "repos/{owner}/{repo}" \
    "$OUT/api/repository.json"

api_object "repos/{owner}/{repo}/languages" \
    "$OUT/api/languages.json"

api_object "repos/{owner}/{repo}/community/profile" \
    "$OUT/api/community_profile.json"

# ---------------------------------------------------------------------------
# Contributors
# ---------------------------------------------------------------------------

api_array "repos/{owner}/{repo}/contributors?anon=true&per_page=100" \
    "$OUT/api/contributors_raw.json"

jq '
map({
    login: (.login // "anonymous"),
    type,
    contributions,
    html_url
})
' "$OUT/api/contributors_raw.json" > "$OUT/api/contributors.json"

rm -f "$OUT/api/contributors_raw.json"

# ---------------------------------------------------------------------------
# Branches, tags, and releases
# ---------------------------------------------------------------------------

api_array "repos/{owner}/{repo}/branches?per_page=100" \
    "$OUT/api/branches_raw.json"

jq '
map({
    name,
    sha: .commit.sha,
    protected
})
' "$OUT/api/branches_raw.json" > "$OUT/api/branches.json"

rm -f "$OUT/api/branches_raw.json"

api_array "repos/{owner}/{repo}/tags?per_page=100" \
    "$OUT/api/tags_raw.json"

jq '
map({
    name,
    sha: .commit.sha,
    tarball_url,
    zipball_url
})
' "$OUT/api/tags_raw.json" > "$OUT/api/tags.json"

rm -f "$OUT/api/tags_raw.json"

api_array "repos/{owner}/{repo}/releases?per_page=100" \
    "$OUT/api/releases_raw.json"

jq '
map({
    id,
    tag_name,
    name,
    draft,
    prerelease,
    created_at,
    published_at,
    author: (.author.login // null),
    assets_count: (.assets | length)
})
' "$OUT/api/releases_raw.json" > "$OUT/api/releases.json"

rm -f "$OUT/api/releases_raw.json"

# ---------------------------------------------------------------------------
# Issues
# The issues endpoint also returns pull requests, which are filtered out.
# Bodies and comments are intentionally not exported.
# ---------------------------------------------------------------------------

api_array "repos/{owner}/{repo}/issues?state=all&per_page=100" \
    "$OUT/api/issues_raw.json"

jq '
map(
    select((has("pull_request") | not))
    | {
        number,
        title,
        state,
        state_reason,
        created_at,
        updated_at,
        closed_at,
        author: (.user.login // null),
        comments,
        locked,
        labels: [.labels[].name],
        assignees: [.assignees[].login],
        milestone: (.milestone.title // null)
    }
)
' "$OUT/api/issues_raw.json" > "$OUT/api/issues.json"

rm -f "$OUT/api/issues_raw.json"

# ---------------------------------------------------------------------------
# Pull requests
# Fetch each pull request to obtain additions, deletions, commits, and changed files.
# ---------------------------------------------------------------------------

api_array "repos/{owner}/{repo}/pulls?state=all&per_page=100" \
    "$OUT/api/pulls_index.json"

while IFS= read -r pr_number; do
    [[ -z "$pr_number" ]] && continue

    output="$OUT/api/pr_details/${pr_number}.json"

    if gh api "repos/{owner}/{repo}/pulls/${pr_number}" 2>>"$ERROR_LOG" |
        jq '{
            number,
            title,
            state,
            draft,
            created_at,
            updated_at,
            closed_at,
            merged_at,
            author: (.user.login // null),
            merged_by: (.merged_by.login // null),
            base_branch: .base.ref,
            head_branch: .head.ref,
            mergeable,
            mergeable_state,
            commits,
            additions,
            deletions,
            changed_files,
            comments,
            review_comments,
            maintainer_can_modify,
            labels: [.labels[].name]
        }' > "$output"; then
        :
    else
        rm -f "$output"
    fi
done < <(jq -r '.[].number' "$OUT/api/pulls_index.json")

shopt -s nullglob
PR_FILES=("$OUT"/api/pr_details/*.json)

if (( ${#PR_FILES[@]} > 0 )); then
    jq -s 'sort_by(.number)' "${PR_FILES[@]}" > "$OUT/api/pulls.json"
else
    echo '[]' > "$OUT/api/pulls.json"
fi

rm -f "$OUT/api/pulls_index.json"

# ---------------------------------------------------------------------------
# GitHub Actions
# ---------------------------------------------------------------------------

if gh api --paginate \
    "repos/{owner}/{repo}/actions/workflows?per_page=100" \
    --jq '.workflows[]' 2>>"$ERROR_LOG" |
    jq -s 'map({
        id,
        name,
        path,
        state,
        created_at,
        updated_at
    })' > "$OUT/api/workflows.json"; then
    :
else
    echo '[]' > "$OUT/api/workflows.json"
fi

if gh api --paginate \
    "repos/{owner}/{repo}/actions/runs?per_page=100" \
    --jq '.workflow_runs[]' 2>>"$ERROR_LOG" |
    jq -s 'map({
        id,
        name,
        display_title,
        event,
        status,
        conclusion,
        workflow_id,
        run_number,
        run_attempt,
        head_branch,
        head_sha,
        created_at,
        run_started_at,
        updated_at,
        actor: (.actor.login // null)
    })' > "$OUT/api/workflow_runs.json"; then
    :
else
    echo '[]' > "$OUT/api/workflow_runs.json"
fi

# ---------------------------------------------------------------------------
# Statistics calculated by GitHub
# ---------------------------------------------------------------------------

stat_api "repos/{owner}/{repo}/stats/contributors" \
    "$OUT/api/stats/contributors.json"

stat_api "repos/{owner}/{repo}/stats/commit_activity" \
    "$OUT/api/stats/commit_activity.json"

stat_api "repos/{owner}/{repo}/stats/code_frequency" \
    "$OUT/api/stats/code_frequency.json"

stat_api "repos/{owner}/{repo}/stats/participation" \
    "$OUT/api/stats/participation.json"

stat_api "repos/{owner}/{repo}/stats/punch_card" \
    "$OUT/api/stats/punch_card.json"

# ---------------------------------------------------------------------------
# Traffic data requires sufficient permissions and covers a limited recent window.
# ---------------------------------------------------------------------------

api_object "repos/{owner}/{repo}/traffic/clones" \
    "$OUT/api/traffic/clones.json"

api_object "repos/{owner}/{repo}/traffic/views" \
    "$OUT/api/traffic/views.json"

api_object "repos/{owner}/{repo}/traffic/popular/paths" \
    "$OUT/api/traffic/popular_paths.json"

api_object "repos/{owner}/{repo}/traffic/popular/referrers" \
    "$OUT/api/traffic/popular_referrers.json"

# ---------------------------------------------------------------------------
# Local Git history
# ---------------------------------------------------------------------------

git remote -v > "$OUT/git/remotes.txt"
git branch -a -vv > "$OUT/git/branches.txt"
git tag --sort=-creatordate > "$OUT/git/tags.txt"
git status --short --branch > "$OUT/git/status.txt"
git count-objects -vH > "$OUT/git/storage.txt"
git shortlog -s -n --all > "$OUT/git/shortlog.txt"
git ls-files > "$OUT/git/tracked_files.txt"

git rev-list --count --all > "$OUT/git/total_commits_all_refs.txt"
git rev-list --count HEAD > "$OUT/git/total_commits_current_branch.txt"

# Generate history CSV files without exporting author emails or file contents.
python3 - "$OUT" <<'PY'
import csv
import json
import os
import pathlib
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

out = pathlib.Path(sys.argv[1])

marker = "__GITHUB_ANALYSIS_COMMIT__"
separator = "\x1f"

pretty = (
    marker
    + separator + "%H"
    + separator + "%aI"
    + separator + "%an"
    + separator + "%P"
    + separator + "%s"
)

result = subprocess.run(
    [
        "git",
        "log",
        "--all",
        "--numstat",
        "--date=iso-strict",
        f"--pretty=format:{pretty}",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    errors="replace",
    check=True,
)

commits = []
current = None

def finish_current():
    global current

    if current is not None:
        commits.append(current)
        current = None

for line in result.stdout.splitlines():
    if line.startswith(marker + separator):
        finish_current()

        parts = line.split(separator)

        if len(parts) < 6:
            continue

        parents = parts[4].split() if parts[4] else []

        current = {
            "sha": parts[1],
            "date": parts[2],
            "author": parts[3],
            "parent_count": len(parents),
            "subject": separator.join(parts[5:]),
            "files_changed": 0,
            "additions": 0,
            "deletions": 0,
            "binary_files": 0,
        }

        continue

    if current is None or "\t" not in line:
        continue

    fields = line.split("\t", 2)

    if len(fields) != 3:
        continue

    added, deleted, _filename = fields

    current["files_changed"] += 1

    if added.isdigit():
        current["additions"] += int(added)
    else:
        current["binary_files"] += 1

    if deleted.isdigit():
        current["deletions"] += int(deleted)

finish_current()

commits.sort(key=lambda item: item["date"])

commit_fields = [
    "sha",
    "date",
    "author",
    "parent_count",
    "subject",
    "files_changed",
    "additions",
    "deletions",
    "binary_files",
]

with (out / "csv" / "commits.csv").open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(handle, fieldnames=commit_fields)
    writer.writeheader()
    writer.writerows(commits)

authors = defaultdict(
    lambda: {
        "commits": 0,
        "merge_commits": 0,
        "files_changed": 0,
        "additions": 0,
        "deletions": 0,
    }
)

months = defaultdict(
    lambda: {
        "commits": 0,
        "merge_commits": 0,
        "files_changed": 0,
        "additions": 0,
        "deletions": 0,
    }
)

weekdays = defaultdict(int)
hours = defaultdict(int)

for commit in commits:
    author_stats = authors[commit["author"]]
    author_stats["commits"] += 1
    author_stats["merge_commits"] += int(commit["parent_count"] > 1)
    author_stats["files_changed"] += commit["files_changed"]
    author_stats["additions"] += commit["additions"]
    author_stats["deletions"] += commit["deletions"]

    month = commit["date"][:7] if commit["date"] else "unknown"
    month_stats = months[month]
    month_stats["commits"] += 1
    month_stats["merge_commits"] += int(commit["parent_count"] > 1)
    month_stats["files_changed"] += commit["files_changed"]
    month_stats["additions"] += commit["additions"]
    month_stats["deletions"] += commit["deletions"]

    try:
        parsed = datetime.fromisoformat(commit["date"])
        weekdays[parsed.strftime("%A")] += 1
        hours[parsed.hour] += 1
    except (TypeError, ValueError):
        pass

with (out / "csv" / "authors.csv").open(
    "w", newline="", encoding="utf-8"
) as handle:
    fieldnames = [
        "author",
        "commits",
        "merge_commits",
        "files_changed",
        "additions",
        "deletions",
        "net_lines",
    ]

    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()

    for author, stats in sorted(
        authors.items(),
        key=lambda item: item[1]["commits"],
        reverse=True,
    ):
        writer.writerow(
            {
                "author": author,
                **stats,
                "net_lines": stats["additions"] - stats["deletions"],
            }
        )

with (out / "csv" / "monthly_activity.csv").open(
    "w", newline="", encoding="utf-8"
) as handle:
    fieldnames = [
        "month",
        "commits",
        "merge_commits",
        "files_changed",
        "additions",
        "deletions",
        "net_lines",
    ]

    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()

    for month in sorted(months):
        stats = months[month]
        writer.writerow(
            {
                "month": month,
                **stats,
                "net_lines": stats["additions"] - stats["deletions"],
            }
        )

with (out / "csv" / "commit_hours.csv").open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.writer(handle)
    writer.writerow(["hour", "commits"])

    for hour in range(24):
        writer.writerow([hour, hours[hour]])

with (out / "csv" / "commit_weekdays.csv").open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.writer(handle)
    writer.writerow(["weekday", "commits"])

    ordered_days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    for day in ordered_days:
        writer.writerow([day, weekdays[day]])

# Tracked-file statistics without copying file contents.
tracked = subprocess.run(
    ["git", "ls-files", "-z"],
    stdout=subprocess.PIPE,
    check=True,
).stdout.split(b"\0")

extensions = defaultdict(
    lambda: {
        "files": 0,
        "bytes": 0,
    }
)

total_files = 0
total_bytes = 0

for raw_path in tracked:
    if not raw_path:
        continue

    path_text = raw_path.decode("utf-8", errors="replace")
    path = pathlib.Path(path_text)

    suffix = path.suffix.lower() or "[no extension]"

    try:
        size = path.stat().st_size
    except OSError:
        size = 0

    extensions[suffix]["files"] += 1
    extensions[suffix]["bytes"] += size

    total_files += 1
    total_bytes += size

with (out / "csv" / "file_types.csv").open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.writer(handle)
    writer.writerow(["extension", "files", "bytes"])

    for extension, values in sorted(
        extensions.items(),
        key=lambda item: item[1]["bytes"],
        reverse=True,
    ):
        writer.writerow(
            [
                extension,
                values["files"],
                values["bytes"],
            ]
        )

summary = {
    "generated_at": datetime.now().astimezone().isoformat(),
    "commits_all_refs": len(commits),
    "authors": len(authors),
    "first_commit": commits[0]["date"] if commits else None,
    "last_commit": commits[-1]["date"] if commits else None,
    "total_additions": sum(commit["additions"] for commit in commits),
    "total_deletions": sum(commit["deletions"] for commit in commits),
    "merge_commits": sum(commit["parent_count"] > 1 for commit in commits),
    "tracked_files": total_files,
    "tracked_file_bytes": total_bytes,
}

with (out / "git" / "local_summary.json").open(
    "w", encoding="utf-8"
) as handle:
    json.dump(summary, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY

# ---------------------------------------------------------------------------
# CLOC language statistics
# ---------------------------------------------------------------------------

if command -v cloc >/dev/null 2>&1; then
    cloc \
        --list-file="$OUT/git/tracked_files.txt" \
        --json \
        --quiet \
        --out="$OUT/git/cloc.json" \
        2>>"$ERROR_LOG" || true
else
    cat > "$OUT/git/cloc.json" <<EOF
{
  "available": false,
  "reason": "cloc is not installed"
}
EOF
fi

# ---------------------------------------------------------------------------
# CSV files derived from GitHub data
# ---------------------------------------------------------------------------

jq -r '
(["login","type","contributions"] | @csv),
(.[] | [
    .login,
    .type,
    .contributions
] | @csv)
' "$OUT/api/contributors.json" > "$OUT/csv/contributors.csv"

jq -r '
(["number","state","created_at","closed_at","author","comments","title","labels"] | @csv),
(.[] | [
    .number,
    .state,
    .created_at,
    .closed_at,
    .author,
    .comments,
    .title,
    (.labels | join("; "))
] | @csv)
' "$OUT/api/issues.json" > "$OUT/csv/issues.csv"

jq -r '
(["number","state","draft","created_at","merged_at","author","base_branch","head_branch","commits","additions","deletions","changed_files","title"] | @csv),
(.[] | [
    .number,
    .state,
    .draft,
    .created_at,
    .merged_at,
    .author,
    .base_branch,
    .head_branch,
    .commits,
    .additions,
    .deletions,
    .changed_files,
    .title
] | @csv)
' "$OUT/api/pulls.json" > "$OUT/csv/pull_requests.csv"

jq -r '
(["id","name","event","status","conclusion","run_number","head_branch","created_at","run_started_at","updated_at","actor"] | @csv),
(.[] | [
    .id,
    .name,
    .event,
    .status,
    .conclusion,
    .run_number,
    .head_branch,
    .created_at,
    .run_started_at,
    .updated_at,
    .actor
] | @csv)
' "$OUT/api/workflow_runs.json" > "$OUT/csv/workflow_runs.csv"

# ---------------------------------------------------------------------------
# Human-readable summary
# ---------------------------------------------------------------------------

REPO_NAME="$(
    jq -r '.full_name // "unknown"' "$OUT/api/repository.json"
)"

{
    echo "GitHub repository analysis export"
    echo "Repository: $REPO_NAME"
    echo "Generated: $(date --iso-8601=seconds)"
    echo
    echo "Main files:"
    echo "- api/repository.json"
    echo "- api/issues.json"
    echo "- api/pulls.json"
    echo "- api/contributors.json"
    echo "- api/workflow_runs.json"
    echo "- api/stats/"
    echo "- api/traffic/"
    echo "- git/local_summary.json"
    echo "- git/cloc.json"
    echo "- csv/commits.csv"
    echo "- csv/monthly_activity.csv"
    echo "- csv/authors.csv"
    echo "- csv/file_types.csv"
} > "$OUT/README.txt"

ZIP="${OUT}.zip"

zip -qr "$ZIP" "$OUT"

echo
echo "Export completed."
echo "Directory: $OUT"
echo "Archive: $ZIP"
