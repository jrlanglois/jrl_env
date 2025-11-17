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
