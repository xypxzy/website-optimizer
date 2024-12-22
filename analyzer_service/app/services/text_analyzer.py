import logging
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
import spacy
from proto import analyzer_pb2_grpc, analyzer_pb2

logger = logging.getLogger(__name__)

# Инициализация NLTK инструментов
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


async def analyze_text(content):
    """
    Функция для анализа текста.
    Возвращает AnalyzeResponse.
    """
    try:
        # Определение языка текста
        language = detect_language(content)
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
        tokens = word_tokenize(content.lower())
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

        # Извлечение сущностей с помощью spaCy
        entities = []
        if nlp:
            doc_full = nlp(content)
            for ent in doc_full.ents:
                entities.append(analyzer_pb2.Entity(name=ent.text, type=ent.label_))
            logger.debug(f"Extracted Entities: {entities}")
        else:
            logger.warning("spaCy model not loaded. Skipping entity extraction.")

        # Анализ тональности
        sentiment_scores = sia.polarity_scores(content)
        logger.debug(f"Sentiment Scores: {sentiment_scores}")

        analyze_response = analyzer_pb2.AnalyzeResponse(
            frequency_distribution=dict(frequency_distribution),
            entities=entities,
            sentiment=analyzer_pb2.Sentiment(
                positive=sentiment_scores.get("pos", 0.0),
                negative=sentiment_scores.get("neg", 0.0),
                neutral=sentiment_scores.get("neu", 0.0),
                compound=sentiment_scores.get("compound", 0.0),
            ),
        )

        logger.info("Analysis completed successfully.")

        return analyze_response

    except Exception as e:
        logger.error(f"Error analyzing content: {e}")
        raise e


class TextAnalyzerServicer(analyzer_pb2_grpc.AnalyzerServiceServicer):
    """
    gRPC service for analyzing text content from an HTML document.
    """

    def __init__(self):
        """Initialization of NLP tools and logger"""
        logger.info("TextAnalyzerService initialized.")

    async def Analyze(self, request, context):
        """
        Performs content analysis and returns AnalyzeResponse.
        """
        content = request.content
        correlation_id = request.correlation_id

        logger.info(f"Analyzing content with correlation_id: {correlation_id}")

        try:
            analyze_response = await analyze_text(content)
            analyze_response.correlation_id = correlation_id
            return analyze_response

        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return analyzer_pb2.AnalyzeResponse()
