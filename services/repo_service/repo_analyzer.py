"""
Repo-to-video (RepoClip-style): GitHub repo → AI summary → presentation script/idea.
"""
import base64
import logging
import re
from typing import Any
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    import os
    if os.getenv("OPENAI_API_KEY"):
        OPENAI_AVAILABLE = True
except ImportError:
    pass


def _parse_github_url(url: str) -> tuple[str, str] | None:
    """Return (owner, repo) from GitHub URL."""
    url = url.strip().rstrip("/")
    # https://github.com/owner/repo or https://github.com/owner/repo/
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url, re.I)
    if m:
        return m.group(1), m.group(2)
    return None


def fetch_readme(owner: str, repo: str) -> str:
    """Fetch repo README and optional description via GitHub API. Returns combined text."""
    try:
        r = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        desc = (data.get("description") or "").strip()
        default_branch = data.get("default_branch") or "main"
    except Exception as e:
        logger.warning("GitHub repo fetch failed: %s", e)
        return ""
    try:
        readme_r = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/readme",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10,
        )
        readme_r.raise_for_status()
        readme_data = readme_r.json()
        content_b64 = readme_data.get("content") or ""
        content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
        return f"Description: {desc}\n\n# README\n\n{content}"
    except Exception as e:
        logger.warning("README fetch failed: %s", e)
        return f"Description: {desc}"


def repo_to_idea(repo_url: str, readme_text: str) -> dict[str, Any]:
    """
    Use LLM to turn repo + README into one video idea (hook, concept, caption, hashtags).
    Fallback: simple template from repo name.
    """
    if OPENAI_AVAILABLE and readme_text:
        try:
            client = OpenAI()
            prompt = (
                "You are writing a short-form video script to present this software project. "
                "Based on the repo description and README below, output exactly:\n"
                "1. A 3–5 word HOOK (first line that grabs attention).\n"
                "2. A 1–2 sentence CONCEPT (what the project does).\n"
                "3. A short CAPTION for the post (1–2 lines).\n"
                "Format your response as:\nHOOK: ...\nCONCEPT: ...\nCAPTION: ..."
            )
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You output only the three lines HOOK, CONCEPT, CAPTION."},
                    {"role": "user", "content": f"{prompt}\n\n---\n\n{readme_text[:6000]}"},
                ],
                max_tokens=400,
            )
            text = (response.choices[0].message.content or "").strip()
            hook = concept = caption = ""
            for line in text.split("\n"):
                if line.upper().startswith("HOOK:"):
                    hook = line.split(":", 1)[-1].strip()
                elif line.upper().startswith("CONCEPT:"):
                    concept = line.split(":", 1)[-1].strip()
                elif line.upper().startswith("CAPTION:"):
                    caption = line.split(":", 1)[-1].strip()
            if hook or concept:
                return {
                    "hook": hook or "Check this out",
                    "concept": concept or "A cool open-source project.",
                    "caption": caption or f"{hook}\n\n{concept}",
                    "hashtags": ["#opensource", "#github", "#coding", "#dev"],
                    "trend_angle": "repo showcase",
                }
        except Exception as e:
            logger.warning("OpenAI repo-to-idea failed: %s", e)
    parsed = _parse_github_url(repo_url)
    repo_name = parsed[1] if parsed else "project"
    return {
        "hook": f"This is {repo_name}",
        "concept": f"Open-source project from GitHub. {readme_text[:200] if readme_text else ''}",
        "caption": f"Repo: {repo_url}",
        "hashtags": ["#opensource", "#github", "#coding"],
        "trend_angle": "repo showcase",
    }


def analyze_repo(repo_url: str) -> dict[str, Any]:
    """Full pipeline: fetch README → generate idea. Returns idea payload + repo info."""
    parsed = _parse_github_url(repo_url)
    if not parsed:
        return {"ok": False, "error": "Invalid GitHub URL", "idea": None}
    owner, repo = parsed
    readme_text = fetch_readme(owner, repo)
    idea = repo_to_idea(repo_url, readme_text)
    return {
        "ok": True,
        "repo": {"owner": owner, "repo": repo, "url": repo_url},
        "idea": idea,
    }
