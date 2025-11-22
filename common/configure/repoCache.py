#!/usr/bin/env python3
"""
HTTP caching system for repository wildcard expansion.
Implements RFC 7232 conditional requests using ETag and Last-Modified headers.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from common.core.logging import printInfo, printWarning, printVerbose, printError


@dataclass
class CacheEntry:
    """Repository cache entry with HTTP caching metadata."""
    pattern: str
    visibility: str
    expanded: List[str]
    etag: Optional[str] = None
    lastModified: Optional[str] = None
    cachedAt: str = ""

    def __post_init__(self):
        """Set cachedAt to current time if not provided."""
        if not self.cachedAt:
            self.cachedAt = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def getCacheDir() -> Path:
    """
    Get the cache directory for repository data.

    Returns:
        Path to cache directory
    """
    # Use XDG_CACHE_HOME if set, otherwise ~/.cache
    if os.name == 'nt':
        # Windows: use LOCALAPPDATA
        cacheBase = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    else:
        # Unix/Linux/macOS: use XDG_CACHE_HOME or ~/.cache
        cacheBase = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))

    cacheDir = cacheBase / 'jrl_env'
    cacheDir.mkdir(parents=True, exist_ok=True)
    return cacheDir


def getCacheFilePath() -> Path:
    """Get the path to the repository cache file."""
    return getCacheDir() / 'repo_cache.json'


def loadCache() -> dict:
    """
    Load repository cache from disk.

    Returns:
        Dictionary of cache entries (pattern -> CacheEntry dict)
    """
    cacheFile = getCacheFilePath()

    if not cacheFile.exists():
        return {}

    try:
        with open(cacheFile, 'r', encoding='utf-8') as f:
            cacheData = json.load(f)
        printVerbose(f"Loaded repository cache from {cacheFile}")
        return cacheData
    except Exception as e:
        printWarning(f"Failed to load repository cache: {e}")
        return {}


def saveCache(cache: dict) -> bool:
    """
    Save repository cache to disk.

    Args:
        cache: Dictionary of cache entries

    Returns:
        True if successful, False otherwise
    """
    cacheFile = getCacheFilePath()

    try:
        with open(cacheFile, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
        printVerbose(f"Saved repository cache to {cacheFile}")
        return True
    except Exception as e:
        printError(f"Failed to save repository cache: {e}")
        return False


def getCacheEntry(pattern: str, visibility: str = "all") -> Optional[CacheEntry]:
    """
    Get cache entry for a pattern if it exists and is valid.

    Args:
        pattern: Repository pattern (e.g., "git@github.com:owner/*")
        visibility: Visibility filter (all/public/private)

    Returns:
        CacheEntry if found and valid, None otherwise
    """
    cache = loadCache()
    cacheKey = f"{pattern}:{visibility}"

    if cacheKey not in cache:
        return None

    try:
        entry = CacheEntry(**cache[cacheKey])

        # Check if cache is stale (older than 7 days)
        cachedTime = datetime.fromisoformat(entry.cachedAt)
        age = datetime.now() - cachedTime
        if age > timedelta(days=7):
            printVerbose(f"Cache entry for {pattern} is stale (age: {age.days} days)")
            return None

        return entry
    except Exception as e:
        printWarning(f"Invalid cache entry for {pattern}: {e}")
        return None


def saveCacheEntry(entry: CacheEntry) -> bool:
    """
    Save a cache entry for a pattern.

    Args:
        entry: CacheEntry to save

    Returns:
        True if successful, False otherwise
    """
    cache = loadCache()
    cacheKey = f"{entry.pattern}:{entry.visibility}"
    cache[cacheKey] = asdict(entry)
    return saveCache(cache)


def clearCache() -> bool:
    """
    Clear all repository cache.

    Returns:
        True if successful, False otherwise
    """
    cacheFile = getCacheFilePath()

    if not cacheFile.exists():
        printInfo("No cache to clear")
        return True

    try:
        cacheFile.unlink()
        printInfo(f"Cleared repository cache: {cacheFile}")
        return True
    except Exception as e:
        printError(f"Failed to clear cache: {e}")
        return False


def clearCacheEntry(pattern: str, visibility: str = "all") -> bool:
    """
    Clear cache entry for a specific pattern.

    Args:
        pattern: Repository pattern
        visibility: Visibility filter

    Returns:
        True if successful, False otherwise
    """
    cache = loadCache()
    cacheKey = f"{pattern}:{visibility}"

    if cacheKey in cache:
        del cache[cacheKey]
        return saveCache(cache)

    return True


__all__ = [
    "CacheEntry",
    "getCacheDir",
    "getCacheFilePath",
    "loadCache",
    "saveCache",
    "getCacheEntry",
    "saveCacheEntry",
    "clearCache",
    "clearCacheEntry",
]
