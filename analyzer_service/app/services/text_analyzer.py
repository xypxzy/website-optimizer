from proto import analyzer_pb2_grpc, analyzer_pb2


class AnalyzerServicer(analyzer_pb2_grpc.AnalyzerServiceServicer):
    def AnalyzeContent(self, request, context):
        # Здесь можно добавить любую логику анализа, NLP, генерации рекомендаций.
        # Пока просто возвращаем "заглушку".

        sentiment = "neutral"
        keyword_suggestions = ["improve", "optimize", "conversion"]
        improved_headers = [h + " (Improved)" for h in request.headers]
        improved_cta = [c + " -> Click here!" for c in request.cta_buttons]
        seo_recommendations = ["Add more keywords", "Improve meta description"]

        return analyzer_pb2.AnalyzeResponse(
            sentiment=sentiment,
            keyword_suggestions=keyword_suggestions,
            improved_headers=improved_headers,
            improved_cta=improved_cta,
            seo_recommendations=seo_recommendations,
        )
