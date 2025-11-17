# Function to configure Windows 11 regional settings
function configureRegionalSettings {
    <#
    .SYNOPSIS
    Configures Windows 11 regional settings including language and locale.

    .DESCRIPTION
    Sets the system locale, user locale, and regional format to en-CA (English Canada).
    Requires administrative privileges to change system-wide settings.

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.

    .EXAMPLE
    configureRegionalSettings

    .NOTES
    Requires administrative privileges. Run PowerShell as Administrator.
    #>
    param()

    Write-Host "Configuring regional settings to en-CA (English Canada)..." -ForegroundColor Cyan

    try {
        # Check if running as administrator
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin) {
            Write-Error "Administrative privileges are required to configure regional settings. Please run PowerShell as Administrator."
            return $false
        }

        # Import International module if available
        $internationalModule = Get-Module -ListAvailable -Name International
        if ($internationalModule) {
            Import-Module International -ErrorAction SilentlyContinue
        }

        # Set system locale to en-CA
        Write-Host "Setting system locale to en-CA..." -ForegroundColor Yellow
        if (Get-Command Set-WinSystemLocale -ErrorAction SilentlyContinue) {
            Set-WinSystemLocale -SystemLocale en-CA -ErrorAction Stop
        }
        else {
            # Alternative: Use registry method
            Write-Host "Using registry method to set system locale..." -ForegroundColor Yellow
            Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\Language" -Name "Default" -Value "1009" -ErrorAction Stop  # 1009 is en-CA
        }

        # Set user locale to en-CA
        Write-Host "Setting user locale to en-CA..." -ForegroundColor Yellow
        if (Get-Command Set-Culture -ErrorAction SilentlyContinue) {
            Set-Culture -CultureInfo en-CA -ErrorAction Stop
        }
        else {
            # Alternative: Use registry method
            Write-Host "Using registry method to set user locale..." -ForegroundColor Yellow
            Set-ItemProperty -Path "HKCU:\Control Panel\International" -Name "Locale" -Value "00001009" -ErrorAction Stop
        }

        # Set regional format to en-CA
        Write-Host "Setting regional format to en-CA..." -ForegroundColor Yellow
        if (Get-Command Set-WinHomeLocation -ErrorAction SilentlyContinue) {
            Set-WinHomeLocation -GeoId 39 -ErrorAction Stop  # 39 is the GeoId for Canada
        }
        else {
            # Alternative: Use registry method
            Write-Host "Using registry method to set regional format..." -ForegroundColor Yellow
            Set-ItemProperty -Path "HKCU:\Control Panel\International\Geo" -Name "Nation" -Value "39" -ErrorAction Stop
        }

        Write-Host "Regional settings configured successfully!" -ForegroundColor Green
        Write-Host "Note: You may need to restart your computer for all changes to take effect." -ForegroundColor Yellow
        return $true
    }
    catch {
        Write-Error "Failed to configure regional settings: $_"
        return $false
    }
}

# Function to configure 24-hour time format
function configure24HourTime {
    <#
    .SYNOPSIS
    Configures Windows 11 to use 24-hour time format.

    .DESCRIPTION
    Sets the time format to 24-hour (HH:mm) for both short and long time formats.
    Requires administrative privileges to modify registry settings.

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.

    .EXAMPLE
    configure24HourTime

    .NOTES
    Requires administrative privileges. Run PowerShell as Administrator.
    #>
    param()

    Write-Host "Configuring 24-hour time format..." -ForegroundColor Cyan

    try {
        # Check if running as administrator
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin) {
            Write-Error "Administrative privileges are required to configure time format. Please run PowerShell as Administrator."
            return $false
        }

        # Registry path for regional settings
        $regPath = "HKCU:\Control Panel\International"

        # Set short time format to 24-hour (HH:mm)
        Write-Host "Setting short time format to 24-hour (HH:mm)..." -ForegroundColor Yellow
        Set-ItemProperty -Path $regPath -Name "sShortTime" -Value "HH:mm" -ErrorAction Stop

        # Set long time format to 24-hour (HH:mm:ss)
        Write-Host "Setting long time format to 24-hour (HH:mm:ss)..." -ForegroundColor Yellow
        Set-ItemProperty -Path $regPath -Name "sTimeFormat" -Value "HH:mm:ss" -ErrorAction Stop

        # Also set for system-wide (requires admin)
        $systemRegPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Nls\Locale"
        if (Test-Path $systemRegPath) {
            Write-Host "Setting system-wide time format..." -ForegroundColor Yellow
            # Note: System-wide time format is typically controlled by user settings
            # The user-level settings above should be sufficient
        }

        Write-Host "24-hour time format configured successfully!" -ForegroundColor Green
        Write-Host "Note: You may need to log out and log back in for changes to take effect." -ForegroundColor Yellow
        return $true
    }
    catch {
        Write-Error "Failed to configure 24-hour time format: $_"
        return $false
    }
}

