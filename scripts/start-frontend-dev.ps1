param(
    [Parameter(Mandatory = $true)]
    [string]$FrontendDir,

    [Parameter(Mandatory = $true)]
    [string]$WaitPortScript,

    [Parameter(Mandatory = $true)]
    [int]$BackendPort,

    [int]$BackendReadyTimeoutSeconds = 120
)

$projectFrontendDir = [System.IO.Path]::GetFullPath($FrontendDir)

# Stop stale Vite processes from this repo so the next launch stays on 5173.
function Stop-StaleFrontendProcesses {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$FrontendDir
    )

    $escapedFrontendDir = [Regex]::Escape($FrontendDir)
    $viteProcesses = Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -eq 'node.exe' -and
            $_.CommandLine -and
            $_.CommandLine -match $escapedFrontendDir -and
            $_.CommandLine -match 'vite'
        } |
        Sort-Object ProcessId -Unique

    if (-not $viteProcesses) {
        Write-Output '[INFO] No stale frontend Vite process found.'
        return
    }

    foreach ($viteProcess in $viteProcesses) {
        Write-Output "[INFO] Stopping stale frontend Vite process PID=$($viteProcess.ProcessId)"
        Stop-Process -Id $viteProcess.ProcessId -Force
    }

    Start-Sleep -Milliseconds 500
}

# Wait for the backend first, then start the frontend in the current window.
$waitProcess = Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $WaitPortScript,
    "-Port", $BackendPort,
    "-TimeoutSeconds", $BackendReadyTimeoutSeconds.ToString()
) -PassThru -Wait -NoNewWindow

if ($waitProcess.ExitCode -ne 0) {
    # 后端未就绪时直接终止前端启动，避免页面首屏请求触发一串代理拒绝连接错误。
    Write-Error "后端在 $BackendReadyTimeoutSeconds 秒内未就绪，已取消前端启动，请先检查当前窗口里的后端日志。"
    exit 1
}

Stop-StaleFrontendProcesses -FrontendDir $projectFrontendDir

# Use the default Vite dev command so the project root is detected correctly.
Set-Location -Path $projectFrontendDir
npm run dev
