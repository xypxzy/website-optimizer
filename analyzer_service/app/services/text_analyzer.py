import logging
import grpc
import traceback

# import spacy
# import nltk
# import spacy.cli
# from nltk.tokenize import word_tokenize
# from nltk.probability import FreqDist
from bs4 import BeautifulSoup
from proto import analyzer_pb2_grpc, analyzer_pb2


logger = logging.getLogger(__name__)


class TextAnalyzerServicer(analyzer_pb2_grpc.AnalyzerServiceServicer):
    """
    gRPC service for analyzing text content from a BeautifulSoup object.
    """

    def __init__(self):
        """Initialize NLP tools and logger"""
        # spacy.cli.download("en_core_web_sm")  # Ensure the spaCy model is downloaded
        # self.spacy_nlp = spacy.load("en_core_web_sm")
        # nltk.download("punkt")  # Download the punkt tokenizer models

        logger.info("TextAnalyzerService initialized.")

    def Analyze(self, request, context):
        """Handles gRPC request to analyze the content of a web page."""
        try:
            soup = BeautifulSoup(request.content, "html.parser")
            text = self._extract_text(soup)
            # tokens = self._tokenize_and_clean_text(text)
            # freq_dist = self._get_frequency_distribution(tokens)
            freq_dist = {}
            # entities = self._extract_entities(text)
            # entity_list = [
            #     analyzer_pb2.Entity(type=key, names=value)
            #     for key, value in entities.items()
            # ]
            entity_list = []
            logger.info("Analysis completed successfully.")
            return analyzer_pb2.AnalyzeResponse(
                frequency_distribution=dict(freq_dist), entities=entity_list
            )
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            traceback.print_exc()
            context.set_details("Internal server error.")
            context.set_code(grpc.StatusCode.INTERNAL)
            return analyzer_pb2.AnalyzeResponse()

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extracts the entire text from the given BeautifulSoup object, removing scripts and styles."""
        for script in soup(["script", "style"]):
            script.decompose()
        return " ".join(soup.stripped_strings)

    # def _tokenize_and_clean_text(self, text: str) -> list:
    #     """Tokenizes the text and removes stopwords."""
    #     try:
    #         tokens = word_tokenize(text)
    #         return [token.lower() for token in tokens if token.isalpha()]
    #     except Exception as e:
    #         logger.error(f"Error tokenizing text: {e}")
    #         return []

    # def _get_frequency_distribution(self, tokens: list) -> FreqDist:
    #     """Creates a frequency distribution for the given tokens."""
    #     try:
    #         return FreqDist(tokens)
    #     except Exception as e:
    #         logger.error(f"Error calculating frequency distribution: {e}")
    #         return FreqDist()

    # def _extract_entities(self, text: str) -> dict:
    #     """Extracts named entities using spaCy."""
    #     try:
    #         doc = self.spacy_nlp(text)
    #         entities = {ent.label_: [] for ent in doc.ents}
    #         for ent in doc.ents:
    #             entities[ent.label_].append(ent.text)
    #         return entities
    #     except Exception as e:
    #         logger.error(f"Error extracting entities: {e}")
    #         return {}
