#!/usr/bin/env bash
# Bash completion for jrl_env setup.py and CLI
# Source this file or add to ~/.bashrc or ~/.zshrc:
#   source /path/to/jrl_env/completions/jrl_env.bash

jrlEnvSetupComplete()
{
    local cur prev opts installTargets updateTargets platforms operations
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Basic options
    opts="--install --update --passphrase --configDir --dryRun --noBackup --verbose --quiet --noTimestamps --clearRepoCache --resume --noResume --listSteps --help --version"

    # Install targets
    installTargets="all fonts apps git cursor repos ssh"

    # Update targets
    updateTargets="all apps system"

    # Handle different argument contexts
    case "${prev}" in
        --install)
            # Complete with install targets
            COMPREPLY=( $(compgen -W "${installTargets}" -- ${cur}) )
            return 0
            ;;
        --update)
            # Complete with update targets
            COMPREPLY=( $(compgen -W "${updateTargets}" -- ${cur}) )
            return 0
            ;;
        --passphrase)
            # Complete with passphrase modes
            COMPREPLY=( $(compgen -W "require no" -- ${cur}) )
            return 0
            ;;
        --configDir)
            # Complete with directories
            COMPREPLY=( $(compgen -d -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac

    # Handle --install=<tab> and --update=<tab>
    if [[ ${cur} == --install=* ]]; then
        local prefix="${cur%%=*}="
        local suffix="${cur#*=}"
        # Handle comma-separated targets
        if [[ ${suffix} == *,* ]]; then
            local lastTarget="${suffix##*,}"
            local currentPrefix="${suffix%,*},"
            COMPREPLY=( $(compgen -W "${installTargets}" -- ${lastTarget}) )
            COMPREPLY=( "${COMPREPLY[@]/#/${currentPrefix}}" )
        else
            COMPREPLY=( $(compgen -W "${installTargets}" -- ${suffix}) )
        fi
        COMPREPLY=( "${COMPREPLY[@]/#/--install=}" )
        return 0
    elif [[ ${cur} == --update=* ]]; then
        local prefix="${cur%%=*}="
        local suffix="${cur#*=}"
        # Handle comma-separated targets
        if [[ ${suffix} == *,* ]]; then
            local lastTarget="${suffix##*,}"
            local currentPrefix="${suffix%,*},"
            COMPREPLY=( $(compgen -W "${updateTargets}" -- ${lastTarget}) )
            COMPREPLY=( "${COMPREPLY[@]/#/${currentPrefix}}" )
        else
            COMPREPLY=( $(compgen -W "${updateTargets}" -- ${suffix}) )
        fi
        COMPREPLY=( "${COMPREPLY[@]/#/--update=}" )
        return 0
    elif [[ ${cur} == --passphrase=* ]]; then
        local suffix="${cur#*=}"
        COMPREPLY=( $(compgen -W "require no" -- ${suffix}) )
        COMPREPLY=( "${COMPREPLY[@]/#/--passphrase=}" )
        return 0
    fi

    # Default completion
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}

jrlEnvCliComplete()
{
    local cur prev opts platforms operations
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Platforms
    platforms="macos win11 ubuntu debian popos linuxmint elementary zorin mxlinux raspberrypi fedora redhat opensuse archlinux manjaro endeavouros alpine"

    # Operations
    operations="fonts apps git ssh cursor repos status rollback verify update"

    # Options
    opts="--help --version --verbose --quiet --dryRun --configDir"

    # Position-based completion
    local cmdCount=0
    for word in "${COMP_WORDS[@]:1}"; do
        if [[ ! $word =~ ^- ]]; then
            ((cmdCount++))
        fi
    done

    case "${prev}" in
        --configDir)
            COMPREPLY=( $(compgen -d -- ${cur}) )
            return 0
            ;;
        *)
            ;;
    esac

    # First argument: platform
    if [[ ${cmdCount} -eq 0 ]]; then
        COMPREPLY=( $(compgen -W "${platforms}" -- ${cur}) )
        return 0
    fi

    # Second argument: operation
    if [[ ${cmdCount} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${operations}" -- ${cur}) )
        return 0
    fi

    # Third+ arguments: options
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
}

# Register completions for Python entry point
complete -F jrlEnvSetupComplete setup.py
complete -F jrlEnvSetupComplete ./setup.py
complete -F jrlEnvSetupComplete python3\ setup.py

# Register completions for shell wrappers
complete -F jrlEnvSetupComplete setup.sh
complete -F jrlEnvSetupComplete ./setup.sh

# For CLI module usage
alias jrlEnvCli='python3 -m common.systems.cli'
complete -F jrlEnvCliComplete jrlEnvCli
