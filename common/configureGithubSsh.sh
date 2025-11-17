#!/bin/bash
# Shared GitHub SSH configuration logic for macOS and Ubuntu

# shellcheck disable=SC2154 # colour variables provided by callers

requireCommand()
{
    local cmd=$1
    local installHint=$2

    if command -v "$cmd" >/dev/null 2>&1; then
        return 0
    fi

    echo -e "${red}✗ Required command '$cmd' not found.${nc}"
    if [ -n "$installHint" ]; then
        echo -e "  ${yellow}$installHint${nc}"
    fi
    return 1
}

configureGithubSsh()
{
    local configPath="${gitConfigPath:?gitConfigPath must be set}"
    local jqHint="${jqInstallHint:-${yellow}Please install jq to parse gitConfig.json.${nc}}"

    requireCommand jq "$jqHint" || return 1
    requireCommand ssh-keygen "" || return 1

    local email username githubUrl keyDir keyName keyPath
    email=$(jq -r '.user.email // empty' "$configPath" 2>/dev/null)
    username=$(jq -r '.user.usernameGitHub // empty' "$configPath" 2>/dev/null)
    githubUrl="https://github.com/settings/ssh/new"

    echo -e "${cyan}=== GitHub SSH Configuration ===${nc}"
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
        echo -e "${red}✗ Email is required to generate SSH key.${nc}"
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
            echo -e "${yellow}Skipping key generation.${nc}"
            return 0
        fi
    fi

    echo -e "${yellow}Generating SSH key...${nc}"
    if ! ssh-keygen -t ed25519 -C "$email" -f "$keyPath" -N "" </dev/null; then
        echo -e "${red}✗ Failed to generate SSH key.${nc}"
        return 1
    fi

    if command -v ssh-agent >/dev/null 2>&1; then
        eval "$(ssh-agent -s)" >/dev/null 2>&1 || true
    fi

    if command -v ssh-add >/dev/null 2>&1; then
        if ssh-add "$keyPath" >/dev/null 2>&1; then
            echo -e "${green}✓ Added key to ssh-agent${nc}"
        elif command -v ssh-add --apple-use-keychain >/dev/null 2>&1; then
            ssh-add --apple-use-keychain "$keyPath" >/dev/null 2>&1 && echo -e "${green}✓ Added key to keychain${nc}"
        else
            echo -e "${yellow}⚠ Unable to add key to agent automatically.${nc}"
        fi
    fi

    echo ""
    echo -e "${yellow}Public key:${nc}"
    echo ""
    cat "${keyPath}.pub"
    echo ""

    if command -v pbcopy >/dev/null 2>&1; then
        pbcopy < "${keyPath}.pub"
        echo -e "${green}✓ Copied public key to clipboard${nc}"
    elif command -v xclip >/dev/null 2>&1; then
        xclip -selection clipboard < "${keyPath}.pub"
        echo -e "${green}✓ Copied public key to clipboard${nc}"
    elif command -v clip >/dev/null 2>&1; then
        clip < "${keyPath}.pub"
        echo -e "${green}✓ Copied public key to clipboard${nc}"
    else
        echo -e "${yellow}⚠ Copy the above key manually.${nc}"
    fi

    read -r -p "Open GitHub SSH keys page now? (Y/n): " openPage
    if [[ "$openPage" =~ ^[Yy]$ || -z "$openPage" ]]; then
        if command -v open >/dev/null 2>&1; then
            open "$githubUrl" >/dev/null 2>&1 || true
        elif command -v xdg-open >/dev/null 2>&1; then
            xdg-open "$githubUrl" >/dev/null 2>&1 || true
        else
            echo -e "${yellow}Open ${githubUrl} in your browser to add the key.${nc}"
        fi
    else
        echo -e "${yellow}Visit ${githubUrl} to add the key when ready.${nc}"
    fi

    echo ""
    echo -e "${green}✓ GitHub SSH configuration complete${nc}"
    return 0
}

