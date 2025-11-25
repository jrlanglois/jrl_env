#!/bin/bash
# Test jrl_env in Docker containers across different distros
# Provides interactive shells and automated testing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

printInfo()
{
    echo -e "${BLUE}$1${NC}"
}

printSuccess()
{
    echo -e "${GREEN}$1${NC}"
}

printError()
{
    echo -e "${RED}$1${NC}"
}

printWarning()
{
    echo -e "${YELLOW}$1${NC}"
}

showHelp()
{
    cat << EOF
jrl_env Docker Testing Tool

Usage: $0 <distro> [command]

Distros:
  ubuntu    Ubuntu 24.04 LTS
  fedora    Fedora 40
  arch      Arch Linux
  alpine    Alpine Linux
  opensuse  OpenSUSE Leap 15.6
  windows   Windows Server (requires Windows host)
  linux     Test all Linux distros
  all       Test all supported distros

Commands:
  shell     Interactive bash shell (default)
  test      Run setup.py --install --dryRun
  install   Run full setup.py --install
  validate  Run validation only

Examples:
  $0 ubuntu shell      # Interactive Ubuntu container
  $0 fedora test       # Dry-run test on Fedora
  $0 all validate      # Validate configs on all distros

Options:
  --verbose            Show verbose output
  --no-cache           Build without Docker cache
EOF
}

buildImage()
{
    local distro=$1
    local nocache=${2:-""}

    printInfo "Building $distro image..."

    cd "$PROJECT_ROOT"
    docker build \
        $nocache \
        -t "jrl-env-test:$distro" \
        -f "test/docker/Dockerfile.$distro" \
        . || {
        printError "Failed to build $distro image"
        return 1
    }

    printSuccess "✓ $distro image built"
}

runInteractive()
{
    local distro=$1

    printInfo "Starting interactive $distro container..."
    printInfo "Fresh system with ONLY git installed!"
    printInfo ""
    printInfo "Inside container, run:"
    printInfo "  ./setup.sh --yes                                   # Auto-accept prompts"
    printInfo "  ./setup.sh --yes --dryRun                          # Preview (no prompts)"
    printInfo "  ./setup.sh --yes --verbose 2>&1 | tee ~/setup.log  # Full logs"
    printInfo "  python3 -X dev setup.py --install --yes --verbose  # Full logs with dev mode"
    echo ""

    docker run -it --rm --dns 8.8.8.8 --dns 8.8.4.4 \
        \
        -v "$PROJECT_ROOT:/home/testuser/jrl_env" \
        --name "jrl-env-$distro-interactive" \
        "jrl-env-test:$distro" \
        bash
}

runTest()
{
    local distro=$1
    local verbose=${2:-""}

    printInfo "Testing jrl_env on $distro (dry-run)..."

    docker run --rm --dns 8.8.8.8 --dns 8.8.4.4 \
        \
        -v "$PROJECT_ROOT:/home/testuser/jrl_env" \
        "jrl-env-test:$distro" \
        bash -c "./setup.sh --yes --dryRun $verbose 2>&1 | tee ~/setup.log && cat ~/setup.log" || {
        printError "✗ $distro test failed"
        return 1
    }

    printSuccess "✓ $distro test passed"
}

runValidate()
{
    local distro=$1

    printInfo "Validating configs on $distro..."

    docker run --rm --dns 8.8.8.8 --dns 8.8.4.4 \
        -v "$PROJECT_ROOT:/home/testuser/jrl_env" \
        "jrl-env-test:$distro" \
        bash -c "python3 -m common.systems.validate" || {
        printError "✗ $distro validation failed"
        return 1
    }

    printSuccess "✓ $distro validation passed"
}

# Main logic
if [ $# -eq 0 ]; then
    showHelp
    exit 0
fi

DISTRO=$1
COMMAND=${2:-shell}
NOCACHE=""
VERBOSE=""

# Parse options
for arg in "$@"; do
    case $arg in
        --no-cache)
            NOCACHE="--no-cache"
            ;;
        --verbose)
            VERBOSE="--verbose"
            ;;
        --help|-h)
            showHelp
            exit 0
            ;;
    esac
done

# Build and run
if [ "$DISTRO" == "all" ]; then
    DISTROS=(ubuntu fedora arch alpine opensuse)
elif [ "$DISTRO" == "linux" ]; then
    DISTROS=(ubuntu fedora arch alpine opensuse)

    printInfo "Testing all distributions..."
    echo ""

    for distro in "${DISTROS[@]}"; do
        buildImage "$distro" "$NOCACHE" || continue

        case $COMMAND in
            test)
                runTest "$distro" "$VERBOSE"
                ;;
            validate)
                runValidate "$distro"
                ;;
            *)
                printWarning "Skipping shell for 'all' - use specific distro for interactive"
                ;;
        esac
        echo ""
    done

    printSuccess "All distros tested!"
else
    # Single distro
    buildImage "$DISTRO" "$NOCACHE" || exit 1

    case $COMMAND in
        shell)
            runInteractive "$DISTRO"
            ;;
        test)
            runTest "$DISTRO" "$VERBOSE"
            ;;
        install)
            printWarning "Running FULL install in container (not dry-run)..."
            docker run -it --rm --dns 8.8.8.8 --dns 8.8.4.4 \
                \
                -v "$PROJECT_ROOT:/home/testuser/jrl_env" \
                "jrl-env-test:$DISTRO" \
                bash -c "./setup.sh --yes --verbose 2>&1 | tee ~/setup.log"
            ;;
        validate)
            runValidate "$DISTRO"
            ;;
        *)
            printError "Unknown command: $COMMAND"
            showHelp
            exit 1
            ;;
    esac
fi
