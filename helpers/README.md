# Helpers

Utility scripts for maintaining code quality and consistency.

## tidy.ps1 / tidy.sh

Trims whitespace and converts tabs to spaces in a single file.

### Features

- Converts tabs to 4 spaces
- Trims trailing whitespace from lines
- Removes trailing blank lines
- Supports dry-run mode

### Usage

**Windows (PowerShell):**
```powershell
# Tidy a single file
.\helpers\tidy.ps1 -filePath "path\to\file.ps1"

# Dry run (preview changes)
.\helpers\tidy.ps1 -filePath "path\to\file.ps1" -dryRun
```

**macOS/Linux (Bash):**
```bash
# Tidy a single file
./helpers/tidy.sh path/to/file.sh

# Dry run (preview changes)
./helpers/tidy.sh path/to/file.sh --dry-run
```

## tidyRepo.ps1 / tidyRepo.sh

Trims whitespace and converts tabs to spaces in all code files in a repository.

### Features

- Processes all `.ps1`, `.sh`, `.json`, and `.md` files recursively
- Uses the `tidy` scripts internally (DRY principle)
- Supports dry-run mode
- Provides summary statistics

### Usage

**Windows (PowerShell):**
```powershell
# Tidy all files in the repository
.\helpers\tidyRepo.ps1

# Tidy files in a specific directory
.\helpers\tidyRepo.ps1 -path "C:\path\to\files"

# Dry run (preview changes)
.\helpers\tidyRepo.ps1 -dryRun
```

**macOS/Linux (Bash):**
```bash
# Tidy all files in the repository
./helpers/tidyRepo.sh

# Tidy files in a specific directory
./helpers/tidyRepo.sh /path/to/files

# Dry run (preview changes)
./helpers/tidyRepo.sh --dry-run
```

### Notes

- The repo scripts process files recursively from the specified path (defaults to repository root)
- Files are modified in-place
- Use dry-run mode to preview changes before applying them
- The `tidy` scripts can be sourced/imported by other scripts to reuse the tidying functionality

