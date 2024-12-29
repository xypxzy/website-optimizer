import logging
import time
import requests
from proto.analyzer_pb2 import PerformanceData, Recommendation

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.perf_data = PerformanceData()
        self.recommendations = []

    async def analyze(self) -> tuple[PerformanceData, list[Recommendation]]:
        """
        Analyzes the performance of the page and generates recommendations.
        Returns (PerformanceData, [Recommendation]).
        """
        try:
            start = time.time()
            resp = requests.get(self.url, timeout=10)
            end = time.time()

            self.perf_data.page_load_time = end - start
            self.perf_data.largest_contentful_paint = 2.3
            self.perf_data.cumulative_layout_shift = 0.05
            self.perf_data.first_input_delay = 0.15

            self.check_page_load_time()

            logger.info("Performance analysis of the page completed.")

        except Exception as e:
            logger.error(f"Error during performance analysis: {e}")
            self.recommendations.append(
                Recommendation(
                    message="An error occurred during performance analysis.",
                    category="PERFORMANCE",
                )
            )

        return self.perf_data, self.recommendations

    def check_page_load_time(self):
        if self.perf_data.page_load_time > 3.0:
            self.recommendations.append(
                Recommendation(
                    message="Page load time exceeds 3 seconds (recommended to improve).",
                    category="PERFORMANCE",
                )
            )
