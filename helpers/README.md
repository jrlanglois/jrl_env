# Helpers

Utility scripts for keeping the repo consistent.
At a glance:

| Script | Purpose | Typical command |
| --- | --- | --- |
| `tidy.py` (via `tidy.ps1` / `tidy.sh`) | Clean a single file (tabs → spaces, trim whitespace, enforce CRLF for supported extensions) | `./helpers/tidy.sh file.sh` |
| `tidyRepo.py` (via `tidyRepo.ps1` / `tidyRepo.sh`) | Clean every file under a path | `./helpers/tidyRepo.sh --dry-run` |
| `convertToAllman.py` | Enforce Allman braces + inline `if …; then` style | `python helpers/convertToAllman.py` |
| `formatRepo.sh` | Run the whole formatting pipeline (Allman + tidy) | `./helpers/formatRepo.sh` |

All helper scripts use Allman-style control blocks and camelCase identifiers for consistency.

## Whitespace tidy

### `tidy.py` (via `tidy.ps1` / `tidy.sh`)

- Converts tabs to four spaces
- Trims trailing whitespace and blank line spam
- Supports dry runs
- Forces CRLF endings for `.ps1`, `.sh`, `.json`, and `.md`

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
