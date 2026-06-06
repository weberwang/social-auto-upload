param(
    [Parameter(Mandatory = $true)]
    [string]$FrontendDir,

    [Parameter(Mandatory = $true)]
    [string]$WaitPortScript,

    [Parameter(Mandatory = $true)]
    [int]$BackendPort
)

# 前端放到独立窗口里等待后端端口，避免批处理里嵌套 cmd 引号和 &&/|| 导致解析失真。
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

# 这里切到前端目录后直接接管窗口，便于持续查看 Vite 输出和后续手动操作。
Set-Location -Path $FrontendDir
npm run dev -- --host 0.0.0.0
