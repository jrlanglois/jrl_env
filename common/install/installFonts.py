#!/usr/bin/env python3
"""
Parallel Google Fonts installation script
Downloads and installs fonts from fonts.json using threading for speed
"""

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

# Import shared logging utilities from common
from pathlib import Path as PathLib

# Add project root to path so we can import from common
scriptDir = PathLib(__file__).parent.parent.parent
sys.path.insert(0, str(scriptDir))

# Import directly from source modules to avoid circular import with common.common
from common.core.logging import (
    Colours,
    printError,
    printH2,
    printInfo,
    printLock,
    printSuccess,
    printWarning,
    safePrint,
)


def downloadFile(url: str, outputPath: str, timeout: int = 5) -> bool:
    """Download a file from URL to output path."""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            with open(outputPath, 'wb') as f:
                shutil.copyfileobj(response, f)
        return os.path.getsize(outputPath) > 1000
    except Exception:
        # Silently fail - we'll try other URLs
        return False


def getVariantPatterns(variant: str) -> List[str]:
    """Get possible variant name patterns for a given variant."""
    patterns = {
        "Regular": ["Regular", "400", "normal", "regular"],
        "Bold": ["Bold", "700", "bold", "BoldRegular"],
        "Italic": ["Italic", "400italic", "italic", "RegularItalic"],
        "BoldItalic": ["BoldItalic", "700italic", "bolditalic", "Bold-Italic"]
    }
    return patterns.get(variant, [variant.replace(" ", "")])


def trySingleUrl(url: str, filePath: str, timeout: int = 5) -> bool:
    """Try to download from a single URL. Returns True if successful."""
    if downloadFile(url, filePath, timeout=timeout):
        return True
    if os.path.exists(filePath):
        try:
            os.remove(filePath)
        except Exception:
            pass
    return False


def tryGithubRepo(fontName: str, variant: str, tempDir: str) -> Optional[str]:
    """Try to download font from GitHub repository. Tries URLs in parallel."""
    normalisedName = fontName.lower().replace(" ", "-")
    variantPatterns = getVariantPatterns(variant)

    repoPaths = ["ofl", "apache", "ufl"]

    # Build all URL patterns to try
    urlsToTry = []
    for variantPattern in variantPatterns[:2]:  # Only try first 2 patterns to speed up
        testVariant = variantPattern.replace(" ", "")
        for repoPath in repoPaths:
            urlsToTry.append((
                f"https://github.com/google/fonts/raw/main/{repoPath}/{normalisedName}/{normalisedName}-{testVariant}.ttf",
                os.path.join(tempDir, f"{normalisedName}-{testVariant}.ttf")
            ))
            urlsToTry.append((
                f"https://github.com/google/fonts/raw/main/{repoPath}/{normalisedName}/{testVariant}.ttf",
                os.path.join(tempDir, f"{normalisedName}-{testVariant}.ttf")
            ))

    # Try URLs in parallel with a small thread pool
    with ThreadPoolExecutor(max_workers=min(6, len(urlsToTry))) as executor:
        futures = {
            executor.submit(trySingleUrl, url, filePath, timeout=3): (url, filePath)
            for url, filePath in urlsToTry
        }

        for future in as_completed(futures):
            if future.result():
                url, filePath = futures[future]
                # Cancel remaining futures and return
                for f in futures:
                    if f != future:
                        f.cancel()
                return filePath

    return None


def tryGoogleFontsApi(fontName: str, variant: str, tempDir: str) -> Optional[str]:
    """Try to get font URL from Google Fonts CSS API"""
    if variant != "Regular":
        return None

    apiFontName = fontName.replace(" ", "+")
    cssUrl = f"https://fonts.googleapis.com/css2?family={apiFontName}&display=swap"

    try:
        req = urllib.request.Request(cssUrl)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=5) as response:  # Shorter timeout
            cssContent = response.read().decode('utf-8')

        # Try to find TTF first
        ttfMatch = re.search(r'url\((https://fonts\.gstatic\.com/[^)]+\.ttf)\)', cssContent)
        if ttfMatch:
            fontUrl = ttfMatch.group(1)
            normalisedName = fontName.lower().replace(" ", "-")
            filePath = os.path.join(tempDir, f"{normalisedName}-{variant}.ttf")
            if downloadFile(fontUrl, filePath, timeout=8):
                return filePath

        # Try WOFF2 as fallback
        woff2Match = re.search(r'url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)', cssContent)
        if woff2Match:
            fontUrl = woff2Match.group(1)
            normalisedName = fontName.lower().replace(" ", "-")
            filePath = os.path.join(tempDir, f"{normalisedName}-{variant}.woff2")
            if downloadFile(fontUrl, filePath, timeout=8):
                return filePath
    except Exception:
        pass

    return None


