#!/bin/bash
# Shared Google Fonts installation logic

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../core/logging.sh"

tempDirBase="${TMPDIR:-/tmp}"
fontInstallDir=""

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
                    logSuccess "    Downloaded $variant successfully"
                    echo "$filePath"
                    return 0
                else
                    rm -f "$filePath"
                fi
            fi
        done
    done

    # Fallback: Try to get font URL from Google Fonts CSS API
    # This works for fonts like Bungee Spice that might not be in the GitHub repo structure
    if [ "$variant" = "Regular" ]; then
        local apiFontName
        apiFontName="${fontName// /+}"
        local cssUrl="https://fonts.googleapis.com/css2?family=${apiFontName}&display=swap"
        local cssContent
        cssContent=$(curl -fsSL "$cssUrl" 2>/dev/null)

        if [ -n "$cssContent" ]; then
            # Extract font URLs from the CSS - prefer TTF over WOFF2 for OS compatibility
            local fontUrl
            local fileExt="ttf"

            # Try to find TTF first (more compatible across OS)
            fontUrl=$(echo "$cssContent" | grep -oE 'url\(https://fonts\.gstatic\.com/[^)]+\.ttf\)' | head -1 | sed 's/url(\(.*\))/\1/')

            # If no TTF found, try WOFF2 (web font format, may need conversion)
            if [ -z "$fontUrl" ]; then
                fontUrl=$(echo "$cssContent" | grep -oE 'url\(https://fonts\.gstatic\.com/[^)]+\.woff2\)' | head -1 | sed 's/url(\(.*\))/\1/')
                fileExt="woff2"
            fi

            if [ -n "$fontUrl" ]; then
                local tempFileName
                tempFileName="${normalisedName}-${variant}.${fileExt}"
                filePath="${outputPath}/${tempFileName}"

                if curl -fsSL -o "$filePath" "$fontUrl" 2>/dev/null && [ -f "$filePath" ] && [ -s "$filePath" ]; then
                    local fileSize
                    fileSize=$(stat -f%z "$filePath" 2>/dev/null || stat -c%s "$filePath" 2>/dev/null || echo "0")
                    if [ "$fileSize" -gt 1000 ]; then
                        # If we got WOFF2, try to convert to TTF if woff2_decompress is available
                        if [ "$fileExt" = "woff2" ]; then
                            if commandExists woff2_decompress; then
                                local ttfPath="${outputPath}/${normalisedName}-${variant}.ttf"
                                if woff2_decompress "$filePath" -o "$ttfPath" 2>/dev/null && [ -f "$ttfPath" ]; then
                                    rm -f "$filePath"
                                    filePath="$ttfPath"
                                    logSuccess "    Downloaded and converted $variant successfully (via Google Fonts API)"
                                else
                                    logWarning "    Downloaded WOFF2 format (may not be installable on all systems)"
                                    logNote "    Install woff2 tools to convert: sudo apt-get install woff2"
                                fi
                            else
                                logWarning "    Downloaded WOFF2 format (may not be installable on all systems)"
                                logNote "    Install woff2 tools to convert: sudo apt-get install woff2"
                            fi
                        else
                            logSuccess "    Downloaded $variant successfully (via Google Fonts API)"
                        fi
                        echo "$filePath"
                        return 0
                    else
                        rm -f "$filePath"
                    fi
                fi
            fi
        fi
    fi

    return 1
}

installFont()
{
    local fontPath=$1

    if [ ! -f "$fontPath" ]; then
        logError "    Font file not found: $fontPath"
        return 1
    fi

    # Check if file is WOFF2 (web font format, not directly installable on most OS)
    local fileExt
    fileExt=$(echo "$fontPath" | sed 's/.*\.//' | tr '[:upper:]' '[:lower:]')
    if [ "$fileExt" = "woff2" ]; then
        logWarning "    WOFF2 format cannot be directly installed"
        logNote "    File saved at: $fontPath"
        logNote "    Convert to TTF first using woff2 tools"
        return 1
    fi

    local fontName
    local destinationPath
    fontName=$(basename "$fontPath")
    destinationPath="${fontInstallDir}/${fontName}"

    if [ -f "$destinationPath" ]; then
        logWarning "    Font already installed, skipping..."
        return 0
    fi

    mkdir -p "$fontInstallDir"

    if cp "$fontPath" "$destinationPath"; then
        logSuccess "    Installed successfully"
        return 0
    else
        logError "    Installation failed"
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

    fontInstallDir="${fontInstallDirPath:?fontInstallDirPath must be set}"

    if [ ${#variants[@]} -eq 0 ]; then
        variants=("Regular" "Bold" "Italic" "BoldItalic")
    fi

    if [ ! -f "$configPath" ]; then
        logError "Configuration file not found: $configPath"
        return 1
    fi

    # Use Python script for parallel processing
    local scriptDir
    scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local pythonScript="${scriptDir}/../helpers/installFonts.py"

    if [ ! -f "$pythonScript" ]; then
        logError "Python script not found: $pythonScript"
        return 1
    fi

    if ! commandExists python3; then
        logError "python3 is required for font installation. Please install it first."
        return 1
    fi

    # Build variant arguments
    local variantArgs=()
    for variant in "${variants[@]}"; do
        variantArgs+=("$variant")
    done

    # Call Python script
    python3 "$pythonScript" "$configPath" "$fontInstallDir" "${variantArgs[@]}"
    return $?
}
