# Security Policy

## Overview

jrl_env is a personal development environment setup tool that handles sensitive operations including:
- Installing system packages with elevated privileges
- Managing Git configuration
- Generating and configuring SSH keys
- Cloning private repositories
- Storing configuration data

This document outlines security considerations, best practices, and our responsible disclosure policy.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

We recommend always using the latest version from the `main` branch for the most up-to-date security fixes.

## Security Considerations

### SSH Key Management

#### Passphrases

**Strongly Recommended:** Always use a passphrase for SSH keys.

jrl_env supports three passphrase options:

1. **Default (Recommended):** Optional passphrase with prompt
   ```bash
   python3 setup.py
   ```
   - You'll be prompted to optionally add a passphrase
   - Press Enter to skip (less secure) or enter a passphrase

2. **Require Passphrase (Most Secure - Default):**
   ```bash
   python3 setup.py --install=ssh --passphrase=require
   # Or just (passphrase is required by default):
   python3 setup.py --install=ssh
   ```
   - Passphrase is required by default
   - Recommended for production environments

3. **No Passphrase (Least Secure):**
   ```bash
   python3 setup.py --install=ssh --passphrase=no
   ```
   - Skips passphrase prompt
   - Only use for testing/development environments
   - **Not recommended for production use**

#### Passphrase Storage

When you provide a passphrase, jrl_env stores it securely in your system keychain:

- **macOS:** Uses Keychain via the `keyring` library
- **Linux:** Uses Secret Service API (GNOME Keyring, KWallet, etc.)
- **Windows:** Uses Windows Credential Manager

**Security Benefits:**
- Passphrases are encrypted by the operating system
- No plaintext storage of passphrases
- Automatic retrieval when needed
- Per-user access control

**Requirements:**
- Python `keyring` library (automatically installed)
- System keychain service must be available
- User must have access to their keychain

#### SSH Key Best Practices

1. **Use Ed25519 Keys:** jrl_env generates Ed25519 keys by default (modern, secure algorithm)
2. **Unique Keys Per Service:** Consider using different keys for different services
3. **Regular Rotation:** Rotate SSH keys periodically (e.g., annually)
4. **Protect Private Keys:** Never share or commit private keys
5. **Use SSH Agent:** jrl_env automatically adds keys to ssh-agent for convenience
6. **Monitor Key Usage:** Regularly review authorized keys on GitHub and other services

### Sudo and Elevated Privileges

jrl_env requires elevated privileges for:
- Package manager operations (`apt`, `brew`, `dnf`, `zypper`, `pacman`, `winget`, `choco`, `snap`)
- System-wide font installation
- Modifying system configuration

**Security Practices:**
- We use `sudo` only when necessary
- Commands are constructed carefully to avoid injection
- You can review commands with `--dryRun` before execution
- All privileged operations are logged

**What We Never Do:**
- Disable sudo password prompts
- Run the entire setup as root
- Execute arbitrary code without validation
- Modify system files outside documented scope

### Configuration Files

Configuration files contain sensitive information:
- Git user email
- GitHub username
- Repository URLs (potentially private)
- Package lists
- Custom commands

**Recommendations:**
1. **Fork This Repository:** Don't modify configs in the main repo
2. **Use Private Config Repository:** Store your configs in a private repo
3. **Review Before Commit:** Never commit secrets or credentials
4. **Use Environment Variables:** For truly sensitive data, use environment variables
5. **Custom Config Directory:** Use `--configDir` to point to your private configs

### Command Execution

Configuration files can specify custom commands via `preInstall` and `postInstall`:

```json
{
  "preInstall": [
    {
      "name": "Update package cache",
      "shell": "bash",
      "command": "sudo apt-get update",
      "runOnce": true
    }
  ]
}
```

**Security Considerations:**
- Commands run with your user privileges (plus sudo where specified)
- Shell injection is possible if configs are compromised
- Only use trusted configuration sources
- Review custom commands before running setup

**Mitigation:**
- Validate your configuration files
- Use `--dryRun` to preview commands
- Keep configs in version control
- Audit changes to config files

### Network Security

jrl_env makes network requests for:
- Package installation from official repositories
- Font downloads from Google Fonts API
- Repository cloning via Git/SSH
- API calls for validation (package existence, font availability)

**What We Don't Do:**
- Make requests to third-party services (except official package repos, Google Fonts, GitHub)
- Send telemetry or analytics
- Download executable code from unverified sources

**What You Should Do:**
- Review repository URLs before cloning
- Use SSH for Git operations (encrypted, authenticated)
- Verify package signatures when possible
- Use VPN on untrusted networks

