#!/usr/bin/env python3
"""
Single entry point for all common Python utilities and modules.
All Python scripts outside of common/ should import from this module.
"""

# Import and expose all logging utilities
from common.core.logging import (
    Colours,
    Verbosity,
    printLock,
    safePrint,
    printInfo,
    printWarning,
    printError,
    printSuccess,
    printVerbose,
    printDebug,
    printH1,
    printH2,
    printH3,
    printSection,
    printHelpText,
    colourise,
    setVerbosity,
    getVerbosity,
    setVerbosityFromArgs,
    setShowConsoleTimestamps,
    getShowConsoleTimestamps,
    setHeadingDepth,
    getHeadingDepth,
    printHeading,
    getSubprocessEnv,
)

# Import and expose all utility functions
from common.core.utilities import (
    commandExists,
    requireCommand,
    getJsonValue,
    getJsonArray,
    getJsonObject,
    findOperatingSystem,
    getOperatingSystem,
    isOperatingSystem,
    getConfigDirectory,
    hasInternetConnectivity,
)
from common.core.signalHandling import (
    setupSignalHandlers,
)

# Import and expose Linux package manager
from common.linux.packageManager import (
    PackageManager,
    AptPackageManager,
    YumPackageManager,
    DnfPackageManager,
    RpmPackageManager,
    validateManager,
    createPackageManager,
    getPackageManager,
    mapPackageName,
    packageMappings,
    supportedManagers,
)

# Import and expose Windows package manager (only on Windows)
try:
    from common.windows.packageManager import (
        isWingetInstalled,
        installWinget,
        updateWinget,
        updateMicrosoftStore,
        isAppInstalled,
    )
    _WINDOWS_AVAILABLE = True
except ImportError:
    # Windows-specific modules not available on non-Windows systems
    _WINDOWS_AVAILABLE = False

# Import and expose setup args
from common.install.setupArgs import (
    SetupArgs,
    RunFlags,
    parseSetupArgs,
    determineRunFlags,
)

# Import and expose setup utilities
from common.install.setupUtils import (
    backupConfigs,
    checkDependencies,
    initLogging,
    shouldCloneRepositories,
)

# Import and expose installation modules
from common.install.installApps import (
    InstallResult,
    CommandConfig,
    installPackages,
    mergeJsonArrays,
    installFromConfig,
    installFromConfigWithLinuxCommon,
    parseCommandJson,
    getCommandFlagFile,
    isCommandAlreadyRun,
    markCommandAsRun,
    executeConfigCommand,
    runConfigCommands,
    installApps,
)

# Import and expose configuration modules
from common.configure.configureGit import (
    isGitInstalled,
    readJsonSection,
    setGitConfig,
    configureGitUser,
    configureGitDefaults,
    configureGitAliases,
    configureGitLfs,
    configureGit,
)
from common.configure.configureCursor import (
    mergeJsonSettings,
    configureCursor,
)
from common.configure.configureGithubSsh import (
    copyToClipboard,
    openUrl,
    startSshAgent,
    addKeyToSshAgent,
    configureGithubSsh,
)
from common.configure.cloneRepositories import (
    isGitInstalled as isGitInstalledForClone,
    getRepositoryOwner,
    getRepositoryName,
    isRepositoryCloned,
    cloneRepository,
    expandPath,
    cloneRepositories,
)
from common.configure.configureAndroid import (
    findAndroidSdkRoot,
    findSdkManager,
    isAndroidStudioInstalled,
    checkAndroidStudioInConfig,
    installSdkComponents,
    configureAndroid,
)
from common.configure.configureShellEnv import (
    getShellConfigFile,
    hasEnvironmentVariable,
    addEnvironmentVariable,
    addToPath,
    configureAndroidEnvironmentVariables,
    findNdkRoot,
)

# Import and expose system orchestration modules
from common.systems.configManager import (
    ConfigManager,
)
from common.systems.validationEngine import (
    ValidationEngine,
)
from common.systems.setupOrchestrator import (
    SetupOrchestrator,
)
from common.systems.stepDefinitions import (
    SetupStep,
    setupSteps,
    getStepsToRun,
    willAnyStepsRun,
)
from common.systems.systemsConfig import (
    SystemConfig,
    systemsConfig,
    getSystemConfig,
    getSupportedPlatforms,
)
# Note: GenericSystem and createSystem are not imported here to avoid circular imports
# Import them directly from common.systems.genericSystem when needed
from common.systems.platform import (
    Platform,
)

__all__ = [
    # Logging utilities
    "Colours",
    "printLock",
    "safePrint",
    "printInfo",
    "printWarning",
    "printError",
    "printSuccess",
    "printH1",
    "printH2",
    "printH3",
    "printSection",
    "colourise",
    # Utility functions
    "commandExists",
    "requireCommand",
    "getJsonValue",
    "getJsonArray",
    "getJsonObject",
    "findOperatingSystem",
    "getOperatingSystem",
    "isOperatingSystem",
    "getConfigDirectory",
    "hasInternetConnectivity",
    # Linux package manager
    "PackageManager",
    "AptPackageManager",
    "YumPackageManager",
    "DnfPackageManager",
    "RpmPackageManager",
    "validateManager",
    "createPackageManager",
    "getPackageManager",
    "mapPackageName",
    "packageMappings",
    "supportedManagers",
    # Setup args
    "SetupArgs",
    "RunFlags",
    "parseSetupArgs",
            "determineRunFlags",
            # Setup utilities
            "backupConfigs",
            "checkDependencies",
            "initLogging",
            "shouldCloneRepositories",
            # Installation
    "InstallResult",
    "CommandConfig",
    "installPackages",
    "mergeJsonArrays",
    "installFromConfig",
    "installFromConfigWithLinuxCommon",
    "parseCommandJson",
    "getCommandFlagFile",
    "isCommandAlreadyRun",
    "markCommandAsRun",
    "executeConfigCommand",
    "runConfigCommands",
    "installApps",
    # Configuration
    "isGitInstalled",
    "readJsonSection",
    "setGitConfig",
    "configureGitUser",
    "configureGitDefaults",
    "configureGitAliases",
    "configureGitLfs",
    "configureGit",
    "mergeJsonSettings",
    "configureCursor",
    "copyToClipboard",
    "openUrl",
    "startSshAgent",
    "addKeyToSshAgent",
    "configureGithubSsh",
    "getRepositoryOwner",
    "getRepositoryName",
    "isRepositoryCloned",
    "cloneRepository",
    "expandPath",
    "cloneRepositories",
    # Android configuration
    "findAndroidSdkRoot",
    "findSdkManager",
    "isAndroidStudioInstalled",
    "checkAndroidStudioInConfig",
    "installSdkComponents",
    "configureAndroid",
    # Shell environment configuration
    "getShellConfigFile",
    "hasEnvironmentVariable",
    "addEnvironmentVariable",
    "addToPath",
    "configureAndroidEnvironmentVariables",
    "findNdkRoot",
    # System orchestration
    "ConfigManager",
    "ValidationEngine",
    "SetupOrchestrator",
    # Step definitions
    "SetupStep",
    "setupSteps",
    "getStepsToRun",
    "willAnyStepsRun",
    # System configuration
    "SystemConfig",
    "systemsConfig",
    "getSystemConfig",
    "getSupportedPlatforms",
    "GenericSystem",
    "createSystem",
    "Platform",
]

# Conditionally add Windows exports if available
if _WINDOWS_AVAILABLE:
    __all__.extend([
        # Windows package manager
        "isWingetInstalled",
        "installWinget",
        "updateWinget",
        "updateMicrosoftStore",
        "isAppInstalled",
    ])
