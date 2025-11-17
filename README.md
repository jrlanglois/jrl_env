# jrl_env

[![CI](https://github.com/jrlanglois/jrl_env/actions/workflows/ci.yml/badge.svg)](https://github.com/jrlanglois/jrl_env/actions/workflows/ci.yml)

Cross-platform development environment setup and configuration. Helper tooling enforces Allman braces, camelCase helpers, and CRLF for `.ps1/.json/.md` while keeping `.sh` LF.

## Overview

Automated setup scripts for Windows 11, macOS, and Ubuntu. Manages application installation, system configuration, Git setup, Cursor editor settings, font installation, and repository cloning.

### Purpose

This repository is designed for configuring my own development machines. The scripts and configurations are tailored to my personal preferences and workflow.

## Structure

```text
jrl_env/
├── configs/          # JSON configuration files
│   ├── win11.json
│   ├── macos.json
│   ├── ubuntu.json
│   ├── fonts.json
│   ├── repositories.json
│   ├── gitConfig.json
│   └── cursorSettings.json
├── win11/            # PowerShell scripts for Windows
├── macos/            # Bash scripts for macOS
└── ubuntu/           # Bash scripts for Ubuntu
```

## Quick Start

### First Time Setup

Clone the repository and run the setup script for your platform:

**Windows 11:**

```powershell
git clone https://github.com/jrlanglois/jrl_env.git
cd jrl_env
.\win11\setup.ps1
```

**macOS:**

```bash
git clone https://github.com/jrlanglois/jrl_env.git
cd jrl_env
./macos/setup.sh
```

**Ubuntu:**

```bash
git clone https://github.com/jrlanglois/jrl_env.git
cd jrl_env
./ubuntu/setup.sh
```

The setup script will run all configuration and installation tasks automatically.

### Updating

After making changes and pushing to the repository, update other machines:

**Windows 11:**

```powershell
cd jrl_env
.\win11\update.ps1
```

**macOS / Ubuntu:**

```bash
cd jrl_env
./macos/update.sh
# or
./ubuntu/update.sh
```

The update script will pull the latest changes and re-run the setup.

## Configuration

Edit JSON files in `configs/` to customize:

- **Apps**: Application packages to install via winget/brew/apt
- **Fonts**: Google Fonts to download and install
- **Repositories**: Git repositories to clone (organized by owner)
- **Git**: User info, defaults, aliases, and GitHub username/email for SSH
- **Cursor**: Editor settings and preferences
- **Shell**: Per-OS shell preferences (e.g., `ohMyZshTheme`)
- **Cruft**: Packages to uninstall (e.g., Ubuntu `apt` wildcard patterns)
- **Commands**: Optional `preInstall`/`postInstall` command objects (name, shell, command, runOnce)

## Using This Repository

To adapt this setup for your own machines:

1. **Fork the repository** and modify the config files with your preferences
2. **Copy the structure** and create your own scripts based on these examples
3. **Use as a template** for building your own environment setup system

The scripts are designed to be modular and configurable. Update the JSON files in `configs/` to match your needs, and adjust script paths or logic as required for your environment.

### GitHub SSH Automation

Each platform now includes an interactive helper to generate and register GitHub SSH keys using the data from `configs/gitConfig.json`:

- macOS / Ubuntu: `./macos/configureGithubSsh.sh` and `./ubuntu/configureGithubSsh.sh`
- Windows 11: `.\win11\configureGithubSsh.ps1`

During full setup you can skip this step with `--skip-ssh` (macOS/Ubuntu) or `-skipSsh` (Windows). The helpers:

1. Read the email and `usernameGitHub` fields from `gitConfig.json`
2. Generate an `ed25519` key pair (default `id_ed25519_github`)
3. Add the key to the local SSH agent when possible
4. Copy the public key to the clipboard and optionally open the GitHub SSH settings page

Re-run the script any time you need to rotate keys or target a new GitHub account.

## Style Guide

This repository follows consistent coding style conventions:

- **Naming**: camelCase for variable names and function names (e.g., `logInfo`, `backupConfigs`, `isWingetInstalled`).
- **Indentation**: 4 spaces, no tabs.
- **Braces**: Allman style (opening brace/bracket on its own line) where possible. Applies to code blocks, JSON objects, and JSON arrays.
- **Boolean functions**: Use `is/was/{verb}` prefixes for clarity (e.g., `isGitInstalled`, `isRepositoryCloned`).
- **Spelling**: Canadian English conventions (`-ise` for verbs, `-our` for nouns like `colour`, `behaviour`).
- **JSON formatting**: 4-space indentation, CRLF line endings.

These conventions apply to all PowerShell (`.ps1`) and Bash (`.sh`) scripts in this repository. Note: PowerShell has some syntax quirks that may prevent Allman braces in certain cases (e.g., pipeline operations), but we use them wherever possible.

## Requirements

- **Windows**: PowerShell 5.1+, winget (Windows Package Manager)
- **macOS**: Homebrew, zsh
- **Ubuntu**: apt, snap, zsh, jq

## License
ISC License. See LICENSE.md for details.
