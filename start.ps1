#Requires -Version 5.1

<#
.SYNOPSIS
    Ghostpad Launcher
.DESCRIPTION
    Installs dependencies, builds frontend, and starts the web application server
.NOTES
    Requires PowerShell 5.1 or higher
#>

param(
    [switch]$Force,
    [switch]$SkipBuild
)

# Set error handling
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Colors for output
$colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error   = "Red"
    Info    = "Cyan"
    Header  = "Magenta"
}

function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    Write-Host $Message -ForegroundColor $colors[$Type]
}

function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Test-RealPython {
    try {
        # First check if python command exists
        if (-not (Test-CommandExists "python")) {
            return $false
        }
        
        # Try to run python --version and capture output
        $result = Start-Process -FilePath "python" -ArgumentList "--version" -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput "temp_python_check.txt" -RedirectStandardError "temp_python_error.txt"
        
        # Check if it actually executed (real Python returns 0)
        $success = ($result.ExitCode -eq 0)
        
        # Clean up temp files
        Remove-Item "temp_python_check.txt" -ErrorAction SilentlyContinue
        Remove-Item "temp_python_error.txt" -ErrorAction SilentlyContinue
        
        return $success
    }
    catch {
        return $false
    }
}

function Test-RealNode {
    try {
        # First check if node command exists
        if (-not (Test-CommandExists "node")) {
            return $false
        }
        
        # Try to run node --version and check exit code
        $result = Start-Process -FilePath "node" -ArgumentList "--version" -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput "temp_node_check.txt" -RedirectStandardError "temp_node_error.txt"
        
        # Check if it actually executed
        $success = ($result.ExitCode -eq 0)
        
        # Clean up temp files
        Remove-Item "temp_node_check.txt" -ErrorAction SilentlyContinue
        Remove-Item "temp_node_error.txt" -ErrorAction SilentlyContinue
        
        return $success
    }
    catch {
        return $false
    }
}

function Refresh-EnvironmentPath {
    Write-ColoredOutput "Refreshing environment variables..." "Info"
    
    # Get machine and user PATH
    $machinePath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    
    # Combine and update current session
    $combinedPath = "$userPath;$machinePath"
    $env:PATH = $combinedPath
    
    Write-ColoredOutput "Environment PATH refreshed" "Success"
}

function Install-Python {
    Write-ColoredOutput "Python not found. Installing Python via winget..." "Warning"
    
    try {
        $result = Start-Process -FilePath "winget" -ArgumentList @(
            "install", "Python.Python.3.12", 
            "--silent", 
            "--accept-source-agreements", 
            "--accept-package-agreements"
        ) -Wait -PassThru -WindowStyle Hidden
        
        if ($result.ExitCode -ne 0) {
            throw "winget install failed with exit code $($result.ExitCode)"
        }
        
        Write-ColoredOutput "Python installed successfully" "Success"
        return $true
    }
    catch {
        Write-ColoredOutput "ERROR: Failed to install Python via winget: $($_.Exception.Message)" "Error"
        throw
    }
}

function Install-NodeJS {
    Write-ColoredOutput "Node.js not found. Installing Node.js via winget..." "Warning"
    
    try {
        $result = Start-Process -FilePath "winget" -ArgumentList @(
            "install", "OpenJS.NodeJS.LTS",
            "--silent",
            "--accept-source-agreements", 
            "--accept-package-agreements"
        ) -Wait -PassThru -WindowStyle Hidden
        
        if ($result.ExitCode -ne 0) {
            throw "winget install failed with exit code $($result.ExitCode)"
        }
        
        Write-ColoredOutput "Node.js installed successfully" "Success"
        return $true
    }
    catch {
        Write-ColoredOutput "ERROR: Failed to install Node.js via winget: $($_.Exception.Message)" "Error"
        throw
    }
}

function Install-UV {
    Write-ColoredOutput "Installing uv..." "Info"
    
    try {
        # Upgrade pip first
        python -m pip install --upgrade pip --quiet
        
        # Install uv
        python -m pip install uv --quiet
        
        Write-ColoredOutput "uv installed successfully" "Success"
    }
    catch {
        Write-ColoredOutput "ERROR: Failed to install uv via pip: $($_.Exception.Message)" "Error"
        throw
    }
}

