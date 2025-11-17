#!/bin/bash
# Script to clone Git repositories from repositories.json
# Clones repositories recursively (including submodules) to a configured work directory

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="${SCRIPT_DIR}/../configs/repositories.json"

# Function to check if Git is installed
isGitInstalled() {
    if command -v git >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Function to check if a repository is already cloned
isRepositoryCloned() {
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
getRepositoryOwner() {
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
getRepositoryName() {
    local repoUrl=$1
    echo "$repoUrl" | sed -E 's|.*[:/]([^/]+?)(\.git)?$|\1|'
}

# Function to clone a single repository recursively
cloneRepository() {
    local repoUrl=$1
    local workPath=$2
    
    local owner=$(getRepositoryOwner "$repoUrl")
    local repoName=$(getRepositoryName "$repoUrl")
    
    if [ -z "$owner" ] || [ -z "$repoName" ]; then
        echo -e "  ${RED}✗ Failed to extract owner or repository name from URL${NC}"
        return 1
    fi
    
    # Create owner directory if it doesn't exist
    local ownerPath="${workPath}/${owner}"
    mkdir -p "$ownerPath"
    
    local repoPath="${ownerPath}/${repoName}"
    
    # Check if already cloned
    if isRepositoryCloned "$repoUrl" "$workPath"; then
        echo -e "  ${YELLOW}⚠ Repository already exists: $owner/$repoName${NC}"
        echo -e "    Skipping clone. Use 'git pull' to update if needed."
        return 0
    fi
    
    echo -e "  ${YELLOW}Cloning $owner/$repoName...${NC}"
    
    # Clone with recursive flag to include submodules
    if git clone --recursive "$repoUrl" "$repoPath" 2>/dev/null; then
        echo -e "    ${GREEN}✓ Cloned successfully${NC}"
        
        # Check if submodules were initialised
        if [ -f "${repoPath}/.gitmodules" ]; then
            echo -e "    ${GREEN}✓ Submodules initialised${NC}"
        fi
        
        return 0
    else
        echo -e "    ${RED}✗ Clone failed${NC}"
        return 1
    fi
}

# Function to clone all repositories
cloneRepositories() {
    local configPath=${1:-$CONFIG_PATH}
    
    echo -e "${CYAN}=== Repository Cloning ===${NC}"
    echo ""
    
    # Check if Git is installed
    if ! isGitInstalled; then
        echo -e "${RED}✗ Git is not installed.${NC}"
        echo -e "${YELLOW}Please install Git first.${NC}"
        return 1
    fi
    
    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${RED}✗ Configuration file not found: $configPath${NC}"
        return 1
    fi
    
    # Check if jq is available
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${RED}✗ jq is required to parse JSON. Please install it first.${NC}"
        echo -e "${YELLOW}  brew install jq${NC}"
        return 1
    fi
    
    # Parse JSON
    local workPath=$(jq -r '.workPathUnix' "$configPath")
    local repositories=$(jq -r '.repositories[]?' "$configPath")
    
    # Expand $HOME and $USER if present in path
    workPath=$(echo "$workPath" | sed "s|\$HOME|$HOME|g" | sed "s|\$USER|$USER|g")
    
    if [ -z "$workPath" ] || [ "$workPath" = "null" ]; then
        echo -e "${RED}✗ JSON file must contain a 'workPathUnix' property.${NC}"
        return 1
    fi
    
    if [ -z "$repositories" ]; then
        echo -e "${YELLOW}No repositories specified in configuration file.${NC}"
        return 0
    fi
    
    local repoCount=$(echo "$repositories" | grep -c . || echo "0")
    echo -e "${CYAN}Work directory: $workPath${NC}"
    echo -e "${CYAN}Found $repoCount repository/repositories in configuration file.${NC}"
    echo ""
    
    # Create work directory if it doesn't exist
    if [ ! -d "$workPath" ]; then
        echo -e "${YELLOW}Creating work directory: $workPath${NC}"
        mkdir -p "$workPath"
        echo -e "${GREEN}✓ Work directory created${NC}"
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
        
        echo -e "${YELLOW}Processing: $repoUrl${NC}"
        
        if cloneRepository "$repoUrl" "$workPath"; then
            ((clonedCount++))
        elif isRepositoryCloned "$repoUrl" "$workPath"; then
            ((skippedCount++))
        else
            ((failedCount++))
        fi
        
        echo ""
    done <<< "$repositories"
    
    echo -e "${CYAN}Summary:${NC}"
    echo -e "  ${GREEN}Cloned: $clonedCount repository/repositories${NC}"
    if [ $skippedCount -gt 0 ]; then
        echo -e "  ${YELLOW}Skipped: $skippedCount repository/repositories (already exist)${NC}"
    fi
    if [ $failedCount -gt 0 ]; then
        echo -e "  ${RED}Failed: $failedCount repository/repositories${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}Repository cloning complete!${NC}"
    
    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    cloneRepositories "$@"
fi
