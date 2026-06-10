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
    [string]$DependencyCheckScript,

    [Parameter()]
    [string]$EnvOutputFile
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

function Format-CommandArgument { # 为 cmd.exe 组装稳定的原生命令行，避免路径和空格被截断。
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    if ($Value -notmatch '[\s"]') {
        return $Value
    }

    return '"' + $Value.Replace('"', '""') + '"'
}

function Invoke-NativeCommand { # 使用独立进程和临时文件捕获输出，避免 stderr warning 被 PowerShell 提升成终止错误。
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter()]
        [string[]]$Arguments = @()
    )

    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    $resolvedFilePath = (Resolve-Path -LiteralPath $FilePath).Path
    $commandSegments = @($resolvedFilePath) + $Arguments
    $commandLine = ($commandSegments | ForEach-Object { Format-CommandArgument -Value $_ }) -join ' '

    try {
        $process = Start-Process `
            -FilePath $env:ComSpec `
            -ArgumentList @('/d', '/c', $commandLine) `
            -NoNewWindow `
            -Wait `
            -PassThru `
            -RedirectStandardOutput $stdoutFile `
            -RedirectStandardError $stderrFile

        foreach ($line in [System.IO.File]::ReadLines($stdoutFile)) {
            [Console]::Error.WriteLine($line)
        }

        foreach ($line in [System.IO.File]::ReadLines($stderrFile)) {
            [Console]::Error.WriteLine($line)
        }

        return $process.ExitCode
    }
    finally {
        Remove-Item -LiteralPath $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue
    }
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

function Rebuild-ProjectVenvWithUv { # 当现有 .venv 元数据损坏时，直接重建项目虚拟环境比原地修补更可靠。
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$VenvPythonExe,

        [Parameter(Mandatory = $true)]
        [string]$UvExecutable,

        [Parameter(Mandatory = $true)]
        [string]$RequirementsFile
    )

    $scriptsDirectory = Split-Path -Path $VenvPythonExe -Parent
    $venvDirectory = Split-Path -Path $scriptsDirectory -Parent
    $resolvedVenvDirectory = [System.IO.Path]::GetFullPath($venvDirectory)

    if ([System.IO.Path]::GetFileName($resolvedVenvDirectory) -ne '.venv') {
        throw "Refusing to rebuild a non-project venv path: $resolvedVenvDirectory"
    }

    Write-StatusLine "[WARN] Rebuilding project virtual environment: $resolvedVenvDirectory"
    if (Test-Path -LiteralPath $resolvedVenvDirectory) {
        Remove-Item -LiteralPath $resolvedVenvDirectory -Recurse -Force
    }

    $exitCode = Invoke-NativeCommand -FilePath $UvExecutable -Arguments @('venv', $resolvedVenvDirectory)
    if ($exitCode -ne 0) {
        throw "uv venv failed with exit code $exitCode."
    }

    $rebuiltPythonExe = Join-Path -Path $resolvedVenvDirectory -ChildPath 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $rebuiltPythonExe)) {
        throw "uv venv completed but no project Python was created: $rebuiltPythonExe"
    }

    $exitCode = Invoke-NativeCommand -FilePath $UvExecutable -Arguments @('pip', 'install', '--python', $rebuiltPythonExe, '-r', $RequirementsFile)
    if ($exitCode -ne 0) {
        throw "uv pip install after venv rebuild failed with exit code $exitCode."
    }

    return @{
        PythonExe = [System.IO.Path]::GetFullPath($rebuiltPythonExe)
        PythonSource = '.venv (rebuilt by uv)'
    }
}

function Install-BackendDependencies { # 缺依赖时按 requirements.txt 收敛环境，并在 pip 缺失时回退到 uv pip。
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
    $canUseUv = $null -ne $uvCommand

    # 当前启动链路仍以 requirements.txt 作为完整依赖清单，先按它收敛环境，避免 uv 元数据不全时把依赖删薄。
    Write-StatusLine '[INFO] Backend dependencies are incomplete. Installing from requirements.txt...'
    $exitCode = Invoke-NativeCommand -FilePath $PythonRuntime.PythonExe -Arguments @('-m', 'pip', 'install', '-r', $RequirementsFile)
    if ($exitCode -eq 0) {
        return $PythonRuntime
    }

    if ($canUseUv) { # 目标解释器没有 pip 时，用 uv 直接向该解释器安装 requirements，避免再次依赖不完整的锁文件。
        Write-StatusLine '[WARN] pip install failed. Falling back to uv pip...'
        $exitCode = Invoke-NativeCommand -FilePath $uvCommand.Source -Arguments @('pip', 'install', '--python', $PythonRuntime.PythonExe, '-r', $RequirementsFile)
        if ($exitCode -eq 0) {
            return $PythonRuntime
        }

        if ($PythonRuntime.PythonSource -like '.venv*') { # 仅对项目内 .venv 执行重建，避免误删用户自定义解释器目录。
            return Rebuild-ProjectVenvWithUv `
                -VenvPythonExe $VenvPythonExe `
                -UvExecutable $uvCommand.Source `
                -RequirementsFile $RequirementsFile
        }

        throw "pip install failed and uv pip failed with exit code $exitCode."
    }

    throw "pip install failed with exit code $exitCode."
}

function Publish-EnvironmentAssignments { # 通过环境文件向批处理回传变量，避免错误输出被当成命令执行。
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$PythonRuntime,

        [Parameter()]
        [string]$EnvOutputFile
    )

    $lines = @(
        ('set "PYTHON_EXE={0}"' -f $PythonRuntime.PythonExe),
        ('set "PYTHON_SOURCE={0}"' -f $PythonRuntime.PythonSource)
    )

    if ([string]::IsNullOrWhiteSpace($EnvOutputFile)) {
        foreach ($line in $lines) {
            Write-Output $line
        }
        return
    }

    $parentDirectory = Split-Path -Path $EnvOutputFile -Parent
    if (-not [string]::IsNullOrWhiteSpace($parentDirectory)) {
        New-Item -ItemType Directory -Path $parentDirectory -Force | Out-Null
    }

    Set-Content -LiteralPath $EnvOutputFile -Value $lines -Encoding Ascii
}

$pythonRuntime = Resolve-BackendPython -VenvPythonExe $VenvPythonExe
Write-StatusLine "[preflight] Using Python from $($pythonRuntime.PythonSource): $($pythonRuntime.PythonExe)"
Write-StatusLine '[preflight] Checking backend Python dependencies...'

$exitCode = Invoke-NativeCommand -FilePath $pythonRuntime.PythonExe -Arguments @($DependencyCheckScript)
if ($exitCode -ne 0) {
    $pythonRuntime = Install-BackendDependencies `
        -PythonRuntime $pythonRuntime `
        -VenvPythonExe $VenvPythonExe `
        -PyprojectFile $PyprojectFile `
        -UvLockFile $UvLockFile `
        -RequirementsFile $RequirementsFile

    Write-StatusLine '[preflight] Re-checking backend Python dependencies...'
    $exitCode = Invoke-NativeCommand -FilePath $pythonRuntime.PythonExe -Arguments @($DependencyCheckScript)
    if ($exitCode -ne 0) {
        throw 'Backend dependencies are still incomplete after installation.'
    }
}

Publish-EnvironmentAssignments -PythonRuntime $pythonRuntime -EnvOutputFile $EnvOutputFile
