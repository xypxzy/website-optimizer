# import logging
# import requests
# import time
# import subprocess
# import json
# import asyncio
# from proto.analyzer_pb2 import PerformanceData, Recommendation

# logger = logging.getLogger(__name__)


# class PerformanceAnalyzer:
#     def __init__(self, url: str):
#         self.url = url
#         self.perf_data = PerformanceData()
#         self.recommendations = []

#     async def analyze(self) -> tuple[PerformanceData, list[Recommendation]]:
#         """
#         Analyzes the performance of the page and generates recommendations.
#         """
#         try:
#             start = time.time()
#             resp = requests.get(self.url, timeout=10)
#             end = time.time()

#             # Основные метрики
#             self.perf_data.page_load_time = end - start
#             self.check_page_load_time()

#             # Дополнительные метрики
#             self.perf_data.time_to_first_byte = self.get_ttfb()
#             self.check_ttfb()

#             # Анализ количества запросов
#             self.perf_data.http_request_count = self.get_http_request_count(resp)
#             self.check_http_request_count()

#             # Анализ заголовков кэширования
#             self.check_cache_headers(resp)

#             # Lighthouse Analysis
#             lighthouse_data = await self.run_lighthouse()
#             if lighthouse_data:
#                 self.extract_lighthouse_metrics(lighthouse_data)

#             # Check CLS
#             self.check_cls()

#             logger.info("Performance analysis completed.")

#         except Exception as e:
#             logger.error(f"Error during performance analysis: {e}")
#             self.recommendations.append(
#                 Recommendation(
#                     message="An error occurred during performance analysis.",
#                     category="PERFORMANCE",
#                 )
#             )

#         return self.perf_data, self.recommendations

#     def get_ttfb(self) -> float:
#         """
#         Calculates Time To First Byte (TTFB).
#         """
#         try:
#             start = time.time()
#             resp = requests.head(self.url, timeout=5)
#             ttfb = resp.elapsed.total_seconds()
#             return ttfb
#         except Exception as e:
#             logger.error(f"Failed to calculate TTFB: {e}")
#             return -1

#     def check_ttfb(self):
#         """
#         Adds recommendation if TTFB exceeds a reasonable threshold.
#         """
#         if self.perf_data.time_to_first_byte > 0.2:  # Рекомендуемый порог
#             self.recommendations.append(
#                 Recommendation(
#                     message="Time To First Byte (TTFB) exceeds 200ms. Optimize server response time.",
#                     category="PERFORMANCE",
#                 )
#             )

#     def get_http_request_count(self, resp) -> int:
#         """
#         Estimates the number of HTTP requests by analyzing the HTML.
#         """
#         try:
#             from bs4 import BeautifulSoup

#             soup = BeautifulSoup(resp.text, "html.parser")
#             links = soup.find_all(["script", "link", "img"])
#             return len(links)
#         except Exception as e:
#             logger.error(f"Failed to count HTTP requests: {e}")
#             return 0

#     def check_http_request_count(self):
#         """
#         Adds recommendation if the number of HTTP requests is too high.
#         """
#         if self.perf_data.http_request_count > 50:  # Рекомендуемый порог
#             self.recommendations.append(
#                 Recommendation(
#                     message="The number of HTTP requests exceeds 50. Consider combining resources to reduce requests.",
#                     category="PERFORMANCE",
#                 )
#             )

#     def check_cache_headers(self, resp):
#         """
#         Checks caching headers and adds recommendations if caching is not set up.
#         """
#         cache_control = resp.headers.get("Cache-Control", "")
#         if "max-age" not in cache_control:
#             self.recommendations.append(
#                 Recommendation(
#                     message="Cache-Control headers are missing or not optimized. Set max-age for static resources.",
#                     category="PERFORMANCE",
#                 )
#             )

#     def check_page_load_time(self):
#         """
#         Adds recommendation if page load time exceeds a reasonable threshold.
#         """
#         if self.perf_data.page_load_time > 3.0:
#             self.recommendations.append(
#                 Recommendation(
#                     message="Page load time exceeds 3 seconds. Optimize resources and server response time.",
#                     category="PERFORMANCE",
#                 )
#             )

#     async def run_lighthouse(self) -> dict:
#         """
#         Runs Lighthouse CLI to analyze the given URL and returns the JSON report.
#         """
#         try:
#             lighthouse_command = [
#                 "lighthouse",
#                 self.url,
#                 "--output=json",
#                 "--quiet",
#                 "--only-categories=performance",
#                 "--output-path=stdout",
#             ]

#             process = await asyncio.create_subprocess_exec(
#                 *lighthouse_command,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#             )
#             stdout, stderr = await process.communicate()

#             if process.returncode != 0:
#                 logger.error(f"Lighthouse failed: {stderr.decode()}")
#                 return None

#             return json.loads(stdout.decode())
#         except Exception as e:
#             logger.error(f"Failed to run Lighthouse: {e}")
#             return None

#     def extract_lighthouse_metrics(self, lighthouse_data: dict):
#         """
#         Extracts CLS and other metrics from the Lighthouse JSON report.
#         """
#         try:
#             performance_metrics = lighthouse_data.get("audits", {})

#             # Extract CLS
#             cls_metric = performance_metrics.get("cumulative-layout-shift", {})
#             cls_value = cls_metric.get("numericValue", 0)
#             self.perf_data.cumulative_layout_shift = cls_value

#             # Add recommendation for CLS
#             if cls_value > 0.1:  # Рекомендуемый порог для CLS
#                 self.recommendations.append(
#                     Recommendation(
#                         message=f"Cumulative Layout Shift (CLS) is {cls_value:.2f}, which exceeds the recommended threshold of 0.1. Optimize layout stability.",
#                         category="PERFORMANCE",
#                     )
#                 )

#             # Extract LCP and other metrics
#             lcp_metric = performance_metrics.get("largest-contentful-paint", {})
#             lcp_value = lcp_metric.get("numericValue", 0)
#             self.perf_data.largest_contentful_paint = lcp_value

#             if lcp_value > 2.5:  # Рекомендуемый порог для LCP
#                 self.recommendations.append(
#                     Recommendation(
#                         message=f"Largest Contentful Paint (LCP) is {lcp_value:.2f} seconds, which exceeds the recommended threshold of 2.5 seconds.",
#                         category="PERFORMANCE",
#                     )
#                 )

#         except Exception as e:
#             logger.error(f"Failed to extract metrics from Lighthouse: {e}")

#     def check_cls(self):
#         """
#         Adds a general recommendation if CLS is too high.
#         """
#         if self.perf_data.cumulative_layout_shift > 0.1:
#             self.recommendations.append(
#                 Recommendation(
#                     message="Cumulative Layout Shift (CLS) is high. Optimize layout stability by reserving space for images, ads, and dynamic content.",
#                     category="PERFORMANCE",
#                 )
#             )
