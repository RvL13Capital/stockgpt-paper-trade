# StockGPT Windows Deployment Script
# One-click deployment for Windows users

param(
    [switch]$Production,
    [switch]$Development,
    [switch]$Monitoring,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Status,
    [switch]$Logs,
    [switch]$Backup,
    [switch]$Update
)

# Colors for output
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Blue = "`e[34m"
$Reset = "`e[0m"

# Configuration
$ProjectName = "StockGPT"
$DockerComposeVersion = "2.23.0"
$DockerVersion = "24.0.7"
$RequiredMemoryGB = 8
$RequiredDiskSpaceGB = 20

# Functions
function Write-Header {
    param([string]$Message)
    Write-Host "`n${Blue}================================================${Reset}" -ForegroundColor Blue
    Write-Host "${Blue}  $Message${Reset}" -ForegroundColor Blue
    Write-Host "${Blue}================================================${Reset}" -ForegroundColor Blue
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "${Green}✅ $Message${Reset}" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "${Yellow}⚠️  $Message${Reset}" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "${Red}❌ $Message${Reset}" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "${Blue}ℹ️  $Message${Reset}" -ForegroundColor Blue
}

function Test-Administrator {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-DockerInstalled {
    try {
        $dockerVersion = docker --version 2>$null
        return $null -ne $dockerVersion
    }
    catch {
        return $false
    }
}

function Test-DockerComposeInstalled {
    try {
        $composeVersion = docker-compose --version 2>$null
        return $null -ne $composeVersion
    }
    catch {
        return $false
    }
}

function Get-SystemInfo {
    $osInfo = Get-CimInstance -ClassName Win32_OperatingSystem
    $totalMemoryGB = [math]::Round($osInfo.TotalVisibleMemorySize / 1MB, 2)
    $freeMemoryGB = [math]::Round($osInfo.FreePhysicalMemory / 1MB, 2)
    
    $diskInfo = Get-CimInstance -ClassName Win32_LogicalDisk | Where-Object { $_.DeviceID -eq "C:" }
    $freeDiskSpaceGB = [math]::Round($diskInfo.FreeSpace / 1GB, 2)
    
    return @{
        TotalMemoryGB = $totalMemoryGB
        FreeMemoryGB = $freeMemoryGB
        FreeDiskSpaceGB = $freeDiskSpaceGB
        OSVersion = $osInfo.Caption
    }
}

function Install-Docker {
    Write-Header "Installing Docker Desktop..."
    
    try {
        # Download Docker Desktop installer
        $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
        Write-Info "Downloading Docker Desktop..."
        Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile $dockerInstaller
        
        # Install Docker Desktop
        Write-Info "Installing Docker Desktop..."
        Start-Process -Wait -FilePath $dockerInstaller -ArgumentList "install", "--quiet", "--accept-license"
        
        Write-Success "Docker Desktop installed successfully!"
        Write-Warning "Please restart your computer to complete Docker installation."
        Write-Warning "After restart, run this script again to continue deployment."
        
        return $false
    }
    catch {
        Write-Error "Failed to install Docker: $($_.Exception.Message)"
        return $false
    }
}

function Install-DockerCompose {
    Write-Header "Installing Docker Compose..."
    
    try {
        # Download Docker Compose
        $composeUrl = "https://github.com/docker/compose/releases/download/v$DockerComposeVersion/docker-compose-Windows-x86_64.exe"
        $composePath = "$env:ProgramFiles\Docker\Docker\resources\bin\docker-compose.exe"
        
        Write-Info "Downloading Docker Compose..."
        Invoke-WebRequest -Uri $composeUrl -OutFile $composePath
        
        Write-Success "Docker Compose installed successfully!"
        return $true
    }
    catch {
        Write-Error "Failed to install Docker Compose: $($_.Exception.Message)"
        return $false
    }
}

function Test-Prerequisites {
    Write-Header "Checking System Prerequisites..."
    
    $systemInfo = Get-SystemInfo
    
    Write-Info "System Information:"
    Write-Info "  OS: $($systemInfo.OSVersion)"
    Write-Info "  Total Memory: $($systemInfo.TotalMemoryGB) GB"
    Write-Info "  Free Memory: $($systemInfo.FreeMemoryGB) GB"
    Write-Info "  Free Disk Space: $($systemInfo.FreeDiskSpaceGB) GB"
    
    # Check memory
    if ($systemInfo.TotalMemoryGB -lt $RequiredMemoryGB) {
        Write-Warning "Insufficient memory. Required: $RequiredMemoryGB GB, Available: $($systemInfo.TotalMemoryGB) GB"
        Write-Warning "Consider closing other applications or upgrading RAM."
    }
    
    # Check disk space
    if ($systemInfo.FreeDiskSpaceGB -lt $RequiredDiskSpaceGB) {
        Write-Warning "Insufficient disk space. Required: $RequiredDiskSpaceGB GB, Available: $($systemInfo.FreeDiskSpaceGB) GB"
        Write-Warning "Consider freeing up disk space."
    }
    
    # Check Docker
    if (-not (Test-DockerInstalled)) {
        Write-Warning "Docker is not installed."
        $installDocker = Read-Host "Would you like to install Docker Desktop? (Y/N)"
        if ($installDocker -eq "Y" -or $installDocker -eq "y") {
            $dockerInstalled = Install-Docker
            if (-not $dockerInstalled) {
                return $false
            }
        } else {
            Write-Error "Docker is required for StockGPT. Please install Docker Desktop manually."
            return $false
        }
    } else {
        Write-Success "Docker is installed."
    }
    
    # Check Docker Compose
    if (-not (Test-DockerComposeInstalled)) {
        Write-Warning "Docker Compose is not installed."
        $composeInstalled = Install-DockerCompose
        if (-not $composeInstalled) {
            return $false
        }
    } else {
        Write-Success "Docker Compose is installed."
    }
    
    return $true
}

function Initialize-Environment {
    Write-Header "Initializing Environment..."
    
    # Create necessary directories
    $directories = @("data", "logs", "backups", "ssl", "secrets")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Success "Created directory: $dir"
        }
    }
    
    # Create .env file if it doesn't exist
    if (-not (Test-Path ".env")) {
        Write-Info "Creating .env file..."
        
        $apiKey1 = -join ((33..126) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
        $apiKey2 = -join ((33..126) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
        $jwtSecret = -join ((33..126) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
        
$envContent = @"
# StockGPT Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database Configuration
POSTGRES_DB=stockgpt
POSTGRES_USER=stockgpt_user
POSTGRES_PASSWORD=stockgpt_password_$(Get-Random -Minimum 1000 -Maximum 9999)

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=stockgpt_redis_password_$(Get-Random -Minimum 1000 -Maximum 9999)

# Security
JWT_SECRET_KEY=$jwtSecret
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API Keys (Replace with your actual keys)
FINNHUB_API_KEY=$apiKey1
ALPHA_VANTAGE_API_KEY=$apiKey2
POLYGON_API_KEY=your_polygon_api_key
TIINGO_API_KEY=your_tiingo_api_key

# CORS Configuration
ALLOWED_HOSTS=["*"]

# Feature Flags
FEATURE_REAL_TIME_DATA=true
FEATURE_ADVANCED_CHARTS=true
FEATURE_MODEL_INSIGHTS=true

# Windows Specific
COMPOSE_PROJECT_NAME=stockgpt
COMPOSE_PATH_SEPARATOR=;
COMPOSE_FILE=docker-compose.yml;docker-compose.windows.yml
"@
        Set-Content -Path ".env" -Value $envContent -Encoding UTF8
        
        Write-Success "Created .env file with default configuration."
        Write-Warning "Please update API keys in .env file for full functionality."
    }
    
    # Generate SSL certificates for development
    if (-not (Test-Path "ssl\fullchain.pem")) {
        Write-Info "Generating SSL certificates for development..."
        
        try {
            # Check if OpenSSL is available
            $opensslAvailable = $false
            try {
                $opensslVersion = openssl version 2>$null
                $opensslAvailable = $null -ne $opensslVersion
            }
            catch {
                $opensslAvailable = $false
            }
            
            if ($opensslAvailable) {
                openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
                    -keyout ssl/privkey.pem `
                    -out ssl/fullchain.pem `
                    -subj "/C=US/ST=Local/L=Local/O=StockGPT/CN=localhost" 2>$null
                
                Write-Success "Generated SSL certificates for localhost."
            } else {
                Write-Warning "OpenSSL not found. SSL certificates not generated."
                Write-Warning "The application will run without SSL in development mode."
            }
        }
        catch {
            Write-Warning "Could not generate SSL certificates: $($_.Exception.Message)"
        }
    }
}

function Start-StockGPT {
    Write-Header "Starting StockGPT..."
    
    # Check if already running
    $runningContainers = docker-compose ps -q 2>$null
    if ($runningContainers) {
        Write-Warning "StockGPT appears to be already running."
        $restartChoice = Read-Host "Would you like to restart it? (Y/N)"
        if ($restartChoice -eq "Y" -or $restartChoice -eq "y") {
            Stop-StockGPT
        } else {
            return
        }
    }
    
    # Pull latest images
    Write-Info "Pulling latest Docker images..."
    docker-compose pull
    
    # Start services
    Write-Info "Starting StockGPT services..."
    
    $composeFiles = @("docker-compose.yml")
    
    if ($Production) {
        $composeFiles += "docker-compose.prod.yml"
    }
    
    if ($Monitoring) {
        $composeFiles += "docker-compose.monitoring.yml"
    }
    
    if ($Development) {
        $composeFiles += "docker-compose.dev.yml"
    }
    
    # Build and start
    $composeCmd = "docker-compose"
    foreach ($file in $composeFiles) {
        $composeCmd += " -f $file"
    }
    
    $composeCmd += " up -d --build"
    
    Write-Info "Executing: $composeCmd"
    Invoke-Expression $composeCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "StockGPT started successfully!"
        Show-Status
    } else {
        Write-Error "Failed to start StockGPT. Check the logs for details."
    }
}

function Stop-StockGPT {
    Write-Header "Stopping StockGPT..."
    
    docker-compose down
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "StockGPT stopped successfully!"
    } else {
        Write-Error "Failed to stop StockGPT."
    }
}

