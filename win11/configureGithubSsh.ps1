$script:gitConfigPath = Join-Path (Join-Path $PSScriptRoot "..\configs") "gitConfig.json"

function Get-GitConfigValue {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Expression
    )

    if (-not (Test-Path $Path)) {
        throw "Configuration file not found: $Path"
    }

    $content = Get-Content $Path -Raw | ConvertFrom-Json
    return (Invoke-Expression "$content$Expression")
}

function Read-Default {
    param(
        [Parameter(Mandatory=$true)][string]$Prompt,
        [string]$Default
    )

    if ([string]::IsNullOrWhiteSpace($Default)) {
        return (Read-Host $Prompt)
    }

    $input = Read-Host "$Prompt [$Default]"
    if ([string]::IsNullOrWhiteSpace($input)) {
        return $Default
    }
    return $input
}

function Configure-GithubSsh {
    . "$PSScriptRoot\logging.ps1"

    if (-not (Get-Command ssh-keygen -ErrorAction SilentlyContinue)) {
        logWarn "ssh-keygen not found. Install OpenSSH before continuing."
        return $false
    }

    try {
        $configJson = Get-Content $script:gitConfigPath -Raw | ConvertFrom-Json
    } catch {
        logWarn "Unable to parse gitConfig.json: $_"
        return $false
    }

    $email = $configJson.user.email
    $username = $configJson.user.usernameGitHub

    logInfo "=== GitHub SSH Configuration ==="

    $email = Read-Default -Prompt "Email for SSH key" -Default $email
    if ([string]::IsNullOrWhiteSpace($email)) {
        logError "Email is required."
        return $false
    }

    $username = Read-Default -Prompt "GitHub username" -Default $username

    $sshDir = Join-Path $HOME ".ssh"
    if (-not (Test-Path $sshDir)) {
        New-Item -ItemType Directory -Path $sshDir | Out-Null
    }

    $keyName = Read-Default -Prompt "Key filename" -Default "id_ed25519_github"
    $keyPath = Join-Path $sshDir $keyName

    if (Test-Path $keyPath) {
        $overwrite = Read-Default -Prompt "Key exists. Overwrite?" -Default "n"
        if ($overwrite -notmatch '^[Yy]$') {
            logWarn "Skipping key generation."
            return $true
        }
    }

    logInfo "Generating SSH key..."
    $sshCmd = "ssh-keygen -t ed25519 -C `"$email`" -f `"$keyPath`" -N `"`""
    if (-not (Invoke-Expression $sshCmd | Out-Null; $?)) {
        logError "Failed to generate SSH key."
        return $false
    }

    try {
        Start-Service ssh-agent -ErrorAction SilentlyContinue | Out-Null
    } catch {
        # ignore
    }

    if (Get-Command ssh-add -ErrorAction SilentlyContinue) {
        & ssh-add $keyPath | Out-Null
        logSuccess "Added key to ssh-agent"
    }

    $pubKeyPath = "$keyPath.pub"
    $publicKey = Get-Content $pubKeyPath -Raw
    logInfo "Public key:"
    Write-Host ""
    Write-Host $publicKey
    Write-Host ""

    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) {
        $publicKey | Set-Clipboard
        logSuccess "Copied public key to clipboard"
    }

    $openPage = Read-Default -Prompt "Open GitHub SSH keys page now? (Y/n)" -Default "y"
    if ($openPage -match '^[Yy]$') {
        Start-Process "https://github.com/settings/ssh/new"
    } else {
        logInfo "Visit https://github.com/settings/ssh/new to add the key."
    }

    logSuccess "GitHub SSH configuration complete."
    return $true
}

