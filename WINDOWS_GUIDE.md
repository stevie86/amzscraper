# Windows Installation and Usage Guide

This guide explains how to run the Amazon Order Scraper on Windows 10/11 systems.

## Prerequisites
- Windows 10 or later (64-bit)
- [Python 3.7+](https://www.python.org/downloads/windows/)
- [Git for Windows](https://git-scm.com/download/win)

## Installation

1. **Install Playwright Requirements**  
   Open PowerShell as Administrator:
   ```powershell
   python -m pip install playwright
   playwright install chromium
   # Allow browser installations if Windows Defender blocks them
   ```

2. **Clone Repository**  
   In PowerShell:
   ```powershell
   git clone https://github.com/yourusername/amzscraper.git
   cd amzscraper
   ```

3. **Create Virtual Environment**  
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # For PowerShell
   # OR for Command Prompt:
   .\.venv\Scripts\activate.bat
   ```

4. **Install Dependencies**  
   ```powershell
   pip install -e .
   ```

## Running the Scraper

### Basic Usage (Command Prompt)
```cmd
python -m amzscraper -u "your@email.com" -p "your_password" 2022 2023 ^
    --dest-dir "C:\path\to\orders" 
```

### With Visual Browser (Recommended First Run)
```powershell
python -m amzscraper -u $env:AMAZON_USER -p $env:AMAZON_PASSWORD 2023 --headless=false
```

### Using Environment Variables (Permanent)
1. Open Start Menu → "Edit Environment Variables"
2. Add these user variables:
   ```
   AMAZON_USER = your@email.com
   AMAZON_PASSWORD = your_password
   ```
3. Then run:  
   ```cmd
   python -m amzscraper 2023
   ```

## SMTP Email Configuration (Optional)
For sending email notifications, use PowerShell:
```powershell
$env:SMTP_HOST="smtp.example.com"
$env:SMTP_PORT=587
$env:SMTP_USER="smtp_user"
$env:SMTP_PASSWORD="smtp_pass"
python -m amzscraper -u "your@email.com" -p "amazon_pass" 2023 --to-email "recipient@example.com"
```

## Windows-Specific Notes
1. **Path Handling**  
   Use quotes for paths with spaces:  
   `--dest-dir "C:\Users\My Name\Documents\Amazon Orders"`

2. **Proxy Settings**  
   If behind a corporate proxy:  
   ```powershell
   $env:HTTPS_PROXY="http://proxy-server:port"
   ```

3. **Troubleshooting**  
   Common fixes:
   - **Playwright Installation Issues**:  
     ```powershell
     playwright install --force chromium
     ```
   - **Virtual Environment Activation Errors**:  
     Set execution policy temporarily:  
     ```powershell
     Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
     ```
   - **Browser Launch Failures**:  
     Disable antivirus/web protection temporarily

## Security Best Practices
1. First-time login with headless mode disabled:  
   ```cmd
   python -m amzscraper --headless=false
   ```
2. Use Windows Credential Manager for secure password storage  
3. Add orders folder to antivirus exclusions if files get quarantined
