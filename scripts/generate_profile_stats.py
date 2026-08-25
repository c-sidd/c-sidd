#!/usr/bin/env python3
"""Generate the profile analytics SVG from live GitHub API data."""

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN = os.environ["GITHUB_TOKEN"]
USERNAME = "c-sidd"
OUTPUT = Path("profile/stats.svg")


def github_json(url: str, headers: dict[str, str]) -> dict:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "c-sidd-profile-stats",
}

# Contributions are available through GraphQL; the other two values use REST.
graphql_query = {
    "query": """
      query {
        user(login: \"c-sidd\") {
          contributionsCollection {
            contributionCalendar { totalContributions }
          }
        }
      }
    """
}
request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps(graphql_query).encode(),
    headers={**headers, "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=30) as response:
    graphql = json.load(response)

if graphql.get("errors"):
    raise RuntimeError(graphql["errors"])

contributions = graphql["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

repos = github_json(
    "https://api.github.com/user/repos?visibility=public&affiliation=owner&per_page=1",
    headers,
)
# REST pagination exposes the total only through Link, so use the search endpoint for an exact count.
repo_search = github_json(
    "https://api.github.com/search/repositories?" + urllib.parse.urlencode({"q": f"user:{USERNAME} fork:false", "per_page": 1}),
    headers,
)
public_repositories = repo_search["total_count"]

pr_search = github_json(
    "https://api.github.com/search/issues?" + urllib.parse.urlencode({"q": f"author:{USERNAME} is:pr", "per_page": 1}),
    headers,
)
pull_requests = pr_search["total_count"]

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="560" height="190" viewBox="0 0 560 190">
  <rect width="560" height="190" rx="14" fill="#0d1117" stroke="#30363d"/>
  <text x="28" y="36" fill="#c9d1d9" font-family="monospace" font-size="19" font-weight="700">GitHub Analytics</text>
  <text x="28" y="78" fill="#58a6ff" font-family="monospace" font-size="28" font-weight="700">{contributions}</text>
  <text x="28" y="99" fill="#8b949e" font-family="monospace" font-size="12">contributions</text>
  <text x="205" y="78" fill="#a371f7" font-family="monospace" font-size="28" font-weight="700">{pull_requests}</text>
  <text x="205" y="99" fill="#8b949e" font-family="monospace" font-size="12">pull requests</text>
  <text x="382" y="78" fill="#3fb950" font-family="monospace" font-size="28" font-weight="700">{public_repositories}</text>
  <text x="382" y="99" fill="#8b949e" font-family="monospace" font-size="12">public repositories</text>
  <line x1="28" y1="123" x2="532" y2="123" stroke="#30363d"/>
  <text x="28" y="151" fill="#8b949e" font-family="monospace" font-size="11">c-sidd • generated from GitHub API</text>
  <text x="28" y="169" fill="#6e7681" font-family="monospace" font-size="10">Updated automatically by GitHub Actions</text>
</svg>
'''

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(svg, encoding="utf-8")
print(f"Generated {OUTPUT}: contributions={contributions}, prs={pull_requests}, repos={public_repositories}")
