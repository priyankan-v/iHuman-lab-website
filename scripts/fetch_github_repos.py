"""
Pre-render script: fetches public repos from the iHuman-Lab GitHub org
and generates software/repos/<name>/index.qmd for each one.

Run automatically via _quarto.yml pre-render, or manually:
    python scripts/fetch_github_repos.py
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ORG = "iHuman-Lab"
API_URL = f"https://api.github.com/orgs/{ORG}/repos?per_page=100&sort=updated"
OUTPUT_DIR = Path(__file__).parent.parent / "software" / "repos"

# Repos to skip (forks handled automatically; add names to skip here)
EXCLUDE_NAMES = {
    "lab-website",
    "lab-manual",
    "shasta",
    "research-manual",
    "cookiecutter-data-science",
    "cookiecutter-python-package",
}


def github_request(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "iHuman-Lab-Website-Builder")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"token {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def fetch_repos():
    return github_request(API_URL)


def fetch_languages(name):
    url = f"https://api.github.com/repos/{ORG}/{name}/languages"
    try:
        data = github_request(url)
        return list(data.keys())  # sorted by bytes descending by GitHub
    except urllib.error.URLError:
        return []


def download_image(url, dest: Path):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "iHuman-Lab-Website-Builder")
    try:
        with urllib.request.urlopen(req) as resp:
            dest.write_bytes(resp.read())
        return True
    except urllib.error.URLError:
        return False


def generate_qmd(repo: dict, repo_dir: Path, languages: list):
    name = repo["name"]
    description = (
        repo.get("description") or "A software project from the iHuman Lab."
    ).replace('"', "'")
    html_url = repo["html_url"]
    homepage = repo.get("homepage") or ""

    pushed_at = repo.get("pushed_at", "")
    try:
        date = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
        date_str = date.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        date_str = "January 01, 2024"

    image_line = 'image: "cover.png"' if (repo_dir / "cover.png").exists() else ""
    homepage_line = f'homepage: "{homepage}"' if homepage else ""
    if languages:
        lang_lines = "repo_languages:\n" + "".join(f'  - "{lang}"\n' for lang in languages)
    else:
        lang_lines = ""

    content = f"""---
title: "{name}"
date: "{date_str}"
draft: false
{image_line}
description: "{description}"
github: "{html_url}"
{lang_lines}{homepage_line}
---
"""
    (repo_dir / "index.qmd").write_text(content)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching repos for {ORG}...")
    try:
        repos = fetch_repos()
    except urllib.error.URLError as e:
        print(f"Warning: could not reach GitHub API ({e}). Skipping repo fetch.")
        return

    generated = []
    for repo in repos:
        name = repo["name"]
        if repo.get("fork") or name in EXCLUDE_NAMES:
            continue

        repo_dir = OUTPUT_DIR / name
        repo_dir.mkdir(exist_ok=True)

        # Download GitHub social preview image if not already present
        image_dest = repo_dir / "cover.png"
        if not image_dest.exists():
            og_url = f"https://opengraph.githubassets.com/1/{ORG}/{name}"
            download_image(og_url, image_dest)

        languages = fetch_languages(name)
        generate_qmd(repo, repo_dir, languages)
        generated.append(name)
        print(f"  Generated: software/repos/{name}/")

    print(f"Done — {len(generated)} repos: {', '.join(generated)}")


if __name__ == "__main__":
    main()
