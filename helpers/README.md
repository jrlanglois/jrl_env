# Helpers

Utility scripts and shared modules for keeping the repo consistent and DRY.

## Overview

This directory contains formatting and maintenance scripts that help maintain code quality and consistency across the repository. All Python scripts import from `common/common.py` for shared logging and utilities.

## Shared Modules

### `common/common.py`

Single entry point for all common utilities:

- **`common/common.py`**: Python entry point - imports all common utilities and modules

All helper scripts import from `common/common.py` for consistent logging and utilities.

See [`common/README.md`](../common/README.md) for detailed documentation on common modules.

## Formatting Scripts

| Script | Purpose | Typical command |
| --- | --- | --- |
| `tidy.py` | Clean files (tabs → spaces, trim whitespace, enforce CRLF on `.ps1/.json/.md` and LF on `.sh/.py`) | `python3 helpers/tidy.py --file file.sh` or `python3 helpers/tidy.py --path .` |
| `convertToAllman.py` | Enforce Allman braces + inline `if …; then` style | `python3 helpers/convertToAllman.py` |
| `formatRepo.py` | Run the whole formatting pipeline (Allman + tidy) | `python3 helpers/formatRepo.py` |
| `validateJson.py` | Validate JSON syntax and optional required fields | `python3 helpers/validateJson.py config.json` |

All helper scripts support `--help` and `--quiet` flags. Use `--help` for detailed usage information.

## Whitespace tidy

### `tidy.py`

- Converts tabs to four spaces
- Trims trailing whitespace and blank line spam
- Supports dry runs via `--dryRun` flag
- Forces CRLF endings for `.ps1`, `.json`, and `.md`, while keeping `.sh` and `.py` files LF
- Processes `.ps1`, `.sh`, `.json`, `.md`, and `.py` files by default
- Can process a single file or an entire directory tree

**Single file:**

```bash
python3 helpers/tidy.py --file path/to/file.sh [--dryRun] [--quiet]
```

**Entire repository or directory:**

```bash
python3 helpers/tidy.py --path . [--dryRun] [--quiet]
python3 helpers/tidy.py --path src/scripts [--dryRun] [--quiet]
```

Use `--quiet` to only show final success/failure message.

## Brace formatting

### `convertToAllman.py`

- Converts Bash functions to Allman braces
- Splits `} else {` blocks
- Keeps `if/while/for` keywords inline (e.g., `if [ … ]; then`)
- Supports dry runs and optional `.bak` backups

```bash
python3 helpers/convertToAllman.py --dryRun [--quiet]
python3 helpers/convertToAllman.py --path macos [--quiet]
python3 helpers/convertToAllman.py --createBackup [--quiet]
```

Use `--quiet` to only show final success/failure message.

## Full pipeline

### `formatRepo.py`

Runs the Allman conversion followed by `tidy.py` so the repo ends up idempotently formatted:

```bash
python3 helpers/formatRepo.py [--dryRun] [--quiet]
```

Supports `--dryRun` to preview changes and `--quiet` to only show final success/failure message.
