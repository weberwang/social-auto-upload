param(
    [Parameter(Mandatory = $true)]
    [string]$FrontendDir,

    [Parameter(Mandatory = $true)]
    [string]$WaitPortScript,

    [Parameter(Mandatory = $true)]
    [int]$BackendPort
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
    "-TimeoutSeconds", "30"
) -PassThru -Wait -NoNewWindow

if ($waitProcess.ExitCode -ne 0) {
    Write-Warning "Backend was not confirmed within 30 seconds. Frontend will still start."
}

Stop-StaleFrontendProcesses -FrontendDir $projectFrontendDir

# Use the default Vite dev command so the project root is detected correctly.
Set-Location -Path $projectFrontendDir
npm run dev
