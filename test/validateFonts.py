#!/usr/bin/env python3
"""
Enhanced validation for Google Fonts.
Checks if fonts actually exist in Google Fonts API.
"""

import json
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent
sys.path.insert(0, str(projectRoot))

from common.common import (
    commandExists,
    getJsonArray,
    printError,
    printInfo,
    printH2,
    printSuccess,
    printWarning,
    requireCommand,
    safePrint,
)


def fetchGoogleFontsList() -> list[str]:
    """
    Fetch list of available Google Fonts from metadata API.

    Returns:
        List of font family names, or empty list if fetch fails
    """
    googleFontsListUrl = "https://fonts.google.com/metadata/fonts"

    try:
        req = urllib.request.Request(googleFontsListUrl)
        req.add_header('User-Agent', 'Mozilla/5.0')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            fontList = [item['family'] for item in data.get('familyMetadataList', [])]
            return fontList
    except Exception:
        return []


def checkFontViaCssApi(fontName: str) -> bool:
    """
    Check if a font exists via Google Fonts CSS API.

    Args:
        fontName: Font name to check

    Returns:
        True if font exists, False otherwise
    """
    fontUrlName = fontName.replace(" ", "+")
    cssUrl = f"https://fonts.googleapis.com/css2?family={fontUrlName}:wght@400"

    try:
        req = urllib.request.Request(cssUrl)
        req.add_header('User-Agent', 'Mozilla/5.0')

        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


def validateFonts(configPath: str) -> int:
    """
    Validate Google Fonts from config file.

    Args:
        configPath: Path to fonts.json config file

    Returns:
        0 if all fonts are valid, 1 otherwise
    """
    configFile = Path(configPath)

    if not configFile.exists():
        printError(f"Config file not found: {configPath}")
        return 1

    printH2("Validating Google Fonts")
    safePrint()

    # Check if curl is available (optional, we use urllib)
    if not commandExists("curl"):
        printWarning("curl is not available, but using Python urllib instead")

    # Get list of fonts from config
    fonts = getJsonArray(configPath, ".googleFonts[]?")

    if not fonts:
        printWarning("No fonts specified in config")
        return 0

    printInfo("Validating fonts against Google Fonts...")
    printInfo("This may take a moment...")

    errors = 0

    # Try to fetch font list from Google Fonts metadata
    fontList = fetchGoogleFontsList()

    if fontList:
        # Use fetched list for validation
        fontListLower = {font.lower() for font in fontList}

        for font in fonts:
            if not font or not font.strip():
                continue

            font = font.strip()
            if font.lower() in fontListLower:
                printSuccess(f"{font}")
            else:
                # Fallback: check via CSS API
                if checkFontViaCssApi(font):
                    printSuccess(f"{font} (verified via CSS API)")
                else:
                    printError(f"{font} (not found in Google Fonts)")
                    errors += 1
    else:
        # Fallback: check each font individually via CSS API
        printInfo("Fetching font list failed, checking fonts individually...")
        for font in fonts:
            if not font or not font.strip():
                continue

            font = font.strip()
            if checkFontViaCssApi(font):
                printSuccess(f"{font}")
            else:
                printError(f"{font} (not found in Google Fonts)")
                errors += 1

    safePrint()

    if errors == 0:
        printSuccess("All fonts are valid!")
        return 0
    else:
        printError(f"Found {errors} invalid font(s)")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        printError("Usage: python3 validateFonts.py <path-to-fonts.json>")
        sys.exit(1)

    configPath = sys.argv[1]
    startTime = time.perf_counter()
    exitCode = validateFonts(configPath)
    elapsed = time.perf_counter() - startTime
    safePrint()
    printInfo(f"Validation completed in {elapsed:.2f}s")
    sys.exit(exitCode)
