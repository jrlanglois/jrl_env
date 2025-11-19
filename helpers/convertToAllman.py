#!/usr/bin/env python3
# Utility script to convert Bash files to an Allman brace style

import argparse
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

# Import shared logging utilities from common
scriptDir = os.path.dirname(os.path.abspath(__file__))
commonDir = os.path.join(os.path.dirname(scriptDir), "common")
sys.path.insert(0, os.path.dirname(commonDir))
from common.common import printSection, printInfo, printSuccess, printWarning
from common.core.logging import setVerbosityFromArgs, getVerbosity, Verbosity


def parseArguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Bash files to Allman brace style.",
        epilog=(
            "Intent: Enforce Allman brace style in Bash scripts by converting function braces\n"
            "and else blocks to separate lines, and enforcing inline control keywords.\n\n"
            "Examples:\n"
            "  python3 helpers/convertToAllman.py\n"
            "  python3 helpers/convertToAllman.py --path scripts/ --extensions .sh .bash\n"
            "  python3 helpers/convertToAllman.py --dryRun"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    defaultRoot = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--path",
        default=str(defaultRoot),
        help="Root directory to process (defaults to repository root).",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".sh"],
        help="File extensions to process (defaults to .sh).",
    )
    parser.add_argument(
        "--dryRun",
        action="store_true",
        help="Preview changes without modifying files.",
    )
    parser.add_argument(
        "--createBackup",
        action="store_true",
        help="Create a .bak backup before modifying any file.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show final success/failure message.",
    )
    return parser.parse_args()


def findShellFiles(rootPath: Path | str, extensions: list[str]) -> Iterator[Path]:
    for root, _, files in os.walk(rootPath):
        for name in files:
            path = Path(root) / name
            if path.suffix in extensions:
                yield path


def convertContent(content: str) -> tuple[str, dict[str, Any]]:
    stats: dict[str, Any] = {
        "changed": False,
        "functionBraceUpdates": 0,
        "elseBraceUpdates": 0,
        "inlineIfUpdates": 0,
        "inlineWhileUpdates": 0,
        "inlineForUpdates": 0,
    }

    functionPattern = re.compile(
        r"^(\s*(?:function\s+)?[a-zA-Z_][\w]*\s*\(\))[ \t]*\{", re.MULTILINE
    )

    def replaceFunction(match):
        stats["functionBraceUpdates"] += 1
        header = match.group(1).rstrip()
        return f"{header}\n{{"

    content, functionCount = functionPattern.subn(replaceFunction, content)

    elsePattern = re.compile(r"\}[ \t]*else[ \t]*\{")
    content, elseCount = elsePattern.subn("}\nelse\n{", content)

    stats["elseBraceUpdates"] = elseCount

    # Enforce inline control keywords (if/while/for ...; then/do)
    inlineIfPattern = re.compile(r"([ \t]*if[^\n]*?)\n[ \t]*then")

    def replaceInlineIf(match):
        return f"{match.group(1)}; then"

    content, ifCount = inlineIfPattern.subn(replaceInlineIf, content)
    stats["inlineIfUpdates"] = ifCount

    inlineWhilePattern = re.compile(r"([ \t]*while[^\n]*?)\n[ \t]*do")

    def replaceInlineWhile(match):
        return f"{match.group(1)}; do"

    content, whileCount = inlineWhilePattern.subn(replaceInlineWhile, content)
    stats["inlineWhileUpdates"] = whileCount

    inlineForPattern = re.compile(r"([ \t]*for[^\n]*?)\n[ \t]*do")

    def replaceInlineFor(match):
        return f"{match.group(1)}; do"

    content, forCount = inlineForPattern.subn(replaceInlineFor, content)
    stats["inlineForUpdates"] = forCount
    stats["changed"] = any(
        count > 0
        for count in (
            functionCount,
            elseCount,
            ifCount,
            whileCount,
            forCount,
        )
    )

    return content, stats


def convertFile(filePath: Path, dryRun: bool = False, createBackup: bool = False) -> dict[str, Any]:
    text = filePath.read_text(encoding="utf-8")
    newText, stats = convertContent(text)

    if not stats["changed"]:
        return stats

    if dryRun:
        return stats

    if createBackup:
        backupPath = filePath.with_suffix(filePath.suffix + ".bak")
        backupPath.write_text(text, encoding="utf-8")

    filePath.write_text(newText, encoding="utf-8")
    return stats


def main() -> None:
    args = parseArguments()
    setVerbosityFromArgs(quiet=args.quiet, verbose=False)

    rootPath = Path(args.path).resolve()
    shellFiles = list(findShellFiles(rootPath, args.extensions))

    if not shellFiles:
        if getVerbosity() == Verbosity.quiet:
            print("Failure")
        else:
            print("No matching files found.")
        return

    totalChanged = 0
    totalFunctionUpdates = 0
    totalElseUpdates = 0
    totalIfUpdates = 0
    totalWhileUpdates = 0
    totalForUpdates = 0

    for filePath in shellFiles:
        stats = convertFile(filePath, dryRun=args.dryRun, createBackup=args.createBackup)
        if stats["changed"]:
            totalChanged += 1
            totalFunctionUpdates += stats["functionBraceUpdates"]
            totalElseUpdates += stats["elseBraceUpdates"]
            totalIfUpdates += stats["inlineIfUpdates"]
            totalWhileUpdates += stats["inlineWhileUpdates"]
            totalForUpdates += stats["inlineForUpdates"]
            status = "[DRY RUN]" if args.dryRun else "[UPDATED]"
            print(
                f"{status} {filePath} "
                f"(functions: {stats['functionBraceUpdates']}, "
                f"else: {stats['elseBraceUpdates']}, "
                f"if: {stats['inlineIfUpdates']}, "
                f"while: {stats['inlineWhileUpdates']}, "
                f"for: {stats['inlineForUpdates']})"
            )

    # Final success/failure message (always show in quiet mode)
    if getVerbosity() == Verbosity.quiet:
        print("Success")
        return

    summaryHeader = "DRY RUN SUMMARY" if args.dryRun else "UPDATE SUMMARY"
    print()
    printSection(summaryHeader)
    printInfo(f"Processed files: {len(shellFiles)}")
    printInfo(f"Files changed : {totalChanged}")
    printInfo(f"Function braces updated: {totalFunctionUpdates}")
    printInfo(f"Else braces updated    : {totalElseUpdates}")
    printInfo(f"Inline if updates      : {totalIfUpdates}")
    printInfo(f"Inline while updates   : {totalWhileUpdates}")
    printInfo(f"Inline for updates     : {totalForUpdates}")


if __name__ == "__main__":
    main()
