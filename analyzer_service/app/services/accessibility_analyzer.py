import logging
import requests
from bs4 import BeautifulSoup
from proto.analyzer_pb2 import AccessibilityData, Recommendation

logger = logging.getLogger(__name__)


class AccessibilityAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.a11y_data = AccessibilityData()
        self.recommendations = []

    async def analyze(self) -> tuple[AccessibilityData, list[Recommendation]]:
        """
        Analyzes the accessibility of the page and generates recommendations.
        Returns (AccessibilityData, [Recommendation]).
        """
        try:
            resp = requests.get(self.url, timeout=10)
            if resp.status_code != 200:
                self.recommendations.append(
                    Recommendation(
                        message=f"The page returned status code {resp.status_code}. Accessibility analysis may be inaccurate.",
                        category="A11Y",
                    )
                )
                return self.a11y_data, self.recommendations

            soup = BeautifulSoup(resp.text, "html.parser")
            self.check_alt_tags(soup)
            self.check_headings(soup)
            # ...additional checks...

            logger.info("Accessibility analysis of the page completed.")

        except Exception as e:
            logger.error(f"Error during accessibility analysis: {e}")
            self.recommendations.append(
                Recommendation(
                    message="An error occurred during accessibility analysis. Check logs for details.",
                    category="A11Y",
                )
            )

        return self.a11y_data, self.recommendations

    def check_alt_tags(self, soup: BeautifulSoup):
        images = soup.find_all("img")
        images_without_alt = [img for img in images if not img.get("alt")]
        if images_without_alt:
            self.a11y_data.has_alt_for_images = False
            self.recommendations.append(
                Recommendation(
                    message=f"{len(images_without_alt)} images are missing alt attributes.",
                    category="A11Y",
                )
            )
        else:
            self.a11y_data.has_alt_for_images = True

    def check_headings(self, soup: BeautifulSoup):
        if not soup.find_all(["h1", "h2", "h3"]):
            self.a11y_data.has_proper_headings = False
            self.recommendations.append(
                Recommendation(
                    message="The page is missing semantic headings (h1/h2/h3).",
                    category="A11Y",
                )
            )
        else:
            self.a11y_data.has_proper_headings = True


# Usage
async def analyze_accessibility(
    url: str,
) -> tuple[AccessibilityData, list[Recommendation]]:
    analyzer = AccessibilityAnalyzer(url)
    return await analyzer.analyze()
