#!/usr/bin/env python3
"""
Repository tidy utility implemented in Python with predictable line endings.

Features:
- Converts tabs to four spaces.
- Trims trailing whitespace.
- Removes trailing blank lines.
- Forces CRLF for `.ps1`, `.json`, and `.md`, while keeping `.sh` files LF.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


DEFAULT_EXTENSIONS = [".ps1", ".sh", ".json", ".md"]
CRLF_EXTENSIONS = {".ps1", ".json", ".md"}


def parseArguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tidies files while preserving line endings.")
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
        default=DEFAULT_EXTENSIONS,
        help="File extensions to include when scanning a directory.",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
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


def tidyContent(text: str, preferredNewline: str | None = None) -> tuple[str, TidyStats]:
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

    for line in lines:
        if "\t" in line:
            tabCount += line.count("\t")
            line = line.replace("\t", "    ")

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


class Colour:
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    CYAN = "\033[0;36m"
    RED = "\033[0;31m"
    RESET = "\033[0m"


def colourise(text: str, code: str, enable: bool) -> str:
    if not enable:
        return text
    return f"{code}{text}{Colour.RESET}"


def gatherFiles(root: Path, extensionsLower: set[str]) -> Iterable[Path]:
    for candidate in root.rglob("*"):
        if candidate.is_file() and candidate.suffix.lower() in extensionsLower:
            yield candidate


def newlineForFile(path: Path, extensionsLower: set[str]) -> str | None:
    suffix = path.suffix.lower()
    if suffix in CRLF_EXTENSIONS:
        return "\r\n"
    if suffix == ".sh":
        return "\n"
    if suffix in extensionsLower:
        return None
    return None


def tidyFile(path: Path, dryRun: bool, preferredNewline: str | None) -> TidyStats | None:
    try:
        originalText = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        sys.stderr.write(f"Skipping non-UTF-8 file: {path}\n")
        return None

    newText, stats = tidyContent(originalText, preferredNewline)

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
    enableColour = sys.stdout.isatty()
    extensionsLower = {ext.lower() for ext in args.extensions}

    try:
        targets, _ = determineTargets(args, extensionsLower)
    except FileNotFoundError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    if not targets:
        print(colourise("No files found to process.", Colour.YELLOW, enableColour))
        return 0

    fileCount = 0
    modifiedCount = 0
    totalTabCount = 0
    totalWhitespaceCount = 0

    for filePath in targets:
        fileCount += 1
        preferredNewline = newlineForFile(filePath, extensionsLower)
        stats = tidyFile(filePath, args.dryRun, preferredNewline)
        if stats is None:
            continue

        if args.dryRun:
            if (
                stats.tabCount
                or stats.whitespaceLineCount
                or stats.removedTrailingBlanks
            ):
                print(colourise(f"Would tidy: {filePath}", Colour.CYAN, enableColour))
                if stats.tabCount:
                    print(
                        colourise(
                            f"  Would convert {stats.tabCount} tab(s) to spaces",
                            Colour.YELLOW,
                            enableColour,
                        )
                    )
                if stats.whitespaceLineCount:
                    print(
                        colourise(
                            f"  Would trim trailing whitespace from {stats.whitespaceLineCount} line(s)",
                            Colour.YELLOW,
                            enableColour,
                        )
                    )
                if stats.removedTrailingBlanks:
                    print(
                        colourise(
                            "  Would remove trailing blank lines",
                            Colour.YELLOW,
                            enableColour,
                        )
                    )
            else:
                print(colourise(f"File is already tidy: {filePath}", Colour.GREEN, enableColour))
        else:
            if stats.modified:
                modifiedCount += 1
                print(colourise(f"Tidied: {filePath}", Colour.GREEN, enableColour))
                if stats.tabCount:
                    print(
                        colourise(
                            f"  Converted {stats.tabCount} tab(s) to spaces",
                            Colour.GREEN,
                            enableColour,
                        )
                    )
                if stats.whitespaceLineCount:
                    print(
                        colourise(
                            f"  Trimmed trailing whitespace from {stats.whitespaceLineCount} line(s)",
                            Colour.GREEN,
                            enableColour,
                        )
                    )
                if stats.removedTrailingBlanks:
                    print(
                        colourise(
                            "  Removed trailing blank lines",
                            Colour.GREEN,
                            enableColour,
                        )
                    )
            else:
                print(colourise(f"File is already tidy: {filePath}", Colour.GREEN, enableColour))

        totalTabCount += stats.tabCount
        totalWhitespaceCount += stats.whitespaceLineCount

    print()

    if args.dryRun:
        print(
            colourise(
                f"DRY RUN: Would process {fileCount} file(s)",
                Colour.YELLOW,
                enableColour,
            )
        )
        if totalTabCount:
            print(
                colourise(
                    f"  Would convert {totalTabCount} tab(s) to spaces",
                    Colour.YELLOW,
                    enableColour,
                )
            )
        if totalWhitespaceCount:
            print(
                colourise(
                    f"  Would trim trailing whitespace from {totalWhitespaceCount} line(s)",
                    Colour.YELLOW,
                    enableColour,
                )
            )
    else:
        print(
            colourise(
                f"Processed {fileCount} file(s)",
                Colour.CYAN,
                enableColour,
            )
        )
        if modifiedCount:
            print(
                colourise(
                    f"Modified {modifiedCount} file(s)",
                    Colour.GREEN,
                    enableColour,
                )
            )
            if totalTabCount:
                print(
                    colourise(
                        f"  Converted {totalTabCount} tab(s) to spaces",
                        Colour.GREEN,
                        enableColour,
                    )
                )
            if totalWhitespaceCount:
                print(
                    colourise(
                        f"  Trimmed trailing whitespace from {totalWhitespaceCount} line(s)",
                        Colour.GREEN,
                        enableColour,
                    )
                )
        else:
            print(colourise("No files needed tidying. All files are clean!", Colour.GREEN, enableColour))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


