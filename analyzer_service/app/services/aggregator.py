import logging

from proto.analyzer_pb2 import AnalyzeResponse
from .text_analyzer import TextAnalyzer
from .seo_analyzer import SEOAnalyzer

# from .performance_analyzer import PerformanceAnalyzer
from .accessibility_analyzer import AccessibilityAnalyzer
from .security_analyzer import SecurityAnalyzer
from .structure_analyzer import StructureAnalyzer

logger = logging.getLogger(__name__)


async def analyze_all(content: str, url: str) -> AnalyzeResponse:
    """
    Calls all analyzers sequentially,
    forms a single AnalyzeResponse with a list of recommendations.
    """

    # Initially empty response
    response = AnalyzeResponse()

    # 1) Text analyzer
    text_analyzer = TextAnalyzer(content)
    text_data, text_recs = await text_analyzer.analyze()
    response.frequency_distribution.extend(text_data.frequency_distribution)
    response.entities.extend(text_data.entities)
    response.sentiment.CopyFrom(text_data.sentiment)
    recommendations = list(text_recs)

    # 2) SEO analyzer
    seo_analyzer = SEOAnalyzer(url)
    seo_data, seo_recs = await seo_analyzer.analyze()
    response.seo_data.CopyFrom(seo_data)
    recommendations.extend(seo_recs)

    # # 3) Performance analyzer
    # TODO: implement performance analyzer

    # 4) Accessibility analyzer
    a11y_analyzer = AccessibilityAnalyzer(url)
    a11y_data, a11y_recs = await a11y_analyzer.analyze()
    response.accessibility_data.CopyFrom(a11y_data)
    recommendations.extend(a11y_recs)

    # 5) Security analyzer
    security_analyzer = SecurityAnalyzer(url)
    security_data, sec_recs = await security_analyzer.analyze()
    response.security_data.CopyFrom(security_data)
    recommendations.extend(sec_recs)

    # 6) Structure analyzer
    structure_analyzer = StructureAnalyzer(url)
    structure_data, struct_recs = await structure_analyzer.analyze()
    response.structure_data.CopyFrom(structure_data)
    recommendations.extend(struct_recs)

    response.recommendations.extend(recommendations)

    return response
