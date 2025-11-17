#!/bin/bash
# Shared Git configuration logic for macOS and Ubuntu

# shellcheck disable=SC2154 # colour variables provided by callers

# Function to check if Git is installed
isGitInstalled()
{
    if command -v git >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to read a JSON section from a config file
readJsonSection()
{
    local configPath=$1
    local sectionKey=$2
    local jsonResult="{}"

    if [ -z "$configPath" ] || [ ! -f "$configPath" ]; then
        echo "$jsonResult"
        return 0
    fi

    if command -v jq >/dev/null 2>&1; then
        jsonResult=$(jq -c ".${sectionKey} // {}" "$configPath" 2>/dev/null || echo "{}")
    elif command -v python3 >/dev/null 2>&1; then
        jsonResult=$(python3 - "$configPath" "$sectionKey" <<'PY' 2>/dev/null || echo "{}"
import json
import sys

try:
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        data = json.load(fh)
    section = data.get(sys.argv[2], {})
    print(json.dumps(section))
except Exception:
    print("{}")
PY
)
    fi

    echo "$jsonResult"
}

# Function to get a value from a JSON object
getJsonValue()
{
    local jsonObject=$1
    local key=$2
    local defaultValue=$3
    local value

    if command -v jq >/dev/null 2>&1; then
        value=$(echo "$jsonObject" | jq -r ".[\"$key\"] // \"$defaultValue\"" 2>/dev/null || echo "$defaultValue")
    elif command -v python3 >/dev/null 2>&1; then
        value=$(python3 - "$jsonObject" "$key" "$defaultValue" <<'PY' 2>/dev/null || echo "$defaultValue"
import json
import sys

try:
    obj = json.loads(sys.argv[1])
    key = sys.argv[2]
    default = sys.argv[3]
    print(obj.get(key, default))
except Exception:
    print(sys.argv[3])
PY
)
    else
        value="$defaultValue"
    fi

    echo "$value"
}

# Function to set a Git config value with output
setGitConfig()
{
    local configKey=$1
    local configValue=$2
    local description=$3
    local successMessage=$4

    if [ -z "$description" ]; then
        description="Setting $configKey..."
    fi
    if [ -z "$successMessage" ]; then
        successMessage="✓ $configKey set to '$configValue'"
    fi

    echo -e "${yellow}$description${nc}"
    git config --global "$configKey" "$configValue"
    echo -e "  ${green}$successMessage${nc}"
}

# Function to configure Git user information
configureGitUser()
{
    echo -e "${cyan}Configuring Git user information...${nc}"

    local currentName
    local currentEmail
    currentName=$(git config --global user.name 2>/dev/null || echo "")
    currentEmail=$(git config --global user.email 2>/dev/null || echo "")

    if [ -n "$currentName" ] && [ -n "$currentEmail" ]; then
        echo -e "${yellow}Current Git user configuration:${nc}"
        echo -e "  Name:  $currentName"
        echo -e "  Email: $currentEmail"
        read -r -p "Keep existing configuration? (Y/N): " keepExisting
        if [[ "$keepExisting" =~ ^[Yy]$ ]]; then
            echo -e "${green}✓ Keeping existing configuration${nc}"
            return 0
        fi
    fi

    if [ -z "$currentName" ]; then
        read -r -p "Enter your name: " userName
    else
        read -r -p "Enter your name [$currentName]: " userName
        userName=${userName:-$currentName}
    fi

    if [ -z "$currentEmail" ]; then
        read -r -p "Enter your email: " userEmail
    else
        read -r -p "Enter your email [$currentEmail]: " userEmail
        userEmail=${userEmail:-$currentEmail}
    fi

    git config --global user.name "$userName"
    git config --global user.email "$userEmail"

    echo -e "${green}✓ Git user information configured successfully${nc}"
    return 0
}

# Function to configure Git defaults
configureGitDefaults()
{
    local configPath="${gitConfigPath:-}"
    local defaultsJson

    echo -e "${cyan}Configuring Git default settings...${nc}"

    defaultsJson=$(readJsonSection "$configPath" "defaults")

    local defaultBranch
    local colorUi
    local pullRebase
    local pushDefault
    local pushAutoSetup
    local rebaseAutoStash
    local mergeFf
    local fetchParallel

    defaultBranch=$(getJsonValue "$defaultsJson" "init.defaultBranch" "main")
    colorUi=$(getJsonValue "$defaultsJson" "color.ui" "auto")
    pullRebase=$(getJsonValue "$defaultsJson" "pull.rebase" "false")
    pushDefault=$(getJsonValue "$defaultsJson" "push.default" "simple")
    pushAutoSetup=$(getJsonValue "$defaultsJson" "push.autoSetupRemote" "true")
    rebaseAutoStash=$(getJsonValue "$defaultsJson" "rebase.autoStash" "true")
    mergeFf=$(getJsonValue "$defaultsJson" "merge.ff" "false")
    fetchParallel=$(getJsonValue "$defaultsJson" "fetch.parallel" "8")

    setGitConfig "init.defaultBranch" "$defaultBranch" "Setting default branch name to '$defaultBranch'..." "✓ Default branch set to '$defaultBranch'"

    setGitConfig "color.ui" "$colorUi" "Enabling colour output..." "✓ Colour output enabled"

    setGitConfig "pull.rebase" "$pullRebase" "Configuring pull behaviour..." ""
    local pullBehaviour
    if [ "$pullRebase" = "true" ]; then
        pullBehaviour="rebase"
    else
        pullBehaviour="merge (default)"
    fi
    echo -e "  ${green}✓ Pull behaviour set to $pullBehaviour${nc}"

    setGitConfig "push.default" "$pushDefault" "Configuring push behaviour..." "✓ Push default set to '$pushDefault'"

    setGitConfig "push.autoSetupRemote" "$pushAutoSetup" "Configuring push auto-setup..." "✓ Push auto-setup remote enabled"

    setGitConfig "rebase.autoStash" "$rebaseAutoStash" "Configuring rebase behaviour..." "✓ Rebase auto-stash enabled"

    setGitConfig "merge.ff" "$mergeFf" "Configuring merge strategy..." ""
    if [ "$mergeFf" = "false" ]; then
        echo -e "  ${green}✓ Merge fast-forward disabled (creates merge commits)${nc}"
    else
        echo -e "  ${green}✓ Merge fast-forward enabled${nc}"
    fi

    if [ -n "$fetchParallel" ] && [ "$fetchParallel" != "null" ]; then
        setGitConfig "fetch.parallel" "$fetchParallel" "Configuring fetch parallel jobs..." "✓ Fetch parallel jobs set to $fetchParallel"
    fi

    echo -e "${green}Git default settings configured successfully!${nc}"
    return 0
}

# Function to add a Git alias if it doesn't exist
addGitAlias()
{
    local aliasName=$1
    local aliasCommand=$2

    if git config --global --get "alias.$aliasName" >/dev/null 2>&1; then
        echo -e "  ${yellow}⚠ Alias '$aliasName' already exists, skipping...${nc}"
        return 1
    else
        git config --global "alias.$aliasName" "$aliasCommand"
        echo -e "  ${green}✓ Added alias: $aliasName${nc}"
        return 0
    fi
}

# Function to configure Git aliases
configureGitAliases()
{
    local configPath="${gitConfigPath:-}"
    local aliasesJson

    echo -e "${cyan}Configuring Git aliases...${nc}"

    aliasesJson=$(readJsonSection "$configPath" "aliases")

    # If no aliases found in config, use defaults
    if [ "$aliasesJson" = "{}" ] || [ -z "$aliasesJson" ]; then
        local defaultAliases=(
            "st:status"
            "co:checkout"
            "br:branch"
            "ci:commit"
            "unstage:reset HEAD --"
            "last:log -1 HEAD"
            "visual:!code"
            "log1:log --oneline"
            "logg:log --oneline --graph --decorate --all"
            "amend:commit --amend"
            "uncommit:reset --soft HEAD^"
            "stash-all:stash --include-untracked"
            "undo:reset HEAD~1"
        )

        for alias in "${defaultAliases[@]}"; do
            local aliasName="${alias%%:*}"
            local aliasCommand="${alias#*:}"
            addGitAlias "$aliasName" "$aliasCommand"
        done
    else
        # Process aliases from JSON
        if command -v jq >/dev/null 2>&1; then
            local aliasNames
            aliasNames=$(echo "$aliasesJson" | jq -r 'keys[]' 2>/dev/null || echo "")

            while IFS= read -r aliasName; do
                if [ -z "$aliasName" ]; then
                    continue
                fi

                local aliasCommand
                aliasCommand=$(getJsonValue "$aliasesJson" "$aliasName" "")

                if [ -z "$aliasCommand" ] || [ "$aliasCommand" = "null" ]; then
                    continue
                fi

                addGitAlias "$aliasName" "$aliasCommand"
            done <<< "$aliasNames"
        elif command -v python3 >/dev/null 2>&1; then
            python3 - "$aliasesJson" <<'PY' 2>/dev/null || true
import json
import subprocess
import sys

try:
    aliases = json.loads(sys.argv[1])
    for alias_name, alias_command in aliases.items():
        # Check if alias already exists
        result = subprocess.run(
            ["git", "config", "--global", "--get", f"alias.{alias_name}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  ⚠ Alias '{alias_name}' already exists, skipping...")
        else:
            subprocess.run(
                ["git", "config", "--global", f"alias.{alias_name}", alias_command],
                check=True
            )
            print(f"  ✓ Added alias: {alias_name}")
except Exception:
    pass
PY
        fi
    fi

    echo -e "${green}Git aliases configured successfully!${nc}"
    return 0
}

# Function to configure Git LFS
configureGitLfs()
{
    echo -e "${cyan}Configuring Git LFS...${nc}"

    if ! command -v git-lfs >/dev/null 2>&1; then
        echo -e "${yellow}⚠ git-lfs is not installed. Skipping LFS configuration.${nc}"
        return 0
    fi

    if git lfs version >/dev/null 2>&1; then
        echo -e "${yellow}Initializing Git LFS...${nc}"
        if git lfs install >/dev/null 2>&1; then
            echo -e "  ${green}✓ Git LFS initialized successfully${nc}"
        else
            echo -e "  ${yellow}⚠ Git LFS may already be initialized${nc}"
        fi
    else
        echo -e "${yellow}⚠ Git LFS command not available${nc}"
        return 0
    fi

    echo -e "${green}Git LFS configured successfully!${nc}"
    return 0
}

# Main configuration function
configureGit()
{
    local installHint="${gitInstallHint:-${yellow}Please install Git via your package manager.${nc}}"

    echo -e "${cyan}=== Git Configuration ===${nc}"
    echo ""

    if ! isGitInstalled; then
        echo -e "${red}✗ Git is not installed.${nc}"
        echo -e "${yellow}Please install Git first.${nc}"
        echo -e "  $installHint"
        return 1
    fi

    local success=true

    if ! configureGitUser; then
        success=false
    fi
    echo ""

    if ! configureGitDefaults; then
        success=false
    fi
    echo ""

    if ! configureGitAliases; then
        success=false
    fi
    echo ""

    if ! configureGitLfs; then
        success=false
    fi
    echo ""

    echo -e "${cyan}=== Configuration Complete ===${nc}"
    if [ "$success" = true ]; then
        echo -e "${green}Git has been configured successfully!${nc}"
    else
        echo -e "${yellow}Some settings may not have been configured. Please review the output above.${nc}"
    fi

    return 0
}
