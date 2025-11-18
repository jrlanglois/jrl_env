#!/bin/bash
# Shared argument parsing logic for setup scripts

# shellcheck source=../core/logging.sh
# shellcheck disable=SC1091 # Path is resolved at runtime
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../core/logging.sh"

# Parse setup script arguments
# Sets global variables: skipFonts, skipApps, skipGit, skipCursor, skipRepos, skipSsh, appsOnly, dryRun, noBackup
parseSetupArgs()
{
    skipFonts=false
    skipApps=false
    skipGit=false
    skipCursor=false
    skipRepos=false
    skipSsh=false
    appsOnly=false
    dryRun=false
    noBackup=false

    # shellcheck disable=SC2034 # Variables are used by scripts that source this file
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-fonts) skipFonts=true ;;
            --skip-apps) skipApps=true ;;
            --skip-git) skipGit=true ;;
            --skip-cursor) skipCursor=true ;;
            --skip-repos) skipRepos=true ;;
            --skip-ssh) skipSsh=true ;;
            --apps-only) appsOnly=true ;;
            --dry-run) dryRun=true ;;
            --no-backup) noBackup=true ;;
            *)
                if commandExists logError; then
                    logError "Unknown option: $1"
                else
                    echo "Error: Unknown option: $1" >&2
                fi
                exit 1
                ;;
        esac
        shift
    done
}

# Determine what to run based on skip flags and appsOnly
# Sets global variables: runFonts, runApps, runGit, runCursor, runRepos, runSsh
determineRunFlags()
{
    runFonts=false
    if [ "$skipFonts" = false ] && [ "$appsOnly" = false ]; then
        # shellcheck disable=SC2034 # Used by scripts that source this file
        runFonts=true
    fi

    runApps=false
    if [ "$skipApps" = false ] || [ "$appsOnly" = true ]; then
        # shellcheck disable=SC2034 # Used by scripts that source this file
        runApps=true
    fi

    runGit=false
    if [ "$skipGit" = false ] && [ "$appsOnly" = false ]; then
        # shellcheck disable=SC2034 # Used by scripts that source this file
        runGit=true
    fi

    runCursor=false
    if [ "$skipCursor" = false ] && [ "$appsOnly" = false ]; then
        # shellcheck disable=SC2034 # Used by scripts that source this file
        runCursor=true
    fi

    runRepos=false
    if [ "$skipRepos" = false ] && [ "$appsOnly" = false ]; then
        # shellcheck disable=SC2034 # Used by scripts that source this file
        runRepos=true
    fi

    runSsh=false
    if [ "$skipSsh" = false ] && [ "$appsOnly" = false ]; then
        # shellcheck disable=SC2034 # Used by scripts that source this file
        runSsh=true
    fi
}
