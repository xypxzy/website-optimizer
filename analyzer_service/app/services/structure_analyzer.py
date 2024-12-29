import logging
import requests
from bs4 import BeautifulSoup
from proto.analyzer_pb2 import StructureData, Recommendation

logger = logging.getLogger(__name__)


async def analyze_structure(url: str):
    """
    Возвращает (StructureData, [Recommendation])
    """
    structure_data = StructureData()
    recommendations = []

    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            recommendations.append(
                Recommendation(
                    message=f"Страница вернула статус {resp.status_code}; анализ структуры может быть неточным.",
                    category="STRUCTURE",
                )
            )
            return structure_data, recommendations

        # Простая проверка на редиректы
        if len(resp.history) > 1:
            structure_data.redirect_count = len(resp.history)
            recommendations.append(
                Recommendation(
                    message=f"Обнаружено {len(resp.history)} редиректа(ов) перед конечной страницей.",
                    category="STRUCTURE",
                )
            )

        # Поиск «битых» ссылок
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.find_all("a", href=True)
        broken_links = 0
        for link in links:
            href = link["href"]
            if href.startswith("http"):
                try:
                    link_resp = requests.head(href, timeout=5)
                    if link_resp.status_code >= 400:
                        broken_links += 1
                except:
                    broken_links += 1

        structure_data.broken_links_count = broken_links
        if broken_links > 0:
            recommendations.append(
                Recommendation(
                    message=f"На странице обнаружено {broken_links} битых ссылок.",
                    category="STRUCTURE",
                )
            )

        # Проверка sitemap.xml и robots.txt (упрощённо)
        base_domain = url.split("//")[-1].split("/")[0]
        sitemap_url = f"https://{base_domain}/sitemap.xml"
        robots_url = f"https://{base_domain}/robots.txt"

        try:
            site_resp = requests.head(sitemap_url, timeout=5)
            if site_resp.status_code == 200:
                structure_data.has_sitemap = True
            else:
                structure_data.has_sitemap = False
                recommendations.append(
                    Recommendation(
                        message="На сайте не найден sitemap.xml (или статус не 200).",
                        category="STRUCTURE",
                    )
                )
        except:
            structure_data.has_sitemap = False

        try:
            robot_resp = requests.head(robots_url, timeout=5)
            if robot_resp.status_code == 200:
                structure_data.has_robots_txt = True
            else:
                structure_data.has_robots_txt = False
                recommendations.append(
                    Recommendation(
                        message="На сайте не найден robots.txt (или статус не 200).",
                        category="STRUCTURE",
                    )
                )
        except:
            structure_data.has_robots_txt = False

    except Exception as e:
        logger.error(f"Ошибка анализа структуры: {e}")
        recommendations.append(
            Recommendation(
                message="Произошла ошибка во время анализа структуры.",
                category="STRUCTURE",
            )
        )

    return structure_data, recommendations
