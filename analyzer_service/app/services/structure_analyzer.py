import logging
import requests
from bs4 import BeautifulSoup
from proto.analyzer_pb2 import StructureData, Recommendation

logger = logging.getLogger(__name__)


class StructureAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.structure_data = StructureData()
        self.recommendations = []

    async def analyze(self) -> tuple[StructureData, list[Recommendation]]:
        """
        Analyzes the structure of the page and generates recommendations.
        Returns (StructureData, [Recommendation]).
        """
        try:
            resp = requests.get(self.url, timeout=10)
            if resp.status_code != 200:
                self.recommendations.append(
                    Recommendation(
                        message=f"The page returned status code {resp.status_code}. Structure analysis may be inaccurate.",
                        category="STRUCTURE",
                    )
                )
                return self.structure_data, self.recommendations

            self.check_redirects(resp)
            soup = BeautifulSoup(resp.text, "html.parser")
            self.check_broken_links(soup)
            self.check_headings_structure(soup)
            self.check_a_tags(soup)
            self.check_img_tags(soup)
            self.check_sitemap_and_robots()

            logger.info("Structure analysis of the page completed.")

        except Exception as e:
            logger.error(f"Error during structure analysis: {e}")
            self.recommendations.append(
                Recommendation(
                    message="An error occurred during structure analysis. Check logs for details.",
                    category="STRUCTURE",
                )
            )

        return self.structure_data, self.recommendations

    def check_redirects(self, resp):
        if len(resp.history) > 1:
            self.structure_data.redirect_count = len(resp.history)
            self.recommendations.append(
                Recommendation(
                    message=f"{len(resp.history)} redirects were detected before reaching the final page.",
                    category="STRUCTURE",
                )
            )

    def check_broken_links(self, soup: BeautifulSoup):
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

        self.structure_data.broken_links_count = broken_links
        if broken_links > 0:
            self.recommendations.append(
                Recommendation(
                    message=f"{broken_links} broken links were found on the page.",
                    category="STRUCTURE",
                )
            )

    def check_headings_structure(self, soup: BeautifulSoup):
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        previous_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if level < previous_level:
                self.recommendations.append(
                    Recommendation(
                        message=f"Incorrect heading structure: <{heading.name}> follows <h{previous_level}>.",
                        category="STRUCTURE",
                    )
                )
            previous_level = level

    def check_a_tags(self, soup: BeautifulSoup):
        a_tags = soup.find_all("a")
        missing_rel_count = sum(1 for a in a_tags if not a.get("rel"))

        if missing_rel_count > 0:
            self.recommendations.append(
                Recommendation(
                    message=f"There are {missing_rel_count} <a> tags without a rel attribute.",
                    category="STRUCTURE",
                )
            )

    def check_img_tags(self, soup: BeautifulSoup):
        img_tags = soup.find_all("img")
        missing_alt_count = sum(1 for img in img_tags if not img.get("alt"))
        missing_src_count = sum(1 for img in img_tags if not img.get("src"))

        if missing_src_count > 0:
            self.recommendations.append(
                Recommendation(
                    message=f"There are {missing_src_count} <img> tags without a src attribute.",
                    category="STRUCTURE",
                )
            )
        if missing_alt_count > 0:
            self.recommendations.append(
                Recommendation(
                    message=f"There are {missing_alt_count} <img> tags without an alt attribute.",
                    category="STRUCTURE",
                )
            )

    def check_sitemap_and_robots(self):
        base_domain = self.url.split("//")[-1].split("/")[0]
        sitemap_url = f"https://{base_domain}/sitemap.xml"
        robots_url = f"https://{base_domain}/robots.txt"

        try:
            site_resp = requests.head(sitemap_url, timeout=5)
            if site_resp.status_code == 200:
                self.structure_data.has_sitemap = True
            else:
                self.structure_data.has_sitemap = False
                self.recommendations.append(
                    Recommendation(
                        message="Sitemap.xml was not found on the site (or returned a non-200 status).",
                        category="STRUCTURE",
                    )
                )
        except:
            self.structure_data.has_sitemap = False

        try:
            robot_resp = requests.head(robots_url, timeout=5)
            if robot_resp.status_code == 200:
                self.structure_data.has_robots_txt = True
            else:
                self.structure_data.has_robots_txt = False
                self.recommendations.append(
                    Recommendation(
                        message="Robots.txt was not found on the site (or returned a non-200 status).",
                        category="STRUCTURE",
                    )
                )
        except:
            self.structure_data.has_robots_txt = False
