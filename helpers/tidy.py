#!/usr/bin/env python3
"""
Repository tidy utility implemented in Python with predictable line endings.

Features:
- Converts tabs to spaces (4 spaces for most files, 2 spaces for YAML).
- Normalises YAML indentation to 2 spaces.
- Trims trailing whitespace.
- Removes trailing blank lines.
- Forces CRLF for `.ps1`, `.json`, and `.md`, while keeping `.sh`, `.py`, `.yml`, and `.yaml` files LF.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

# Import shared logging utilities from common
scriptDir = os.path.dirname(os.path.abspath(__file__))
commonDir = os.path.join(os.path.dirname(scriptDir), "common")
sys.path.insert(0, os.path.dirname(commonDir))
from common.common import Colours, colourise
from common.core.logging import setVerbosityFromArgs, getVerbosity, Verbosity


defaultExtensions = [".ps1", ".sh", ".json", ".md", ".py", ".yml", ".yaml"]
crlfExtensions = {".ps1", ".json", ".md"}


def parseArguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tidies files while preserving line endings.",
        epilog=(
            "Intent: Clean up files by converting tabs to spaces, trimming whitespace,\n"
            "and enforcing proper line endings (CRLF for .ps1/.json/.md, LF for .sh/.py/.yml/.yaml).\n\n"
            "Examples:\n"
            "  python3 helpers/tidy.py --file script.sh\n"
            "  python3 helpers/tidy.py --path src/ --extensions .py .sh\n"
            "  python3 helpers/tidy.py --dryRun"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    defaultRoot = Path(__file__).resolve().parents[1]

    parser.add_argument(
        "-p",
        "--path",
        dest="path",
        help="Directory to tidy (defaults to repository root).",
    )
    parser.add_argument(
        "--file",
        dest="files",
        action="append",
        help="Specific file to tidy. Can be specified multiple times.",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        nargs="+",
        default=defaultExtensions,
        help="File extensions to include when scanning a directory.",
    )
    parser.add_argument(
        "-d",
        "--dryRun",
        dest="dryRun",
        action="store_true",
        help="Preview changes without modifying files.",
    )
    parser.add_argument(
        "positionalPath",
        nargs="?",
        help="Optional path argument for backward compatibility.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        action="store_true",
        help="Only show final success/failure message.",
    )
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Show verbose output including per-file status messages.",
    )

    parser.set_defaults(defaultRoot=str(defaultRoot))
    return parser.parse_args()


def detectNewlineStyle(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    if "\r" in text:
        return "\r"
    if "\n" in text:
        return "\n"
    return os.linesep


@dataclass
class TidyStats:
    modified: bool
    tabCount: int
    whitespaceLineCount: int
    removedTrailingBlanks: bool


def normaliseNewlines(text: str) -> str:
    if not text:
        return text
    return text.replace("\r\n", "\n").replace("\r", "\n")


def rebuildWithNewlines(text: str, newlineStyle: str) -> str:
    if newlineStyle == "\n":
        return text
    if newlineStyle == "\r\n":
        return text.replace("\n", "\r\n")
    if newlineStyle == "\r":
        return text.replace("\n", "\r")
    return text


def tidyContent(text: str, preferredNewline: str | None = None, isYaml: bool = False) -> tuple[str, TidyStats]:
    newlineStyle = preferredNewline or detectNewlineStyle(text)
    normalised = normaliseNewlines(text)
    hadTrailingNewline = normalised.endswith("\n")
    lines: List[str]

    if normalised:
        lines = normalised.split("\n")
        if hadTrailingNewline:
            lines = lines[:-1]
    else:
        lines = []

    tabCount = 0
    whitespaceLineCount = 0
    processedLines: List[str] = []
    indentSize = 2 if isYaml else 4

    for line in lines:
        if "\t" in line:
            tabCount += line.count("\t")
            line = line.replace("\t", " " * indentSize)

        # For YAML files, normalise indentation to 2 spaces
        if isYaml and line and not line.strip().startswith("#"):
            # Count leading spaces
            leadingSpaces = len(line) - len(line.lstrip())
            if leadingSpaces > 0:
                # Normalise to multiples of 2 spaces (round down odd numbers)
                normalisedIndent = (leadingSpaces // 2) * 2
                line = " " * normalisedIndent + line.lstrip()

        trimmedLine = line.rstrip()
        if trimmedLine != line:
            whitespaceLineCount += 1
        processedLines.append(trimmedLine)

    removedTrailingBlanks = False
    while processedLines and processedLines[-1] == "":
        processedLines.pop()
        removedTrailingBlanks = True

    rebuilt = "\n".join(processedLines)
    if hadTrailingNewline:
        rebuilt = f"{rebuilt}\n" if rebuilt else "\n"

    rebuiltWithNewlines = rebuildWithNewlines(rebuilt, newlineStyle)

    modified = rebuiltWithNewlines != text
    stats = TidyStats(
        modified=modified,
        tabCount=tabCount,
        whitespaceLineCount=whitespaceLineCount,
        removedTrailingBlanks=removedTrailingBlanks,
    )

    return rebuiltWithNewlines, stats


# Colour class and colourise function now imported from logging module


def gatherFiles(root: Path, extensionsLower: set[str]) -> Iterable[Path]:
    for candidate in root.rglob("*"):
        if candidate.is_file() and candidate.suffix.lower() in extensionsLower:
            yield candidate


def newlineForFile(path: Path, extensionsLower: set[str]) -> str | None:
    suffix = path.suffix.lower()
    if suffix in crlfExtensions:
        return "\r\n"
    if suffix == ".sh":
        return "\n"
    if suffix in extensionsLower:
        return None
    return None


def tidyFile(path: Path, dryRun: bool, preferredNewline: str | None, isYaml: bool = False) -> TidyStats | None:
    try:
        # Read file in binary mode to preserve exact line endings, then decode.
        # This prevents Python from normalising CRLF to LF during read.
        originalBytes = path.read_bytes()
        originalText = originalBytes.decode("utf-8")
    except UnicodeDecodeError:
        sys.stderr.write(f"Skipping non-UTF-8 file: {path}\n")
        return None

    newText, stats = tidyContent(originalText, preferredNewline, isYaml)

    if stats.modified and not dryRun:
        with path.open("w", encoding="utf-8", newline="") as destination:
            destination.write(newText)

    return stats


def determineTargets(args: argparse.Namespace, extensionsLower: set[str]) -> tuple[list[Path], bool]:
    if args.files:
        files = [Path(file).resolve() for file in args.files]
        return files, True

    chosenPath = args.path or args.positionalPath or args.defaultRoot
    root = Path(chosenPath).resolve()

    if root.is_file():
        return [root], True

    if not root.exists():
        raise FileNotFoundError(f"Path not found: {root}")

    return list(gatherFiles(root, extensionsLower)), False


def main() -> int:
    args = parseArguments()
    setVerbosityFromArgs(quiet=args.quiet, verbose=args.verbose)
    enableColour = sys.stdout.isatty()
    extensionsLower = {ext.lower() for ext in args.extensions}

    try:
        targets, _ = determineTargets(args, extensionsLower)
    except FileNotFoundError as exc:
        if getVerbosity() == Verbosity.quiet:
            print("Failure")
        else:
            sys.stderr.write(f"{exc}\n")
        return 1

    if not targets:
        if getVerbosity() == Verbosity.quiet:
            print("Success")
        else:
            print(colourise("No files found to process.", Colours.YELLOW, enableColour))
        return 0

    fileCount = 0
    modifiedCount = 0
    totalTabCount = 0
    totalWhitespaceCount = 0

    for filePath in targets:
        fileCount += 1
        preferredNewline = newlineForFile(filePath, extensionsLower)
        isYaml = filePath.suffix.lower() in {".yml", ".yaml"}
        stats = tidyFile(filePath, args.dryRun, preferredNewline, isYaml)
        if stats is None:
            continue

        # Skip all output in quiet mode
        if getVerbosity() == Verbosity.quiet:
            if stats.modified:
                modifiedCount += 1
            totalTabCount += stats.tabCount
            totalWhitespaceCount += stats.whitespaceLineCount
            continue

        if args.dryRun:
            if (
                stats.tabCount
                or stats.whitespaceLineCount
                or stats.removedTrailingBlanks
            ):
                print(colourise(f"Would tidy: {filePath}", Colours.CYAN, enableColour))
                if stats.tabCount:
                    print(
                        colourise(
                            f"  Would convert {stats.tabCount} tab(s) to spaces",
                            Colours.YELLOW,
                            enableColour,
                        )
                    )
                if stats.whitespaceLineCount:
                    print(
                        colourise(
                            f"  Would trim trailing whitespace from {stats.whitespaceLineCount} line(s)",
                            Colours.YELLOW,
                            enableColour,
                        )
                    )
                if stats.removedTrailingBlanks:
                    print(
                        colourise(
                            "  Would remove trailing blank lines",
                            Colours.YELLOW,
                            enableColour,
                        )
                    )
            else:
                if getVerbosity() == Verbosity.verbose:
                    print(colourise(f"File is already tidy: {filePath}", Colours.GREEN, enableColour))
        else:
            if stats.modified:
                modifiedCount += 1
                print(colourise(f"Tidied: {filePath}", Colours.GREEN, enableColour))
                if stats.tabCount:
                    print(
                        colourise(
                            f"  Converted {stats.tabCount} tab(s) to spaces",
                            Colours.GREEN,
                            enableColour,
                        )
                    )
                if stats.whitespaceLineCount:
                    print(
                        colourise(
                            f"  Trimmed trailing whitespace from {stats.whitespaceLineCount} line(s)",
                            Colours.GREEN,
                            enableColour,
                        )
                    )
                if stats.removedTrailingBlanks:
                    print(
                        colourise(
                            "  Removed trailing blank lines",
                            Colours.GREEN,
                            enableColour,
                        )
                    )
            else:
                if getVerbosity() == Verbosity.verbose:
                    print(colourise(f"File is already tidy: {filePath}", Colours.GREEN, enableColour))

        totalTabCount += stats.tabCount
        totalWhitespaceCount += stats.whitespaceLineCount

    if getVerbosity() != Verbosity.quiet:
        print()

    if getVerbosity() != Verbosity.quiet:
        if args.dryRun:
            print(
                colourise(
                    f"DRY RUN: Would process {fileCount} file(s)",
                    Colours.YELLOW,
                    enableColour,
                )
            )
            if totalTabCount:
                print(
                    colourise(
                        f"  Would convert {totalTabCount} tab(s) to spaces",
                        Colours.YELLOW,
                        enableColour,
                    )
                )
            if totalWhitespaceCount:
                print(
                    colourise(
                        f"  Would trim trailing whitespace from {totalWhitespaceCount} line(s)",
                        Colours.YELLOW,
                        enableColour,
                    )
                )
        else:
            extensionsList = ', '.join(args.extensions)
            print(
                colourise(
                    f"Processed {fileCount} file(s) ({extensionsList})",
                    Colours.CYAN,
                    enableColour,
                )
            )
            if modifiedCount:
                print(
                    colourise(
                        f"Modified {modifiedCount} file(s)",
                        Colours.GREEN,
                        enableColour,
                    )
                )
                if totalTabCount:
                    print(
                        colourise(
                            f"  Converted {totalTabCount} tab(s) to spaces",
                            Colours.GREEN,
                            enableColour,
                        )
                    )
                if totalWhitespaceCount:
                    print(
                        colourise(
                            f"  Trimmed trailing whitespace from {totalWhitespaceCount} line(s)",
                            Colours.GREEN,
                            enableColour,
                        )
                    )
            else:
                print(colourise("No files needed tidying. All files are clean!", Colours.GREEN, enableColour))

    # Final success/failure message (always show in quiet mode)
    if getVerbosity() == Verbosity.quiet:
        print("Success")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
