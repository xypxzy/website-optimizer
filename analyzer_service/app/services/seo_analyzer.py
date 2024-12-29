import logging
from bs4 import BeautifulSoup
import requests

from proto.analyzer_pb2 import SEOData, Recommendation

logger = logging.getLogger(__name__)


class SEOAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.seo_data = SEOData()
        self.recommendations = []

    async def analyze(self) -> tuple[SEOData, list[Recommendation]]:
        """
        Analyze SEO aspects of the page and generate recommendations.
        Returns SEOData and a list of Recommendation objects.
        """
        try:
            response = requests.get(self.url, timeout=10)
            if response.status_code != 200:
                self.recommendations.append(
                    Recommendation(
                        message=f"The page returned status code {response.status_code}. Full SEO analysis cannot be performed.",
                        category="SEO",
                    )
                )
                return self.seo_data, self.recommendations

            soup = BeautifulSoup(response.text, "html.parser")

            # Perform checks
            self.check_title(soup)
            self.check_description(soup)
            self.check_canonical(soup)
            self.check_meta_social(soup)
            self.check_meta_base(soup)

            logger.info("SEO analysis of the page completed.")
            return self.seo_data, self.recommendations

        except Exception as e:
            logger.error(f"Error during SEO analysis: {e}")
            self.recommendations.append(
                Recommendation(
                    message="An error occurred during SEO analysis. Check logs for details.",
                    category="SEO",
                )
            )
            return self.seo_data, self.recommendations

    def check_title(self, soup: BeautifulSoup):
        title_tag = soup.find("title")
        if title_tag:
            self.seo_data.has_title_tag = True
            self.seo_data.title_length = len(title_tag.text)
            if self.seo_data.title_length < 30:
                self.recommendations.append(
                    Recommendation(
                        message=f"The title is too short ({self.seo_data.title_length}). The minimum recommended length is 30 characters.",
                        category="SEO",
                    )
                )
            if self.seo_data.title_length > 60:
                self.recommendations.append(
                    Recommendation(
                        message=f"The title is too long ({self.seo_data.title_length}). The maximum recommended length is 60 characters.",
                        category="SEO",
                    )
                )
        else:
            self.seo_data.has_title_tag = False
            self.recommendations.append(
                Recommendation(
                    message="The page is missing a <title> tag.", category="SEO"
                )
            )

    def check_description(self, soup: BeautifulSoup):
        description_tag = soup.find("meta", attrs={"name": "description"})
        if description_tag and description_tag.get("content"):
            self.seo_data.has_description_tag = True
            self.seo_data.description_length = len(description_tag["content"])
            if self.seo_data.description_length < 160:
                self.recommendations.append(
                    Recommendation(
                        message=f"The meta description is too short ({self.seo_data.description_length}). The minimum recommended length is 160 characters.",
                        category="SEO",
                    )
                )
            if self.seo_data.description_length > 300:
                self.recommendations.append(
                    Recommendation(
                        message=f"The meta description is too long ({self.seo_data.description_length}). The maximum recommended length is 300 characters.",
                        category="SEO",
                    )
                )
        else:
            self.seo_data.has_description_tag = False
            self.recommendations.append(
                Recommendation(
                    message="The page is missing a meta description.", category="SEO"
                )
            )

    def check_canonical(self, soup: BeautifulSoup):
        canonical_tag = soup.find("link", rel="canonical")
        if not canonical_tag:
            self.recommendations.append(
                Recommendation(
                    message="The page is missing a <link rel='canonical'> tag.",
                    category="SEO",
                )
            )
        elif not canonical_tag.get("href"):
            self.recommendations.append(
                Recommendation(
                    message="The canonical tag is missing the href attribute.",
                    category="SEO",
                )
            )
        elif not canonical_tag["href"].endswith("/"):
            self.recommendations.append(
                Recommendation(
                    message="The href attribute in the canonical tag does not end with a slash.",
                    category="SEO",
                )
            )

    def check_meta_social(self, soup: BeautifulSoup):
        social_meta_tags = [
            "og:url",
            "og:type",
            "og:site_name",
            "og:title",
            "og:description",
            "og:image",
            "twitter:card",
            "twitter:url",
        ]
        for tag in social_meta_tags:
            meta_tag = soup.find("meta", property=tag)
            if not meta_tag:
                self.recommendations.append(
                    Recommendation(
                        message=f"The page is missing a <meta property='{tag}'> tag.",
                        category="SEO",
                    )
                )
            elif not meta_tag.get("content"):
                self.recommendations.append(
                    Recommendation(
                        message=f"The content attribute in <meta property='{tag}'> is empty.",
                        category="SEO",
                    )
                )

    def check_meta_base(self, soup: BeautifulSoup):
        base_meta_tags = ["viewport", "description"]
        for tag in base_meta_tags:
            meta_tag = soup.find("meta", attrs={"name": tag})
            if not meta_tag:
                self.recommendations.append(
                    Recommendation(
                        message=f"The page is missing a <meta name='{tag}'> tag.",
                        category="SEO",
                    )
                )
            elif not meta_tag.get("content"):
                self.recommendations.append(
                    Recommendation(
                        message=f"The content attribute in <meta name='{tag}'> is empty.",
                        category="SEO",
                    )
                )
