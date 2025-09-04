@echo off
REM Launch the PowerShell script with execution policy bypass
powershell.exe -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
pause