import re
import logging
import requests
from bs4 import BeautifulSoup
from proto.analyzer_pb2 import AccessibilityData, Recommendation

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from color_contrast import AccessibilityLevel, check_contrast


logger = logging.getLogger(__name__)


class AccessibilityAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.a11y_data = AccessibilityData()
        self.recommendations = []

    async def analyze(self) -> tuple[AccessibilityData, list[Recommendation]]:
        try:
            # First, check if the page is accessible at all
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

            # Run all checks
            self.check_alt_tags(soup)
            self.check_headings(soup)
            # For color contrast, we need to use Selenium, so pass the URL to the method
            self.check_color_contrast(self.url)
            self.check_focusable_elements(soup)
            self.check_aria_attributes(soup)
            self.check_semantic_elements(soup)
            self.check_forms(soup)

            logger.info(
                f"Accessibility analysis completed with {len(self.recommendations)} recommendations."
            )

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
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        previous_level = 0
        for heading in headings:
            level = int(heading.name[1])
            if level > previous_level + 1:
                self.recommendations.append(
                    Recommendation(
                        message=f"Incorrect heading hierarchy: <{heading.name}> follows <h{previous_level}>.",
                        category="A11Y",
                    )
                )
            previous_level = level

    def check_color_contrast(self, url: str):
        """
        Check the contrast of text with the background using Selenium.
        In this example, we iterate over all visible text elements (tags p, span, div, etc.),
        get their text color (color) and background color (background-color),
        and then calculate the contrast.
        """

        # Set up the browser (headless)
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Initialize the driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.get(url)

            # Find all elements that may contain text
            # (p, span, div, headers, etc.)
            text_tags = [
                "p",
                "span",
                "div",
                "li",
                "a",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
            ]
            elements = []
            for tag in text_tags:
                elements.extend(driver.find_elements_by_tag_name(tag))

            # Function to convert color from "rgb(...)" to tuple (r, g, b)
            def rgb_to_tuple(rgb_str: str):
                # rgb(255, 255, 255) -> (255, 255, 255)
                found = re.findall(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", rgb_str)
                if not found:
                    return (255, 255, 255)  # Default to white
                return tuple(map(int, found[0]))

            for element in elements:
                # Check if the element is visible (has text)
                if not element.is_displayed():
                    continue

                text = element.text.strip()
                if not text:
                    continue

                # Get the current text color and background color
                text_color = element.value_of_css_property("color")
                background_color = element.value_of_css_property("background-color")

                text_color_rgb = rgb_to_tuple(text_color)
                background_color_rgb = rgb_to_tuple(background_color)

                # Calculate contrast
                contrast_ratio = check_contrast(
                    text_color_rgb, background_color_rgb, AccessibilityLevel.AA
                )

                # Check for compliance with WCAG 2.1 (level AA)
                # For normal text, the threshold is 4.5, for large text it can be 3.0
                # In this example, we simply use 4.5 for simplicity
                if contrast_ratio:
                    self.recommendations.append(
                        Recommendation(
                            message=(
                                f"Low contrast ratio ({contrast_ratio:.2f}) detected between "
                                f"text color {text_color_rgb} and background {background_color_rgb} "
                                f'in element <{element.tag_name}>: "{text[:30]}..."'
                            ),
                            category="A11Y",
                        )
                    )

        except Exception as exc:
            logger.error(f"Error in check_color_contrast: {exc}")
            self.recommendations.append(
                Recommendation(
                    message="An error occurred during color contrast analysis. Check logs for details.",
                    category="A11Y",
                )
            )
        finally:
            driver.quit()

    def check_focusable_elements(self, soup: BeautifulSoup):
        interactive_elements = soup.find_all(["a", "button", "input", "textarea"])
        for element in interactive_elements:
            if "tabindex" not in element.attrs:
                self.recommendations.append(
                    Recommendation(
                        message=f"Interactive element <{element.name}> is missing tabindex.",
                        category="A11Y",
                    )
                )

    def check_aria_attributes(self, soup: BeautifulSoup):
        elements_with_aria = soup.find_all(attrs={"aria-label": True})
        for element in elements_with_aria:
            if not element["aria-label"]:
                self.recommendations.append(
                    Recommendation(
                        message=f"Element <{element.name}> has an empty aria-label attribute.",
                        category="A11Y",
                    )
                )

    def check_semantic_elements(self, soup: BeautifulSoup):
        semantic_elements = ["header", "footer", "main", "article", "aside", "nav"]
        for element in semantic_elements:
            if not soup.find(element):
                self.recommendations.append(
                    Recommendation(
                        message=f"The page is missing the semantic <{element}> element.",
                        category="A11Y",
                    )
                )

    def check_forms(self, soup: BeautifulSoup):
        forms = soup.find_all("form")
        for form in forms:
            inputs = form.find_all("input")
            for input_field in inputs:
                if not input_field.get("aria-labelledby") and not soup.find(
                    "label", {"for": input_field.get("id")}
                ):
                    self.recommendations.append(
                        Recommendation(
                            message=f"Input field with id '{input_field.get('id')}' is missing a label.",
                            category="A11Y",
                        )
                    )
