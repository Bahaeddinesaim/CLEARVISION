$ErrorActionPreference = "Stop"

$domain = "clearvisionai.local"
$ip = "10.68.247.21"
$hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
$entry = "$ip $domain"

$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Please run this script as Administrator:"
    Write-Host "powershell -ExecutionPolicy Bypass -File scripts\setup_local_domain.ps1"
    exit 1
}

$hostsContent = Get-Content -LiteralPath $hostsPath -ErrorAction Stop
$alreadyConfigured = $hostsContent | Where-Object { $_ -match "^\s*$ip\s+$domain\s*$" }

if ($alreadyConfigured) {
    Write-Host "$domain is already configured."
} else {
    Add-Content -LiteralPath $hostsPath -Value $entry
    Write-Host "Added: $entry"
}

Write-Host "Now start Streamlit with:"
Write-Host "powershell -ExecutionPolicy Bypass -File scripts\start_lan.ps1"
Write-Host "Then open: http://clearvisionai.local:8502"
