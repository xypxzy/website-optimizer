import logging
import time
import requests
from proto.analyzer_pb2 import PerformanceData, Recommendation

logger = logging.getLogger(__name__)


async def analyze_performance(url: str):
    """
    Возвращает (PerformanceData, [Recommendation])
    """

    perf_data = PerformanceData()
    recommendations = []

    try:
        start = time.time()
        resp = requests.get(url, timeout=10)
        end = time.time()

        # Допустим, page_load_time — это время HTTP-запроса
        perf_data.page_load_time = end - start

        # LCP, CLS, FID обычно замеряют скриптами в браузере,
        # но для примера зададим фейковые данные
        perf_data.largest_contentful_paint = 2.3
        perf_data.cumulative_layout_shift = 0.05
        perf_data.first_input_delay = 0.15

        # Пример рекомендаций
        if perf_data.page_load_time > 3.0:
            recommendations.append(
                Recommendation(
                    message="Время загрузки страницы превышает 3 секунды (рекомендуется улучшить).",
                    category="PERFORMANCE",
                )
            )
    except Exception as e:
        logger.error(f"Ошибка анализа производительности: {e}")
        recommendations.append(
            Recommendation(
                message="Произошла ошибка при анализе производительности.",
                category="PERFORMANCE",
            )
        )

    return perf_data, recommendations
