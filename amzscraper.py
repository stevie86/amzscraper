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
        self.year = year
        self.orders_dir = dest_dir
        self.from_email = from_email
        self.to_email = to_email
        self.emailer = emailer
        self.br = brcls()
        self.br.login(user, password)

    def _fetch_url(self, url):
        key = hashlib.md5(url.encode("utf-8")).hexdigest()
        print("fetching %s from server (with random sleep)" % url)
        val = self.br.get_url(url)
        rand_sleep()
        return val

    def get_order_nums(self):
        order_nums = set()
        url = self.start_url.format(yr=self.year)
        for page_num in itertools.count(start=2, step=1):
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


def main():
    args = vars(parse_args())
    smtp_args = {k: args.pop(k) for k in list(args.keys()) if k.startswith("smtp_")}
    if len(smtp_args) == 4:
        emailer = Emailer(**smtp_args)
    elif len(smtp_args) == 0:
        emailer = None
    else:
        raise Exception("Did not get 0 or 4 SMTP arguments.")
    years = args.pop("year")
    for year in years:
        AmzScraper(year=year, emailer=emailer, **args).run()


if __name__ == "__main__":
    main()
