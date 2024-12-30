import logging
import ssl
import socket
from urllib.parse import urlparse
from proto.analyzer_pb2 import SecurityData, Recommendation

logger = logging.getLogger(__name__)


class SecurityAnalyzer:
    """
    Class for performing security analysis of a website.

    Attributes:
        url (str): URL of the website to analyze.
        security_data (SecurityData): Object to store security-related data.
        recommendations (list[Recommendation]): List of security recommendations.
    """

    def __init__(self, url: str):
        """
        Initialize the SecurityAnalyzer with the target URL.

        Args:
            url (str): The URL to analyze.
        """
        self.url = url
        self.security_data = SecurityData()
        self.recommendations = []

    async def analyze(self) -> tuple[SecurityData, list[Recommendation]]:
        """
        Perform a comprehensive security analysis of the given URL.

        Returns:
            tuple: A tuple containing SecurityData and a list of Recommendations.

        Raises:
            ValueError: If the URL is invalid.

        References:
            - https://docs.python.org/3/library/ssl.html
            - https://docs.python.org/3/library/socket.html
            - https://tools.ietf.org/html/rfc6797 (HSTS specification)
        """
        parsed_url = urlparse(self.url)
        if not parsed_url.netloc:
            logger.error("Invalid URL: %s", self.url)
            raise ValueError("Invalid URL provided.")

        await self.check_https(parsed_url)
        await self.check_ssl_certificate(parsed_url.netloc)
        await self.check_hsts(parsed_url.netloc)

        logger.info("Security analysis of the page completed.")
        return self.security_data, self.recommendations

    async def check_https(self, parsed_url):
        """
        Check if the website uses HTTPS.

        Args:
            parsed_url (ParseResult): Parsed URL object.

        Updates:
            - security_data.uses_https
            - recommendations (if HTTPS is not used)
        """
        if parsed_url.scheme == "https":
            self.security_data.uses_https = True
        else:
            self.security_data.uses_https = False
            self.recommendations.append(
                Recommendation(
                    message="The site does not use HTTPS. It is recommended to use a secure connection.",
                    category="SECURITY",
                )
            )

    async def check_ssl_certificate(self, hostname):
        """
        Validate the SSL certificate of the website.

        Args:
            hostname (str): Hostname extracted from the URL.

        Updates:
            - security_data.valid_ssl_certificate
            - recommendations (if SSL certificate is invalid)

        References:
            - https://docs.python.org/3/library/ssl.html#ssl.SSLSocket.getpeercert
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    if not cert:
                        raise ssl.CertificateError("No certificate found.")
                    self.security_data.valid_ssl_certificate = True
                    logger.info("SSL certificate is valid for %s", hostname)
        except ssl.CertificateError as cert_err:
            self.security_data.valid_ssl_certificate = False
            self.recommendations.append(
                Recommendation(
                    message=f"SSL certificate error: {cert_err}.",
                    category="SECURITY",
                )
            )
            logger.warning("SSL certificate error: %s", cert_err)
        except Exception as e:
            self.security_data.valid_ssl_certificate = False
            self.recommendations.append(
                Recommendation(
                    message="SSL certificate check failed or the certificate is invalid.",
                    category="SECURITY",
                )
            )
            logger.error("SSL certificate check failed: %s", e)

    async def check_hsts(self, hostname):
        """
        Check if the website has HTTP Strict Transport Security (HSTS) enabled.

        Args:
            hostname (str): Hostname extracted from the URL.

        Updates:
            - security_data.hsts_enabled
            - recommendations (if HSTS is not enabled)

        References:
            - https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security
        """
        try:
            import http.client

            conn = http.client.HTTPSConnection(hostname, timeout=5)
            conn.request("HEAD", "/")
            response = conn.getresponse()
            headers = dict(response.getheaders())
            if "Strict-Transport-Security" in headers:
                self.security_data.hsts_enabled = True
                logger.info("HSTS is enabled for %s", hostname)
            else:
                self.security_data.hsts_enabled = False
                self.recommendations.append(
                    Recommendation(
                        message="The site does not enable HSTS. It is recommended to use HTTP Strict Transport Security.",
                        category="SECURITY",
                    )
                )
        except Exception as e:
            self.recommendations.append(
                Recommendation(
                    message="Failed to check HSTS due to an error.",
                    category="SECURITY",
                )
            )
            logger.error("Failed to check HSTS for %s: %s", hostname, e)
