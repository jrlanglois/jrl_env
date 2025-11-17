# jrl_env

Cross-platform development environment setup and configuration.

## Overview

Automated setup scripts for Windows 11, macOS, and Ubuntu. Manages application installation, system configuration, Git setup, Cursor editor settings, font installation, and repository cloning.

### Purpose

This repository is designed for configuring my own development machines. The scripts and configurations are tailored to my personal preferences and workflow.

## Structure

```text
jrl_env/
├── configs/          # JSON configuration files
│   ├── win11Apps.json
│   ├── macosApps.json
│   ├── ubuntuApps.json
│   ├── fonts.json
│   ├── repositories.json
│   ├── gitConfig.json
│   └── cursorSettings.json
├── win11/            # PowerShell scripts for Windows
├── macos/            # Bash scripts for macOS
└── ubuntu/           # Bash scripts for Ubuntu
```

## Quick Start

### Windows 11

```powershell
# Setup development environment
. .\win11\setupDevEnv.ps1
setupDevEnv

# Install fonts
. .\win11\installFonts.ps1
installGoogleFonts

# Install applications
. .\win11\installApps.ps1
installOrUpdateApps

# Configure Git
. .\win11\configureGit.ps1
configureGit

# Configure Cursor
. .\win11\configureCursor.ps1
configureCursor

# Clone repositories
. .\win11\cloneRepositories.ps1
cloneRepositories
```

### macOS / Ubuntu

```bash
# Setup development environment (zsh, Oh My Zsh, Homebrew/apt)
./macos/setupDevEnv.sh
# or
./ubuntu/setupDevEnv.sh

# Install fonts
./macos/installFonts.sh
# or
./ubuntu/installFonts.sh

# Install applications
./macos/installApps.sh
# or
./ubuntu/installApps.sh

# Configure Git
./macos/configureGit.sh
# or
./ubuntu/configureGit.sh

# Configure Cursor
./macos/configureCursor.sh
# or
./ubuntu/configureCursor.sh

# Clone repositories
./macos/cloneRepositories.sh
# or
./ubuntu/cloneRepositories.sh
```

## Configuration

Edit JSON files in `configs/` to customize:

- **Apps**: Application packages to install via winget/brew/apt
- **Fonts**: Google Fonts to download and install
- **Repositories**: Git repositories to clone (organized by owner)
- **Git**: User info, defaults, and aliases
- **Cursor**: Editor settings and preferences

## Using This Repository

To adapt this setup for your own machines:

1. **Fork the repository** and modify the config files with your preferences
2. **Copy the structure** and create your own scripts based on these examples
3. **Use as a template** for building your own environment setup system

The scripts are designed to be modular and configurable. Update the JSON files in `configs/` to match your needs, and adjust script paths or logic as required for your environment.

## Requirements

- **Windows**: PowerShell 5.1+, winget (Windows Package Manager)
- **macOS**: Homebrew, zsh
- **Ubuntu**: apt, snap, zsh, jq

## License

ISC License. See LICENSE.md for details.
