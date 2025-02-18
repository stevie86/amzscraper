#Requires -RunAsAdministrator
<#
.SYNOPSIS
Amazon Scraper Setup Script for Windows

.DESCRIPTION
Automates environment setup using uv package manager and Playwright
#>

$ErrorActionPreference = "Stop"

function Test-CommandExists {
    param($command)
    return (Get-Command $command -ErrorAction SilentlyContinue)
}

try {
    # Check prerequisites
    if (-not (Test-CommandExists "python")) {
        throw "Python not found. Install from https://www.python.org/downloads/windows/"
    }

    if (-not (Test-CommandExists "winget")) {
        throw "Winget not available. Requires Windows 10 1709+ or Windows 11"
    }

    # Install UV if missing
    if (-not (Test-CommandExists "uv")) {
        Write-Host "Installing uv package manager..." -ForegroundColor Cyan
        python -m pip install uv
    }

    # Create and activate virtual environment
    Write-Host "`nCreating virtual environment..." -ForegroundColor Green
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

    # Install dependencies
    Write-Host "`nInstalling project dependencies..." -ForegroundColor Cyan
    uv pip install --only-binary=lxml -e .
    
    # Install Playwright browsers
    Write-Host "`nSetting up Playwright..." -ForegroundColor Green
    playwright install chromium
    playwright install-deps chromium

    # Configuration wizard
    Write-Host "`n=== Configuration ===" -ForegroundColor Yellow
    
    # Get Amazon credentials
    $email = Read-Host "Enter your Amazon login email"
    $password = Read-Host "Enter your Amazon password" -AsSecureString
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
    )

    # Store credentials as environment variables
    [Environment]::SetEnvironmentVariable("AMAZON_USER", $email, "User")
    [Environment]::SetEnvironmentVariable("AMAZON_PASSWORD", $plainPassword, "User")

    # Email configuration
    $configureEmail = Read-Host "Configure email notifications? (y/n)"
    if ($configureEmail -eq "y") {
        $smtpHost = Read-Host "SMTP Server Host"
        $smtpPort = Read-Host "SMTP Port [587]"
        $smtpUser = Read-Host "SMTP Username"
        $smtpPass = Read-Host "SMTP Password" -AsSecureString
        
        [Environment]::SetEnvironmentVariable("SMTP_HOST", $smtpHost, "User")
        [Environment]::SetEnvironmentVariable("SMTP_PORT", $smtpPort, "User")
        [Environment]::SetEnvironmentVariable("SMTP_USER", $smtpUser, "User")
        $plainSmtpPass = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($smtpPass)
        )
        [Environment]::SetEnvironmentVariable("SMTP_PASSWORD", $plainSmtpPass, "User")
    }

    # Final setup
    Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
    Write-Host "Virtual environment: .venv"
    Write-Host "Stored credentials in user environment variables"
    
    $runNow = Read-Host "Run scraper now? (y/n)"
    if ($runNow -eq "y") {
        $years = Read-Host "Enter years to scrape (space-separated, e.g., 2022 2023)"
        Write-Host "`nFirst run recommendations:" -ForegroundColor Yellow
        Write-Host "1. Keep browser visible for potential CAPTCHA/2FA"
        Write-Host "2. Antivirus may temporarily block Playwright - allow if prompted`n"
        
        python -m amzscraper --years $years --headless=false
    }
    else {
        Write-Host "`nTo run manually later:"
        Write-Host "1. Activate environment: .\.venv\Scripts\Activate.ps1"
        Write-Host "2. Run: python -m amzscraper --years 2022 2023"
    }
}
catch {
    Write-Host "`nError occurred:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
