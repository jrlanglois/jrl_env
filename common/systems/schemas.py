#!/usr/bin/env python3
"""
JSON schemas for configuration file validation.
Defines schemas for all config file types used in jrl_env.
Uses composition to avoid redundancy (DRY principles).
"""

# ============================================================================
# Common Schema Fragments (Reusable Components)
# ============================================================================

commandSchema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "shell": {"type": "string", "default": "bash"},
        "command": {"type": "string"},
        "runOnce": {"type": "boolean", "default": False},
    },
    "required": ["name", "command"],
    "additionalProperties": False,
}

shellConfigSchema = {
    "type": "object",
    "properties": {
        "ohMyZshTheme": {"type": "string"},
    },
    "additionalProperties": False,
}

commandsConfigSchema = {
    "type": "object",
    "properties": {
        "preInstall": {
            "type": "array",
            "items": commandSchema,
        },
        "postInstall": {
            "type": "array",
            "items": commandSchema,
        },
    },
    "additionalProperties": False,
}

packageArraySchema = {
    "type": "array",
    "items": {"type": "string"},
}

cruftSchema = {
    "type": "object",
    "additionalProperties": packageArraySchema,  # Allow any package manager
}

androidConfigFragment = {
    "type": "object",
    "properties": {
        "sdkComponents": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}


def createLinuxConfigSchema(packageManagers: list) -> dict:
    """
    Create a Linux distribution config schema with specified package managers.

    Args:
        packageManagers: List of package manager names (e.g., ["apt", "snap", "flatpak"])

    Returns:
        Complete config schema for the distribution
    """
    properties = {
        "useLinuxCommon": {"type": "boolean"},
        "android": androidConfigFragment,
        "commands": commandsConfigSchema,
        "shell": shellConfigSchema,
        "cruft": cruftSchema,
    }

    # Add package manager properties
    for pm in packageManagers:
        properties[pm] = packageArraySchema

    return {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }


# ============================================================================
# Platform-Specific Schemas
# ============================================================================

# Platform config schema (base)
platformConfigSchema = {
    "type": "object",
    "properties": {
        "commands": {
            "type": "object",
            "properties": {
                "preInstall": {
                    "type": "array",
                    "items": commandSchema,
                },
                "postInstall": {
                    "type": "array",
                    "items": commandSchema,
                },
            },
            "additionalProperties": False,
        },
        "shell": {
            "type": "object",
            "properties": {
                "ohMyZshTheme": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "cruft": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": True,  # Allow platform-specific package arrays
    "minProperties": 1,  # At least one property must exist
}

# APT-based distributions (Debian, Ubuntu, Pop!_OS, Mint, Elementary, Zorin, MX, Raspberry Pi)
ubuntuConfigSchema = createLinuxConfigSchema(["apt", "snap", "flatpak"])

# macOS config schema
macosConfigSchema = {
    "type": "object",
    "properties": {
        "brew": packageArraySchema,
        "brewCask": packageArraySchema,
        "android": androidConfigFragment,
        "commands": commandsConfigSchema,
        "shell": shellConfigSchema,
        "cruft": cruftSchema,
    },
    "additionalProperties": False,
}

# Windows config schema
win11ConfigSchema = {
    "type": "object",
    "properties": {
        "chocolatey": packageArraySchema,
        "vcpkg": packageArraySchema,
        "winget": packageArraySchema,
        "windowsStore": packageArraySchema,
        "android": androidConfigFragment,
        "commands": commandsConfigSchema,
        "cruft": cruftSchema,
    },
    "additionalProperties": False,
}

# DNF-based distributions (Fedora, RedHat/CentOS)
redhatConfigSchema = createLinuxConfigSchema(["dnf", "snap", "flatpak"])

# Zypper-based distributions (OpenSUSE)
opensuseConfigSchema = createLinuxConfigSchema(["zypper", "snap", "flatpak"])

# Pacman-based distributions (Arch, Manjaro, EndeavourOS)
archlinuxConfigSchema = createLinuxConfigSchema(["pacman", "snap", "flatpak"])

# Git config schema
gitConfigSchema = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "usernameGitHub": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "ssh": {
            "type": "object",
            "properties": {
                "algorithm": {
                    "type": "string",
                    "enum": ["rsa", "dsa", "ecdsa", "ed25519"],
                },
                "keySize": {
                    "type": ["integer", "null"],
                },
                "keyFilename": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "defaults": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "aliases": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

# Fonts config schema
fontsConfigSchema = {
    "type": "object",
    "properties": {
        "googleFonts": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["googleFonts"],
    "additionalProperties": False,
}

# Repository entry schema (for wildcard support)
repositoryEntrySchema = {
    "oneOf": [
        # String format (backward compatible): "git@github.com:owner/repo"
        {"type": "string"},
        # Object format (wildcard support)
        {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "visibility": {
                    "type": "string",
                    "enum": ["all", "public", "private"],
                    "default": "all"
                },
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
    ]
}

# Repositories config schema
repositoriesConfigSchema = {
    "type": "object",
    "properties": {
        "workPathWindows": {"type": "string"},
        "workPathUnix": {"type": "string"},
        "repositories": {
            "type": "array",
            "items": repositoryEntrySchema,
        },
    },
    "additionalProperties": False,
}

# Linux common config schema
linuxCommonConfigSchema = {
    "type": "object",
    "properties": {
        "apt": {
            "type": "array",
            "items": {"type": "string"},
        },
        "dnf": {
            "type": "array",
            "items": {"type": "string"},
        },
        "pacman": {
            "type": "array",
            "items": {"type": "string"},
        },
        "zypper": {
            "type": "array",
            "items": {"type": "string"},
        },
        "snap": {
            "type": "array",
            "items": {"type": "string"},
        },
        "flatpak": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["apt", "dnf", "pacman", "zypper", "snap", "flatpak"],
    "additionalProperties": False,
}

# Cursor settings schema (very flexible, just needs to be valid JSON object)
cursorSettingsSchema = {
    "type": "object",
    "additionalProperties": True,
}

# Alpine config schema (APK-based, no linuxCommon - Alpine is standalone)
alpineConfigSchema = createLinuxConfigSchema(["apk"])
# Remove useLinuxCommon from Alpine since it doesn't use it
alpineConfigSchema["properties"].pop("useLinuxCommon", None)

# Android config schema
androidConfigSchema = {
    "type": "object",
    "properties": {
        "android": {
            "type": "object",
            "properties": {
                "sdkComponents": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["sdkComponents"],
            "additionalProperties": False,
        },
    },
    "required": ["android"],
    "additionalProperties": False,
}


def getSchemaForConfig(configType: str, platform: str = None):
    """
    Get the appropriate schema for a config file.

    Args:
        configType: Type of config ("platform", "gitConfig", "fonts", "repositories", "linuxCommon", "cursorSettings", "android")
        platform: Platform name (required for "platform" type)

    Returns:
        Schema dictionary or None if not found
    """
    if configType == "platform":
        if platform == "ubuntu" or platform == "raspberrypi":
            return ubuntuConfigSchema
        # APT-based distributions (Debian/Ubuntu family)
        elif platform in ("debian", "popos", "linuxmint", "elementary", "zorin", "mxlinux"):
            return ubuntuConfigSchema
        # macOS
        elif platform == "macos":
            return macosConfigSchema
        # Windows
        elif platform == "win11":
            return win11ConfigSchema
        # DNF-based distributions (Fedora/RedHat)
        elif platform in ("fedora", "redhat"):
            return redhatConfigSchema
        # Zypper-based (OpenSUSE)
        elif platform == "opensuse":
            return opensuseConfigSchema
        # Pacman-based distributions (Arch family)
        elif platform in ("archlinux", "manjaro", "endeavouros"):
            return archlinuxConfigSchema
        # Alpine (APK-based) - needs its own schema
        elif platform == "alpine":
            return alpineConfigSchema
    elif configType == "gitConfig":
        return gitConfigSchema
    elif configType == "fonts":
        return fontsConfigSchema
    elif configType == "repositories":
        return repositoriesConfigSchema
    elif configType == "linuxCommon":
        return linuxCommonConfigSchema
    elif configType == "cursorSettings":
        return cursorSettingsSchema
    elif configType == "android":
        return androidConfigSchema

    return None