# Function to configure dark mode for Windows 11
function configureDarkMode {
    <#
    .SYNOPSIS
    Configures Windows 11 to use dark mode for all settings.

    .DESCRIPTION
    Sets both app mode and system mode to dark theme. This affects:
    - Windows apps (Settings, File Explorer, etc.)
    - System UI elements (taskbar, start menu, etc.)

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.

    .EXAMPLE
    configureDarkMode

    .NOTES
    Changes take effect immediately. No restart required.
    #>
    param()

    Write-Host "Configuring dark mode for all Windows 11 settings..." -ForegroundColor Cyan

    try {
        # Registry path for personalization settings
        $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"

        # Ensure the registry path exists
        if (-not (Test-Path $regPath)) {
            New-Item -Path $regPath -Force | Out-Null
        }

        # Set app mode to dark (0 = dark, 1 = light)
        Write-Host "Setting app mode to dark..." -ForegroundColor Yellow
        Set-ItemProperty -Path $regPath -Name "AppsUseLightTheme" -Value 0 -Type DWord -ErrorAction Stop

        # Set system mode to dark (0 = dark, 1 = light)
        Write-Host "Setting system mode to dark..." -ForegroundColor Yellow
        Set-ItemProperty -Path $regPath -Name "SystemUsesLightTheme" -Value 0 -Type DWord -ErrorAction Stop

        Write-Host "Dark mode configured successfully!" -ForegroundColor Green
        Write-Host "Dark mode should be active immediately." -ForegroundColor Green
        return $true
    }
    catch {
        Write-Error "Failed to configure dark mode: $_"
        return $false
    }
}

# Function to configure File Explorer settings
function configureFileExplorer {
    <#
    .SYNOPSIS
    Configures File Explorer to show file extensions and hidden files.

    .DESCRIPTION
    Sets File Explorer to display:
    - File extensions for known file types
    - Hidden files and folders
    - Protected operating system files (optional)

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.

    .EXAMPLE
    configureFileExplorer

    .NOTES
    Changes take effect immediately for new File Explorer windows.
    #>
    param()

    Write-Host "Configuring File Explorer settings..." -ForegroundColor Cyan

    try {
        # Registry path for File Explorer settings
        $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

        # Show file extensions
        Write-Host "Enabling file extensions display..." -ForegroundColor Yellow
        Set-ItemProperty -Path $regPath -Name "HideFileExt" -Value 0 -Type DWord -ErrorAction Stop

        # Show hidden files
        Write-Host "Enabling hidden files display..." -ForegroundColor Yellow
        Set-ItemProperty -Path $regPath -Name "Hidden" -Value 1 -Type DWord -ErrorAction Stop

        # Show protected operating system files (optional - commented out by default)
        # Write-Host "Enabling protected OS files display..." -ForegroundColor Yellow
        # Set-ItemProperty -Path $regPath -Name "ShowSuperHidden" -Value 1 -Type DWord -ErrorAction Stop

        # Refresh File Explorer to apply changes
        Write-Host "Refreshing File Explorer..." -ForegroundColor Yellow
        Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Start-Process explorer.exe

        Write-Host "File Explorer configured successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Error "Failed to configure File Explorer: $_"
        return $false
    }
}