function Setup-PythonEnvironment {
    Write-ColoredOutput "Setting up Python environment..." "Info"
    
    # Clean existing virtual environment if it exists or if Force is specified
    if ((Test-Path ".venv") -and ($Force -or (Read-Host "Virtual environment exists. Recreate? (y/N)") -eq "y")) {
        Write-ColoredOutput "Cleaning existing virtual environment..." "Warning"
        Remove-Item -Path ".venv" -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path ".venv")) {
        Write-ColoredOutput "Creating virtual environment..." "Info"
        uv venv
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment"
        }
    }
    
    # Install Python dependencies
    Write-ColoredOutput "Installing Python dependencies..." "Info"
    uv sync
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColoredOutput "First sync attempt failed, retrying..." "Warning"
        Remove-Item -Path ".venv" -Recurse -Force -ErrorAction SilentlyContinue
        uv venv
        uv sync
        
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install Python dependencies"
        }
    }
    
    Write-ColoredOutput "Python environment ready" "Success"
}

function Test-FrontendBuildNeeded {
    if ($SkipBuild) {
        return $false
    }
    
    if (-not (Test-Path "frontend\dist")) {
        return $true
    }
    
    if (-not (Test-Path "frontend\package.json")) {
        return $false
    }
    
    $packageJsonTime = (Get-Item "frontend\package.json").LastWriteTime
    $distFiles = Get-ChildItem "frontend\dist" -Recurse -File -ErrorAction SilentlyContinue
    
    if (-not $distFiles) {
        return $true
    }
    
    $oldestDistFile = ($distFiles | Sort-Object LastWriteTime | Select-Object -First 1).LastWriteTime
    
    return $packageJsonTime -gt $oldestDistFile
}

function Build-Frontend {
    if (-not (Test-FrontendBuildNeeded)) {
        Write-ColoredOutput "Frontend build is up to date" "Success"
        return
    }
    
    Write-ColoredOutput "Building React frontend..." "Info"
    
    Push-Location "frontend"
    try {
        # Install npm dependencies if needed
        if (-not (Test-Path "node_modules")) {
            Write-ColoredOutput "Installing npm dependencies..." "Info"
            npm install
            if ($LASTEXITCODE -ne 0) {
                throw "npm install failed"
            }
        }
        
        # Build the frontend
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed"
        }
        
        Write-ColoredOutput "Frontend build completed" "Success"
    }
    finally {
        Pop-Location
    }
}

function Start-Server {
    Write-ColoredOutput "" "Info"
    Write-ColoredOutput "Starting server at http://127.0.0.1:8000" "Header"
    Write-ColoredOutput "Press Ctrl+C to stop" "Info"
    Write-ColoredOutput "" "Info"
    
    uv run python api/main.py
}

# Main execution
try {
    Write-ColoredOutput "=== Ghostpad Launcher ===" "Header"
    Write-ColoredOutput "" "Info"
    
    $needsPathRefresh = $false
    
    # Check and install Python
    if (-not (Test-RealPython)) {
        Install-Python
        $needsPathRefresh = $true
    } else {
        Write-ColoredOutput "Python is already installed" "Success"
    }
    
    # Check and install Node.js
    if (-not (Test-RealNode)) {
        Install-NodeJS
        $needsPathRefresh = $true
    } else {
        Write-ColoredOutput "Node.js is already installed" "Success"
    }
    
    # Refresh PATH if installations occurred
    if ($needsPathRefresh) {
        Refresh-EnvironmentPath
    }
    
    # Verify installations worked
    if (-not (Test-RealPython)) {
        throw "Python installation failed - real Python not found after installation"
    }
    if (-not (Test-RealNode)) {
        throw "Node.js installation failed - real Node.js not found after installation"
    }
    
    # Install uv if needed
    if (-not (Test-CommandExists "uv")) {
        Install-UV
    } else {
        Write-ColoredOutput "uv is already installed" "Success"
    }
    
    # Setup Python environment
    Setup-PythonEnvironment
    
    # Build frontend
    Build-Frontend
    
    # Start the server
    Start-Server
}
catch {
    Write-ColoredOutput "" "Info"
    Write-ColoredOutput "ERROR: $($_.Exception.Message)" "Error"
    Write-ColoredOutput "" "Info"
    Read-Host "Press Enter to exit"
    exit 1
}