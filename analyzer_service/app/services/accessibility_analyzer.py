import logging
import requests
from bs4 import BeautifulSoup
from proto.analyzer_pb2 import AccessibilityData, Recommendation

logger = logging.getLogger(__name__)


async def analyze_accessibility(url: str):
    """
    Возвращает (AccessibilityData, [Recommendation])
    """
    a11y_data = AccessibilityData()
    recommendations = []

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            recommendations.append(
                Recommendation(
                    message=f"Страница вернула статус {resp.status_code}, A11Y-анализ может быть неточным.",
                    category="A11Y",
                )
            )
            return a11y_data, recommendations

        soup = BeautifulSoup(resp.text, "html.parser")

        # Пример: проверка alt-тегов
        images = soup.find_all("img")
        images_without_alt = [img for img in images if not img.get("alt")]
        if images_without_alt:
            a11y_data.has_alt_for_images = False
            recommendations.append(
                Recommendation(
                    message=f"Найдено {len(images_without_alt)} изображений без alt-тегов.",
                    category="A11Y",
                )
            )
        else:
            a11y_data.has_alt_for_images = True

        # Пример: проверка семантических заголовков
        if not soup.find_all(["h1", "h2", "h3"]):
            a11y_data.has_proper_headings = False
            recommendations.append(
                Recommendation(
                    message="На странице отсутствуют семантические заголовки (h1/h2/h3).",
                    category="A11Y",
                )
            )
        else:
            a11y_data.has_proper_headings = True

    except Exception as e:
        logger.error(f"Ошибка A11Y анализа: {e}")
        recommendations.append(
            Recommendation(
                message="Произошла ошибка во время A11Y-анализа.", category="A11Y"
            )
        )

    return a11y_data, recommendations
