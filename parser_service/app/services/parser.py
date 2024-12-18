import requests
from bs4 import BeautifulSoup

from proto import parser_pb2, parser_pb2_grpc


class ParserServicer(parser_pb2_grpc.ParserServiceServicer):
    def ParsePage(self, request, context):
        url = request.url
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        headers = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3"])]
        cta_buttons = [a.get_text(strip=True) for a in soup.find_all("a", class_="cta")]
        meta_tags = [meta.get("content", "") for meta in soup.find_all("meta")]
        texts = [p.get_text(strip=True) for p in soup.find_all("p")]

        return parser_pb2.ParseResponse(
            headers=headers, cta_buttons=cta_buttons, meta_tags=meta_tags, texts=texts
        )
