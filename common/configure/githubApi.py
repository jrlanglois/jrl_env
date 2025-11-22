#!/usr/bin/env python3
"""
GitHub API integration for repository discovery.
Supports wildcard patterns and HTTP caching with ETags.
"""

import json
import os
import re
import urllib.error
import urllib.request
from typing import Optional, List, Tuple

from common.core.logging import printError, printInfo, printWarning, printVerbose
from common.configure.repoCache import CacheEntry, getCacheEntry, saveCacheEntry


def parseGitHubPattern(pattern: str) -> Optional[Tuple[str, bool]]:
    """
    Parse a GitHub pattern to extract owner/org and determine if it's a wildcard.

    Args:
        pattern: Pattern like "git@github.com:owner/*" or "https://github.com/owner/*"

    Returns:
        Tuple of (owner, isWildcard) if valid, None if invalid
    """
    # Match SSH format: git@github.com:owner/*
    sshMatch = re.match(r'^git@github\.com:([^/]+)/\*$', pattern)
    if sshMatch:
        return (sshMatch.group(1), True)

    # Match HTTPS format: https://github.com/owner/*
    httpsMatch = re.match(r'^https://github\.com/([^/]+)/\*$', pattern)
    if httpsMatch:
        return (httpsMatch.group(1), True)

    # Invalid patterns
    if '*' in pattern:
        printWarning(f"Invalid wildcard pattern: {pattern}")
        printWarning("Valid formats: git@github.com:owner/* or https://github.com/owner/*")
        return None

    return None


def fetchGitHubRepos(
    owner: str,
    visibility: str = "all",
    cachedEntry: Optional[CacheEntry] = None
) -> Tuple[Optional[List[str]], Optional[str], Optional[str]]:
    """
    Fetch repositories from GitHub API with HTTP caching support.

    Args:
        owner: GitHub username or organization name
        visibility: Filter by visibility (all/public/private)
        cachedEntry: Optional cache entry with ETag for conditional request

    Returns:
        Tuple of (repo_list, etag, last_modified)
        - repo_list is None if 304 Not Modified (use cache)
        - etag and last_modified are cache metadata
    """
    # Map visibility to GitHub API type parameter
    typeMap = {
        "all": "all",
        "public": "public",
        "private": "private",
    }
    repoType = typeMap.get(visibility, "all")

    # GitHub API endpoint
    apiUrl = f"https://api.github.com/users/{owner}/repos?type={repoType}&per_page=100"

    # Check if owner might be an organization
    # Try users first, fall back to orgs if it fails
    urls = [
        f"https://api.github.com/users/{owner}/repos?type={repoType}&per_page=100",
        f"https://api.github.com/orgs/{owner}/repos?type={repoType}&per_page=100",
    ]

    for url in urls:
        try:
            # Build request with headers
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'jrl_env-repo-discovery')
            req.add_header('Accept', 'application/vnd.github.v3+json')

            # Add GitHub token if available (increases rate limit)
            githubToken = os.environ.get('GITHUB_TOKEN')
            if githubToken:
                req.add_header('Authorization', f'token {githubToken}')
                printVerbose("Using GITHUB_TOKEN for authentication")

            # Add conditional request headers if we have cached data
            if cachedEntry and cachedEntry.etag:
                req.add_header('If-None-Match', cachedEntry.etag)
                printVerbose(f"Conditional request with ETag: {cachedEntry.etag}")

            # Make request
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    # Extract caching metadata
                    etag = response.headers.get('ETag')
                    lastModified = response.headers.get('Last-Modified')

                    # Parse response
                    data = json.loads(response.read().decode('utf-8'))

                    # Extract SSH clone URLs
                    repos = []
                    for repo in data:
                        if 'ssh_url' in repo:
                            repos.append(repo['ssh_url'])

                    printVerbose(f"Fetched {len(repos)} repositories for {owner}")
                    return (repos, etag, lastModified)

            except urllib.error.HTTPError as e:
                if e.code == 304:
                    # Not Modified - use cached data
                    printVerbose(f"Cache valid for {owner} (304 Not Modified)")
                    return (None, cachedEntry.etag if cachedEntry else None, None)
                elif e.code == 404:
                    # Not found - try next URL (might be org instead of user)
                    continue
                elif e.code == 403:
                    # Rate limit or forbidden
                    printWarning(f"GitHub API rate limit or forbidden (403) for {owner}")
                    # Use cached data if available
                    if cachedEntry:
                        printInfo("Using cached repository list")
                        return (None, cachedEntry.etag, None)
                    return (None, None, None)
                else:
                    printWarning(f"GitHub API error {e.code} for {owner}")
                    continue

        except Exception as e:
            printVerbose(f"Error fetching repos for {owner} from {url}: {e}")
            continue

    # All attempts failed
    printError(f"Failed to fetch repositories for {owner}")
    if cachedEntry:
        printWarning("Using stale cached data")
        return (None, cachedEntry.etag, None)

    return (None, None, None)


def expandWildcardPattern(
    pattern: str,
    visibility: str = "all"
) -> Optional[List[str]]:
    """
    Expand a wildcard pattern to a list of repository URLs.
    Uses HTTP caching to minimize API calls.

    Args:
        pattern: Wildcard pattern (e.g., "git@github.com:owner/*")
        visibility: Visibility filter (all/public/private)

    Returns:
        List of repository URLs, or None if expansion failed
    """
    # Parse pattern
    parsed = parseGitHubPattern(pattern)
    if not parsed:
        return None

    owner, isWildcard = parsed
    if not isWildcard:
        # Not a wildcard, return as-is
        return [pattern]

    printInfo(f"Expanding wildcard pattern: {owner}/* (visibility: {visibility})")

    # Check cache
    cachedEntry = getCacheEntry(pattern, visibility)

    # Fetch from API (with conditional request if cached)
    repos, etag, lastModified = fetchGitHubRepos(owner, visibility, cachedEntry)

    # Handle response
    if repos is None:
        # 304 Not Modified or error - use cached data
        if cachedEntry:
            printInfo(f"Using cached repository list ({len(cachedEntry.expanded)} repos)")
            return cachedEntry.expanded
        else:
            printError(f"No repositories found for pattern: {pattern}")
            return None

    # Save to cache
    newEntry = CacheEntry(
        pattern=pattern,
        visibility=visibility,
        expanded=repos,
        etag=etag,
        lastModified=lastModified,
    )
    saveCacheEntry(newEntry)

    printInfo(f"Expanded to {len(repos)} repositories")
    return repos


__all__ = [
    "parseGitHubPattern",
    "fetchGitHubRepos",
    "expandWildcardPattern",
]
