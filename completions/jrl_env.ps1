# PowerShell completion for jrl_env setup.ps1 and CLI
# Add to your PowerShell profile:
#   . /path/to/jrl_env/completions/jrl_env.ps1

# Completion for setup.ps1
Register-ArgumentCompleter -CommandName setup.ps1 -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    $installTargets = @('all', 'fonts', 'apps', 'git', 'cursor', 'repos', 'ssh')
    $updateTargets = @('all', 'apps', 'system')
    $passphraseMode = @('require', 'no')

    # Handle --install=<tab>
    if ($wordToComplete -like '--install=*')
    {
        $prefix = '--install='
        $suffix = $wordToComplete.Substring($prefix.Length)

        # Handle comma-separated targets
        if ($suffix -like '*,*')
        {
            $parts = $suffix -split ','
            $currentPrefix = ($parts[0..($parts.Count - 2)] -join ',') + ','
            $lastPart = $parts[-1]

            $installTargets | Where-Object { $_ -like "$lastPart*" } | ForEach-Object {
                [System.Management.Automation.CompletionResult]::new(
                    "$prefix$currentPrefix$_",
                    $_,
                    'ParameterValue',
                    "Install: $_"
                )
            }
        }
        else
        {
            $installTargets | Where-Object { $_ -like "$suffix*" } | ForEach-Object {
                [System.Management.Automation.CompletionResult]::new(
                    "$prefix$_",
                    $_,
                    'ParameterValue',
                    "Install: $_"
                )
            }
        }
        return
    }

    # Handle --update=<tab>
    if ($wordToComplete -like '--update=*')
    {
        $prefix = '--update='
        $suffix = $wordToComplete.Substring($prefix.Length)

        # Handle comma-separated targets
        if ($suffix -like '*,*')
        {
            $parts = $suffix -split ','
            $currentPrefix = ($parts[0..($parts.Count - 2)] -join ',') + ','
            $lastPart = $parts[-1]

            $updateTargets | Where-Object { $_ -like "$lastPart*" } | ForEach-Object {
                [System.Management.Automation.CompletionResult]::new(
                    "$prefix$currentPrefix$_",
                    $_,
                    'ParameterValue',
                    "Update: $_"
                )
            }
        }
        else
        {
            $updateTargets | Where-Object { $_ -like "$suffix*" } | ForEach-Object {
                [System.Management.Automation.CompletionResult]::new(
                    "$prefix$_",
                    $_,
                    'ParameterValue',
                    "Update: $_"
                )
            }
        }
        return
    }

    # Handle --passphrase=<tab>
    if ($wordToComplete -like '--passphrase=*')
    {
        $prefix = '--passphrase='
        $suffix = $wordToComplete.Substring($prefix.Length)

        $passphraseMode | Where-Object { $_ -like "$suffix*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new(
                "$prefix$_",
                $_,
                'ParameterValue',
                "Passphrase mode: $_"
            )
        }
        return
    }

    # Default options
    $options = @(
        '--install',
        '--update',
        '--passphrase',
        '--configDir',
        '--dryRun',
        '--noBackup',
        '--verbose',
        '--quiet',
        '--noTimestamps',
        '--clearRepoCache',
        '--resume',
        '--noResume',
        '--listSteps',
        '--help',
        '--version'
    )

    $options | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterName', $_)
    }
}

# Completion for CLI module
$jrlEnvCliCompleter = {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    $platforms = @('macos', 'win11', 'ubuntu', 'debian', 'popos', 'linuxmint', 'elementary', 'zorin', 'mxlinux', 'raspberrypi', 'fedora', 'redhat', 'opensuse', 'archlinux', 'manjaro', 'endeavouros', 'alpine')
    $operations = @('fonts', 'apps', 'git', 'ssh', 'cursor', 'repos', 'status', 'rollback', 'verify', 'update')
    $options = @('--help', '--version', '--verbose', '--quiet', '--dryRun', '--configDir')

    # Get positional argument count (non-flags)
    $positionalArgs = @($commandAst.CommandElements | Where-Object { $_ -notmatch '^-' })
    $argCount = $positionalArgs.Count - 1  # Subtract 1 for the command itself

    # First positional: platform
    if ($argCount -eq 1)
    {
        $platforms | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', "Platform: $_")
        }
        return
    }

    # Second positional: operation
    if ($argCount -eq 2)
    {
        $operations | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', "Operation: $_")
        }
        return
    }

    # Third+: options
    $options | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterName', $_)
    }
}

# Register CLI completion
Register-ArgumentCompleter -CommandName 'jrlEnvCli' -ScriptBlock $jrlEnvCliCompleter

# Also register for the full python command
Register-ArgumentCompleter -CommandName 'python3' -ParameterName 'ArgumentList' -ScriptBlock {
    param($commandName, $parameterName, $wordToComplete, $commandAst, $fakeBoundParameters)

    # Only complete if running common.systems.cli
    $commandLine = $commandAst.ToString()
    if ($commandLine -match 'common\.systems\.cli' -or $commandLine -match 'common/systems/cli')
    {
        & $jrlEnvCliCompleter $commandName $parameterName $wordToComplete $commandAst $fakeBoundParameters
    }
}

Write-Host "jrl_env completion loaded for PowerShell" -ForegroundColor Green
