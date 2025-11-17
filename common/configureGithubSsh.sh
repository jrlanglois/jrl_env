#!/bin/bash
# Shared GitHub SSH configuration logic for macOS and Ubuntu

# shellcheck disable=SC2154 # colour variables provided by callers

# Source utilities and logging functions (utilities must be direct source)
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../helpers/utilities.sh
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../helpers/logging.sh
sourceIfExists "$scriptDir/../helpers/logging.sh"

configureGithubSsh()
{
    local configPath="${gitConfigPath:?gitConfigPath must be set}"
    local jqHint="${jqInstallHint:-Please install jq to parse gitConfig.json.}"

    requireCommand jq "$jqHint" || return 1
    requireCommand ssh-keygen "" || return 1

    local email username githubUrl keyDir keyName keyPath
    email=$(getJsonValue "$configPath" ".user.email" "")
    username=$(getJsonValue "$configPath" ".user.usernameGitHub" "")
    githubUrl="https://github.com/settings/ssh/new"

    logSection "GitHub SSH Configuration"
    echo ""

    if [ -z "$email" ] || [ "$email" = "null" ]; then
        read -r -p "Enter email for SSH key: " email
    else
        read -r -p "Enter email for SSH key [$email]: " input
        email=${input:-$email}
    fi

    if [ -z "$username" ] || [ "$username" = "null" ]; then
        read -r -p "Enter GitHub username: " username
    else
        read -r -p "Enter GitHub username [$username]: " input
        username=${input:-$username}
    fi

    if [ -z "$email" ]; then
        logError "Email is required to generate SSH key."
        return 1
    fi

    keyDir="$HOME/.ssh"
    keyName="id_ed25519_github"
    read -r -p "Key filename [$keyName]: " input
    keyName=${input:-$keyName}
    keyPath="$keyDir/$keyName"

    mkdir -p "$keyDir"

    if [ -f "$keyPath" ]; then
        read -r -p "Key file exists. Overwrite? (y/N): " overwrite
        if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
            logNote "Skipping key generation."
            return 0
        fi
    fi

    logNote "Generating SSH key..."
    if ! ssh-keygen -t ed25519 -C "$email" -f "$keyPath" -N "" </dev/null; then
        logError "Failed to generate SSH key."
        return 1
    fi

    if command -v ssh-agent >/dev/null 2>&1; then
        eval "$(ssh-agent -s)" >/dev/null 2>&1 || true
    fi

    if command -v ssh-add >/dev/null 2>&1; then
        if ssh-add "$keyPath" >/dev/null 2>&1; then
            logSuccess "Added key to ssh-agent"
        elif command -v ssh-add --apple-use-keychain >/dev/null 2>&1; then
            ssh-add --apple-use-keychain "$keyPath" >/dev/null 2>&1 && logSuccess "Added key to keychain"
        else
            logWarning "Unable to add key to agent automatically."
        fi
    fi

    echo ""
    logNote "Public key:"
    echo ""
    cat "${keyPath}.pub"
    echo ""

    if command -v pbcopy >/dev/null 2>&1; then
        pbcopy < "${keyPath}.pub"
        logSuccess "Copied public key to clipboard"
    elif command -v xclip >/dev/null 2>&1; then
        xclip -selection clipboard < "${keyPath}.pub"
        logSuccess "Copied public key to clipboard"
    elif command -v clip >/dev/null 2>&1; then
        clip < "${keyPath}.pub"
        logSuccess "Copied public key to clipboard"
    else
        logWarning "Copy the above key manually."
    fi

    read -r -p "Open GitHub SSH keys page now? (Y/n): " openPage
    if [[ "$openPage" =~ ^[Yy]$ || -z "$openPage" ]]; then
        if command -v open >/dev/null 2>&1; then
            open "$githubUrl" >/dev/null 2>&1 || true
        elif command -v xdg-open >/dev/null 2>&1; then
            xdg-open "$githubUrl" >/dev/null 2>&1 || true
        else
            logNote "Open ${githubUrl} in your browser to add the key."
        fi
    else
        logNote "Visit ${githubUrl} to add the key when ready."
    fi

    echo ""
    logSuccess "GitHub SSH configuration complete"
    return 0
}
