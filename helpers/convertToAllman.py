#!/usr/bin/env python3
# Utility script to convert Bash files to an Allman brace style

import argparse
import os
import re
from pathlib import Path


def parseArguments():
    parser = argparse.ArgumentParser(
        description="Convert Bash files to Allman brace style."
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
    return parser.parse_args()


def findShellFiles(rootPath, extensions):
    for root, _, files in os.walk(rootPath):
        for name in files:
            path = Path(root) / name
            if path.suffix in extensions:
                yield path


def convertContent(content):
    stats = {
        "changed": False,
        "functionBraceUpdates": 0,
        "elseBraceUpdates": 0,
        "inlineIfUpdates": 0,
        "inlineWhileUpdates": 0,
        "inlineForUpdates": 0,
    }

    functionPattern = re.compile(
        r"^(\s*(?:function\s+)?[a-zA-Z_][\w]*\s*\(\))\s*\{", re.MULTILINE
    )

    def replaceFunction(match):
        stats["functionBraceUpdates"] += 1
        header = match.group(1).rstrip()
        return f"{header}\n{{"

    content, functionCount = functionPattern.subn(replaceFunction, content)

    elsePattern = re.compile(r"\}\s*else\s*\{")
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


def convertFile(filePath, dryRun=False, createBackup=False):
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


def main():
    args = parseArguments()
    rootPath = Path(args.path).resolve()
    shellFiles = list(findShellFiles(rootPath, args.extensions))

    if not shellFiles:
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

    summaryHeader = "DRY RUN SUMMARY" if args.dryRun else "UPDATE SUMMARY"
    print(f"\n=== {summaryHeader} ===")
    print(f"Processed files: {len(shellFiles)}")
    print(f"Files changed : {totalChanged}")
    print(f"Function braces updated: {totalFunctionUpdates}")
    print(f"Else braces updated    : {totalElseUpdates}")
    print(f"Inline if updates      : {totalIfUpdates}")
    print(f"Inline while updates   : {totalWhileUpdates}")
    print(f"Inline for updates     : {totalForUpdates}")


if __name__ == "__main__":
    main()

