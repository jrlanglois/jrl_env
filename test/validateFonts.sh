#!/bin/bash
# Enhanced validation for Google Fonts
# Checks if fonts actually exist in Google Fonts API

# Source all core tools (singular entry point)
# shellcheck source=../common/core/tools.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../common/core/tools.sh"

validateFonts()
{
    local configPath=$1
    local errors=0

    if [ ! -f "$configPath" ]; then
        logError "Config file not found: $configPath"
        return 1
    fi

    logSection "Validating Google Fonts"
    echo ""

    # Check if curl is available
    if ! command -v curl >/dev/null 2>&1; then
        logError "curl is not available. Cannot validate fonts."
        return 1
    fi

    # Get list of fonts from config
    local fonts
    fonts=$(jq -r '.googleFonts[]?' "$configPath" 2>/dev/null || echo "")

    if [ -z "$fonts" ]; then
        logWarning "No fonts specified in config"
        return 0
    fi

    logNote "Validating fonts against Google Fonts..."
    logNote "This may take a moment..."

    # Use Google Fonts CSS API to check if fonts exist
    # We'll check each font individually by trying to fetch its CSS
    local tempFontList
    tempFontList=$(mktemp)

    # Try to fetch font list from a public source
    # Using fonts.google.com metadata endpoint (no API key needed)
    local googleFontsListUrl="https://fonts.google.com/metadata/fonts"
    local fetched=false

    # Try to fetch the font list
    if curl -s --max-time 10 -H "User-Agent: Mozilla/5.0" "$googleFontsListUrl" 2>/dev/null | jq -r '.familyMetadataList[].family' 2>/dev/null > "$tempFontList"; then
        fetched=true
    fi

    if [ "$fetched" = true ]; then
        while IFS= read -r font; do
            if [ -z "$font" ]; then
                continue
            fi

            # Normalize font name (replace spaces with + for URL)
            local fontUrlName
            fontUrlName=$(echo "$font" | sed 's/ /+/g')

            # Check if font exists in the fetched list
            if grep -qi "^${font}$" "$tempFontList" 2>/dev/null; then
                logSuccess "  $font"
            else
                # Try checking via CSS API directly
                local cssUrl="https://fonts.googleapis.com/css2?family=${fontUrlName}:wght@400"
                if curl -s --max-time 5 -o /dev/null -w "%{http_code}" "$cssUrl" 2>/dev/null | grep -q "200"; then
                    logSuccess "  $font (verified via CSS API)"
                else
                    logError "  $font (not found in Google Fonts)"
                    ((errors++))
                fi
            fi
        done <<< "$fonts"
    else
        # Fallback: check each font individually via CSS API
        logNote "Fetching font list failed, checking fonts individually..."
        while IFS= read -r font; do
            if [ -z "$font" ]; then
                continue
            fi

            local fontUrlName
            fontUrlName=$(echo "$font" | sed 's/ /+/g')
            local cssUrl="https://fonts.googleapis.com/css2?family=${fontUrlName}:wght@400"

            if curl -s --max-time 5 -o /dev/null -w "%{http_code}" "$cssUrl" 2>/dev/null | grep -q "200"; then
                logSuccess "  $font"
            else
                logError "  $font (not found in Google Fonts)"
                ((errors++))
            fi
        done <<< "$fonts"
    fi

    rm -f "$tempFontList"
    echo ""

    if [ $errors -eq 0 ]; then
        logSuccess "All fonts are valid!"
        return 0
    else
        logError "Found $errors invalid font(s)"
        return 1
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [ $# -eq 0 ]; then
        logError "Usage: $0 <path-to-fonts.json>"
        exit 1
    fi
    validateFonts "$1"
    exit $?
fi
