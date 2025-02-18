Amazon Order Scraper
====================

Modern Python utility using Playwright to scrape Amazon orders and generate PDF receipts
for tax/record keeping purposes.

To use::

    python -m venv .venv
    source .venv/bin/activate
    pip install .
    playwright install
    python -m amzscraper -u <email> -p <password> 2021 2022 2023

Orders will be saved to the ``orders/`` directory by default. PDF generation is handled
natively by Playwright without external dependencies.

For further options, see::

    python -m amzscraper -h

Requirements
------------

* Python 3.7+
- Playwright (will install supported browser automatically)
- smtp credentials if emailing receipts

Email Configuration
-------------------
To email PDF receipts, provide SMTP credentials either via command-line options or
environment variables:

    --smtp-host SMTP_HOST   SMTP hostname (env: SMTP_HOST)
    --smtp-port SMTP_PORT   SMTP port (env: SMTP_PORT)
    --smtp-user SMTP_USER   SMTP username (env: SMTP_USER)
    --smtp-password SMTP_PASSWORD SMTP password (env: SMTP_PASSWORD)

Security Note
-------------
Credentials are never stored and only used for the current session. Consider using
environment variables for sensitive credentials.
