# Helpers

Utility scripts and shared modules for keeping the repo consistent and DRY.

## Shared Modules

### `utilities.sh`
Generic Bash utility functions used across the codebase:
- **`sourceIfExists(filePath)`**: Safely source a file if it exists, otherwise echo an error to stderr. Used throughout all `.sh` files to prevent failures when optional files are missing.

### `logging.sh`
Shared Bash logging functions for consistent output formatting. All scripts should use these instead of raw `echo` statements:
- **`logInfo(message)`**: Print an info message in cyan
- **`logSuccess(message)`**: Print a success message with green checkmark
- **`logError(message)`**: Print an error message with red cross
- **`logWarning(message)`**: Print a warning message with yellow warning symbol
- **`logNote(message)`**: Print a note in yellow
- **`logSection(message)`**: Print a section header in cyan with `===` borders

**Note**: Requires `common/colours.sh` to be sourced first.

### `logging.py`
Shared Python logging functions for consistent output formatting in Python scripts:
- **`printInfo(message)`**: Print an info message in cyan
- **`printSuccess(message)`**: Print a success message in green
- **`printError(message)`**: Print an error message in red
- **`printWarning(message)`**: Print a warning message in yellow
- **`printSection(message)`**: Print a section header in cyan with `===` borders
- **`safePrint(*args, **kwargs)`**: Thread-safe print function (uses a lock)
- **`colourise(text, code, enable)`**: Apply ANSI colour codes to text if enabled

## Formatting Scripts

At a glance:

| Script | Purpose | Typical command |
| --- | --- | --- |
| `tidy.py` (via `tidy.ps1` / `tidy.sh`) | Clean a single file (tabs → spaces, trim whitespace, enforce CRLF on `.ps1/.json/.md` and LF on `.sh`) | `./helpers/tidy.sh file.sh` |
| `tidyRepo.py` (via `tidyRepo.ps1` / `tidyRepo.sh`) | Clean every file under a path | `./helpers/tidyRepo.sh --dry-run` |
| `convertToAllman.py` | Enforce Allman braces + inline `if …; then` style | `python helpers/convertToAllman.py` |
| `formatRepo.sh` | Run the whole formatting pipeline (Allman + tidy) | `./helpers/formatRepo.sh` |

All helper scripts use Allman-style control blocks and camelCase identifiers for consistency.

## Whitespace tidy

### `tidy.py` (via `tidy.ps1` / `tidy.sh`)

- Converts tabs to four spaces
- Trims trailing whitespace and blank line spam
- Supports dry runs
- Forces CRLF endings for `.ps1`, `.json`, and `.md`, while keeping `.sh` LF

```
# Windows
.\helpers\tidy.ps1 -filePath "path\to\file.ps1" [-dryRun]

# macOS/Linux
./helpers/tidy.sh path/to/file.sh [--dry-run]
```

### `tidyRepo.py` (via `tidyRepo.ps1` / `tidyRepo.sh`)

- Recursively runs the single-file tidy across `.ps1`, `.sh`, `.json`, and `.md`
- Shares the same flags as the single-file version (`--dry-run`, `--path`, etc.)

```
./helpers/tidyRepo.sh              # entire repo
./helpers/tidyRepo.sh src/scripts  # specific directory
./helpers/tidyRepo.sh --dry-run
```

## Brace formatting

### `convertToAllman.py`

- Converts Bash functions to Allman braces
- Splits `} else {` blocks
- Keeps `if/while/for` keywords inline (e.g., `if [ … ]; then`)
- Supports dry runs and optional `.bak` backups

```
python3 helpers/convertToAllman.py --dryRun
python3 helpers/convertToAllman.py --path macos
python3 helpers/convertToAllman.py --createBackup
```

## Full pipeline

### `formatRepo.sh`
Runs the Allman conversion followed by `tidyRepo.sh` so the repo ends up idempotently formatted:

```
./helpers/formatRepo.sh
```
