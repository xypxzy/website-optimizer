from fastapi import APIRouter
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
def analyze_url(url: str):
    # Подключаемся к парсеру
    with grpc.insecure_channel("parser_service:50051") as channel:
        parser_stub = ParserServiceStub(channel)
        parse_response = parser_stub.ParsePage(ParseRequest(url=url))
        parsed_data = MessageToDict(parse_response)

    # Получаем данные для анализа
    headers = parsed_data.get("headers", [])
    texts = parsed_data.get("texts", [])
    cta_buttons = parsed_data.get("ctaButtons", [])
    meta_tags = parsed_data.get("metaTags", [])

    # Анализируем через analyzer_service
    with grpc.insecure_channel("analyzer_service:50052") as channel:
        analyzer_stub = AnalyzerServiceStub(channel)
        analyze_response = analyzer_stub.AnalyzeContent(
            AnalyzeRequest(
                texts=texts,
                headers=headers,
                cta_buttons=cta_buttons,
                meta_tags=meta_tags,
            )
        )
        analyzed_result = MessageToDict(analyze_response)

    return {"parsed_data": parsed_data, "analyzed_data": analyzed_result}
