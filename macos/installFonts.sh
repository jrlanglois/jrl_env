#!/bin/bash
# Script to download and install Google Fonts on macOS
# Downloads fonts from Google Fonts GitHub repository and installs them

set -e

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="${SCRIPT_DIR}/../configs/fonts.json"
FONTS_DIR="$HOME/Library/Fonts"

# Function to check if a command exists
commandExists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a font is installed
isFontInstalled() {
    local fontName=$1
    if [ -f "${FONTS_DIR}/${fontName}" ] || find "$FONTS_DIR" -iname "*${fontName}*" -type f | grep -q .; then
        return 0
    fi
    return 1
}

# Function to download a Google Font
downloadGoogleFont() {
    local fontName=$1
    local variant=${2:-"Regular"}
    local outputPath=${3:-$TMPDIR}
    
    # Normalise font name for URL (lowercase, spaces to hyphens)
    local normalisedName=$(echo "$fontName" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    local normalisedVariant=$(echo "$variant" | tr -d ' ')
    
    # Try different URL patterns
    local urlPatterns=(
        "https://github.com/google/fonts/raw/main/ofl/${normalisedName}/${normalisedName}-${normalisedVariant}.ttf"
        "https://github.com/google/fonts/raw/main/ofl/${normalisedName}/${normalisedVariant}.ttf"
        "https://github.com/google/fonts/raw/main/apache/${normalisedName}/${normalisedName}-${normalisedVariant}.ttf"
        "https://github.com/google/fonts/raw/main/apache/${normalisedName}/${normalisedVariant}.ttf"
    )
    
    local fileName="${normalisedName}-${normalisedVariant}.ttf"
    local filePath="${outputPath}/${fileName}"
    
    echo -e "  ${YELLOW}Downloading $fontName $variant...${NC}"
    
    for url in "${urlPatterns[@]}"; do
        if curl -fsSL -o "$filePath" "$url" 2>/dev/null && [ -f "$filePath" ] && [ -s "$filePath" ]; then
            echo -e "    ${GREEN}✓ Downloaded successfully${NC}"
            echo "$filePath"
            return 0
        fi
    done
    
    echo -e "    ${RED}✗ Download failed: font variant not found${NC}"
    return 1
}

# Function to install a font
installFont() {
    local fontPath=$1
    
    if [ ! -f "$fontPath" ]; then
        echo -e "    ${RED}✗ Font file not found: $fontPath${NC}"
        return 1
    fi
    
    local fontName=$(basename "$fontPath")
    local destinationPath="${FONTS_DIR}/${fontName}"
    
    # Check if already installed
    if [ -f "$destinationPath" ]; then
        echo -e "    ${YELLOW}⚠ Font already installed, skipping...${NC}"
        return 0
    fi
    
    # Create Fonts directory if it doesn't exist
    mkdir -p "$FONTS_DIR"
    
    # Copy font to Fonts directory
    if cp "$fontPath" "$destinationPath"; then
        echo -e "    ${GREEN}✓ Installed successfully${NC}"
        return 0
    else
        echo -e "    ${RED}✗ Installation failed${NC}"
        return 1
    fi
}

# Function to install Google Fonts
installGoogleFonts() {
    local configPath=${1:-$CONFIG_PATH}
    local variants=("${@:2}")
    
    if [ ${#variants[@]} -eq 0 ]; then
        variants=("Regular" "Bold" "Italic" "BoldItalic")
    fi
    
    echo -e "${CYAN}=== Google Fonts Installation ===${NC}"
    echo ""
    
    # Check if config file exists
    if [ ! -f "$configPath" ]; then
        echo -e "${RED}✗ Configuration file not found: $configPath${NC}"
        return 1
    fi
    
    # Check if jq is available
    if ! commandExists jq; then
        echo -e "${RED}✗ jq is required to parse JSON. Please install it first.${NC}"
        echo -e "${YELLOW}  brew install jq${NC}"
        return 1
    fi
    
    # Parse JSON
    local fontNames=$(jq -r '.googleFonts[]?' "$configPath" 2>/dev/null)
    
    if [ -z "$fontNames" ]; then
        echo -e "${YELLOW}No fonts specified in configuration file.${NC}"
        return 0
    fi
    
    local fontCount=$(echo "$fontNames" | grep -c . || echo "0")
    echo -e "${CYAN}Found $fontCount font(s) in configuration file.${NC}"
    echo ""
    
    # Create temporary directory
    local tempDir=$(mktemp -d -t GoogleFonts.XXXXXX)
    local installedCount=0
    local skippedCount=0
    local failedCount=0
    
    # Process each font
    while IFS= read -r fontName; do
        if [ -z "$fontName" ]; then
            continue
        fi
        
        echo -e "${YELLOW}Processing: $fontName${NC}"
        
        local fontInstalled=false
        
        # Try to download and install each variant
        for variant in "${variants[@]}"; do
            local fontPath=$(downloadGoogleFont "$fontName" "$variant" "$tempDir")
            
            if [ -n "$fontPath" ] && [ -f "$fontPath" ]; then
                if installFont "$fontPath"; then
                    ((installedCount++))
                    fontInstalled=true
                else
                    ((failedCount++))
                fi
            else
                echo -e "    ${YELLOW}⚠ Variant '$variant' not available, skipping...${NC}"
            fi
        done
        
        if [ "$fontInstalled" = false ]; then
            ((skippedCount++))
        fi
        
        echo ""
    done <<< "$fontNames"
    
    # Clean up
    echo -e "${CYAN}Cleaning up downloaded files...${NC}"
    rm -rf "$tempDir"
    echo -e "${GREEN}✓ Temporary files removed successfully${NC}"
    echo ""
    
    echo -e "${CYAN}Summary:${NC}"
    echo -e "  ${GREEN}Installed: $installedCount font file(s)${NC}"
    if [ $skippedCount -gt 0 ]; then
        echo -e "  ${YELLOW}Skipped: $skippedCount font(s)${NC}"
    fi
    if [ $failedCount -gt 0 ]; then
        echo -e "  ${RED}Failed: $failedCount font file(s)${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}Font installation complete!${NC}"
    echo -e "${YELLOW}Note: You may need to restart applications for new fonts to appear.${NC}"
    
    return 0
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    installGoogleFonts "$@"
fi
