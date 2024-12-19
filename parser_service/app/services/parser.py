import logging
import requests
import psycopg2
import pika
import os
from bs4 import BeautifulSoup
import grpc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from proto import parser_pb2, parser_pb2_grpc

logger = logging.getLogger(__name__)


class ParserServicer(parser_pb2_grpc.ParserServiceServicer):
    """
    gRPC service for analyzing website content. Supports both static and dynamic sites.
    """

    DYNAMIC_SITE_MARKERS = ["<script", "window.__INITIAL_STATE__", "data-reactroot"]
    HTML_CONTENT_TYPE = "text/html"

    def __init__(self):
        # connect to the database
        self.db_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        self.db_cursor = self.db_conn.cursor()

        # connect to the message broker (RabbitMQ)
        self.rabbitmq_conn = pika.BlockingConnection(
            pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST"))
        )
        self.rabbitmq_channel = self.rabbitmq_conn.channel()
        self.rabbitmq_channel.queue_declare(queue="analyze_queue")

    def Parse(self, request, context):
        url = request.url
        logger.info(f"Starting parsing site: {url}")
        try:
            if self.is_dynamic_site(url):
                soup = self.parse_dynamic_site(url)
            else:
                soup = self.parse_static_site(url)

            # save to the database
            self.save_to_db(url, str(soup))

            # send to the message broker
            self.rabbitmq_channel.basic_publish(
                exchange="", routing_key="analyze_queue", body=str(soup)
            )

            return parser_pb2.ParseResponse(content=str(soup))
        except Exception as e:
            logger.error(f"Error parsing the site {url}: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return parser_pb2.ParseResponse()

    def is_dynamic_site(self, url: str) -> bool:
        """Determines if the site is dynamic."""
        try:
            logger.info(f"Checking if site is dynamic: {url}")

            response = requests.get(url, timeout=10, stream=True)
            content_type = response.headers.get("Content-Type", "")

            if self.HTML_CONTENT_TYPE in content_type:
                chunk = response.raw.read(2048).decode(
                    "utf-8", errors="ignore"
                )  # Read the first 2048 bytes
                if any(marker in chunk for marker in self.DYNAMIC_SITE_MARKERS):
                    logger.info(f"The site is dynamic: {url}")
                    return True
            logger.info(f"The site is static: {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking the site {url}: {e}")

        return False

    def parse_static_site(self, url: str) -> BeautifulSoup:
        """Parses static sites."""
        logger.info(f"Parsing static site: {url}")
        try:
            html_content = self.extract_html(url)
            soup = self.parse_html(html_content)
            logger.info(f"Static site successfully parsed: {url}")
            return soup
        except Exception as e:
            logger.error(f"Error parsing static site {url}: {e}")
            return None

    def parse_dynamic_site(self, url: str) -> BeautifulSoup:
        """Parses dynamic sites."""
        logger.info(f"Parsing dynamic site: {url}")
        try:
            options = self.get_selenium_options()
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=options
            )
            driver.get(url)
            html_content = driver.page_source
            driver.quit()
            soup = self.parse_html(html_content)
            logger.info(f"Dynamic site successfully parsed: {url}")
            return soup
        except Exception as e:
            logger.error(f"Error parsing dynamic site {url}: {e}")
            return None

    def extract_html(self, url: str) -> str:
        """Extracts the HTML content of a page."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error extracting HTML content from {url}: {e}")
            raise

    @staticmethod
    def parse_html(html: str) -> BeautifulSoup:
        """Parses HTML content."""
        return BeautifulSoup(html, "html.parser")

    @staticmethod
    def get_selenium_options() -> Options:
        """Configures Selenium options."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return options

    def save_to_db(self, url: str, html_content: str):
        """Saves the parsed content to the database."""
        try:
            query = "INSERT INTO parsed_pages (url, html_content, status) VALUES (%s, %s, %s)"
            self.db_cursor.execute(query, (url, html_content, "success"))
            self.db_conn.commit()
        except psycopg2.Error as e:
            logger.error(f"Error saving to the database: {e}")
            raise
