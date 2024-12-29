import logging
from bs4 import BeautifulSoup
import requests

from proto.analyzer_pb2 import SEOData, Recommendation

logger = logging.getLogger(__name__)


async def analyze_seo(url: str) -> tuple[SEOData, list[Recommendation]]:
    """
    Анализ SEO-аспектов страницы и формирование рекомендаций.
    Возвращает SEOData и список Recommendation.
    """
    seo_data = SEOData()
    recommendations = []

    try:
        response = requests.get(url, timeout=10)
        # Если статус не 200 — уже можно выдать рекомендацию
        if response.status_code != 200:
            recommendations.append(
                Recommendation(
                    message=f"Страница вернула статус {response.status_code}, невозможен полный SEO-анализ.",
                    category="SEO",
                )
            )
            return seo_data, recommendations

        soup = BeautifulSoup(response.text, "html.parser")

        # Проверка title
        title_tag = soup.find("title")
        if title_tag:
            seo_data.has_title_tag = True
            seo_data.title_length = len(title_tag.text)
            if seo_data.title_length > 65:
                recommendations.append(
                    Recommendation(
                        message="Title слишком длинный. Рекомендуется до 65 символов.",
                        category="SEO",
                    )
                )
        else:
            seo_data.has_title_tag = False
            recommendations.append(
                Recommendation(
                    message="На странице отсутствует <title> тег.", category="SEO"
                )
            )

        # Проверка description
        description_tag = soup.find("meta", attrs={"name": "description"})
        if description_tag and description_tag.get("content"):
            seo_data.has_description_tag = True
            seo_data.description_length = len(description_tag["content"])
            if seo_data.description_length < 50:
                recommendations.append(
                    Recommendation(
                        message="Description слишком короткий. Рекомендуется от 50 символов и выше.",
                        category="SEO",
                    )
                )
        else:
            seo_data.has_description_tag = False
            recommendations.append(
                Recommendation(message="Отсутствует meta description.", category="SEO")
            )

        # Дополнительные проверки ...
        # Например, h1, robots.txt, sitemap.xml, canonical, keywords, т.д.

        logger.info("SEO-анализ страницы завершён.")
        return seo_data, recommendations

    except Exception as e:
        logger.error(f"Ошибка при SEO-анализе: {e}")
        recommendations.append(
            Recommendation(
                message="Ошибка при SEO-анализе страницы. Подробности в логах.",
                category="SEO",
            )
        )
        return seo_data, recommendations
