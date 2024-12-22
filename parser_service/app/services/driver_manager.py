from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
import logging

logger = logging.getLogger(__name__)


class DriverManager:
    _instance = None
    _lock = asyncio.Lock()

    def __init__(self):
        if DriverManager._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=options
            )
            DriverManager._instance = self

    @classmethod
    async def get_instance(cls):
        async with cls._lock:
            if cls._instance is None:
                cls()
            return cls._instance.driver

    @classmethod
    async def close_driver(cls):
        async with cls._lock:
            if cls._instance:
                cls._instance.driver.quit()
                cls._instance = None
