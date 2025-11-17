#!/bin/bash
# Shared repository cloning logic

# shellcheck disable=SC2154 # colour variables provided by callers

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
        echo -e "  ${red}✗ Failed to extract owner or repository name from URL${nc}"
        return 1
    fi

    local ownerPath="${workPath}/${owner}"
    mkdir -p "$ownerPath"

    local repoPath="${ownerPath}/${repoName}"

    if isRepositoryCloned "$repoUrl" "$workPath"; then
        echo -e "  ${yellow}⚠ Repository already exists: $owner/$repoName${nc}"
        echo -e "    Skipping clone. Use 'git pull' to update if needed."
        return 0
    fi

    echo -e "  ${yellow}Cloning $owner/$repoName...${nc}"

    if git clone --recursive "$repoUrl" "$repoPath" 2>/dev/null; then
        echo -e "    ${green}✓ Cloned successfully${nc}"
        if [ -f "${repoPath}/.gitmodules" ]; then
            echo -e "    ${green}✓ Submodules initialised${nc}"
        fi
        return 0
    else
        echo -e "    ${red}✗ Clone failed${nc}"
        return 1
    fi
}

cloneRepositories()
{
    local configPath=${1:-$repoConfigPath}
    local jqHint="${jqInstallHint:-${yellow}Please install jq via your package manager.${nc}}"

    echo -e "${cyan}=== Repository Cloning ===${nc}"
    echo ""

    if ! isGitInstalled; then
        echo -e "${red}✗ Git is not installed.${nc}"
        echo -e "${yellow}Please install Git first.${nc}"
        return 1
    fi

    if [ ! -f "$configPath" ]; then
        echo -e "${red}✗ Configuration file not found: $configPath${nc}"
        return 1
    fi

    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${red}✗ jq is required to parse JSON. Please install it first.${nc}"
        echo -e "  $jqHint"
        return 1
    fi

    local workPath
    local repositories
    workPath=$(jq -r '.workPathUnix' "$configPath")
    repositories=$(jq -r '.repositories[]?' "$configPath")

    workPath=$(echo "$workPath" | sed "s|\$HOME|$HOME|g" | sed "s|\$USER|$USER|g")

    if [ -z "$workPath" ] || [ "$workPath" = "null" ]; then
        echo -e "${red}✗ JSON file must contain a 'workPathUnix' property.${nc}"
        return 1
    fi

    if [ -z "$repositories" ]; then
        echo -e "${yellow}No repositories specified in configuration file.${nc}"
        return 0
    fi

    local repoCount
    repoCount=$(echo "$repositories" | grep -c . || echo "0")
    echo -e "${cyan}Work directory: $workPath${nc}"
    echo -e "${cyan}Found $repoCount repository/repositories in configuration file.${nc}"
    echo ""

    if [ ! -d "$workPath" ]; then
        echo -e "${yellow}Creating work directory: $workPath${nc}"
        mkdir -p "$workPath"
        echo -e "${green}✓ Work directory created${nc}"
        echo ""
    fi

    local clonedCount=0
    local skippedCount=0
    local failedCount=0

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