def convertWoff2ToTtf(woff2Path: str, ttfPath: str) -> bool:
    """Convert WOFF2 file to TTF"""
    # Try woff2_decompress (Linux/macOS)
    if shutil.which("woff2_decompress"):
        try:
            result = subprocess.run(
                ["woff2_decompress", woff2Path, "-o", ttfPath],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0 and os.path.exists(ttfPath) and os.path.getsize(ttfPath) > 1000:
                return True
        except Exception:
            pass

    # Try Node.js woff2 package (Windows/cross-platform)
    if shutil.which("node"):
        try:
            script = f"""
const woff2 = require('woff2');
const fs = require('fs');
try {{
    const input = fs.readFileSync('{woff2Path}');
    const output = woff2.decompress(input);
    fs.writeFileSync('{ttfPath}', output);
}} catch(e) {{
    process.exit(1);
}}
"""
            result = subprocess.run(
                ["node", "-e", script],
                capture_output=True,
                timeout=30
            )
            if result.returncode == 0 and os.path.exists(ttfPath) and os.path.getsize(ttfPath) > 1000:
                return True
        except Exception:
            pass

    return False


def downloadFont(fontName: str, variant: str, tempDir: str) -> Optional[str]:
    """Download a font variant, trying multiple sources - tries both in parallel"""
    # Try both sources in parallel for speed
    with ThreadPoolExecutor(max_workers=2) as executor:
        githubFuture = executor.submit(tryGithubRepo, fontName, variant, tempDir)
        apiFuture = executor.submit(tryGoogleFontsApi, fontName, variant, tempDir)

        # Wait for first successful result
        for future in as_completed([githubFuture, apiFuture]):
            try:
                filePath = future.result()
                if filePath:
                    # Cancel the other future
                    if future == githubFuture:
                        apiFuture.cancel()
                    else:
                        githubFuture.cancel()

                    # If it's WOFF2, try to convert
                    if filePath.endswith('.woff2'):
                        ttfPath = filePath.replace('.woff2', '.ttf')
                        if convertWoff2ToTtf(filePath, ttfPath):
                            try:
                                os.remove(filePath)
                            except Exception:
                                pass
                            return ttfPath
                        else:
                            # Conversion failed, but return WOFF2 anyway
                            return filePath
                    return filePath
            except Exception:
                continue

    return None


def installFontFile(fontPath: str, installDir: str) -> bool:
    """Install a font file to the installation directory"""
    if not os.path.exists(fontPath):
        return False

    # Check if it's WOFF2
    if fontPath.endswith('.woff2'):
        printWarning("WOFF2 format cannot be directly installed")
        return False

    fontName = os.path.basename(fontPath)
    system = platform.system()

    if system == "Windows":
        # Windows: Try system Fonts folder first, fall back to installDir if no permissions
        systemFontsFolder = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        destination = None

        # Check if we can write to system fonts folder
        try:
            testFile = os.path.join(systemFontsFolder, '.font_install_test')
            try:
                with open(testFile, 'w') as f:
                    f.write('test')
                os.remove(testFile)
                # We have write access, use system folder
                destination = os.path.join(systemFontsFolder, fontName)
            except (PermissionError, OSError):
                # No write access, use installDir
                destination = os.path.join(installDir, fontName)
        except Exception:
            # Fall back to installDir
            destination = os.path.join(installDir, fontName)

        if os.path.exists(destination):
            return True  # Already installed

        os.makedirs(os.path.dirname(destination), exist_ok=True)

        try:
            # Copy font file
            shutil.copy2(fontPath, destination)

            # Try to register in registry if we installed to system folder
            if destination.startswith(systemFontsFolder):
                try:
                    import winreg
                    registryPath = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
                    fontRegistryName = fontName.replace('.ttf', '').replace('.otf', '').replace('-', ' ')

                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registryPath, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(key, fontRegistryName, 0, winreg.REG_SZ, fontName)
                    winreg.CloseKey(key)
                except (ImportError, PermissionError, Exception):
                    # Registry write might fail, but font copy should still work
                    pass

            return True
        except Exception as e:
            printError(f"Installation failed: {e}")
            return False
    else:
        # Linux/macOS: Install to user font directory
        destination = os.path.join(installDir, fontName)

        if os.path.exists(destination):
            return True  # Already installed

        os.makedirs(installDir, exist_ok=True)

        try:
            shutil.copy2(fontPath, destination)
            return True
        except Exception as e:
            printError(f"Installation failed: {e}")
            return False


def downloadFontVariant(fontName: str, variant: str, tempDir: str) -> Optional[Tuple[str, str, str]]:
    """Download a single font variant"""
    filePath = downloadFont(fontName, variant, tempDir)
    if filePath and os.path.exists(filePath):
        return (fontName, variant, filePath)
    return None


def convertFontFile(fontName: str, variant: str, filePath: str, tempDir: str) -> Optional[Tuple[str, str, str]]:
    """Convert a font file if needed (WOFF2 to TTF)"""
    if filePath.endswith('.woff2'):
        ttfPath = filePath.replace('.woff2', '.ttf')
        if convertWoff2ToTtf(filePath, ttfPath):
            try:
                os.remove(filePath)
            except Exception:
                pass
            return (fontName, variant, ttfPath)
        else:
            printWarning(f"⚠ {fontName} {variant}: WOFF2 conversion failed")
            return None
    return (fontName, variant, filePath)


def verifyFontInstalled(fontPath: str, installDir: str) -> bool:
    """Verify that a font file exists in the installation directory"""
    fontName = os.path.basename(fontPath)
    system = platform.system()

    if system == "Windows":
        # Check system fonts folder or installDir
        systemFontsFolder = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        systemDestination = os.path.join(systemFontsFolder, fontName)
        userDestination = os.path.join(installDir, fontName)
        return os.path.exists(systemDestination) or os.path.exists(userDestination)
    else:
        destination = os.path.join(installDir, fontName)
        return os.path.exists(destination)


def installFontVariant(fontName: str, variant: str, filePath: str, installDir: str, results: dict) -> Tuple[bool, str, str, Optional[str]]:
    """Install a single font variant - returns result tuple instead of printing"""
    if installFontFile(filePath, installDir):
        # Verify the font was actually installed
        if verifyFontInstalled(filePath, installDir):
            if printLock:
                with printLock:
                    results['installed'] += 1
            else:
                results['installed'] += 1
            return (True, fontName, variant, None)
        else:
            if printLock:
                with printLock:
                    results['failed'] += 1
            else:
                results['failed'] += 1
            return (False, fontName, variant, "verification failed")
    else:
        if printLock:
            with printLock:
                results['failed'] += 1
        else:
            results['failed'] += 1
        return (False, fontName, variant, "installation failed")


def refreshFontCache(installDir: str) -> None:
    """Refresh font cache (Linux/macOS)"""
    system = platform.system()
    if system == "Linux":
        try:
            subprocess.run(
                ["fc-cache", "-f", "-v", installDir],
                capture_output=True,
                timeout=30
            )
        except Exception:
            pass
    elif system == "Darwin":  # macOS
        # macOS doesn't need explicit cache refresh
        pass


def main() -> None:
    """Main function"""
    if len(sys.argv) < 3:
        safePrint(f"Usage: {sys.argv[0]} <configPath> <installDir> [variants...] [--dryRun]")
        safePrint(f"--dryRun: Show what would be downloaded/installed without actually doing it")
        sys.exit(1)

    # Parse arguments
    args = sys.argv[1:]
    dryRun = False
    if '--dryRun' in args:
        dryRun = True
        args.remove('--dryRun')

    configPath = args[0]
    installDir = args[1]
    variants = args[2:] if len(args) > 2 else ["Regular", "Bold", "Italic", "BoldItalic"]

    # Check admin rights first (before reading config)
    system = platform.system()
    hasAdmin = False
    if system == "Windows":
        systemFontsFolder = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        # Check if we can write to system folder
        try:
            testFile = os.path.join(systemFontsFolder, '.font_install_test')
            try:
                with open(testFile, 'w') as f:
                    f.write('test')
                os.remove(testFile)
                hasAdmin = True
            except (PermissionError, OSError):
                hasAdmin = False
        except Exception:
            hasAdmin = False

    # Read config
    try:
        with open(configPath, 'r', encoding='utf-8') as f:
            config = json.load(f)
        fontNames = config.get('googleFonts', [])
    except Exception as e:
        printError(f"Failed to read config: {e}")
        sys.exit(1)

    if not fontNames:
        printWarning("No fonts specified in configuration file.")
        sys.exit(0)

    printH2("Google Fonts Installation", dryRun=dryRun)
    printInfo(f"Found {len(fontNames)} font(s) in configuration file.")

    # Show install location
    if system == "Windows":
        if hasAdmin:
            if dryRun:
                printInfo(f"Would install to: {systemFontsFolder} (system folder)")
            else:
                printInfo(f"Installing to: {systemFontsFolder} (system folder)")
        else:
            if dryRun:
                printWarning(f"No admin access - would install to: {installDir}")
            else:
                printWarning(f"No admin access - installing to: {installDir}")
            if not dryRun:
                printWarning("(Run as Administrator to install system-wide)")
    else:
        if dryRun:
            printInfo(f"Would install to: {installDir}")
        else:
            printInfo(f"Installing to: {installDir}")

    safePrint("")

    if dryRun:
        printWarning("DRY RUN MODE: No files will be downloaded or installed")
        safePrint("")
        printInfo("Would process:")
        for fontName in fontNames:
            safePrint(f"- {fontName}: {', '.join(variants)}")
        safePrint("")
        printInfo(f"Total: {len(fontNames)} font(s) × {len(variants)} variant(s) = {len(fontNames) * len(variants)} font file(s)")
        sys.exit(0)

    # Start timer
    startTime = time.time()

    # Create temp directory
    tempDir = tempfile.mkdtemp(prefix='GoogleFonts_')

    # Results tracking
    results = {'installed': 0, 'skipped': 0, 'failed': 0}
    # Increase workers significantly for faster parallel processing
    maxWorkers = min(20, len(fontNames) * len(variants))  # More concurrent operations

    # Phase 1: Download all fonts in parallel
    printInfo(f"Phase 1: Downloading fonts (parallel, max {maxWorkers} workers)...")
    downloadedFiles = []
    downloadCount = 0
    totalDownloads = len(fontNames) * len(variants)

    with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
        downloadFutures = {
            executor.submit(downloadFontVariant, fontName, variant, tempDir): (fontName, variant)
            for fontName in fontNames
            for variant in variants
        }

        for future in as_completed(downloadFutures):
            fontName, variant = downloadFutures[future]
            try:
                result = future.result()
                downloadCount += 1
                if result:
                    downloadedFiles.append(result)
                    printSuccess(f"Downloading font {downloadCount}/{totalDownloads}: ✓ {fontName} {variant}")
                else:
                    # Don't show failures for every variant to reduce noise
                    pass
            except Exception as e:
                downloadCount += 1
                printError(f"Downloading font {downloadCount}/{totalDownloads}: ✗ {fontName} {variant}: {e}")

    printSuccess(f"Downloaded {len(downloadedFiles)}/{totalDownloads} font file(s)")
    safePrint("")

    if not downloadedFiles:
        printWarning("No fonts were downloaded. Exiting.")
        shutil.rmtree(tempDir, ignore_errors=True)
        sys.exit(0)

    # Phase 2: Convert WOFF2 files to TTF in parallel
    woff2Files = [f for f in downloadedFiles if f[2].endswith('.woff2')]
    if woff2Files:
        printInfo(f"Phase 2: Converting fonts (WOFF2 → TTF, parallel, max {maxWorkers} workers)...")
        convertedFiles = []
        convertCount = 0
        totalConverts = len(downloadedFiles)

        with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
            convertFutures = {
                executor.submit(convertFontFile, fontName, variant, filePath, tempDir): (fontName, variant, filePath)
                for fontName, variant, filePath in downloadedFiles
            }

            for future in as_completed(convertFutures):
                fontName, variant, filePath = convertFutures[future]
                convertCount += 1
                try:
                    result = future.result()
                    if result:
                        convertedFiles.append(result)
                        if filePath.endswith('.woff2'):
                            printSuccess(f"[{convertCount}/{totalConverts}] ✓ Converted {fontName} {variant}")
                    else:
                        # Non-WOFF2 files pass through
                        convertedFiles.append((fontName, variant, filePath))
                except Exception as e:
                    printError(f"[{convertCount}/{totalConverts}] ✗ Error converting {fontName} {variant}: {e}")

        printSuccess(f"Converted {len([f for f in convertedFiles if f[2].endswith('.ttf')])} font file(s)")
        safePrint("")
    else:
        # No WOFF2 files, just pass through
        convertedFiles = downloadedFiles
        printInfo("Phase 2: No WOFF2 files to convert, skipping...")
        safePrint("")

    # Phase 3: Install all fonts in parallel
    printInfo("Phase 3: Installing fonts...")

    # Group by font name for better output
    fontsByName = {}
    for fontName, variant, filePath in convertedFiles:
        if fontName not in fontsByName:
            fontsByName[fontName] = []
        fontsByName[fontName].append((variant, filePath))

    # Collect all installation tasks
    installTasks = []
    for fontName, variantsList in fontsByName.items():
        for variant, filePath in variantsList:
            installTasks.append((fontName, variant, filePath))

    totalInstalls = len(installTasks)
    installCount = 0
    installResults = []

    with ThreadPoolExecutor(max_workers=maxWorkers) as executor:
        installFutures = {
            executor.submit(installFontVariant, fontName, variant, filePath, installDir, results): (fontName, variant, filePath)
            for fontName, variant, filePath in installTasks
        }

        for future in as_completed(installFutures):
            fontName, variant, filePath = installFutures[future]
            installCount += 1
            try:
                result = future.result()
                installResults.append(result)
                if result[0]:  # Success
                    printSuccess(f"Installing font {installCount}/{totalInstalls}: ✓ {fontName} {variant}")
                else:
                    printError(f"Installing font {installCount}/{totalInstalls}: ✗ {fontName} {variant}")
            except Exception as e:
                installResults.append((False, fontName, variant, str(e)))
                printError(f"Installing font {installCount}/{totalInstalls}: ✗ {fontName} {variant}: {e}")

        # Mark fonts with no successful installs as skipped
        for fontName in fontNames:
            if fontName not in fontsByName:
                if printLock:
                    with printLock:
                        results['skipped'] += 1
                else:
                    results['skipped'] += 1
                installResults.append((False, fontName, None, "no variants available"))

    # Group and display results
    successful = [r for r in installResults if r[0]]
    failed = [r for r in installResults if not r[0]]

    if successful:
        printSuccess("Successfully installed:")
        for success, fontName, variant, error in sorted(successful, key=lambda x: (x[1], x[2])):
            printSuccess(f"{fontName} {variant} (verified)")
        safePrint("")

    if failed:
        printError("Failed to install:")
        for success, fontName, variant, error in sorted(failed, key=lambda x: (x[1], x[2] or "")):
            if variant:
                printError(f"{fontName} {variant}: {error}")
            else:
                printWarning(f"{fontName}: {error}")
        safePrint("")

    # End timer
    endTime = time.time()
    elapsedTime = endTime - startTime

    # Cleanup
    printInfo("Cleaning up downloaded files...")
    try:
        shutil.rmtree(tempDir)
        printSuccess("Temporary files removed successfully")
    except Exception:
        pass

    safePrint("")

    # Refresh font cache
    refreshFontCache(installDir)

    # Summary
    printInfo("Summary:")
    printSuccess(f"Installed: {results['installed']} font file(s)")
    if results['skipped'] > 0:
        printWarning(f"Skipped: {results['skipped']} font(s)")
    if results['failed'] > 0:
        printError(f"Failed: {results['failed']} font file(s)")

    # Format elapsed time
    if elapsedTime < 60:
        timeStr = f"{elapsedTime:.2f} seconds"
    elif elapsedTime < 3600:
        minutes = int(elapsedTime // 60)
        seconds = elapsedTime % 60
        timeStr = f"{minutes} minute(s) {seconds:.2f} seconds"
    else:
        hours = int(elapsedTime // 3600)
        minutes = int((elapsedTime % 3600) // 60)
        seconds = elapsedTime % 60
        timeStr = f"{hours} hour(s) {minutes} minute(s) {seconds:.2f} seconds"

    printInfo(f"Total time: {timeStr}")
    safePrint("")
    printSuccess("Font installation complete!")
    printWarning("Note: You may need to restart applications for new fonts to appear.")


if __name__ == "__main__":
    main()
