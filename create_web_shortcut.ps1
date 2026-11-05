# Creates a "PharmaSuite Web" icon on the Desktop that starts the web app and opens it.
$here = $PSScriptRoot
$desktop = [Environment]::GetFolderPath("Desktop")
$icon = Join-Path $here "..\pharmasuite_desktop\assets\pharmasuite.ico"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("$desktop\PharmaSuite Web.lnk")
$shortcut.TargetPath = "$here\start_web.bat"
$shortcut.WorkingDirectory = $here
if (Test-Path $icon) { $shortcut.IconLocation = (Resolve-Path $icon).Path }
$shortcut.Description = "PharmaSuite Pro (web)"
$shortcut.Save()
Write-Host "Shortcut created on Desktop: PharmaSuite Web"
