param(
    [Parameter(Mandatory = $true)]
    [string]$BackendEntry,

    [Parameter(Mandatory = $true)]
    [int]$BackendPort
)

$backendPath = [System.IO.Path]::GetFullPath($BackendEntry)
$backendName = [System.IO.Path]::GetFileName($backendPath)
$netstatExe = Join-Path $env:SystemRoot "System32\netstat.exe"
$portPattern = "^\s*TCP\s+\S+:$BackendPort\s+\S+\s+LISTENING\s+(\d+)\s*$"

$listenerProcessIds = @(
    & $netstatExe -ano |
        ForEach-Object {
            if ($_ -match $portPattern) {
                [int]$Matches[1]
            }
        }
) | Sort-Object -Unique

if ($listenerProcessIds) {
    Write-Output "[INFO] Backend listener PIDs on port ${BackendPort}: $($listenerProcessIds -join ', ')"
}

# 同时按命令行和监听端口识别旧后端，覆盖 .\sau_backend.py 这类相对路径启动方式。
$processes = Get-CimInstance Win32_Process |
    Where-Object {
        $isPython = $_.Name -match '^python(?:w)?\.exe$'
        $isBackendCommand = $_.CommandLine -and (
            $_.CommandLine.Contains($backendPath) -or
            $_.CommandLine.Contains($backendName)
        )
        $isBackendListener = $listenerProcessIds -contains ([int]$_.ProcessId)

        $isPython -and $_.ProcessId -ne $PID -and ($isBackendCommand -or $isBackendListener)
    } |
    Sort-Object ProcessId -Unique

if (-not $processes) {
    Write-Output '[INFO] No old backend process found.'
    exit 0
}

foreach ($process in $processes) {
    Write-Output "[INFO] Stopping old backend process PID=$($process.ProcessId)"
    Stop-Process -Id $process.ProcessId -Force
}

Start-Sleep -Milliseconds 500
Write-Output '[INFO] Old backend cleanup complete.'