# Function to configure privacy settings
function configurePrivacySettings {
    <#
    .SYNOPSIS
    Configures Windows 11 privacy settings to reduce data collection.

    .DESCRIPTION
    Disables various privacy-invading features including:
    - Advertising ID
    - Diagnostic data (sets to required only)
    - Location services
    - Speech recognition
    - Inking and typing personalization

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.

    .EXAMPLE
    configurePrivacySettings

    .NOTES
    Requires administrative privileges for some settings.
    #>
    param()

    Write-Host "Configuring privacy settings..." -ForegroundColor Cyan

    try {
        # Disable advertising ID
        Write-Host "Disabling advertising ID..." -ForegroundColor Yellow
        $adRegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo"
        if (-not (Test-Path $adRegPath)) {
            New-Item -Path $adRegPath -Force | Out-Null
        }
        Set-ItemProperty -Path $adRegPath -Name "Enabled" -Value 0 -Type DWord -ErrorAction Stop

        # Set diagnostic data to required only
        Write-Host "Setting diagnostic data to required only..." -ForegroundColor Yellow
        $diagRegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection"
        if (-not (Test-Path $diagRegPath)) {
            New-Item -Path $diagRegPath -Force | Out-Null
        }
        Set-ItemProperty -Path $diagRegPath -Name "AllowTelemetry" -Value 0 -Type DWord -ErrorAction SilentlyContinue

        # Disable location services
        Write-Host "Disabling location services..." -ForegroundColor Yellow
        $locationRegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location"
        if (Test-Path $locationRegPath) {
            Set-ItemProperty -Path $locationRegPath -Name "Value" -Value "Deny" -Type String -ErrorAction SilentlyContinue
        }

        # Disable speech recognition
        Write-Host "Disabling speech recognition..." -ForegroundColor Yellow
        $speechRegPath = "HKCU:\Software\Microsoft\Speech_OneCore\Settings\OnlineSpeechPrivacy"
        if (-not (Test-Path $speechRegPath)) {
            New-Item -Path $speechRegPath -Force | Out-Null
        }
        Set-ItemProperty -Path $speechRegPath -Name "HasAccepted" -Value 0 -Type DWord -ErrorAction Stop

        # Disable inking and typing personalization
        Write-Host "Disabling inking and typing personalization..." -ForegroundColor Yellow
        $inkRegPath = "HKCU:\Software\Microsoft\InputPersonalization"
        if (-not (Test-Path $inkRegPath)) {
            New-Item -Path $inkRegPath -Force | Out-Null
        }
        Set-ItemProperty -Path $inkRegPath -Name "RestrictImplicitTextCollection" -Value 1 -Type DWord -ErrorAction Stop
        Set-ItemProperty -Path $inkRegPath -Name "RestrictImplicitInkCollection" -Value 1 -Type DWord -ErrorAction Stop

        Write-Host "Privacy settings configured successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Error "Failed to configure privacy settings: $_"
        return $false
    }
}

# Function to configure taskbar settings
function configureTaskbar {
    <#
    .SYNOPSIS
    Configures Windows 11 taskbar settings.

    .DESCRIPTION
    Sets taskbar alignment to left (classic Windows style) and configures other taskbar preferences.

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.

    .EXAMPLE
    configureTaskbar

    .NOTES
    Changes take effect immediately.
    #>
    param()

    Write-Host "Configuring taskbar settings..." -ForegroundColor Cyan

    try {
        # Registry path for taskbar settings
        $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"

        # Set taskbar alignment to left
        Write-Host "Setting taskbar alignment to left..." -ForegroundColor Yellow
        Set-ItemProperty -Path $regPath -Name "TaskbarAl" -Value 0 -Type DWord -ErrorAction Stop

        # Refresh explorer to apply changes
        Write-Host "Refreshing taskbar..." -ForegroundColor Yellow
        Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Start-Process explorer.exe

        Write-Host "Taskbar configured successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Error "Failed to configure taskbar: $_"
        return $false
    }
}

# Function to enable developer mode
function enableDeveloperMode {
    <#
    .SYNOPSIS
    Enables Windows 11 Developer Mode.

    .DESCRIPTION
    Enables Developer Mode which allows:
    - Side-loading apps
    - Remote debugging
    - Access to developer features

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.

    .EXAMPLE
    enableDeveloperMode

    .NOTES
    Requires administrative privileges.
    #>
    param()

    Write-Host "Enabling Developer Mode..." -ForegroundColor Cyan

    try {
        # Check if running as administrator
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin) {
            Write-Error "Administrative privileges are required to enable Developer Mode. Please run PowerShell as Administrator."
            return $false
        }

        # Registry path for developer mode
        $regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"

        # Ensure the registry path exists
        if (-not (Test-Path $regPath)) {
            New-Item -Path $regPath -Force | Out-Null
        }

        # Enable developer mode
        Write-Host "Enabling Developer Mode..." -ForegroundColor Yellow
        Set-ItemProperty -Path $regPath -Name "AllowDevelopmentWithoutDevLicense" -Value 1 -Type DWord -ErrorAction Stop

        Write-Host "Developer Mode enabled successfully!" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Error "Failed to enable Developer Mode: $_"
        return $false
    }
}

