import logging
import spacy
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
from proto import analyzer_pb2

nltk.download("stopwords")
nltk.download("vader_lexicon")
nltk.download("punkt_tab")

logger = logging.getLogger(__name__)

try:
    nltk_stopwords_en = set(stopwords.words("english"))
    nltk_stopwords_ru = set(stopwords.words("russian"))
except LookupError as e:
    logger.error(f"Error loading NLTK stopwords: {e}")
    nltk_stopwords_en = set()
    nltk_stopwords_ru = set()

sia = SentimentIntensityAnalyzer()

# Инициализация spaCy модели для NER (английский язык)
try:
    nlp_en = spacy.load("en_core_web_sm")
    logger.info("spaCy English model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load spaCy English model: {e}")
    nlp_en = None

# Инициализация spaCy модели для NER (русский язык)
try:
    nlp_ru = spacy.load("ru_core_news_sm")
    logger.info("spaCy Russian model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load spaCy Russian model: {e}")
    nlp_ru = None


def detect_language(content):
    """Простая эвристика для определения языка текста."""
    # Используем библиотеку langdetect для более точного определения языка
    try:
        from langdetect import detect

        return detect(content)
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        return "unknown"


class TextAnalyzer:
    def __init__(self, content: str):
        self.content = content
        self.text_data = analyzer_pb2.AnalyzeResponse()
        self.recommendations = []

    async def analyze(
        self,
    ) -> tuple[analyzer_pb2.AnalyzeResponse, list[analyzer_pb2.Recommendation]]:
        """
        Analyzes the text content and generates recommendations.
        Returns (AnalyzeResponse, [Recommendation]).
        """
        try:
            self.analyze_frequency_distribution()
            self.analyze_entities()
            self.analyze_sentiment()

        except Exception as e:
            logger.error(f"Error during text analysis: {e}")
            self.recommendations.append(
                analyzer_pb2.Recommendation(
                    message="An error occurred during text analysis. Check logs for details.",
                    category="TEXT",
                )
            )

        return self.text_data, self.recommendations

    def analyze_frequency_distribution(self):
        # Определение языка текста
        language = detect_language(self.content)
        if language.startswith("ru"):
            stopwords_set = nltk_stopwords_ru
            nlp = nlp_ru
            logger.debug("Detected language: Russian")
        elif language.startswith("en"):
            stopwords_set = nltk_stopwords_en
            nlp = nlp_en
            logger.debug("Detected language: English")
        else:
            stopwords_set = set()
            nlp = None
            logger.debug(f"Detected language: {language}")

        # Токенизация текста
        tokens = word_tokenize(self.content.lower())
        logger.debug(f"Tokens: {tokens}")

        # Удаление стоп-слов и неалфавитных токенов
        filtered_tokens = [
            word for word in tokens if word.isalpha() and word not in stopwords_set
        ]
        logger.debug(f"Filtered Tokens: {filtered_tokens}")

        # Лемматизация (при использовании spaCy)
        if nlp:
            doc = nlp(" ".join(filtered_tokens))
            lemmatized_tokens = [token.lemma_ for token in doc]
            logger.debug(f"Lemmatized Tokens: {lemmatized_tokens}")
        else:
            lemmatized_tokens = filtered_tokens

        # Частотное распределение
        frequency_distribution = Counter(lemmatized_tokens)
        logger.debug(f"Frequency Distribution: {frequency_distribution}")

        # Convert frequency distribution to protobuf format
        frequency_distribution_entries = [
            analyzer_pb2.FrequencyDistributionEntry(key=word, value=count)
            for word, count in frequency_distribution.items()
        ]

        self.text_data.frequency_distribution.extend(frequency_distribution_entries)

    def analyze_entities(self):
        # Извлечение сущностей с помощью spaCy
        entities = []
        language = detect_language(self.content)
        if language.startswith("ru"):
            nlp = nlp_ru
        elif language.startswith("en"):
            nlp = nlp_en
        else:
            nlp = None

        if nlp:
            doc_full = nlp(self.content)
            for ent in doc_full.ents:
                entities.append(
                    analyzer_pb2.AnalyzeResponse.Entity(name=ent.text, type=ent.label_)
                )
            logger.debug(f"Extracted Entities: {entities}")
        else:
            logger.warning("spaCy model not loaded. Skipping entity extraction.")

        self.text_data.entities.extend(entities)

    def analyze_sentiment(self):
        # Анализ тональности
        sentiment_scores = sia.polarity_scores(self.content)
        logger.debug(f"Sentiment Scores: {sentiment_scores}")

        self.text_data.sentiment.positive = sentiment_scores["pos"]
        self.text_data.sentiment.negative = sentiment_scores["neg"]
        self.text_data.sentiment.neutral = sentiment_scores["neu"]
