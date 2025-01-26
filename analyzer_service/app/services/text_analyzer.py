import logging
from collections import Counter
import re

from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from proto import analyzer_pb2

logger = logging.getLogger(__name__)

# 1) Sentiment analyzer
sentiment_pipeline = pipeline(
    "text-classification", model="tabularisai/multilingual-sentiment-analysis"
)


ner_tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
ner_model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")

# 2) Named Entity Recognition (NER) analyzer
ner_pipeline = pipeline(
    "ner",
    model=ner_model,
    tokenizer=ner_tokenizer,
)

# Cписок простых стоп-слов (для примера)
STOPWORDS = {"the", "a", "an", "is", "it", "and", "or", "of", "to", "in"}


class TextAnalyzer:
    def __init__(self, content: str):
        self.content = content
        self.text_data = analyzer_pb2.AnalyzeResponse()
        self.recommendations = []

    async def analyze(
        self,
    ) -> tuple[analyzer_pb2.AnalyzeResponse, list[analyzer_pb2.Recommendation]]:
        """
        Анализирует текст (частотное распределение, NER, тональность).
        Возвращает (AnalyzeResponse, [Recommendation]).
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
        # Упрощённая токенизация: разбиваем по не-буквенным символам, приводим к нижнему регистру
        tokens = re.findall(r"[a-zA-Zа-яА-Я]+", self.content.lower())

        # Фильтруем короткие слова, стоп-слова и т.д.
        filtered_tokens = [t for t in tokens if len(t) > 1 and t not in STOPWORDS]

        # Считаем частоты
        frequency_distribution = Counter(filtered_tokens)

        # Перекладываем в protobuf-формат
        freq_entries = [
            analyzer_pb2.FrequencyDistributionEntry(key=word, value=count)
            for word, count in frequency_distribution.items()
        ]
        self.text_data.frequency_distribution.extend(freq_entries)

    def analyze_entities(self):
        # Для Named Entity Recognition используем Hugging Face pipeline
        # Применяем к исходному тексту (или куску, если очень большой)
        ner_results = ner_pipeline(self.content[:5000])  # ограничим до 5000 символов

        entities = []
        for item in ner_results:
            # item обычно содержит поля "entity_group", "word", "score" и т.д.
            entity_name = item["word"]
            entity_type = item["entity_group"]
            entities.append(
                analyzer_pb2.AnalyzeResponse.Entity(name=entity_name, type=entity_type)
            )

        self.text_data.entities.extend(entities)

    def analyze_sentiment(self):
        # Анализ тональности (sentiment-analysis)
        # Для больших текстов иногда берут только первые N символов/предложений
        sentiment_result = sentiment_pipeline(self.content[:3000])[0]

        # sentiment_result может выглядеть как {'label': '4 stars', 'score': 0.65} (для выбранной модели)
        # Сконвертируем в структуру analyzer_pb2.Sentiment
        label = sentiment_result["label"].lower()
        score = float(sentiment_result["score"])

        # Условно сопоставим label -> positive/negative/neutral
        # Пример: если label содержит "negative" -> negative=score
        #         если label содержит "positive" -> positive=score
        # Но т.к. в multi-class sentiment (1..5 stars) сложнее, сделаем упрощённо:
        if "1 star" in label or "2 star" in label:
            self.text_data.sentiment.negative = score
        elif "4 star" in label or "5 star" in label:
            self.text_data.sentiment.positive = score
        else:
            self.text_data.sentiment.neutral = score
