#!/bin/bash
# Script to download and install Google Fonts on macOS
# Downloads fonts from Google Fonts GitHub repository and installs them

set -e

# Colours for output
red='\033[0;31m'
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
nc='\033[0m' # No Colour

# Get script directory
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
configPath="${scriptDir}/../configs/fonts.json"
fontsDir="$HOME/Library/Fonts"
FONTS_DIR="$fontsDir"

# Function to check if a command exists
commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a font is installed
isFontInstalled()
{
    local fontName=$1
    if [ -f "${FONTS_DIR}/${fontName}" ] || find "$fontsDir" -iname "*${fontName}*" -type f | grep -q .; then
        return 0
    fi
    return 1
}

# Function to download a Google Font
downloadGoogleFont()
{
    local fontName=$1
    local variant=${2:-"Regular"}
    local outputPath=${3:-$TMPDIR}
    local normalisedName
    local normalisedVariant
    local fileName
    local filePath

    # Normalise font name for URL (lowercase, spaces to hyphens)
    normalisedName=$(echo "$fontName" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    normalisedVariant=$(echo "$variant" | tr -d ' ')

    # Try different URL patterns
    local urlPatterns=(
        "https://github.com/google/fonts/raw/main/ofl/${normalisedName}/${normalisedName}-${normalisedVariant}.ttf"
        "https://github.com/google/fonts/raw/main/ofl/${normalisedName}/${normalisedVariant}.ttf"
        "https://github.com/google/fonts/raw/main/apache/${normalisedName}/${normalisedName}-${normalisedVariant}.ttf"
        "https://github.com/google/fonts/raw/main/apache/${normalisedName}/${normalisedVariant}.ttf"
    )

    fileName="${normalisedName}-${normalisedVariant}.ttf"
    filePath="${outputPath}/${fileName}"

    echo -e "  ${yellow}Downloading $fontName $variant...${nc}"

    for url in "${urlPatterns[@]}"; do
        if curl -fsSL -o "$filePath" "$url" 2>/dev/null && [ -f "$filePath" ] && [ -s "$filePath" ]; then
            echo -e "    ${green}✓ Downloaded successfully${nc}"
            echo "$filePath"
            return 0
        fi
    done

    echo -e "    ${red}✗ Download failed: font variant not found${nc}"
    return 1
}

# Function to install a font
installFont()
{
    local fontPath=$1
    local fontName
    local destinationPath

    if [ ! -f "$fontPath" ]; then
        echo -e "    ${red}✗ Font file not found: $fontPath${nc}"
        return 1
    fi

    fontName=$(basename "$fontPath")
    destinationPath="${FONTS_DIR}/${fontName}"

    # Check if already installed
    if [ -f "$destinationPath" ]; then
        echo -e "    ${yellow}⚠ Font already installed, skipping...${nc}"
        return 0
    fi

    # Create Fonts directory if it doesn't exist
    mkdir -p "$fontsDir"

    # Copy font to Fonts directory
    if cp "$fontPath" "$destinationPath"; then
        echo -e "    ${green}✓ Installed successfully${nc}"
        return 0
    else
        echo -e "    ${red}✗ Installation failed${nc}"
        return 1
    fi
}

# Function to install Google Fonts
installGoogleFonts()
{
    local configPath=${1:-$configPath}
    local variants=("${@:2}")
    local fontNames
    local fontCount
    local tempDir
    local installedCount=0
    local skippedCount=0
    local failedCount=0

    if [ ${#variants[@]} -eq 0 ]; then
        variants=("Regular" "Bold" "Italic" "BoldItalic")
    fi

    echo -e "${cyan}=== Google Fonts Installation ===${nc}"
    echo ""

    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${red}✗ Configuration file not found: $configPath${nc}"
        return 1
    fi

    # Check if jq is available
    if ! commandExists jq; then
        echo -e "${red}✗ jq is required to parse JSON. Please install it first.${nc}"
        echo -e "${yellow}  brew install jq${nc}"
        return 1
    fi

    # Parse JSON
    fontNames=$(jq -r '.googleFonts[]?' "$configPath" 2>/dev/null)

    if [ -z "$fontNames" ]; then
        echo -e "${yellow}No fonts specified in configuration file.${nc}"
        return 0
    fi

    fontCount=$(echo "$fontNames" | grep -c . || echo "0")
    echo -e "${cyan}Found $fontCount font(s) in configuration file.${nc}"
    echo ""

    # Create temporary directory
    tempDir=$(mktemp -d -t GoogleFonts.XXXXXX)

    # Process each font
    while IFS= read -r fontName; do
        if [ -z "$fontName" ]; then
            continue
        fi

        echo -e "${yellow}Processing: $fontName${nc}"

        local fontInstalled=false

        # Try to download and install each variant
        for variant in "${variants[@]}"; do
            local fontPath
            fontPath=$(downloadGoogleFont "$fontName" "$variant" "$tempDir")

            if [ -n "$fontPath" ] && [ -f "$fontPath" ]; then
                if installFont "$fontPath"; then
                    ((installedCount++))
                    fontInstalled=true
                else
                    ((failedCount++))
                fi
            else
                echo -e "    ${yellow}⚠ Variant '$variant' not available, skipping...${nc}"
            fi
        done

        if [ "$fontInstalled" = false ]; then
            ((skippedCount++))
        fi

        echo ""
    done <<< "$fontNames"

    # Clean up
    echo -e "${cyan}Cleaning up downloaded files...${nc}"
    rm -rf "$tempDir"
    echo -e "${green}✓ Temporary files removed successfully${nc}"
    echo ""

    echo -e "${cyan}Summary:${nc}"
    echo -e "  ${green}Installed: $installedCount font file(s)${nc}"
    if [ $skippedCount -gt 0 ]; then
        echo -e "  ${yellow}Skipped: $skippedCount font(s)${nc}"
    fi
    if [ $failedCount -gt 0 ]; then
        echo -e "  ${red}Failed: $failedCount font file(s)${nc}"
    fi

    echo ""
    echo -e "${green}Font installation complete!${nc}"
    echo -e "${yellow}Note: You may need to restart applications for new fonts to appear.${nc}"

    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installGoogleFonts "$@"
fi
