# Amazon Order Scraper

Modern Python utility using Playwright to scrape Amazon order histories and generate PDF invoices in bulk.

## Features
- Browser automation with anti-detection measures
- Async PDF generation using Playwright
- Year-based order filtering
- Optional email notifications with SMTP integration

## Installation

1. Install prerequisites:
```bash
python -m pip install playwright
```

2. Clone repository and install:
```bash
git clone https://github.com/yourusername/amzscraper.git
cd amzscraper
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install .
playwright install chromium
```

## Usage

Basic command:
```bash
python -m amzscraper -u EMAIL -p PASSWORD [YEAR1 YEAR2...]
```

Example for multiple years:
```bash
python -m amzscraper -u user@example.com -p 'securepassword' 2021 2022 2023
```

### Advanced options:
```bash
# Command line arguments:
  -h, --help            show this help message and exit
  --dest-dir DEST_DIR   Destination directory for order PDFs (default: orders/)
  --smtp-host SMTP_HOST SMTP server hostname
  --smtp-port SMTP_PORT SMTP server port (default: 587)
  --smtp-user SMTP_USER SMTP username for authentication
  --smtp-password SMTP_PASSWORD SMTP password for authentication
  --from-email FROM_EMAIL Sender email address
  --to-email TO_EMAIL   Recipient email address
```

## File Structure
Orders are saved with the following structure:
```
dest_dir/
├── ORDER_ID_1/
│   └── ORDER_ID_1.pdf
├── ORDER_ID_2/
│   └── ORDER_ID_2.pdf
...
```

## Security Notes
1. Credentials are ONLY used during the scraping session
2. Browser automation may trigger Amazon security checks:
   - First-time runs should use a non-headless browser
   - You may need to manually complete CAPTCHAs/2FA
3. For production use:
```bash
# Read credentials from environment variables
export AMAZON_USER='user@example.com'
export AMAZON_PASSWORD='securepassword'
python -m amzscraper
```

## Requirements
- Python 3.7+ (async/await support)
- Playwright 1.30+
- Modern Chromium browser

## Troubleshooting
For manual intervention mode:
```bash
python -m amzscraper -u EMAIL -p PASSWORD --headless=false 2022
```

## Development
```bash
# Run tests
playwright test

# Generate debug logs
python -m amzscraper -u EMAIL -p PASSWORD 2023 --log-level=DEBUG
```

## Legal Note
Use of this tool must comply with Amazon's Terms of Service. Check order history access permissions for your account type.