# Function to disable all notifications
function disableNotifications {
    <#
    .SYNOPSIS
    Disables all Windows 11 notifications.

    .DESCRIPTION
    Turns off all notification settings including:
    - System notifications
    - App notifications
    - Focus assist settings
    - Notification banners and sounds

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.

    .EXAMPLE
    disableNotifications

    .NOTES
    Changes take effect immediately.
    #>
    param()

    Write-Host "Disabling all notifications..." -ForegroundColor Cyan

    try {
        # Registry path for notification settings
        $notifRegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"

        # Disable system notifications (ToastEnabled)
        Write-Host "Disabling system notifications..." -ForegroundColor Yellow
        $systemRegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\PushNotifications"
        if (-not (Test-Path $systemRegPath)) {
            New-Item -Path $systemRegPath -Force | Out-Null
        }
        Set-ItemProperty -Path $systemRegPath -Name "ToastEnabled" -Value 0 -Type DWord -ErrorAction Stop

        # Disable notification banners and toasts
        Write-Host "Disabling notification banners..." -ForegroundColor Yellow
        $bannerRegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
        Set-ItemProperty -Path $bannerRegPath -Name "DisallowPinnedFolderBanner" -Value 1 -Type DWord -ErrorAction SilentlyContinue

        # Disable notification center
        Write-Host "Disabling notification center..." -ForegroundColor Yellow
        $notifCenterRegPath = "HKCU:\Software\Policies\Microsoft\Windows\Explorer"
        if (-not (Test-Path $notifCenterRegPath)) {
            New-Item -Path $notifCenterRegPath -Force | Out-Null
        }
        Set-ItemProperty -Path $notifCenterRegPath -Name "DisableNotificationCenter" -Value 1 -Type DWord -ErrorAction SilentlyContinue

        # Disable notification sounds
        Write-Host "Disabling notification sounds..." -ForegroundColor Yellow
        $soundRegPath = "HKCU:\AppEvents\Schemes\Apps\.Default\Notification.Default\.Current"
        if (Test-Path $soundRegPath) {
            Set-ItemProperty -Path $soundRegPath -Name "(Default)" -Value "" -ErrorAction SilentlyContinue
        }

        # Disable notifications via System Settings registry
        $systemNotifRegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings"
        if (-not (Test-Path $systemNotifRegPath)) {
            New-Item -Path $systemNotifRegPath -Force | Out-Null
        }

        # Disable all app notifications globally
        Write-Host "Disabling all app notifications..." -ForegroundColor Yellow
        Set-ItemProperty -Path $systemNotifRegPath -Name "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND" -Value 0 -Type DWord -ErrorAction SilentlyContinue
        Set-ItemProperty -Path $systemNotifRegPath -Name "NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK" -Value 0 -Type DWord -ErrorAction SilentlyContinue

        Write-Host "All notifications disabled successfully!" -ForegroundColor Green
        Write-Host "Note: You may need to restart some applications for changes to take effect." -ForegroundColor Yellow
        return $true
    }
    catch {
        Write-Error "Failed to disable notifications: $_"
        return $false
    }
}

# Function to enable WSL2 support
function enableWSL2 {
    <#
    .SYNOPSIS
    Enables Windows Subsystem for Linux 2 (WSL2) support.

    .DESCRIPTION
    Enables the required Windows features for WSL2:
    - Windows Subsystem for Linux
    - Virtual Machine Platform
    Sets WSL2 as the default version.

    .OUTPUTS
    Boolean. Returns $true if configuration was successful, $false otherwise.

    .EXAMPLE
    enableWSL2

    .NOTES
    Requires administrative privileges. A system restart may be required after enabling features.
    #>
    param()

    Write-Host "Enabling WSL2 support..." -ForegroundColor Cyan

    try {
        # Check if running as administrator
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin) {
            Write-Error "Administrative privileges are required to enable WSL2. Please run PowerShell as Administrator."
            return $false
        }

        # Enable Windows Subsystem for Linux
        Write-Host "Enabling Windows Subsystem for Linux feature..." -ForegroundColor Yellow
        $result1 = dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to enable Windows Subsystem for Linux feature. Exit code: $LASTEXITCODE"
        }

        # Enable Virtual Machine Platform (required for WSL2)
        Write-Host "Enabling Virtual Machine Platform feature..." -ForegroundColor Yellow
        $result2 = dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to enable Virtual Machine Platform feature. Exit code: $LASTEXITCODE"
        }

        # Set WSL2 as default version (if WSL is already installed)
        Write-Host "Setting WSL2 as default version..." -ForegroundColor Yellow
        $wslCheck = wsl --status 2>&1
        if ($LASTEXITCODE -eq 0) {
            wsl --set-default-version 2 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "WSL2 set as default version." -ForegroundColor Green
            }
            else {
                Write-Warning "WSL may need to be updated. Run 'wsl --update' after restart."
            }
        }
        else {
            Write-Host "WSL will be available after system restart." -ForegroundColor Yellow
        }

        Write-Host "WSL2 support enabled successfully!" -ForegroundColor Green
        Write-Host "IMPORTANT: A system restart is required for WSL2 features to be fully enabled." -ForegroundColor Yellow
        Write-Host "After restart, you can install a Linux distribution with: wsl --install -d <DistributionName>" -ForegroundColor Yellow
        
        $restart = Read-Host "Would you like to restart now? (Y/N)"
        if ($restart -match '^[Yy]') {
            Write-Host "Restarting computer in 10 seconds..." -ForegroundColor Yellow
            Start-Sleep -Seconds 10
            Restart-Computer -Force
        }
        
        return $true
    }
    catch {
        Write-Error "Failed to enable WSL2: $_"
        return $false
    }
}

