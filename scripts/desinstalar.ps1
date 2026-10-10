#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Remove a tarefa de inicializacao e a regra de firewall do Desligador.

.DESCRIPTION
    A configuracao (PIN) em %APPDATA%\Desligador e os logs em %LOCALAPPDATA%\Desligador
    sao mantidos. Apague essas pastas manualmente se quiser remover tudo.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\desinstalar.ps1
#>
$ErrorActionPreference = "Stop"
$NomeTarefa = "Desligador"
$NomeRegra = "Desligador (Tailscale)"

if (Get-ScheduledTask -TaskName $NomeTarefa -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $NomeTarefa
    Unregister-ScheduledTask -TaskName $NomeTarefa -Confirm:$false
    Write-Host "Tarefa '$NomeTarefa' removida."
} else {
    Write-Host "Tarefa '$NomeTarefa' nao estava instalada."
}

Get-NetFirewallRule -DisplayName $NomeRegra -ErrorAction SilentlyContinue | Remove-NetFirewallRule
Write-Host "Regra de firewall '$NomeRegra' removida (se existia)."
Write-Host "Config mantida em $env:APPDATA\Desligador e logs em $env:LOCALAPPDATA\Desligador."