function Restart-StockGPT {
    Write-Header "Restarting StockGPT..."
    
    Stop-StockGPT
    Start-Sleep -Seconds 5
    Start-StockGPT
}

function Show-Status {
    Write-Header "StockGPT Status"
    
    Write-Info "Checking service status..."
    docker-compose ps
    
    Write-Info ""
    Write-Info "Access URLs:"
    Write-Info "  Frontend: http://localhost"
    Write-Info "  API: http://localhost/api"
    Write-Info "  API Docs: http://localhost/api/docs"
    
    if ($Monitoring) {
        Write-Info "  Grafana: http://localhost:3001 (admin/admin123)"
        Write-Info "  Prometheus: http://localhost:9090"
        Write-Info "  AlertManager: http://localhost:9093"
    }
}

function Show-Logs {
    param([string]$Service = "")
    
    Write-Header "StockGPT Logs"
    
    if ($Service) {
        Write-Info "Showing logs for service: $Service"
        docker-compose logs -f $Service
    } else {
        Write-Info "Showing logs for all services..."
        docker-compose logs -f
    }
}

function Backup-StockGPT {
    Write-Header "Backing up StockGPT..."
    
    $backupDir = "backups\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    Write-Info "Creating backup in: $backupDir"
    
    # Backup database
    try {
        Write-Info "Backing up database..."
        docker-compose exec postgres pg_dump -U stockgpt_user stockgpt > "$backupDir\database.sql"
        Write-Success "Database backup completed."
    }
    catch {
        Write-Warning "Database backup failed: $($_.Exception.Message)"
    }
    
    # Backup Redis data
    try {
        Write-Info "Backing up Redis data..."
        docker-compose exec redis redis-cli BGSAVE
        Start-Sleep -Seconds 5
        Copy-Item "redis_data\dump.rdb" "$backupDir\redis.rdb" -ErrorAction SilentlyContinue
        Write-Success "Redis backup completed."
    }
    catch {
        Write-Warning "Redis backup failed: $($_.Exception.Message)"
    }
    
    # Create backup info file
$backupInfo = @"
StockGPT Backup
Created: $(Get-Date)
Services: $(docker-compose ps --services)
"@
    Set-Content -Path "$backupDir\backup_info.txt" -Value $backupInfo -Encoding UTF8
    
    Write-Success "Backup completed in: $backupDir"
}

