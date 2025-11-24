# Tab Completion for jrl_env

This directory contains tab completion scripts for `setup.py` and the CLI module across different shells.

## Features

- **Bash/Zsh Completion**: Smart completion for all flags, targets, platforms, and operations
- **PowerShell Completion**: Full IntelliSense support with descriptions
- **Python argcomplete**: Native Python-based completion support
- **Composable Targets**: Tab completion for comma-separated lists (e.g., `--install=fonts,<TAB>`)

## Installation

### Bash

Add to your `~/.bashrc`:

```bash
source /path/to/jrl_env/completions/jrl_env.bash
```

### Zsh

Add to your `~/.zshrc`:

```bash
# Enable bash completion compatibility
autoload -U +X bashcompinit && bashcompinit

# Load jrl_env completions
source /path/to/jrl_env/completions/jrl_env.bash
```

### PowerShell

Add to your PowerShell profile (`$PROFILE`):

```powershell
. C:\path\to\jrl_env\completions\jrl_env.ps1
```

To find your profile location:
```powershell
echo $PROFILE
```

### Python (argcomplete)

Install the argcomplete package (already in `requirements.txt`):

```bash
pip install argcomplete
```

Then activate global completion:

```bash
# Bash
activate-global-python-argcomplete --user

# Zsh
activate-global-python-argcomplete --user
```

Restart your shell after installation.

## Usage Examples

Once installed, you can use tab completion:

```bash
# Setup.py completions
python3 setup.py --inst<TAB>           # Completes to --install
python3 setup.py --install=<TAB>       # Shows: all, fonts, apps, git, cursor, repos, ssh
python3 setup.py --install=fonts,<TAB> # Shows remaining targets
python3 setup.py --update=<TAB>        # Shows: all, apps, system
python3 setup.py --passphrase=<TAB>    # Shows: require, no

# CLI completions
python3 -m common.systems.cli <TAB>    # Shows all platforms
python3 -m common.systems.cli macos <TAB>  # Shows all operations
jrlEnvCli macos <TAB>                  # Shows all operations (if alias is set)
```

## Supported Completions

### setup.py

**Flags:**
- `--install`, `--update`, `--passphrase`, `--configDir`
- `--dryRun`, `--noBackup`, `--verbose`, `--quiet`
- `--noTimestamps`, `--clearRepoCache`, `--resume`, `--noResume`
- `--listSteps`, `--help`, `--version`

**Install Targets:**
- `all`, `fonts`, `apps`, `git`, `cursor`, `repos`, `ssh`

**Update Targets:**
- `all`, `apps`, `system`

**Passphrase Modes:**
- `require`, `no`

### CLI Module

**Platforms:**
- `macos`, `win11`
- `ubuntu`, `debian`, `popos`, `linuxmint`, `elementary`, `zorin`, `mxlinux`, `raspberrypi`
- `fedora`, `redhat`
- `opensuse`
- `archlinux`, `manjaro`, `endeavouros`
- `alpine`

**Operations:**
- `fonts`, `apps`, `git`, `ssh`, `cursor`, `repos`
- `status`, `rollback`, `verify`, `update`

**Options:**
- `--help`, `--version`, `--verbose`, `--quiet`, `--dryRun`, `--configDir`

## Advanced Features

### Comma-Separated Target Completion

The bash completion supports intelligent completion of comma-separated targets:

```bash
python3 setup.py --install=fonts,<TAB>  # Suggests: apps, git, cursor, repos, ssh
python3 setup.py --install=fonts,apps,<TAB>  # Suggests: git, cursor, repos, ssh
```

### Directory Completion

```bash
python3 setup.py --configDir <TAB>  # Completes directory paths
```

### Platform-Specific Completion

```bash
python3 -m common.systems.cli u<TAB>  # Expands to ubuntu
python3 -m common.systems.cli ubuntu s<TAB>  # Suggests: ssh, status
```

## Troubleshooting

### Bash/Zsh: Completions Not Working

1. Verify the completion script is sourced:
   ```bash
   echo $BASH_COMPLETION_USER_FILE
   source /path/to/jrl_env/completions/jrl_env.bash
   ```

2. Reload your shell:
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```

### PowerShell: Completions Not Working

1. Check your execution policy:
   ```powershell
   Get-ExecutionPolicy
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. Reload your profile:
   ```powershell
   . $PROFILE
   ```

### Python argcomplete: Not Activating

1. Ensure argcomplete is installed:
   ```bash
   pip install argcomplete
   ```

2. Activate global completion:
   ```bash
   activate-global-python-argcomplete --user
   ```

3. Restart your shell

## Technical Details

- **Bash completion** uses `complete -F` for custom completion functions
- **PowerShell completion** uses `Register-ArgumentCompleter` for rich IntelliSense
- **Python argcomplete** provides cross-platform completion via the argcomplete library
- All completions are position-aware and context-sensitive
- Comma-separated list completion is fully supported
