from dataclasses import dataclass
import re
import httpx

GITHUB_API = "https://api.github.com"


@dataclass
class PRFile:
    filename: str
    patch: str | None
    additions: int
    deletions: int


@dataclass
class ReviewComment:
    path: str
    line: int
    body: str


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_pr_files(repo: str, pr_number: int, token: str) -> list[PRFile]:
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/files"
    results = []
    page = 1
    while True:
        resp = httpx.get(
            url,
            headers=_headers(token),
            params={"per_page": 100, "page": page},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return [
        PRFile(
            filename=f["filename"],
            patch=f.get("patch"),
            additions=f["additions"],
            deletions=f["deletions"],
        )
        for f in results
    ]


def get_pr_commit_sha(repo: str, pr_number: int, token: str) -> str:
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    resp = httpx.get(url, headers=_headers(token), timeout=30.0)
    resp.raise_for_status()
    return resp.json()["head"]["sha"]


HUNK_LINE_RE = re.compile(r"\+(\d+)")


def get_valid_lines(patch: str) -> set[int]:
    """Return line numbers in the new file that appear in the diff hunk."""
    valid = set()
    current_line = 0
    for raw in patch.splitlines():
        if raw.startswith("@@"):
            m = HUNK_LINE_RE.search(raw)
            if m:
                try:
                    current_line = int(m.group(1)) - 1
                except ValueError:
                    continue
        elif raw.startswith("-"):
            pass  # old file line, skip
        elif raw.startswith("+"):
            current_line += 1
            valid.add(current_line)
        else:
            current_line += 1
    return valid


def post_review(
    repo: str,
    pr_number: int,
    commit_sha: str,
    comments: list[ReviewComment],
    token: str,
    summary: str,
    pr_files: list[PRFile],
) -> int:
    """Post a PR review and return the review ID."""
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}/reviews"

    # Only keep comments on lines that actually appear in the diff
    valid_map = {
        f.filename: get_valid_lines(f.patch)
        for f in pr_files
        if f.patch
    }
    inline = [
        {
            "path": c.path,
            "line": c.line,
            "side": "RIGHT",
            "body": c.body,
        }
        for c in comments
        if c.line in valid_map.get(c.path, set())
    ]

    skipped = len(comments) - len(inline)
    if skipped:
        summary += f"\n\n_{skipped} comment(s) could not be placed inline (line not in diff)._"

    body = {
        "commit_id": commit_sha,
        "body": summary,
        "event": "COMMENT",
        "comments": inline,
    }
    resp = httpx.post(url, headers=_headers(token), json=body, timeout=30.0)
    resp.raise_for_status()
    review_id: int = resp.json()["id"]
    print(f"Posted review: {len(inline)} inline comment(s) (review_id={review_id})")
    return review_id