function Update-StockGPT {
    Write-Header "Updating StockGPT..."
    
    Write-Info "Pulling latest images..."
    docker-compose pull
    
    Write-Info "Rebuilding and restarting services..."
    docker-compose up -d --build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "StockGPT updated successfully!"
    } else {
        Write-Error "Failed to update StockGPT."
    }
}

function Show-Help {
    Write-Header "StockGPT Windows Deployment Help"

    Write-Host "Usage: .\windows-deploy.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Production     Deploy in production mode with SSL and optimizations"
    Write-Host "  -Development    Deploy in development mode (default)"
    Write-Host "  -Monitoring     Include monitoring stack (Prometheus, Grafana)"
    Write-Host "  -Stop           Stop all StockGPT services"
    Write-Host "  -Restart        Restart all StockGPT services"
    Write-Host "  -Status         Show service status and access URLs"
    Write-Host "  -Logs           Show logs (optionally for specific service)"
    Write-Host "  -Backup         Create backup of database and Redis data"
    Write-Host "  -Update         Update StockGPT to latest version"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\windows-deploy.ps1                          # Development deployment"
    Write-Host "  .\windows-deploy.ps1 -Production              # Production deployment"
    Write-Host "  .\windows-deploy.ps1 -Production -Monitoring  # Production with monitoring"
    Write-Host "  .\windows-deploy.ps1 -Status                  # Check status"
    Write-Host "  .\windows-deploy.ps1 -Backup                 # Create backup"
    Write-Host "  .\windows-deploy.ps1 -Stop                   # Stop services"
}

