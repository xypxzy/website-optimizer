import logging
import grpc
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

    async def Analyze(self, request, context):
        """
        Выполняет анализ контента и возвращает AnalyzeResponse.
        """
        content = request.content
        correlation_id = request.correlation_id

        logger.info(f"Анализ содержимого с correlation_id: {correlation_id}")

        try:
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
        except Exception as e:
            logger.error(f"Ошибка при анализе содержимого: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return analyzer_pb2.AnalyzeResponse()
