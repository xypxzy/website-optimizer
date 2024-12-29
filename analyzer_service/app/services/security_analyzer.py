import logging
import ssl
import socket
from proto.analyzer_pb2 import SecurityData, Recommendation

logger = logging.getLogger(__name__)


async def analyze_security(url: str):
    """
    Возвращает (SecurityData, [Recommendation])
    """

    security_data = SecurityData()
    recommendations = []

    # Упрощённый пример: проверка HTTPS (url.startswith("https"))
    if url.lower().startswith("https"):
        security_data.uses_https = True
    else:
        security_data.uses_https = False
        recommendations.append(
            Recommendation(
                message="Сайт не использует HTTPS. Рекомендуется использовать защищённое соединение.",
                category="SECURITY",
            )
        )

    # Проверка SSL-сертификата
    # (это может быть сложнее, нужно получить домен, подключиться через socket, ssl).
    try:
        # Примерно:
        hostname = url.split("//")[-1].split("/")[0]  # грубый парс домена
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Если удачно, значит сертификат валидный
                security_data.valid_ssl_certificate = True
                # Также можно посмотреть сертификат: ssock.getpeercert()
    except Exception as e:
        security_data.valid_ssl_certificate = False
        recommendations.append(
            Recommendation(
                message="Проверка SSL сертификата не прошла или сертификат невалиден.",
                category="SECURITY",
            )
        )

    # Проверка заголовков безопасности — чаще всего делается через GET запрос и анализ headers.
    # ...
    return security_data, recommendations
