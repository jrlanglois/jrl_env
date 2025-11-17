#!/bin/bash
# Shared application installation logic

# shellcheck disable=SC2154 # colours supplied by wrappers

commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

installPackages()
{
    local packageList=$1
    local checkFunction=$2
    local installFunction=$3
    local updateFunction=$4
    local label=$5
    local installedCount=0
    local updatedCount=0
    local failedCount=0

    if [ -z "$packageList" ]; then
        return 0
    fi

    echo -e "${cyan}=== Processing ${label} ===${nc}"
    echo ""

    while IFS= read -r packageName; do
        if [ -z "$packageName" ]; then
            continue
        fi

        echo -e "${yellow}Processing: $packageName${nc}"

        if "$checkFunction" "$packageName"; then
            echo -e "  ${cyan}Already installed. Updating...${nc}"
            if "$updateFunction" "$packageName"; then
                echo -e "  ${green}✓ Updated successfully${nc}"
                ((updatedCount++))
            else
                echo -e "  ${yellow}⚠ Update check completed (may already be up to date)${nc}"
                ((updatedCount++))
            fi
        else
            echo -e "  ${cyan}Not installed. Installing...${nc}"
            if "$installFunction" "$packageName"; then
                echo -e "  ${green}✓ Installed successfully${nc}"
                ((installedCount++))
            else
                echo -e "  ${red}✗ Installation failed${nc}"
                ((failedCount++))
            fi
        fi
        echo ""
    done <<< "$packageList"

    installPackages_installedCount=$installedCount
    installPackages_updatedCount=$updatedCount
    installPackages_failedCount=$failedCount
}

installFromConfig()
{
    local configPath=${1:-$appsConfigPath}
    local packageExtractor=$2
    local packageLabel=$3
    local checkFunction=$4
    local installFunction=$5
    local updateFunction=$6

    local packages
    packages=$(jq -r "$packageExtractor" "$configPath" 2>/dev/null || echo "")

    installPackages "$packages" "$checkFunction" "$installFunction" "$updateFunction" "$packageLabel"

    local installed=$installPackages_installedCount
    local updated=$installPackages_updatedCount
    local failed=$installPackages_failedCount

    installFromConfig_installed=$installed
    installFromConfig_updated=$updated
    installFromConfig_failed=$failed
}

installApps()
{
    local configPath=${1:-$appsConfigPath}
    local jqHint="${jqInstallHint:-${yellow}Please install jq via your package manager.${nc}}"

    if [ ! -f "$configPath" ]; then
        echo -e "${red}✗ Configuration file not found: $configPath${nc}"
        return 1
    fi

    if ! commandExists jq; then
        echo -e "${red}✗ jq is required to parse JSON. Please install it first.${nc}"
        echo -e "  $jqHint"
        return 1
    fi

    echo -e "${cyan}=== Application Installation ===${nc}"
    echo ""

    local totalInstalled=0
    local totalUpdated=0
    local totalFailed=0

    installFromConfig "$configPath" "${installApps_extractPrimary:-.brew[]?}" "Primary packages" installApps_checkPrimary installApps_installPrimary installApps_updatePrimary
    totalInstalled=$((totalInstalled + installFromConfig_installed))
    totalUpdated=$((totalUpdated + installFromConfig_updated))
    totalFailed=$((totalFailed + installFromConfig_failed))

    installFromConfig "$configPath" "${installApps_extractSecondary:-.brewCask[]?}" "Secondary packages" installApps_checkSecondary installApps_installSecondary installApps_updateSecondary
    totalInstalled=$((totalInstalled + installFromConfig_installed))
    totalUpdated=$((totalUpdated + installFromConfig_updated))
    totalFailed=$((totalFailed + installFromConfig_failed))

    echo -e "${cyan}Summary:${nc}"
    echo -e "  ${green}Installed: $totalInstalled${nc}"
    echo -e "  ${green}Updated: $totalUpdated${nc}"
    if [ $totalFailed -gt 0 ]; then
        echo -e "  ${red}Failed: $totalFailed${nc}"
    fi

    return 0
}
