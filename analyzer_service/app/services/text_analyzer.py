import logging
import grpc
from proto import analyzer_pb2_grpc, analyzer_pb2

logger = logging.getLogger(__name__)


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
            words = content.lower().split()
            frequency_distribution = {}
            for word in words:
                frequency_distribution[word] = frequency_distribution.get(word, 0) + 1

            entities = []

            analyze_response = analyzer_pb2.AnalyzeResponse(
                correlation_id=correlation_id,
                frequency_distribution=frequency_distribution,
                entities=entities,
            )

            logger.info("Analysis completed successfully.")

            return analyze_response
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return analyzer_pb2.AnalyzeResponse()
