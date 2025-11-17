# Function to check if Git is installed
function isGitInstalled {
    <#
    .SYNOPSIS
    Checks if Git is installed and available in the system PATH.

    .OUTPUTS
    Boolean. Returns $true if Git is installed, $false otherwise.
    #>
    param()

    try {
        $gitVersion = git --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
}

# Function to configure Git user information
function configureGitUser {
    <#
    .SYNOPSIS
    Configures Git user name and email from gitConfig.json.

    .DESCRIPTION
    Reads user name and email from gitConfig.json and configures Git accordingly.
    If config file is not found or values are missing, prompts the user.

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$configPath = (Join-Path (Join-Path $PSScriptRoot "..\configs") "gitConfig.json")
    )

    Write-Host "Configuring Git user information..." -ForegroundColor Cyan

    try {
        $userName = $null
        $userEmail = $null

        # Try to read from config file
        if (Test-Path $configPath) {
            try {
                $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json
                if ($jsonContent.user) {
                    $userName = $jsonContent.user.name
                    $userEmail = $jsonContent.user.email
                }
            } catch {
                Write-Warning "Failed to parse gitConfig.json: $_"
            }
        }

        # Fallback to prompting if config file doesn't exist or values are missing
        if (-not $userName -or -not $userEmail) {
            $currentName = git config --global user.name 2>$null
            $currentEmail = git config --global user.email 2>$null

            if (-not $userName) {
                if (-not $currentName) {
                    $userName = Read-Host "Enter your Git user name"
                } else {
                    $userName = Read-Host "Enter your Git user name (or press Enter to keep: $currentName)"
                    if (-not $userName) { $userName = $currentName }
                }
            }

            if (-not $userEmail) {
                if (-not $currentEmail) {
                    $userEmail = Read-Host "Enter your Git email"
                } else {
                    $userEmail = Read-Host "Enter your Git email (or press Enter to keep: $currentEmail)"
                    if (-not $userEmail) { $userEmail = $currentEmail }
                }
            }
        }

        # Set Git user configuration
        if ($userName) {
            git config --global user.name $userName
            Write-Host "Git user name set to: $userName" -ForegroundColor Green
        }
        if ($userEmail) {
            git config --global user.email $userEmail
            Write-Host "Git user email set to: $userEmail" -ForegroundColor Green
        }

        Write-Host "Git user information configured successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Error "Failed to configure Git user information: $_"
        return $false
    }
}

