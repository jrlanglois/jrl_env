#!/usr/bin/env python3
"""
JSON schemas for configuration file validation.
Defines schemas for all config file types used in jrl_env.
"""

# Command schema (used in platform configs)
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

# Ubuntu/Raspberry Pi config schema
ubuntuConfigSchema = {
    "type": "object",
    "properties": {
        "linuxCommon": {"type": "boolean"},
        "apt": {
            "type": "array",
            "items": {"type": "string"},
        },
        "snap": {
            "type": "array",
            "items": {"type": "string"},
        },
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
    "additionalProperties": False,
}

# macOS config schema
macosConfigSchema = {
    "type": "object",
    "properties": {
        "brew": {
            "type": "array",
            "items": {"type": "string"},
        },
        "brewCask": {
            "type": "array",
            "items": {"type": "string"},
        },
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
    "additionalProperties": False,
}

# Windows config schema
win11ConfigSchema = {
    "type": "object",
    "properties": {
        "winget": {
            "type": "array",
            "items": {"type": "string"},
        },
        "windowsStore": {
            "type": "array",
            "items": {"type": "string"},
        },
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
    "additionalProperties": False,
}

# RedHat config schema
redhatConfigSchema = {
    "type": "object",
    "properties": {
        "linuxCommon": {"type": "boolean"},
        "dnf": {
            "type": "array",
            "items": {"type": "string"},
        },
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
    "additionalProperties": False,
}

# OpenSUSE config schema
opensuseConfigSchema = {
    "type": "object",
    "properties": {
        "linuxCommon": {"type": "boolean"},
        "zypper": {
            "type": "array",
            "items": {"type": "string"},
        },
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
    "additionalProperties": False,
}

# ArchLinux config schema
archlinuxConfigSchema = {
    "type": "object",
    "properties": {
        "linuxCommon": {"type": "boolean"},
        "pacman": {
            "type": "array",
            "items": {"type": "string"},
        },
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
    "additionalProperties": False,
}

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

# Repositories config schema
repositoriesConfigSchema = {
    "type": "object",
    "properties": {
        "workPathWindows": {"type": "string"},
        "workPathUnix": {"type": "string"},
        "repositories": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

# Linux common config schema
linuxCommonConfigSchema = {
    "type": "object",
    "properties": {
        "linuxCommon": {
            "type": "array",
            "items": {"type": "string"},
        },
        "_notes": {
            "type": "object",
            "additionalProperties": True,
        },
    },
    "required": ["linuxCommon"],
    "additionalProperties": True,
}

# Cursor settings schema (very flexible, just needs to be valid JSON object)
cursorSettingsSchema = {
    "type": "object",
    "additionalProperties": True,
}


def getSchemaForConfig(configType: str, platform: str = None):
    """
    Get the appropriate schema for a config file.

    Args:
        configType: Type of config ("platform", "gitConfig", "fonts", "repositories", "linuxCommon", "cursorSettings")
        platform: Platform name (required for "platform" type)

    Returns:
        Schema dictionary or None if not found
    """
    if configType == "platform":
        if platform == "ubuntu" or platform == "raspberrypi":
            return ubuntuConfigSchema
        elif platform == "macos":
            return macosConfigSchema
        elif platform == "win11":
            return win11ConfigSchema
        elif platform == "redhat":
            return redhatConfigSchema
        elif platform == "opensuse":
            return opensuseConfigSchema
        elif platform == "archlinux":
            return archlinuxConfigSchema
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

    return None