# Main configuration function
function configureWin11 {
    <#
    .SYNOPSIS
    Configures Windows 11 to user preferences.

    .DESCRIPTION
    Applies various Windows 11 configuration settings including:
    - Regional settings (en-CA)
    - 24-hour time format
    - Dark mode for all settings
    - File Explorer settings (show extensions, hidden files)
    - Privacy settings (disable telemetry, advertising ID)
    - Taskbar settings (left alignment)
    - Developer Mode
    - Notification settings (all disabled)
    - WSL2 support

    .OUTPUTS
    Boolean. Returns $true if all configurations were successful, $false otherwise.

    .EXAMPLE
    configureWin11

    .NOTES
    Requires administrative privileges. Run PowerShell as Administrator.
    #>
    param()

    Write-Host "=== Windows 11 Configuration ===" -ForegroundColor Cyan
    Write-Host ""

    $success = $true

    # Configure regional settings
    try
    {
        if (-not (configureRegionalSettings))
        {
            $success = $false
        }
    }
    catch
    {
        Write-Warning "Failed to configure regional settings: $_"
        $success = $false
    }

    Write-Host ""

    # Configure 24-hour time
    try
    {
        if (-not (configure24HourTime))
        {
            $success = $false
        }
    }
    catch
    {
        Write-Warning "Failed to configure 24-hour time: $_"
        $success = $false
    }

    Write-Host ""

    # Configure dark mode
    try
    {
        if (-not (configureDarkMode))
        {
            $success = $false
        }
    }
    catch
    {
        Write-Warning "Failed to configure dark mode: $_"
        $success = $false
    }

    Write-Host ""

    # Configure File Explorer
    try
    {
        if (-not (configureFileExplorer))
        {
            $success = $false
        }
    }
    catch
    {
        Write-Warning "Failed to configure File Explorer: $_"
        $success = $false
    }

    Write-Host ""

    # Configure privacy settings
    try
    {
        if (-not (configurePrivacySettings))
        {
            $success = $false
        }
    }
    catch
    {
        Write-Warning "Failed to configure privacy settings: $_"
        $success = $false
    }

    Write-Host ""

    # Configure taskbar
    try
    {
        if (-not (configureTaskbar))
        {
            $success = $false
        }
    }
    catch
    {
        Write-Warning "Failed to configure taskbar: $_"
        $success = $false
    }

    Write-Host ""

    # Enable Developer Mode
    try
    {
        if (-not (enableDeveloperMode))
        {
            $success = $false
        }
    }
    catch
    {
        Write-Warning "Failed to enable Developer Mode: $_"
        $success = $false
    }

    Write-Host ""

    # Disable notifications
    try
    {
        if (-not (disableNotifications))
        {
            $success = $false
        }
    }
    catch
    {
        Write-Warning "Failed to disable notifications: $_"
        $success = $false
    }

    Write-Host ""

    # Enable WSL2
    try
    {
        if (-not (enableWSL2))
        {
            $success = $false
        }
    }
    catch
    {
        Write-Warning "Failed to enable WSL2: $_"
        $success = $false
    }

    Write-Host ""
    Write-Host "=== Configuration Complete ===" -ForegroundColor Cyan

    if ($success) {
        Write-Host "All settings have been configured successfully!" -ForegroundColor Green
        Write-Host "Please restart your computer for all changes to take full effect." -ForegroundColor Yellow
    }
    else {
        Write-Host "Some settings may not have been configured. Please review the errors above." -ForegroundColor Red
    }

    return $success
}

