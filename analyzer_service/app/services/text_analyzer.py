import logging
import grpc
import psycopg2
import pika
import os
import traceback
from proto import analyzer_pb2_grpc, analyzer_pb2


logger = logging.getLogger(__name__)


class TextAnalyzerServicer(analyzer_pb2_grpc.AnalyzerServiceServicer):
    """
    gRPC service for analyzing text content from a BeautifulSoup object.
    """

    def __init__(self):
        """Initialize NLP tools and logger"""
        self.db_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        self.db_cursor = self.db_conn.cursor()
        self.rabbitmq_connection = pika.BlockingConnection(
            pika.URLParameters(os.getenv("RABBITMQ_URL"))
        )
        self.rabbitmq_channel = self.rabbitmq_connection.channel()
        self.rabbitmq_channel.queue_declare(queue="analyze_queue")

    def Analyze(self, request, context):
        """Handles gRPC request to analyze the content of a web page."""
        content = request.content
        try:
            tokens = content.split()
            frequency_distribution = {word: tokens.count(word) for word in set(tokens)}

            self.save_to_db(content, frequency_distribution)

            logger.info("Analysis completed successfully.")

            return analyzer_pb2.AnalyzeResponse(
                frequency_distribution=frequency_distribution
            )
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            traceback.print_exc()
            context.set_details("Internal server error.")
            context.set_code(grpc.StatusCode.INTERNAL)
            return analyzer_pb2.AnalyzeResponse()

    def save_to_db(self, content, freq_dist):
        try:
            query = "INSERT INTO analysis_results (content, frequency_distribution) VALUES (%s, %s)"
            self.db_cursor.execute(query, (content, freq_dist))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error saving analysis results to the database: {e}")
