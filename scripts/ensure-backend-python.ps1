param(
    [Parameter(Mandatory = $true)]
    [string]$VenvPythonExe,

    [Parameter(Mandatory = $true)]
    [string]$PyprojectFile,

    [Parameter(Mandatory = $true)]
    [string]$UvLockFile,

    [Parameter(Mandatory = $true)]
    [string]$RequirementsFile,

    [Parameter(Mandatory = $true)]
    [string]$DependencyCheckScript
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-StatusLine {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    [Console]::Error.WriteLine($Message)
}

function Invoke-StderrPassthrough {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter()]
        [string[]]$Arguments = @()
    )

    $mergedOutput = & $FilePath @Arguments 2>&1
    foreach ($line in $mergedOutput) {
        [Console]::Error.WriteLine([string]$line)
    }

    return $LASTEXITCODE
}

function Resolve-BackendPython { # 优先项目 .venv，避免误用外部托管 Python。
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$VenvPythonExe
    )

    if (Test-Path -LiteralPath $VenvPythonExe) {
        return @{
            PythonExe = [System.IO.Path]::GetFullPath($VenvPythonExe)
            PythonSource = '.venv'
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pythonCommand) {
        return @{
            PythonExe = $pythonCommand.Source
            PythonSource = 'PATH'
        }
    }

    throw 'No available Python interpreter was found.'
}

function Install-BackendDependencies { # 缺依赖时优先复用 uv 锁文件恢复项目环境。
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$PythonRuntime,

        [Parameter(Mandatory = $true)]
        [string]$VenvPythonExe,

        [Parameter(Mandatory = $true)]
        [string]$PyprojectFile,

        [Parameter(Mandatory = $true)]
        [string]$UvLockFile,

        [Parameter(Mandatory = $true)]
        [string]$RequirementsFile
    )

    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    $canUseUv = $null -ne $uvCommand -and (Test-Path -LiteralPath $PyprojectFile) -and (Test-Path -LiteralPath $UvLockFile)

    if ($canUseUv) { # uv 项目统一把依赖落到 .venv，避免污染 PATH 解释器。
        Write-StatusLine '[INFO] Backend dependencies are incomplete. Syncing project environment with uv...'
        $exitCode = Invoke-StderrPassthrough -FilePath $uvCommand.Source -Arguments @('sync', '--frozen')
        if ($exitCode -ne 0) {
            throw "uv sync failed with exit code $exitCode."
        }

        if (-not (Test-Path -LiteralPath $VenvPythonExe)) {
            throw "uv sync completed but no project Python was created: $VenvPythonExe"
        }

        return @{
            PythonExe = [System.IO.Path]::GetFullPath($VenvPythonExe)
            PythonSource = '.venv (uv sync)'
        }
    }

    Write-StatusLine '[INFO] Backend dependencies are incomplete. Installing from requirements.txt...'
    $exitCode = Invoke-StderrPassthrough -FilePath $PythonRuntime.PythonExe -Arguments @('-m', 'pip', 'install', '-r', $RequirementsFile)
    if ($exitCode -ne 0) {
        throw "pip install failed with exit code $exitCode."
    }

    return $PythonRuntime
}

$pythonRuntime = Resolve-BackendPython -VenvPythonExe $VenvPythonExe
Write-StatusLine "[preflight] Using Python from $($pythonRuntime.PythonSource): $($pythonRuntime.PythonExe)"
Write-StatusLine '[preflight] Checking backend Python dependencies...'

$exitCode = Invoke-StderrPassthrough -FilePath $pythonRuntime.PythonExe -Arguments @($DependencyCheckScript)
if ($exitCode -ne 0) {
    $pythonRuntime = Install-BackendDependencies `
        -PythonRuntime $pythonRuntime `
        -VenvPythonExe $VenvPythonExe `
        -PyprojectFile $PyprojectFile `
        -UvLockFile $UvLockFile `
        -RequirementsFile $RequirementsFile

    Write-StatusLine '[preflight] Re-checking backend Python dependencies...'
    $exitCode = Invoke-StderrPassthrough -FilePath $pythonRuntime.PythonExe -Arguments @($DependencyCheckScript)
    if ($exitCode -ne 0) {
        throw 'Backend dependencies are still incomplete after installation.'
    }
}

Write-Output ('set "PYTHON_EXE={0}"' -f $pythonRuntime.PythonExe)
Write-Output ('set "PYTHON_SOURCE={0}"' -f $pythonRuntime.PythonSource)