# Function to configure Git default settings
function configureGitDefaults {
    <#
    .SYNOPSIS
    Configures Git with common developer-friendly default settings from gitConfig.json.

    .DESCRIPTION
    Reads settings from gitConfig.json and configures Git accordingly.
    Falls back to defaults if config file is not found.

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$configPath = (Join-Path (Join-Path $PSScriptRoot "..\configs") "gitConfig.json")
    )

    Write-Host "Configuring Git default settings..." -ForegroundColor Cyan

    try {
        $defaults = @{}

        # Try to read from config file
        if (Test-Path $configPath) {
            try {
                $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json
                if ($jsonContent.defaults) {
                    $jsonContent.defaults.PSObject.Properties | ForEach-Object {
                        $defaults[$_.Name] = $_.Value
                    }
                }
            } catch {
                Write-Warning "Failed to parse gitConfig.json: $_"
            }
        }

        # Set default branch name
        $defaultBranch = if ($defaults.ContainsKey("init.defaultBranch")) { $defaults["init.defaultBranch"] } else { "main" }
        Write-Host "Setting default branch name to '$defaultBranch'..." -ForegroundColor Yellow
        git config --global init.defaultBranch $defaultBranch
        Write-Host "  ✓ Default branch set to '$defaultBranch'" -ForegroundColor Green

        # Set core editor (VS Code if available, otherwise notepad)
        Write-Host "Setting default editor..." -ForegroundColor Yellow
        $codePath = Get-Command code -ErrorAction SilentlyContinue
        if ($codePath) {
            git config --global core.editor "code --wait"
            Write-Host "  ✓ Editor set to VS Code" -ForegroundColor Green
        }

        # Configure line ending handling (auto CRLF for Windows)
        Write-Host "Configuring line ending handling..." -ForegroundColor Yellow
        git config --global core.autocrlf true
        Write-Host "  ✓ Line endings set to auto (CRLF on Windows)" -ForegroundColor Green

        # Enable colour output
        $colorUi = if ($defaults.ContainsKey("color.ui")) { $defaults["color.ui"] } else { "auto" }
        Write-Host "Enabling colour output..." -ForegroundColor Yellow
        git config --global color.ui $colorUi
        Write-Host "  ✓ Colour output enabled" -ForegroundColor Green

        # Set pull rebase behaviour
        $pullRebase = if ($defaults.ContainsKey("pull.rebase")) { $defaults["pull.rebase"] } else { "false" }
        Write-Host "Configuring pull behaviour..." -ForegroundColor Yellow
        git config --global pull.rebase $pullRebase
        $pullBehaviour = if ($pullRebase -eq "true") { "rebase" } else { "merge (default)" }
        Write-Host "  ✓ Pull behaviour set to $pullBehaviour" -ForegroundColor Green

        # Configure credential helper for Windows
        Write-Host "Configuring credential helper..." -ForegroundColor Yellow
        git config --global credential.helper manager-core
        Write-Host "  ✓ Credential helper set to Windows Credential Manager" -ForegroundColor Green

        # Set push default behaviour
        $pushDefault = if ($defaults.ContainsKey("push.default")) { $defaults["push.default"] } else { "simple" }
        Write-Host "Configuring push behaviour..." -ForegroundColor Yellow
        git config --global push.default $pushDefault
        Write-Host "  ✓ Push default set to '$pushDefault'" -ForegroundColor Green

        # Enable push auto-setup remote tracking
        $pushAutoSetup = if ($defaults.ContainsKey("push.autoSetupRemote")) { $defaults["push.autoSetupRemote"] } else { "true" }
        Write-Host "Configuring push auto-setup..." -ForegroundColor Yellow
        git config --global push.autoSetupRemote $pushAutoSetup
        Write-Host "  ✓ Push auto-setup remote enabled" -ForegroundColor Green

        # Set merge tool (VS Code if available)
        Write-Host "Configuring merge tool..." -ForegroundColor Yellow
        if ($codePath) {
            git config --global merge.tool vscode
            git config --global mergetool.vscode.cmd "code --wait `$MERGED"
            Write-Host "  ✓ Merge tool set to VS Code" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠ Merge tool not configured (VS Code not found)" -ForegroundColor Yellow
        }

        # Set diff tool (VS Code if available)
        Write-Host "Configuring diff tool..." -ForegroundColor Yellow
        if ($codePath) {
            git config --global diff.tool vscode
            git config --global difftool.vscode.cmd "code --wait --diff `$LOCAL `$REMOTE"
            Write-Host "  ✓ Diff tool set to VS Code" -ForegroundColor Green
        }
        else {
            Write-Host "  ⚠ Diff tool not configured (VS Code not found)" -ForegroundColor Yellow
        }

        # Configure rebase behaviour
        $rebaseAutoStash = if ($defaults.ContainsKey("rebase.autoStash")) { $defaults["rebase.autoStash"] } else { "true" }
        Write-Host "Configuring rebase behaviour..." -ForegroundColor Yellow
        git config --global rebase.autoStash $rebaseAutoStash
        Write-Host "  ✓ Rebase auto-stash enabled" -ForegroundColor Green

        # Set default merge strategy
        $mergeFf = if ($defaults.ContainsKey("merge.ff")) { $defaults["merge.ff"] } else { "false" }
        Write-Host "Configuring merge strategy..." -ForegroundColor Yellow
        git config --global merge.ff $mergeFf
        $mergeStrategy = if ($mergeFf -eq "true") { "enabled" } else { "disabled (creates merge commits)" }
        Write-Host "  ✓ Merge fast-forward $mergeStrategy" -ForegroundColor Green

        Write-Host "Git default settings configured successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Error "Failed to configure Git default settings: $_"
        return $false
    }
}