# Main execution
if ($args.Count -eq 0 -and $PSBoundParameters.Count -eq 0) {
    # No parameters provided, show interactive menu
    Write-Header "StockGPT Windows Deployment"
    Write-Info "Welcome to StockGPT One-Click Deployment for Windows!"
    Write-Info ""
    
    # Check prerequisites
    $prereqsMet = Test-Prerequisites
    if (-not $prereqsMet) {
        Write-Error "Prerequisites not met. Please install required software and try again."
        exit 1
    }
    
    # Initialize environment
    Initialize-Environment
    
    # Show deployment options
    Write-Info "Deployment Options:"
    Write-Info "  1. Development (Quick start)"
    Write-Info "  2. Production (Full deployment with SSL)"
    Write-Info "  3. Production with Monitoring"
    Write-Info "  4. Custom deployment"
    Write-Info ""
    
    $choice = Read-Host "Select deployment option (1-4)"
    
    switch ($choice) {
        "1" { 
            Write-Info "Starting development deployment..."
            Start-StockGPT 
        }
        "2" { 
            Write-Info "Starting production deployment..."
            $Production = $true
            Start-StockGPT 
        }
        "3" { 
            Write-Info "Starting production deployment with monitoring..."
            $Production = $true
            $Monitoring = $true
            Start-StockGPT 
        }
        "4" {
            Write-Info "Custom deployment options:"
            $prod = Read-Host "Production mode? (Y/N)"
            $mon = Read-Host "Include monitoring? (Y/N)"
            
            if ($prod -eq "Y" -or $prod -eq "y") { $Production = $true }
            if ($mon -eq "Y" -or $mon -eq "y") { $Monitoring = $true }
            
            Start-StockGPT
        }
        default {
            Write-Info "Starting default development deployment..."
            Start-StockGPT
        }
    }
}
else {
    # Parameters provided, execute accordingly
    if ($Stop) {
        Stop-StockGPT
    }
    elseif ($Restart) {
        Restart-StockGPT
    }
    elseif ($Status) {
        Show-Status
    }
    elseif ($Logs) {
        Show-Logs -Service $Service
    }
    elseif ($Backup) {
        Backup-StockGPT
    }
    elseif ($Update) {
        Update-StockGPT
    }
    else {
        # Check prerequisites
        $prereqsMet = Test-Prerequisites
        if (-not $prereqsMet) {
            Write-Error "Prerequisites not met. Please install required software and try again."
            exit 1
        }
        
        # Initialize environment
        Initialize-Environment
        
        # Start with specified options
        Start-StockGPT
    }
}