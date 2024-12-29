import logging
from proto.analyzer_pb2 import AnalyzeResponse

from app.services.text_analyzer import analyze_text
from app.services.seo_analyzer import analyze_seo
from app.services.perfomance_analyzer import analyze_performance
from app.services.accessibility_analyzer import analyze_accessibility
from app.services.security_analyzer import analyze_security
from app.services.structure_analyzer import analyze_structure

logger = logging.getLogger(__name__)


async def analyze_all(content: str, url: str) -> AnalyzeResponse:
    """
    Вызывает все анализаторы последовательно,
    формирует единый AnalyzeResponse со списком рекомендаций.
    """

    # Изначально пустой ответ
    response = AnalyzeResponse()

    # 1) Анализ текста
    text_result = await analyze_text(content)
    response.frequency_distribution.extend(text_result["frequency_distribution"])
    response.entities.extend(text_result["entities"])
    response.sentiment.CopyFrom(text_result["sentiment"])
    recommendations = text_result["recommendations"]  # частичный список рекомендаций

    # 2) SEO-анализ
    seo_data, seo_recs = await analyze_seo(url)
    response.seo_data.CopyFrom(seo_data)
    recommendations.extend(seo_recs)

    # 3) Анализ производительности
    perf_data, perf_recs = await analyze_performance(url)
    response.performance_data.CopyFrom(perf_data)
    recommendations.extend(perf_recs)

    # 4) Доступность
    a11y_data, a11y_recs = await analyze_accessibility(url)
    response.accessibility_data.CopyFrom(a11y_data)
    recommendations.extend(a11y_recs)

    # 5) Безопасность
    security_data, sec_recs = await analyze_security(url)
    response.security_data.CopyFrom(security_data)
    recommendations.extend(sec_recs)

    # 6) Структура
    structure_data, struct_recs = await analyze_structure(url)
    response.structure_data.CopyFrom(structure_data)
    recommendations.extend(struct_recs)

    # Собираем все рекомендации в один список
    response.recommendations.extend(recommendations)

    return response