# Function to configure Git aliases
function configureGitAliases {
    <#
    .SYNOPSIS
    Configures useful Git aliases from gitConfig.json.

    .DESCRIPTION
    Reads aliases from gitConfig.json and configures Git accordingly.
    Falls back to default aliases if config file is not found.

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$configPath = (Join-Path (Join-Path $PSScriptRoot "..\configs") "gitConfig.json")
    )

    Write-Host "Configuring Git aliases..." -ForegroundColor Cyan

    try {
        $aliases = @{}

        # Try to read from config file
        if (Test-Path $configPath) {
            try {
                $jsonContent = Get-Content $configPath -Raw | ConvertFrom-Json
                if ($jsonContent.aliases) {
                    $jsonContent.aliases.PSObject.Properties | ForEach-Object {
                        $aliases[$_.Name] = $_.Value
                    }
                }
            } catch {
                Write-Warning "Failed to parse gitConfig.json: $_"
            }
        }

        # Fallback to default aliases if config file doesn't exist
        if ($aliases.Count -eq 0) {
            $aliases = @{
                "st" = "status"
                "co" = "checkout"
                "br" = "branch"
                "ci" = "commit"
                "unstage" = "reset HEAD --"
                "last" = "log -1 HEAD"
                "visual" = "!code"
                "log1" = "log --oneline"
                "logg" = "log --oneline --graph --decorate --all"
                "amend" = "commit --amend"
                "uncommit" = "reset --soft HEAD^"
                "stash-all" = "stash --include-untracked"
                "undo" = "reset HEAD~1"
            }
        }

        # Configure aliases
        Write-Host "Setting up aliases..." -ForegroundColor Yellow
        foreach ($aliasName in $aliases.Keys) {
            $aliasCommand = $aliases[$aliasName]

            # Check if alias already exists
            $existingAlias = git config --global --get "alias.$aliasName" 2>$null
            if ($existingAlias) {
                Write-Host "  ⚠ Alias '$aliasName' already exists, skipping..." -ForegroundColor Yellow
            } else {
                git config --global "alias.$aliasName" $aliasCommand
                Write-Host "  ✓ Added alias: $aliasName" -ForegroundColor Green
            }
        }
        git config --global alias.lga "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit --all"
        git config --global alias.ll "log --oneline --decorate --all --graph"

        # Branch aliases
        Write-Host "Setting up branch aliases..." -ForegroundColor Yellow
        git config --global alias.branch-name "rev-parse --abbrev-ref HEAD"
        git config --global alias.recent "branch --sort=-committerdate"

        # Commit aliases
        Write-Host "Setting up commit aliases..." -ForegroundColor Yellow
        git config --global alias.amend "commit --amend --no-edit"
        git config --global alias.save "!git add -A && git commit -m 'SAVEPOINT'"

        # Stash aliases
        Write-Host "Setting up stash aliases..." -ForegroundColor Yellow
        git config --global alias.stash-list "stash list --date=local"

        # Diff aliases
        Write-Host "Setting up diff aliases..." -ForegroundColor Yellow
        git config --global alias.dc "diff --cached"
        git config --global alias.diffstat "diff --stat"

        # Remote aliases
        Write-Host "Setting up remote aliases..." -ForegroundColor Yellow
        git config --global alias.remotes "remote -v"

        Write-Host "Git aliases configured successfully!" -ForegroundColor Green
        Write-Host "Common aliases:" -ForegroundColor Cyan
        Write-Host "  git st      - status" -ForegroundColor Gray
        Write-Host "  git co      - checkout" -ForegroundColor Gray
        Write-Host "  git br      - branch" -ForegroundColor Gray
        Write-Host "  git ci      - commit" -ForegroundColor Gray
        Write-Host "  git lg      - pretty log" -ForegroundColor Gray
        Write-Host "  git unstage - unstage files" -ForegroundColor Gray
        return $true
    }
    catch {
        Write-Error "Failed to configure Git aliases: $_"
        return $false
    }
}

# Main configuration function
function configureGit {
    <#
    .SYNOPSIS
    Configures Git to user preferences.

    .DESCRIPTION
    Checks if Git is installed and configures it with:
    - User name and email (with prompts)
    - Default settings (branch name, editor, line endings, etc.)
    - Useful aliases for common operations

    .OUTPUTS
    Boolean. Returns $true if all configurations were successful, $false otherwise.

    .EXAMPLE
    configureGit

    .NOTES
    Git must be installed and available in the system PATH.
    #>
    param()

    Write-Host "=== Git Configuration ===" -ForegroundColor Cyan
    Write-Host ""

    # Check if Git is installed
    if (-not (isGitInstalled)) {
        Write-Error "Git is not installed or not available in PATH. Please install Git first."
        Write-Host "You can install Git using: winget install Git.Git" -ForegroundColor Yellow
        return $false
    }

    $gitVersion = git --version
    Write-Host "Git version: $gitVersion" -ForegroundColor Green
    Write-Host ""

    $success = $true

    # Configure user information
    if (-not (configureGitUser)) {
        $success = $false
    }

    Write-Host ""

    # Configure default settings
    if (-not (configureGitDefaults)) {
        $success = $false
    }

    Write-Host ""

    # Configure aliases
    if (-not (configureGitAliases)) {
        $success = $false
    }

    Write-Host ""
    Write-Host "=== Configuration Complete ===" -ForegroundColor Cyan

    if ($success) {
        Write-Host "Git has been configured successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Current Git configuration:" -ForegroundColor Cyan
        git config --global --list | Select-String -Pattern "^(user\.|core\.|pull\.|push\.|credential\.|alias\.)" | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "Some Git settings may not have been configured. Please review the errors above." -ForegroundColor Red
    }

    return $success
}
