#!/bin/bash
# Shared repository cloning logic

# shellcheck disable=SC2154 # colour variables provided by callers

# Source utilities and logging functions (utilities must be direct source)
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../helpers/utilities.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$scriptDir/../helpers/utilities.sh"
# shellcheck source=../helpers/logging.sh
sourceIfExists "$scriptDir/../helpers/logging.sh"

isGitInstalled()
{
    if command -v git >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

isRepositoryCloned()
{
    local repoUrl=$1
    local workPath=$2
    local owner
    local repoName

    owner=$(getRepositoryOwner "$repoUrl")
    repoName=$(getRepositoryName "$repoUrl")

    if [ -z "$owner" ] || [ -z "$repoName" ]; then
        return 1
    fi

    local repoPath="${workPath}/${owner}/${repoName}"
    if [ -d "$repoPath" ] && [ -d "${repoPath}/.git" ]; then
        return 0
    fi
    return 1
}

getRepositoryOwner()
{
    local repoUrl=$1
    local owner
    owner=$(echo "$repoUrl" | sed -E 's|.*github\.com/([^/]+)/.*|\1|')
    if [ "$owner" = "$repoUrl" ]; then
        owner=$(echo "$repoUrl" | sed -E 's|.*:([^/]+)/.*|\1|')
    fi
    echo "$owner"
}

getRepositoryName()
{
    local repoUrl=$1
    echo "$repoUrl" | sed -E 's|.*[:/]([^/]+?)(\.git)?$|\1|'
}

cloneRepository()
{
    local repoUrl=$1
    local workPath=$2
    local owner
    local repoName

    owner=$(getRepositoryOwner "$repoUrl")
    repoName=$(getRepositoryName "$repoUrl")

    if [ -z "$owner" ] || [ -z "$repoName" ]; then
        logError "  Failed to extract owner or repository name from URL"
        return 1
    fi

    local ownerPath="${workPath}/${owner}"
    mkdir -p "$ownerPath"

    local repoPath="${ownerPath}/${repoName}"

    if isRepositoryCloned "$repoUrl" "$workPath"; then
        logWarning "  Repository already exists: $owner/$repoName"
        echo "    Skipping clone. Use 'git pull' to update if needed."
        return 0
    fi

    logNote "  Cloning $owner/$repoName..."

    if git clone --recursive "$repoUrl" "$repoPath" 2>/dev/null; then
        logSuccess "    Cloned successfully"
        if [ -f "${repoPath}/.gitmodules" ]; then
            logSuccess "    Submodules initialised"
        fi
        return 0
    else
        logError "    Clone failed"
        return 1
    fi
}

cloneRepositories()
{
    local configPath=${1:-$repoConfigPath}
    local jqHint="${jqInstallHint:-${yellow}Please install jq via your package manager.${nc}}"

    logSection "Repository Cloning"
    echo ""

    if ! isGitInstalled; then
        logError "Git is not installed."
        logNote "Please install Git first."
        return 1
    fi

    if [ ! -f "$configPath" ]; then
        logError "Configuration file not found: $configPath"
        return 1
    fi

    local jqHint="${jqInstallHint:-Please install jq via your package manager.}"
    if ! requireJq "$jqHint"; then
        return 1
    fi

    local workPath
    local repositories
    workPath=$(getJsonValue "$configPath" ".workPathUnix" "")
    repositories=$(getJsonArray "$configPath" ".repositories[]?")

    workPath=$(echo "$workPath" | sed "s|\$HOME|$HOME|g" | sed "s|\$USER|$USER|g")

    if [ -z "$workPath" ] || [ "$workPath" = "null" ]; then
        logError "JSON file must contain a 'workPathUnix' property."
        return 1
    fi

    if [ -z "$repositories" ]; then
        logNote "No repositories specified in configuration file."
        return 0
    fi

    local repoCount
    repoCount=$(echo "$repositories" | grep -c . || echo "0")
    logInfo "Work directory: $workPath"
    logInfo "Found $repoCount repository/repositories in configuration file."
    echo ""

    if [ ! -d "$workPath" ]; then
        logNote "Creating work directory: $workPath"
        mkdir -p "$workPath"
        logSuccess "Work directory created"
        echo ""
    fi

    local clonedCount=0
    local skippedCount=0
    local failedCount=0

    while IFS= read -r repoUrl; do
        if [ -z "$repoUrl" ]; then
            continue
        fi

        logNote "Processing: $repoUrl"

        if cloneRepository "$repoUrl" "$workPath"; then
            ((clonedCount++))
        elif isRepositoryCloned "$repoUrl" "$workPath"; then
            ((skippedCount++))
        else
            ((failedCount++))
        fi

        echo ""
    done <<< "$repositories"

    logInfo "Summary:"
    logSuccess "  Cloned: $clonedCount repository/repositories"
    if [ $skippedCount -gt 0 ]; then
        logNote "  Skipped: $skippedCount repository/repositories (already exist)"
    fi
    if [ $failedCount -gt 0 ]; then
        logError "  Failed: $failedCount repository/repositories"
    fi

    echo ""
    logSuccess "Repository cloning complete!"

    return 0
}
