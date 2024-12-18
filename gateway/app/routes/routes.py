from fastapi import APIRouter, Query
import grpc
from google.protobuf.json_format import MessageToDict

from proto.parser_pb2_grpc import ParserServiceStub
from proto.parser_pb2 import ParseRequest
from proto.analyzer_pb2_grpc import AnalyzerServiceStub
from proto.analyzer_pb2 import AnalyzeRequest

router = APIRouter()


@router.get("/healthcheck")
def healthcheck():
    return {"status": "ok"}


@router.post("/analyze_url")
def analyze_url(url: str = Query(..., description="The URL to analyze")):
    # Connect to the parser service
    with grpc.insecure_channel("parser_service:50051") as channel:
        parser_stub = ParserServiceStub(channel)
        parse_response = parser_stub.Parse(ParseRequest(url=url))
        parsed_data = MessageToDict(parse_response)

    # Analyze the parsed content through analyzer_service
    with grpc.insecure_channel("analyzer_service:50052") as channel:
        analyzer_stub = AnalyzerServiceStub(channel)
        analyze_response = analyzer_stub.Analyze(
            AnalyzeRequest(content=parsed_data.get("content", ""))
        )
        analyzed_result = MessageToDict(analyze_response)

    return {"parsed_data": parsed_data, "analyzed_data": analyzed_result}
