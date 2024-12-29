import logging
import grpc
from concurrent import futures
from proto import analyzer_pb2_grpc, analyzer_pb2
from app.services.aggregator import analyze_all


logger = logging.getLogger(__name__)


class AnalyzerServicer(analyzer_pb2_grpc.AnalyzerServiceServicer):
    """
    gRPC service for analyzing text content + SEO.
    """

    def __init__(self):
        logger.info("AnalyzerService initialized.")

    async def Analyze(self, request, context):
        content = request.content
        url = request.url
        correlation_id = request.correlation_id

        logger.info(
            f"Start analyzing content + SEO with correlation_id: {correlation_id}"
        )

        try:
            analyze_response = await analyze_all(content, url)
            analyze_response.correlation_id = correlation_id

            return analyze_response

        except Exception as e:
            logger.error(f"Error analyzing: {e}")
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)
            return analyzer_pb2.AnalyzeResponse()


async def serve_grpc():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    analyzer_pb2_grpc.add_AnalyzerServiceServicer_to_server(AnalyzerServicer(), server)
    server.add_insecure_port("[::]:50052")
    await server.start()
    logger.info("gRPC server started on port 50052.")
    await server.wait_for_termination()
