import logging
import traceback
import grpc
from concurrent import futures
from app.services.text_analyzer import TextAnalyzerServicer
from proto import analyzer_pb2_grpc

logger = logging.getLogger(__name__)


def serve():
    """Starts the gRPC server to listen for incoming requests."""
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        analyzer_pb2_grpc.add_AnalyzerServiceServicer_to_server(
            TextAnalyzerServicer(), server
        )
        server.add_insecure_port("[::]:50052")
        logger.info("gRPC server is starting on port 50052.")
        server.start()
        server.wait_for_termination()
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting TextAnalyzerService.")
    serve()
