from __future__ import annotations
import argparse
import asyncio
import datetime
import logging
import os
import random
import sys
from dataclasses import dataclass
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from pathlib import Path
import re
import smtplib
import subprocess
from typing import Optional, List

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

@dataclass
class Config:
    email: str
    password: str
    years: List[int]
    output_dir: Path = Path("orders")
    headless: bool = True
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    notify_email: Optional[str] = None



class Emailer(object):
    def __init__(self, smtp_host, smtp_port, smtp_user, smtp_password):
        self.smtp_host = smtp_host
        self.smtp_port = int(smtp_port)
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def send_mail(self, send_from, send_to, subject, text, files=None):
        assert isinstance(send_to, list)
        msg = MIMEMultipart()
        msg["From"] = send_from
        msg["To"] = COMMASPACE.join(send_to)
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject
        msg.attach(MIMEText(text))

        for f in files or []:
            with open(f, "rb") as fil:
                print("attaching", os.path.basename(f))
                msg.attach(
                    MIMEApplication(
                        fil.read(),
                        "pdf",
                        name=os.path.basename(f),
                        Content_Disposition='attachment; filename="%s"'
                        % os.path.basename(f),
                    )
                )

        smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
        smtp.starttls()
        if self.smtp_user:
            smtp.login(self.smtp_user, self.smtp_password)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.close()


class AmazonScraper:
    BASE_URL = "https://www.amazon.com"
    LOGIN_URL = f"{BASE_URL}/ap/signin"
    ORDER_HISTORY_URL = f"{BASE_URL}/gp/css/order-history"
    ORDER_DETAILS_TEMPLATE = f"{BASE_URL}/gp/css/summary/print.html/ref=od_aui_print_invoice?ie=UTF8&orderID={{order_id}}"

    def __init__(self, config: Config):
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.config.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.context.close()
        await self.browser.close()

    async def get_orders_for_year(self, year: int) -> List[str]:
        logger.info(f"Fetching orders for year {year}")
        order_ids = []
        
        await self.page.goto(f"{self.ORDER_HISTORY_URL}?year={year}")
        
        while True:
            html = self._fetch_url(url)
            soup = BeautifulSoup(html, "lxml")
            order_links = soup.find_all("a", href=self.order_id_re)
            order_nums |= set(
                [self.order_id_re.search(link["href"]).group(1) for link in order_links]
            )
            page_links = soup.find_all("a", text=str(page_num))
            if not page_links:
                print("found no links for page_num=%s; assuming completion" % page_num)
                break
            url = self.base_url + page_links[0]["href"]
        print("found %s orders in %s" % (len(order_nums), self.year))
        return order_nums

    def run(self):
        order_nums = self.get_order_nums()
        for oid in order_nums:
            orders = os.listdir(self.orders_dir)
            if any(["{oid}.pdf".format(oid=oid) in o for o in orders]):
                print("skipping order %s (already exists)" % oid)
                continue
            url = self.order_url.format(oid=oid)
            html = self._fetch_url(url)
            if "Final Details for Order #" not in html:
                print("skipping order %s (not final)" % oid)
                continue
            soup = BeautifulSoup(html, "lxml")
            order_txt = soup.find_all(text=self.order_date_re)[0]
            date = order_txt.parent.next_sibling.strip()
            date = datetime.datetime.strptime(date, "%B %d, %Y").strftime("%Y-%m-%d")
            fn = "amazon_order_{date}_{oid}.".format(date=date, oid=oid) + "{ext}"
            fn = os.path.join(self.orders_dir, fn)
            with open(fn.format(ext="html"), "w") as f:
                f.write(html)
            subprocess.check_call(
                [
                    "wkhtmltopdf",
                    "--no-images",
                    "--disable-javascript",
                    fn.format(ext="html"),
                    fn.format(ext="pdf"),
                ]
            )
            os.remove(fn.format(ext="html"))
            if self.from_email and self.to_email and self.emailer:
                # email the PDF
                subject = os.path.basename(fn.format(ext="pdf"))
                body = ""
                self.emailer.send_mail(
                    self.from_email,
                    [self.to_email],
                    subject,
                    body,
                    [os.path.abspath(fn.format(ext="pdf"))],
                )
            else:
                print("skipping email send for order %s" % oid)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape an Amazon account and create order PDFs."
    )
    parser.add_argument(
        "-u",
        "--user",
        help="Amazon.com username (email).",
        default=os.environ["AMAZON_USER"],
    )
    parser.add_argument(
        "-p",
        "--password",
        help="Amazon.com password.",
        default=os.environ["AMAZON_PASSWORD"],
    )
    parser.add_argument(
        "--smtp-user",
        required=False,
        help="SMTP username (optional).",
        default=os.environ.get("SMTP_USER"),
    )
    parser.add_argument(
        "--smtp-password",
        required=False,
        help="SMTP password (optional)",
        default=os.environ.get("SMTP_PASSWORD"),
    )
    parser.add_argument(
        "--smtp-host",
        required=False,
        help="SMTP host (optional)",
        default=os.environ.get("SMTP_HOST"),
    )
    parser.add_argument(
        "--smtp-port",
        required=False,
        help="SMTP port (optional)",
        default=os.environ.get("SMTP_PORT"),
    )
    parser.add_argument(
        "--from-email",
        required=False,
        help="From email (for sending emails).",
        default=os.environ.get("FROM_EMAIL"),
    )
    parser.add_argument(
        "--to-email",
        required=False,
        help="To email (for sending emails).",
        default=os.environ.get("TO_EMAIL"),
    )
    parser.add_argument(
        "--dest-dir",
        required=False,
        default="orders/",
        help='Destination directory for scraped order PDFs. Defaults to "orders/"',
    )
    parser.add_argument(
        "year",
        nargs="*",
        type=int,
        default=datetime.datetime.today().year,
        help="One or more years for which to retrieve orders. Will default to the "
        "current year if no year is specified.",
    )
    return parser.parse_args()


async def main(config: Config):
    async with AmazonScraper(config) as scraper:
        try:
            await scraper.login()
            for year in config.years:
                order_ids = await scraper.get_orders_for_year(year)
                for order_id in order_ids:
                    await scraper.save_order_invoice(order_id)
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            sys.exit(1)

def main():
    args = parse_args()
    config = Config(
        email=args.user,
        password=args.password,
        years=args.year,
        output_dir=Path(args.dest_dir),
        headless=True
    )
    asyncio.run(main(config))


if __name__ == "__main__":
    main()
