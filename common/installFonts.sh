#!/bin/bash
# Shared Google Fonts installation logic

# shellcheck disable=SC2154 # colour variables provided by callers

tempDirBase="${TMPDIR:-/tmp}"
fontInstallDir=""

commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

isFontInstalled()
{
    local fontName=$1
    if [ -f "${fontInstallDir}/${fontName}" ] || find "$fontInstallDir" -iname "*${fontName}*" -type f 2>/dev/null | grep -q .; then
        return 0
    fi
    return 1
}

downloadGoogleFont()
{
    local fontName=$1
    local variant=${2:-"Regular"}
    local outputPath=${3:-$tempDirBase}
    local normalisedName
    local normalisedVariant
    local fileName
    local filePath

    normalisedName=$(echo "$fontName" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    normalisedVariant=$(echo "$variant" | tr -d ' ')

    # Map common variant names to possible file name patterns
    local variantPatterns=()
    case "$variant" in
        "Regular")
            variantPatterns=("Regular" "400" "normal" "regular")
            ;;
        "Bold")
            variantPatterns=("Bold" "700" "bold" "Bold" "BoldRegular")
            ;;
        "Italic")
            variantPatterns=("Italic" "400italic" "italic" "Italic" "RegularItalic")
            ;;
        "BoldItalic")
            variantPatterns=("BoldItalic" "700italic" "bolditalic" "BoldItalic" "Bold-Italic")
            ;;
        *)
            variantPatterns=("$normalisedVariant" "$variant")
            ;;
    esac

    # Try different URL patterns and variant names
    for variantPattern in "${variantPatterns[@]}"; do
        local testVariant
        testVariant=$(echo "$variantPattern" | tr -d ' ')
        
        local urlPatterns=(
            "https://github.com/google/fonts/raw/main/ofl/${normalisedName}/${normalisedName}-${testVariant}.ttf"
            "https://github.com/google/fonts/raw/main/ofl/${normalisedName}/${testVariant}.ttf"
            "https://github.com/google/fonts/raw/main/apache/${normalisedName}/${normalisedName}-${testVariant}.ttf"
            "https://github.com/google/fonts/raw/main/apache/${normalisedName}/${testVariant}.ttf"
            "https://github.com/google/fonts/raw/main/ufl/${normalisedName}/${normalisedName}-${testVariant}.ttf"
            "https://github.com/google/fonts/raw/main/ufl/${normalisedName}/${testVariant}.ttf"
        )

        for url in "${urlPatterns[@]}"; do
            # Use a temporary file name to avoid conflicts
            local tempFileName
            tempFileName="${normalisedName}-${testVariant}.ttf"
            filePath="${outputPath}/${tempFileName}"

            # Try to download the file
            if curl -fsSL -o "$filePath" "$url" 2>/dev/null && [ -f "$filePath" ] && [ -s "$filePath" ]; then
                # Verify it's actually a font file (check file size and basic structure)
                local fileSize
                fileSize=$(stat -f%z "$filePath" 2>/dev/null || stat -c%s "$filePath" 2>/dev/null || echo "0")
                if [ "$fileSize" -gt 1000 ]; then
                    # Basic check: TTF/OTF files should have reasonable size
                    echo -e "    ${green}✓ Downloaded $variant successfully${nc}"
                    echo "$filePath"
                    return 0
                else
                    rm -f "$filePath"
                fi
            fi
        done
    done

    return 1
}

installFont()
{
    local fontPath=$1

    if [ ! -f "$fontPath" ]; then
        echo -e "    ${red}✗ Font file not found: $fontPath${nc}"
        return 1
    fi

    local fontName
    local destinationPath
    fontName=$(basename "$fontPath")
    destinationPath="${fontInstallDir}/${fontName}"

    if [ -f "$destinationPath" ]; then
        echo -e "    ${yellow}⚠ Font already installed, skipping...${nc}"
        return 0
    fi

    mkdir -p "$fontInstallDir"

    if cp "$fontPath" "$destinationPath"; then
        echo -e "    ${green}✓ Installed successfully${nc}"
        return 0
    else
        echo -e "    ${red}✗ Installation failed${nc}"
        return 1
    fi
}

refreshFontCache()
{
    if [ -n "${fontCacheCmd:-}" ]; then
        eval "$fontCacheCmd"
    fi
}

installGoogleFonts()
{
    local configPath=${1:-$fontsConfigPath}
    local variants=("${@:2}")
    local jqHint="${jqInstallHint:-${yellow}Please install jq via your package manager.${nc}}"

    fontInstallDir="${fontInstallDirPath:?fontInstallDirPath must be set}"

    if [ ${#variants[@]} -eq 0 ]; then
        variants=("Regular" "Bold" "Italic" "BoldItalic")
    fi

    echo -e "${cyan}=== Google Fonts Installation ===${nc}"
    echo ""

    if [ ! -f "$configPath" ]; then
        echo -e "${red}✗ Configuration file not found: $configPath${nc}"
        return 1
    fi

    if ! commandExists jq; then
        echo -e "${red}✗ jq is required to parse JSON. Please install it first.${nc}"
        echo -e "  $jqHint"
        return 1
    fi

    local fontNames
    fontNames=$(jq -r '.googleFonts[]?' "$configPath" 2>/dev/null)

    if [ -z "$fontNames" ]; then
        echo -e "${yellow}No fonts specified in configuration file.${nc}"
        return 0
    fi

    local fontCount
    fontCount=$(echo "$fontNames" | grep -c . || echo "0")
    echo -e "${cyan}Found $fontCount font(s) in configuration file.${nc}"
    echo ""

    local tempDir
    tempDir=$(mktemp -d -t GoogleFonts.XXXXXX)
    local installedCount=0
    local skippedCount=0
    local failedCount=0

    while IFS= read -r fontName; do
        if [ -z "$fontName" ]; then
            continue
        fi

        echo -e "${yellow}Processing: $fontName${nc}"
        local fontInstalled=false
        local anyVariantFound=false

        for variant in "${variants[@]}"; do
            local fontPath
            fontPath=$(downloadGoogleFont "$fontName" "$variant" "$tempDir" 2>/dev/null)

            if [ -n "$fontPath" ] && [ -f "$fontPath" ]; then
                anyVariantFound=true
                if installFont "$fontPath"; then
                    ((installedCount++))
                    fontInstalled=true
                else
                    ((failedCount++))
                fi
            fi
        done

        if [ "$fontInstalled" = false ] && [ "$anyVariantFound" = false ]; then
            echo -e "  ${yellow}⚠ No variants available for this font${nc}"
        fi

        if [ "$fontInstalled" = false ]; then
            ((skippedCount++))
        fi

        echo ""
    done <<< "$fontNames"

    echo -e "${cyan}Cleaning up downloaded files...${nc}"
    rm -rf "$tempDir"
    echo -e "${green}✓ Temporary files removed successfully${nc}"
    echo ""

    refreshFontCache

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
