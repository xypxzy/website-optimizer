import logging
import ssl
import socket
from proto.analyzer_pb2 import SecurityData, Recommendation

logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.security_data = SecurityData()
        self.recommendations = []

    async def analyze(self) -> tuple[SecurityData, list[Recommendation]]:
        """
        Returns (SecurityData, [Recommendation])
        """
        self.check_https()
        self.check_ssl_certificate()

        logger.info("Security analysis of the page completed.")

        return self.security_data, self.recommendations

    def check_https(self):
        if self.url.lower().startswith("https"):
            self.security_data.uses_https = True
        else:
            self.security_data.uses_https = False
            self.recommendations.append(
                Recommendation(
                    message="The site does not use HTTPS. It is recommended to use a secure connection.",
                    category="SECURITY",
                )
            )

    def check_ssl_certificate(self):
        try:
            hostname = self.url.split("//")[-1].split("/")[0]  # rough domain parsing
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    self.security_data.valid_ssl_certificate = True
        except Exception as e:
            self.security_data.valid_ssl_certificate = False
            self.recommendations.append(
                Recommendation(
                    message="SSL certificate check failed or the certificate is invalid.",
                    category="SECURITY",
                )
            )
