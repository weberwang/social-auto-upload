param(
    [Parameter(Mandatory = $true)]
    [int]$Port,

    [int]$TimeoutSeconds = 30,

    [string]$TargetHost = "127.0.0.1"
)

function Test-PortReady {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetHost,

        [Parameter(Mandatory = $true)]
        [int]$Port,

        [Parameter(Mandatory = $true)]
        [datetime]$Deadline
    )

    # 使用原生 TcpClient 轮询端口，避免依赖固定 HTTP 路由，减少后端实现差异带来的误判。
    while ((Get-Date) -lt $Deadline) {
        $client = New-Object System.Net.Sockets.TcpClient

        try {
            $asyncResult = $client.BeginConnect($TargetHost, $Port, $null, $null)
            if ($asyncResult.AsyncWaitHandle.WaitOne(1000, $false) -and $client.Connected) {
                $client.EndConnect($asyncResult)
                return $true
            }
        }
        catch {
            # 连接失败通常说明服务仍在启动中，这里静默重试，避免污染批处理输出。
        }
        finally {
            $client.Dispose()
        }

        Start-Sleep -Milliseconds 500
    }

    return $false
}

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
if (Test-PortReady -TargetHost $TargetHost -Port $Port -Deadline $deadline) {
    exit 0
}

exit 1
