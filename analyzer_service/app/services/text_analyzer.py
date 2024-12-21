import logging
from bs4 import BeautifulSoup
from proto import analyzer_pb2_grpc, analyzer_pb2


logger = logging.getLogger(__name__)


class TextAnalyzerServicer(analyzer_pb2_grpc.AnalyzerServiceServicer):
    """
    gRPC сервис для анализа текстового контента из HTML-документа.
    """

    def __init__(self):
        """Инициализация инструментов NLP и логгера"""
        # Раскомментируйте и настройте, если используете spaCy или nltk
        # import spacy
        # import nltk
        # spacy.cli.download("en_core_web_sm")
        # self.spacy_nlp = spacy.load("en_core_web_sm")
        # nltk.download("punkt")

        logger.info("TextAnalyzerService инициализирован.")

    def Analyze(self, parse_response):
        """
        Выполняет анализ контента и возвращает AnalyzeResponse.
        """
        content = parse_response.content
        correlation_id = parse_response.correlation_id

        logger.info(f"Анализ содержимого с correlation_id: {correlation_id}")

        # Пример простого анализа: подсчёт слов
        words = content.lower().split()
        frequency_distribution = {}
        for word in words:
            frequency_distribution[word] = frequency_distribution.get(word, 0) + 1

        # Пример извлечения сущностей (здесь просто пустой список)
        entities = []

        analyze_response = analyzer_pb2.AnalyzeResponse(
            correlation_id=correlation_id,
            frequency_distribution=frequency_distribution,
            entities=entities,
        )

        logger.info("Анализ завершен успешно.")

        return analyze_response

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Извлекает весь текст из объекта BeautifulSoup, удаляя скрипты и стили."""
        for script in soup(["script", "style"]):
            script.decompose()
        return " ".join(soup.stripped_strings)

    def _get_frequency_distribution(self, text: str) -> dict:
        """Создает частотное распределение слов в тексте."""
        words = text.lower().split()
        freq_dist = {}
        for word in words:
            freq_dist[word] = freq_dist.get(word, 0) + 1
        return freq_dist

    def _extract_entities(self, text: str) -> list:
        """Извлекает сущности из текста. Реализуйте с помощью spaCy или другой библиотеки."""
        # Пример заглушки. Реализуйте настоящую логику.
        return []