### Credential Management

**What jrl_env Does:**
- Stores SSH passphrases in system keychain (encrypted)
- Generates SSH keys locally
- Configures Git with user info (name, email)

**What jrl_env Does NOT Do:**
- Store passwords or access tokens
- Handle GitHub personal access tokens (use GitHub CLI separately)
- Store credentials in plaintext
- Transmit credentials over network

### File Permissions

jrl_env sets appropriate permissions:
- SSH directory: `0700` (`~/.ssh/`)
- SSH private keys: Handled by `ssh-keygen` (typically `0600`)
- Configuration backups: User-readable only
- Log files: User-readable only

### Rollback and Recovery

If setup fails, jrl_env provides rollback capability:
```bash
python3 -m common.systems.cli <platform> rollback
```

**What Gets Rolled Back:**
- Configuration file changes (restored from backup)
- Packages installed during the session (uninstalled)

**What Does NOT Get Rolled Back:**
- System package updates
- Repository clones
- SSH keys (must be manually removed)

## Best Practices for Users

1. **Review Before Running:**
   ```bash
   python3 setup.py --dryRun --verbose
   ```

2. **Use a Dedicated Machine First:** Test on a VM or secondary machine

3. **Keep Backups:** jrl_env backs up configs, but keep your own backups too

4. **Use Passphrases:** Always protect SSH keys with strong passphrases

5. **Private Configs:** Store your configs in a private repository

6. **Regular Updates:** Keep jrl_env and dependencies updated

7. **Audit Logs:** Review setup logs after completion

8. **Principle of Least Privilege:** Don't run as root unless necessary

## Reporting Security Vulnerabilities

We take security seriously. If you discover a security vulnerability in jrl_env, please report it responsibly.

### Please Do:
- **Email:** Report to the repository owner via GitHub
- **Provide Details:** Include steps to reproduce, impact assessment, and potential fixes
- **Allow Time:** Give reasonable time (90 days) for fixes before public disclosure
- **Be Respectful:** We're working to improve security together

### Please Don't:
- Publicly disclose vulnerabilities before they're fixed
- Exploit vulnerabilities maliciously
- Test against systems you don't own

### What to Report:
- Code injection vulnerabilities
- Privilege escalation issues
- Credential leakage
- Unsafe file operations
- Dependency vulnerabilities with proof of exploitability

### What We'll Do:
1. Acknowledge your report within 48 hours
2. Investigate and verify the issue
3. Develop and test a fix
4. Release a patch
5. Credit you in the release notes (if desired)

## Security-Related Configuration

### Disable Passphrase Storage

If you prefer not to store passphrases in the keychain:
1. Don't use a passphrase, OR
2. Manually remove from keychain after setup:
   ```python
   from common.configure.configureGithubSsh import deleteStoredPassphrase
   deleteStoredPassphrase("id_ed25519_github")
   ```

### Custom SSH Key Location

While jrl_env uses standard `~/.ssh/` locations, you can:
1. Generate keys elsewhere after setup
2. Move keys and update SSH config
3. Use different key names (prompted during setup)

### Limit Package Installation

To review packages before installation:
1. Use `--dryRun` to preview
2. Modify config to remove untrusted packages
3. Use `--install=fonts,git,cursor` to skip package installation entirely
4. Manually install packages after review

## Security Audit Trail

Every setup run creates logs with:
- Timestamp (ISO8601)
- Commands executed
- Packages installed
- Configuration changes
- Errors encountered

**Log Locations:**
- **macOS:** `~/Library/Logs/jrl_env_setup_<timestamp>.log`
- **Linux:** `~/.cache/jrl_env/jrl_env_setup_<timestamp>.log`
- **Windows:** `%LOCALAPPDATA%\jrl_env\Logs\jrl_env_setup_<timestamp>.log`

Review these logs to audit setup activities.

## Third-Party Dependencies

jrl_env uses minimal dependencies:
- `jsonschema`: JSON validation (no network access, no external dependencies)
- `keyring`: System keychain access (OS-provided security)

**Dependency Security:**
- We use version pinning in `requirements.txt`
- Dependencies are from PyPI (official Python package index)
- Review `requirements.txt` before installing

## Licence and Liability

jrl_env is provided under the ISC Licence. See LICENCE.md for details.

**Important:** This software is provided "as is" without warranty. Use at your own risk, especially:
- On production systems
- With elevated privileges
- With sensitive data

Always test in a safe environment first.

---

**Last Updated:** 2025-11-20

For questions or concerns, please open an issue on GitHub.
