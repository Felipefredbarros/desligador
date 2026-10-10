#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Faz o Desligador iniciar sozinho (sem janela) quando voce entra no Windows.

.DESCRIPTION
    1. Registra a tarefa "Desligador" no Agendador de Tarefas (gatilho: logon do usuario atual).
    2. Cria regra de firewall liberando a porta apenas para a rede do Tailscale (100.64.0.0/10).
    3. Inicia a tarefa e mostra o PIN e o endereco de acesso.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
#>
param(
    [int]$Porta = 8765
)

$ErrorActionPreference = "Stop"
$NomeTarefa = "Desligador"
$NomeRegra = "Desligador (Tailscale)"
$PastaSrc = (Resolve-Path (Join-Path $PSScriptRoot "..\src")).Path
$ArquivoConfig = Join-Path $env:APPDATA "Desligador\config.json"

Write-Host "==> Localizando o Python..." -ForegroundColor Cyan
$python = (& py -c "import sys; print(sys.executable)").Trim()
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) {
    throw "pythonw.exe nao encontrado em '$pythonw'. Instale o Python pelo python.org."
}
Write-Host "    $pythonw"

Write-Host "==> Registrando a tarefa '$NomeTarefa'..." -ForegroundColor Cyan
$usuario = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$acao = New-ScheduledTaskAction -Execute $pythonw -Argument "-m desligador" -WorkingDirectory $PastaSrc
$gatilho = New-ScheduledTaskTrigger -AtLogOn -User $usuario
$principal = New-ScheduledTaskPrincipal -UserId $usuario -LogonType Interactive -RunLevel Limited
$ajustes = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $NomeTarefa -Action $acao -Trigger $gatilho `
    -Principal $principal -Settings $ajustes -Force `
    -Description "Servidor do Desligador (desligar o PC pelo celular via Tailscale)." | Out-Null

Write-Host "==> Criando regra de firewall (porta $Porta, somente Tailscale)..." -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName $NomeRegra -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName $NomeRegra -Direction Inbound -Action Allow `
    -Protocol TCP -LocalPort $Porta -RemoteAddress "100.64.0.0/10" -Profile Any | Out-Null

Write-Host "==> Iniciando..." -ForegroundColor Cyan
Stop-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue
Start-ScheduledTask -TaskName $NomeTarefa
Start-Sleep -Seconds 3

if (-not (Test-Path $ArquivoConfig)) {
    Write-Warning "O config ainda nao foi criado. Veja o log em $env:LOCALAPPDATA\Desligador\desligador.log"
    exit 1
}
$config = Get-Content $ArquivoConfig -Raw | ConvertFrom-Json

$ipTailscale = $null
if (Get-Command tailscale -ErrorAction SilentlyContinue) {
    $ipTailscale = (& tailscale ip -4 2>$null | Select-Object -First 1)
}

Write-Host ""
Write-Host "Pronto! O Desligador vai iniciar sozinho sempre que voce entrar no Windows." -ForegroundColor Green
Write-Host "  PIN:    $($config.pin)   (em $ArquivoConfig)"
Write-Host "  Neste PC: http://localhost:$($config.porta)"
if ($ipTailscale) {
    Write-Host "  Celular:  http://$($env:COMPUTERNAME.ToLower()):$($config.porta)  ou  http://${ipTailscale}:$($config.porta)"
} else {
    Write-Warning "Tailscale nao encontrado. Instale em https://tailscale.com/download para acessar pelo celular."
}
