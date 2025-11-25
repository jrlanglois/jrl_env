#!/bin/bash
# Unified setup wrapper for Unix-like systems (macOS, Linux)
# Auto-detects OS and runs the appropriate Python setup script
#
# Options:
#   --yes, -y    Auto-accept prompts (for Docker/CI)

# Parse --yes flag before set -u
AUTO_YES=false
for arg in "$@"; do
    case $arg in
        --yes|-y)
            AUTO_YES=true
            ;;
    esac
done

set -euo pipefail

# Get the directory where this script is located
scriptDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Simple commandExists function (no longer need common.sh)
commandExists()
{
    command -v "$1" >/dev/null 2>&1
}

# Check if Python 3 is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required but not found in PATH" >&2
    echo ""

    # Detect OS to provide installation instructions
    osType="unknown"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        osType="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Try to detect specific Linux distribution
        if [ -f /etc/os-release ]; then
            # shellcheck source=/dev/null
            source /etc/os-release

            if [[ "$ID" == "ubuntu" ]] || [[ "$ID" == "debian" ]]; then
                osType="ubuntu"
            elif [[ "$ID" == "raspbian" ]]; then
                osType="raspberrypi"
            elif [[ "$ID" == "rhel" ]] || [[ "$ID" == "fedora" ]] || [[ "$ID" == "centos" ]]; then
                osType="redhat"
            elif [[ "$ID" == "opensuse-leap" ]] || [[ "$ID" == "opensuse-tumbleweed" ]] || [[ "$ID" == "sles" ]]; then
                osType="opensuse"
            elif [[ "$ID" == "arch" ]]; then
                osType="archlinux"
            elif [[ "$ID_LIKE" == *"rhel"* ]] || [[ "$ID_LIKE" == *"fedora"* ]] || [[ "$ID_LIKE" == *"centos"* ]]; then
                osType="redhat"
            elif [[ "$ID_LIKE" == *"suse"* ]] || [[ "$ID_LIKE" == *"opensuse"* ]]; then
                osType="opensuse"
            elif [[ "$ID_LIKE" == *"arch"* ]]; then
                osType="archlinux"
            fi
        fi
    fi

    # Prompt user to install Python3 (unless --yes flag provided)
    if [ "$AUTO_YES" = true ]; then
        echo "Auto-installing Python3 (--yes flag provided)..."
    else
        echo "Would you like to install Python3? (y/N)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Setup cancelled. Python3 is required to continue."
            exit 1
        fi
    fi

    # Attempt to install Python3 based on OS
    installSuccess=false
    case "$osType" in
        macos)
            echo "Installing Python3 via Homebrew..."
            if command -v brew >/dev/null 2>&1; then
                if brew install python3; then
                    installSuccess=true
                fi
            else
                echo "Error: Homebrew not found. Please install Homebrew first:" >&2
                echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"" >&2
            fi
            ;;
        ubuntu|raspberrypi)
            echo "Installing Python3 via apt..."
            if command -v sudo >/dev/null 2>&1; then
                if sudo apt-get update && sudo apt-get install -y python3 python3-pip; then
                    installSuccess=true
                fi
            else
                echo "Error: sudo not available. Please install Python3 manually:" >&2
                echo "apt-get update && apt-get install -y python3 python3-pip" >&2
            fi
            ;;
        redhat)
            echo "Installing Python3 via package manager..."
            if command -v dnf >/dev/null 2>&1; then
                if command -v sudo >/dev/null 2>&1; then
                    if sudo dnf install -y python3 python3-pip; then
                        installSuccess=true
                    fi
                else
                    echo "Error: sudo not available. Please install Python3 manually:" >&2
                    echo "dnf install -y python3 python3-pip" >&2
                fi
            elif command -v yum >/dev/null 2>&1; then
                if command -v sudo >/dev/null 2>&1; then
                    if sudo yum install -y python3 python3-pip; then
                        installSuccess=true
                    fi
                else
                    echo "Error: sudo not available. Please install Python3 manually:" >&2
                    echo "yum install -y python3 python3-pip" >&2
                fi
            else
                echo "Error: No suitable package manager found (dnf/yum)." >&2
                echo "Please install Python3 manually." >&2
            fi
            ;;
        opensuse)
            echo "Installing Python3 via zypper..."
            if command -v zypper >/dev/null 2>&1; then
                if command -v sudo >/dev/null 2>&1; then
                    if sudo zypper install -y python3 python3-pip; then
                        installSuccess=true
                    fi
                else
                    echo "Error: sudo not available. Please install Python3 manually:" >&2
                    echo "zypper install -y python3 python3-pip" >&2
                fi
            else
                echo "Error: zypper not found. Please install Python3 manually." >&2
            fi
            ;;
        archlinux)
            echo "Installing Python3 via pacman..."
            if command -v pacman >/dev/null 2>&1; then
                if command -v sudo >/dev/null 2>&1; then
                    if sudo pacman -S --noconfirm python python-pip; then
                        installSuccess=true
                    fi
                else
                    echo "Error: sudo not available. Please install Python3 manually:" >&2
                    echo "pacman -S --noconfirm python python-pip" >&2
                fi
            else
                echo "Error: pacman not found. Please install Python3 manually." >&2
            fi
            ;;
        *)
            echo "Error: Unable to auto-install Python3 on this system." >&2
            echo "Please install Python3 manually and try again." >&2
            ;;
    esac

    if [ "$installSuccess" = false ]; then
        echo "Failed to install Python3. Setup cancelled." >&2
        exit 1
    fi

    # Verify Python3 is now available
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Error: Python3 installation completed but python3 command not found in PATH." >&2
        echo "Please restart your terminal and try again." >&2
        exit 1
    fi

    echo "Python3 installed successfully!"
    echo ""
fi

# Run the unified Python setup script
exec python3 "$scriptDir/setup.py" "$@"
