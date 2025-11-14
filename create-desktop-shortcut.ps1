# Create Desktop Shortcut for StockGPT
# This script creates a convenient desktop shortcut for easy access

param(
    [string]$Name = "StockGPT Terminal",
    [string]$Description = "StockGPT Paper Trade Terminal - One-Click Access"
)

# Get desktop path
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "$Name.lnk"

# Get the current directory (where StockGPT is installed)
$stockGPTPath = $PSScriptRoot
if (-not $stockGPTPath) {
    $stockGPTPath = Get-Location
}

# Create the shortcut
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)

# Set shortcut properties
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$stockGPTPath\StockGPT-Deploy.bat`""
$shortcut.WorkingDirectory = $stockGPTPath
$shortcut.Description = $Description
$shortcut.IconLocation = "powershell.exe, 0"

# Save the shortcut
$shortcut.Save()

Write-Host ""
Write-Host "✅ Desktop shortcut created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Shortcut Details:" -ForegroundColor Yellow
Write-Host "  Name: $Name" -ForegroundColor White
Write-Host "  Location: $shortcutPath" -ForegroundColor White
Write-Host "  Description: $Description" -ForegroundColor White
Write-Host ""
Write-Host "You can now double-click the shortcut on your desktop to access StockGPT!" -ForegroundColor Green
Write-Host ""

# Optional: Create Start Menu shortcut
$startMenuPath = [Environment]::GetFolderPath("StartMenu")
$startMenuShortcutPath = Join-Path $startMenuPath "Programs\$Name.lnk"

$startMenuShortcut = $shell.CreateShortcut($startMenuShortcutPath)
$startMenuShortcut.TargetPath = "powershell.exe"
$startMenuShortcut.Arguments = "-ExecutionPolicy Bypass -File `"$stockGPTPath\StockGPT-Deploy.bat`""
$startMenuShortcut.WorkingDirectory = $stockGPTPath
$startMenuShortcut.Description = $Description
$startMenuShortcut.IconLocation = "powershell.exe, 0"
$startMenuShortcut.Save()

Write-Host "✅ Start Menu shortcut also created!" -ForegroundColor Green
Write-Host ""

# Clean up COM objects
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($shortcut) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($startMenuShortcut) | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell) | Out-Null

Write-Host "Installation complete! 🎉" -ForegroundColor Green