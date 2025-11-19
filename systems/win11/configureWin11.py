#!/usr/bin/env python3
"""
Windows 11 system configuration module.
Configures regional settings, dark mode, File Explorer, privacy, taskbar, Developer Mode, notifications, and WSL2.
"""

import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path

# Add project root to path so we can import from common
scriptDir = Path(__file__).parent.absolute()
projectRoot = scriptDir.parent.parent
sys.path.insert(0, str(projectRoot))

from common.common import (
    printError,
    printInfo,
    printSection,
    printSuccess,
    printWarning,
    safePrint,
)

try:
    import winreg
except ImportError:
    printError("winreg module not available. This script requires Windows.")
    sys.exit(1)


def isAdministrator() -> bool:
    """Check if running as administrator."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def configureRegionalSettings(dryRun: bool = False) -> bool:
    """
    Configure Windows 11 regional settings including language and locale.
    Sets the system locale, user locale, and regional format to en-CA (English Canada).

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if configuration was successful, False otherwise
    """
    printInfo("Configuring regional settings to en-CA (English Canada)...")

    try:
        if not isAdministrator():
            printError("Administrative privileges are required to configure regional settings. Please run as Administrator.")
            return False

        # Set system locale to en-CA
        if dryRun:
            printInfo("[DRY RUN] Would set system locale to en-CA...")
        else:
            printInfo("Setting system locale to en-CA...")
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\Nls\Language",
                    0,
                    winreg.KEY_WRITE,
                )
                winreg.SetValueEx(key, "Default", 0, winreg.REG_SZ, "1009")  # 1009 is en-CA
                winreg.CloseKey(key)
            except Exception as e:
                printWarning(f"Failed to set system locale via registry: {e}")
                # Try PowerShell method as fallback
                try:
                    subprocess.run(
                        [
                            "powershell.exe",
                            "-NoProfile",
                            "-ExecutionPolicy", "Bypass",
                            "-Command",
                            "Set-WinSystemLocale -SystemLocale en-CA",
                        ],
                        check=False,
                        capture_output=True,
                    )
                except Exception:
                    pass

        # Set user locale to en-CA
        if dryRun:
            printInfo("[DRY RUN] Would set user locale to en-CA...")
        else:
            printInfo("Setting user locale to en-CA...")
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Control Panel\International",
                    0,
                    winreg.KEY_WRITE,
                )
                winreg.SetValueEx(key, "Locale", 0, winreg.REG_SZ, "00001009")
                winreg.CloseKey(key)
            except Exception as e:
                printWarning(f"Failed to set user locale via registry: {e}")
                # Try PowerShell method as fallback
                try:
                    subprocess.run(
                        [
                            "powershell.exe",
                            "-NoProfile",
                            "-ExecutionPolicy", "Bypass",
                            "-Command",
                            "Set-Culture -CultureInfo en-CA",
                        ],
                        check=False,
                        capture_output=True,
                    )
                except Exception:
                    pass

        # Set regional format to en-CA
        if dryRun:
            printInfo("[DRY RUN] Would set regional format to en-CA...")
        else:
            printInfo("Setting regional format to en-CA...")
            try:
                geoKeyPath = r"Control Panel\International\Geo"
                try:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        geoKeyPath,
                        0,
                        winreg.KEY_WRITE,
                    )
                except FileNotFoundError:
                    # Create the key if it doesn't exist
                    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, geoKeyPath)

                winreg.SetValueEx(key, "Nation", 0, winreg.REG_SZ, "39")  # 39 is GeoId for Canada
                winreg.CloseKey(key)
            except Exception as e:
                printWarning(f"Failed to set regional format via registry: {e}")
                # Try PowerShell method as fallback
                try:
                    subprocess.run(
                        [
                            "powershell.exe",
                            "-NoProfile",
                            "-ExecutionPolicy", "Bypass",
                            "-Command",
                            "Set-WinHomeLocation -GeoId 39",
                        ],
                        check=False,
                        capture_output=True,
                    )
                except Exception:
                    pass

        if dryRun:
            printSuccess("[DRY RUN] Regional settings would be configured successfully!")
        else:
            printSuccess("Regional settings configured successfully!")
        printWarning("Note: You may need to restart your computer for all changes to take effect.")
        return True
    except Exception as e:
        printError(f"Failed to configure regional settings: {e}")
        return False


def configure24HourTime(dryRun: bool = False) -> bool:
    """
    Configure Windows 11 to use 24-hour time format.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if configuration was successful, False otherwise
    """
    printInfo("Configuring 24-hour time format...")

    try:
        if not isAdministrator():
            printError("Administrative privileges are required to configure time format. Please run as Administrator.")
            return False

        regPath = r"Control Panel\International"

        # Set short time format to 24-hour (HH:mm)
        if dryRun:
            printInfo("[DRY RUN] Would set short time format to 24-hour (HH:mm)...")
        else:
            printInfo("Setting short time format to 24-hour (HH:mm)...")
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    regPath,
                    0,
                    winreg.KEY_WRITE,
                )
                winreg.SetValueEx(key, "sShortTime", 0, winreg.REG_SZ, "HH:mm")
                winreg.SetValueEx(key, "sTimeFormat", 0, winreg.REG_SZ, "HH:mm:ss")
                winreg.CloseKey(key)
            except Exception as e:
                printError(f"Failed to set time format: {e}")
                return False

        if dryRun:
            printSuccess("[DRY RUN] 24-hour time format would be configured successfully!")
        else:
            printSuccess("24-hour time format configured successfully!")
        printWarning("Note: You may need to log out and log back in for changes to take effect.")
        return True
    except Exception as e:
        printError(f"Failed to configure 24-hour time format: {e}")
        return False


def configureDarkMode(dryRun: bool = False) -> bool:
    """
    Configure Windows 11 to use dark mode for all settings.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if configuration was successful, False otherwise
    """
    printInfo("Configuring dark mode for all Windows 11 settings...")

    try:
        regPath = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"

        if dryRun:
            printInfo("[DRY RUN] Would set app mode to dark...")
            printInfo("[DRY RUN] Would set system mode to dark...")
        else:
            # Ensure the registry path exists
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, regPath, 0, winreg.KEY_WRITE)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, regPath)

            # Set app mode to dark (0 = dark, 1 = light)
            printInfo("Setting app mode to dark...")
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 0)

            # Set system mode to dark (0 = dark, 1 = light)
            printInfo("Setting system mode to dark...")
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 0)

            winreg.CloseKey(key)

        if dryRun:
            printSuccess("[DRY RUN] Dark mode would be configured successfully!")
        else:
            printSuccess("Dark mode configured successfully!")
        printInfo("Dark mode should be active immediately.")
        return True
    except Exception as e:
        printError(f"Failed to configure dark mode: {e}")
        return False


def configureFileExplorer(dryRun: bool = False) -> bool:
    """
    Configure File Explorer to show file extensions and hidden files.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if configuration was successful, False otherwise
    """
    printInfo("Configuring File Explorer settings...")

    try:
        regPath = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

        if dryRun:
            printInfo("[DRY RUN] Would enable file extensions display...")
            printInfo("[DRY RUN] Would enable hidden files display...")
            printInfo("[DRY RUN] Would refresh File Explorer...")
        else:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                regPath,
                0,
                winreg.KEY_WRITE,
            )

            # Show file extensions
            printInfo("Enabling file extensions display...")
            winreg.SetValueEx(key, "HideFileExt", 0, winreg.REG_DWORD, 0)

            # Show hidden files
            printInfo("Enabling hidden files display...")
            winreg.SetValueEx(key, "Hidden", 0, winreg.REG_DWORD, 1)

            winreg.CloseKey(key)

            # Refresh File Explorer to apply changes
            printInfo("Refreshing File Explorer...")
            try:
                subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], check=False, capture_output=True)
                time.sleep(2)
                subprocess.Popen("explorer.exe")
            except Exception:
                pass

        if dryRun:
            printSuccess("[DRY RUN] File Explorer would be configured successfully!")
        else:
            printSuccess("File Explorer configured successfully!")
        return True
    except Exception as e:
        printError(f"Failed to configure File Explorer: {e}")
        return False


def configurePrivacySettings(dryRun: bool = False) -> bool:
    """
    Configure Windows 11 privacy settings to reduce data collection.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if configuration was successful, False otherwise
    """
    printInfo("Configuring privacy settings...")

    try:
        if dryRun:
            printInfo("[DRY RUN] Would disable advertising ID...")
            printInfo("[DRY RUN] Would set diagnostic data to required only...")
            printInfo("[DRY RUN] Would disable location services...")
            printInfo("[DRY RUN] Would disable speech recognition...")
            printInfo("[DRY RUN] Would disable inking and typing personalization...")
        else:
            # Disable advertising ID
            printInfo("Disabling advertising ID...")
            try:
                adRegPath = r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo"
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, adRegPath, 0, winreg.KEY_WRITE)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, adRegPath)
            winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        except Exception as e:
            printWarning(f"Failed to disable advertising ID: {e}")

        # Set diagnostic data to required only (requires admin)
        if isAdministrator():
            printInfo("Setting diagnostic data to required only...")
            try:
                diagRegPath = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection"
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, diagRegPath, 0, winreg.KEY_WRITE)
                except FileNotFoundError:
                    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, diagRegPath)
                winreg.SetValueEx(key, "AllowTelemetry", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
            except Exception as e:
                printWarning(f"Failed to set diagnostic data: {e}")

        # Disable location services (requires admin)
        if isAdministrator():
            printInfo("Disabling location services...")
            try:
                locationRegPath = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location"
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, locationRegPath, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(key, "Value", 0, winreg.REG_SZ, "Deny")
                    winreg.CloseKey(key)
                except FileNotFoundError:
                    pass
            except Exception as e:
                printWarning(f"Failed to disable location services: {e}")

        # Disable speech recognition
        printInfo("Disabling speech recognition...")
        try:
            speechRegPath = r"Software\Microsoft\Speech_OneCore\Settings\OnlineSpeechPrivacy"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, speechRegPath, 0, winreg.KEY_WRITE)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, speechRegPath)
            winreg.SetValueEx(key, "HasAccepted", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        except Exception as e:
            printWarning(f"Failed to disable speech recognition: {e}")

        # Disable inking and typing personalization
        printInfo("Disabling inking and typing personalization...")
        try:
            inkRegPath = r"Software\Microsoft\InputPersonalization"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, inkRegPath, 0, winreg.KEY_WRITE)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, inkRegPath)
            winreg.SetValueEx(key, "RestrictImplicitTextCollection", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "RestrictImplicitInkCollection", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except Exception as e:
            printWarning(f"Failed to disable inking and typing personalization: {e}")

        if dryRun:
            printSuccess("[DRY RUN] Privacy settings would be configured successfully!")
        else:
            printSuccess("Privacy settings configured successfully!")
        return True
    except Exception as e:
        printError(f"Failed to configure privacy settings: {e}")
        return False


def configureTaskbar(dryRun: bool = False) -> bool:
    """
    Configure Windows 11 taskbar settings.
    Sets taskbar alignment to left (classic Windows style).

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if configuration was successful, False otherwise
    """
    printInfo("Configuring taskbar settings...")

    try:
        regPath = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

        if dryRun:
            printInfo("[DRY RUN] Would set taskbar alignment to left...")
            printInfo("[DRY RUN] Would refresh taskbar...")
        else:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                regPath,
                0,
                winreg.KEY_WRITE,
            )

            # Set taskbar alignment to left
            printInfo("Setting taskbar alignment to left...")
            winreg.SetValueEx(key, "TaskbarAl", 0, winreg.REG_DWORD, 0)

            winreg.CloseKey(key)

            # Refresh explorer to apply changes
            printInfo("Refreshing taskbar...")
            try:
                subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"], check=False, capture_output=True)
                time.sleep(2)
                subprocess.Popen("explorer.exe")
            except Exception:
                pass

        if dryRun:
            printSuccess("[DRY RUN] Taskbar would be configured successfully!")
        else:
            printSuccess("Taskbar configured successfully!")
        return True
    except Exception as e:
        printError(f"Failed to configure taskbar: {e}")
        return False


def enableDeveloperMode(dryRun: bool = False) -> bool:
    """
    Enable Windows 11 Developer Mode.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if configuration was successful, False otherwise
    """
    printInfo("Enabling Developer Mode...")

    try:
        if not isAdministrator():
            printError("Administrative privileges are required to enable Developer Mode. Please run as Administrator.")
            return False

        if dryRun:
            printInfo("[DRY RUN] Would enable Developer Mode...")
        else:
            regPath = r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"

            # Ensure the registry path exists
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, regPath, 0, winreg.KEY_WRITE)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, regPath)

            # Enable developer mode
            printInfo("Enabling Developer Mode...")
            winreg.SetValueEx(key, "AllowDevelopmentWithoutDevLicense", 0, winreg.REG_DWORD, 1)

            winreg.CloseKey(key)

        if dryRun:
            printSuccess("[DRY RUN] Developer Mode would be enabled successfully!")
        else:
            printSuccess("Developer Mode enabled successfully!")
        return True
    except Exception as e:
        printError(f"Failed to enable Developer Mode: {e}")
        return False


def disableNotifications(dryRun: bool = False) -> bool:
    """
    Disable all Windows 11 notifications.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if configuration was successful, False otherwise
    """
    printInfo("Disabling all notifications...")

    try:
        if dryRun:
            printInfo("[DRY RUN] Would disable system notifications...")
            printInfo("[DRY RUN] Would disable notification banners...")
            printInfo("[DRY RUN] Would disable notification centre...")
            printInfo("[DRY RUN] Would disable all app notifications...")
        else:
            # Disable system notifications (ToastEnabled)
            printInfo("Disabling system notifications...")
            try:
                systemRegPath = r"Software\Microsoft\Windows\CurrentVersion\PushNotifications"
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, systemRegPath, 0, winreg.KEY_WRITE)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, systemRegPath)
            winreg.SetValueEx(key, "ToastEnabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        except Exception as e:
            printWarning(f"Failed to disable system notifications: {e}")

        # Disable notification banners
        printInfo("Disabling notification banners...")
        try:
            bannerRegPath = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, bannerRegPath, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "DisallowPinnedFolderBanner", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except Exception as e:
            printWarning(f"Failed to disable notification banners: {e}")

        # Disable notification centre
        printInfo("Disabling notification centre...")
        try:
            notifCentreRegPath = r"Software\Policies\Microsoft\Windows\Explorer"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, notifCentreRegPath, 0, winreg.KEY_WRITE)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, notifCentreRegPath)
            winreg.SetValueEx(key, "DisableNotificationCenter", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except Exception as e:
            printWarning(f"Failed to disable notification centre: {e}")

        # Disable all app notifications globally
        printInfo("Disabling all app notifications...")
        try:
            systemNotifRegPath = r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, systemNotifRegPath, 0, winreg.KEY_WRITE)
            except FileNotFoundError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, systemNotifRegPath)
            winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        except Exception as e:
            printWarning(f"Failed to disable app notifications: {e}")

        if dryRun:
            printSuccess("[DRY RUN] All notifications would be disabled successfully!")
        else:
            printSuccess("All notifications disabled successfully!")
        printWarning("Note: You may need to restart some applications for changes to take effect.")
        return True
    except Exception as e:
        printError(f"Failed to disable notifications: {e}")
        return False


def enableWSL2(dryRun: bool = False) -> bool:
    """
    Enable Windows Subsystem for Linux 2 (WSL2) support.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if configuration was successful, False otherwise
    """
    printInfo("Enabling WSL2 support...")

    try:
        if not isAdministrator():
            printError("Administrative privileges are required to enable WSL2. Please run as Administrator.")
            return False

        if dryRun:
            printInfo("[DRY RUN] Would enable Windows Subsystem for Linux feature...")
            printInfo("[DRY RUN] Would enable Virtual Machine Platform feature...")
            printInfo("[DRY RUN] Would set WSL2 as default version...")
        else:
            # Enable Windows Subsystem for Linux
            printInfo("Enabling Windows Subsystem for Linux feature...")
            result1 = subprocess.run(
                [
                    "dism.exe",
                    "/online",
                    "/enable-feature",
                    "/featurename:Microsoft-Windows-Subsystem-Linux",
                    "/all",
                    "/norestart",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result1.returncode != 0:
                printWarning(f"Failed to enable Windows Subsystem for Linux feature. Exit code: {result1.returncode}")

            # Enable Virtual Machine Platform (required for WSL2)
            printInfo("Enabling Virtual Machine Platform feature...")
            result2 = subprocess.run(
                [
                    "dism.exe",
                    "/online",
                    "/enable-feature",
                    "/featurename:VirtualMachinePlatform",
                    "/all",
                    "/norestart",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result2.returncode != 0:
                printWarning(f"Failed to enable Virtual Machine Platform feature. Exit code: {result2.returncode}")

            # Set WSL2 as default version (if WSL is already installed)
            printInfo("Setting WSL2 as default version...")
            wslCheck = subprocess.run(
                ["wsl", "--status"],
                capture_output=True,
                text=True,
                check=False,
            )
            if wslCheck.returncode == 0:
                wslSetDefault = subprocess.run(
                    ["wsl", "--set-default-version", "2"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if wslSetDefault.returncode == 0:
                    printSuccess("WSL2 set as default version.")
                else:
                    printWarning("WSL may need to be updated. Run 'wsl --update' after restart.")
            else:
                printInfo("WSL will be available after system restart.")

        if dryRun:
            printSuccess("[DRY RUN] WSL2 support would be enabled successfully!")
        else:
            printSuccess("WSL2 support enabled successfully!")
        printWarning("IMPORTANT: A system restart is required for WSL2 features to be fully enabled.")
        printInfo("After restart, you can install a Linux distribution with: wsl --install -d <DistributionName>")

        if not dryRun:
            response = input("Would you like to restart now? (Y/N): ").strip()
            if response.upper() == "Y":
            printInfo("Restarting computer in 10 seconds...")
            time.sleep(10)
            subprocess.run(["shutdown", "/r", "/t", "0"], check=False)

        return True
    except Exception as e:
        printError(f"Failed to enable WSL2: {e}")
        return False


def configureWin11(dryRun: bool = False) -> bool:
    """
    Main configuration function for Windows 11.
    Applies various Windows 11 configuration settings.

    Args:
        dryRun: If True, don't actually configure

    Returns:
        True if all configurations were successful, False otherwise
    """
    printSection("Windows 11 Configuration", dryRun=dryRun)
    safePrint()

    success = True

    # Configure regional settings
    try:
        if not configureRegionalSettings(dryRun=dryRun):
            success = False
    except Exception as e:
        printWarning(f"Failed to configure regional settings: {e}")
        success = False

    safePrint()

    # Configure 24-hour time
    try:
        if not configure24HourTime(dryRun=dryRun):
            success = False
    except Exception as e:
        printWarning(f"Failed to configure 24-hour time: {e}")
        success = False

    safePrint()

    # Configure dark mode
    try:
        if not configureDarkMode(dryRun=dryRun):
            success = False
    except Exception as e:
        printWarning(f"Failed to configure dark mode: {e}")
        success = False

    safePrint()

    # Configure File Explorer
    try:
        if not configureFileExplorer(dryRun=dryRun):
            success = False
    except Exception as e:
        printWarning(f"Failed to configure File Explorer: {e}")
        success = False

    safePrint()

    # Configure privacy settings
    try:
        if not configurePrivacySettings(dryRun=dryRun):
            success = False
    except Exception as e:
        printWarning(f"Failed to configure privacy settings: {e}")
        success = False

    safePrint()

    # Configure taskbar
    try:
        if not configureTaskbar(dryRun=dryRun):
            success = False
    except Exception as e:
        printWarning(f"Failed to configure taskbar: {e}")
        success = False

    safePrint()

    # Enable Developer Mode
    try:
        if not enableDeveloperMode(dryRun=dryRun):
            success = False
    except Exception as e:
        printWarning(f"Failed to enable Developer Mode: {e}")
        success = False

    safePrint()

    # Disable notifications
    try:
        if not disableNotifications(dryRun=dryRun):
            success = False
    except Exception as e:
        printWarning(f"Failed to disable notifications: {e}")
        success = False

    safePrint()

    # Enable WSL2
    try:
        if not enableWSL2(dryRun=dryRun):
            success = False
    except Exception as e:
        printWarning(f"Failed to enable WSL2: {e}")
        success = False

    safePrint()
    printSection("Configuration Complete", dryRun=dryRun)

    if success:
        if dryRun:
            printSuccess("All settings would be configured successfully!")
        else:
            printSuccess("All settings have been configured successfully!")
        printWarning("Please restart your computer for all changes to take full effect.")
    else:
        printWarning("Some settings may not have been configured. Please review the errors above.")

    return success


if __name__ == "__main__":
    # Parse arguments
    dryRun = "--dryRun" in sys.argv or "--dry-run" in sys.argv
    sys.exit(0 if configureWin11(dryRun=dryRun) else 1)
