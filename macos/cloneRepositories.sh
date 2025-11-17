#!/bin/bash
# Script to clone Git repositories from repositories.json
# Clones repositories recursively (including submodules) to a configured work directory

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
configPath="${scriptDir}/../configs/repositories.json"

# Function to check if Git is installed
isGitInstalled()
{
    if command -v git >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to check if a repository is already cloned
isRepositoryCloned()
{
    local repoUrl=$1
    local workPath=$2

    # Extract username and repository name from URL
    local owner=$(getRepositoryOwner "$repoUrl")
    local repoName=$(getRepositoryName "$repoUrl")

    if [ -z "$owner" ] || [ -z "$repoName" ]; then
        return 1
    fi

    local repoPath="${workPath}/${owner}/${repoName}"

    if [ -d "$repoPath" ] && [ -d "${repoPath}/.git" ]; then
        return 0
    fi
    return 1
}

# Function to get username/organization from URL
getRepositoryOwner()
{
    local repoUrl=$1
    # Extract username/organization from URL (handles both HTTPS and SSH)
    # Try HTTPS pattern first (github.com/username/), then SSH pattern (:username/)
    local owner=$(echo "$repoUrl" | sed -E 's|.*github\.com/([^/]+)/.*|\1|')
    if [ "$owner" = "$repoUrl" ]; then
        # HTTPS pattern didn't match, try SSH pattern
        owner=$(echo "$repoUrl" | sed -E 's|.*:([^/]+)/.*|\1|')
    fi
    echo "$owner"
}

# Function to get repository name from URL
getRepositoryName()
{
    local repoUrl=$1
    echo "$repoUrl" | sed -E 's|.*[:/]([^/]+?)(\.git)?$|\1|'
}

# Function to clone a single repository recursively
cloneRepository()
{
    local repoUrl=$1
    local workPath=$2

    local owner=$(getRepositoryOwner "$repoUrl")
    local repoName=$(getRepositoryName "$repoUrl")

    if [ -z "$owner" ] || [ -z "$repoName" ]; then
        echo -e "  ${red}✗ Failed to extract owner or repository name from URL${nc}"
        return 1
    fi

    # Create owner directory if it doesn't exist
    local ownerPath="${workPath}/${owner}"
    mkdir -p "$ownerPath"

    local repoPath="${ownerPath}/${repoName}"

    # Check if already cloned
    if isRepositoryCloned "$repoUrl" "$workPath"; then
        echo -e "  ${yellow}⚠ Repository already exists: $owner/$repoName${nc}"
        echo -e "    Skipping clone. Use 'git pull' to update if needed."
        return 0
    fi

    echo -e "  ${yellow}Cloning $owner/$repoName...${nc}"

    # Clone with recursive flag to include submodules
    if git clone --recursive "$repoUrl" "$repoPath" 2>/dev/null; then
        echo -e "    ${green}✓ Cloned successfully${nc}"

        # Check if submodules were initialised
        if [ -f "${repoPath}/.gitmodules" ]; then
            echo -e "    ${green}✓ Submodules initialised${nc}"
        fi

        return 0
    else
        echo -e "    ${red}✗ Clone failed${nc}"
        return 1
    fi
}

# Function to clone all repositories
cloneRepositories()
{
    local configPath=${1:-$configPath}

    echo -e "${cyan}=== Repository Cloning ===${nc}"
    echo ""

    # Check if Git is installed
    if ! isGitInstalled; then
        echo -e "${red}✗ Git is not installed.${nc}"
        echo -e "${yellow}Please install Git first.${nc}"
        return 1
    fi

    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${red}✗ Configuration file not found: $configPath${nc}"
        return 1
    fi

    # Check if jq is available
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${red}✗ jq is required to parse JSON. Please install it first.${nc}"
        echo -e "${yellow}  brew install jq${nc}"
        return 1
    fi

    # Parse JSON
    local workPath=$(jq -r '.workPathUnix' "$configPath")
    local repositories=$(jq -r '.repositories[]?' "$configPath")

    # Expand $HOME and $USER if present in path
    workPath=$(echo "$workPath" | sed "s|\$HOME|$HOME|g" | sed "s|\$USER|$USER|g")

    if [ -z "$workPath" ] || [ "$workPath" = "null" ]; then
        echo -e "${red}✗ JSON file must contain a 'workPathUnix' property.${nc}"
        return 1
    fi

    if [ -z "$repositories" ]; then
        echo -e "${yellow}No repositories specified in configuration file.${nc}"
        return 0
    fi

    local repoCount=$(echo "$repositories" | grep -c . || echo "0")
    echo -e "${cyan}Work directory: $workPath${nc}"
    echo -e "${cyan}Found $repoCount repository/repositories in configuration file.${nc}"
    echo ""

    # Create work directory if it doesn't exist
    if [ ! -d "$workPath" ]; then
        echo -e "${yellow}Creating work directory: $workPath${nc}"
        mkdir -p "$workPath"
        echo -e "${green}✓ Work directory created${nc}"
        echo ""
    fi

    local clonedCount=0
    local skippedCount=0
    local failedCount=0

    # Process each repository
    while IFS= read -r repoUrl; do
        if [ -z "$repoUrl" ]; then
            continue
        fi

        echo -e "${yellow}Processing: $repoUrl${nc}"

        if cloneRepository "$repoUrl" "$workPath"; then
            ((clonedCount++))
        elif isRepositoryCloned "$repoUrl" "$workPath"; then
            ((skippedCount++))
        else
            ((failedCount++))
        fi

        echo ""
    done <<< "$repositories"

    echo -e "${cyan}Summary:${nc}"
    echo -e "  ${green}Cloned: $clonedCount repository/repositories${nc}"
    if [ $skippedCount -gt 0 ]; then
        echo -e "  ${yellow}Skipped: $skippedCount repository/repositories (already exist)${nc}"
    fi
    if [ $failedCount -gt 0 ]; then
        echo -e "  ${red}Failed: $failedCount repository/repositories${nc}"
    fi

    echo ""
    echo -e "${green}Repository cloning complete!${nc}"

    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cloneRepositories "$@"
fi
