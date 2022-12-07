from app.models.news import News, NewsProcessingState


class NewsImporterBase:
    def __init__(self, source) -> None:
        super().__init__()
        self.source = source
        if not self.source:
            raise ValueError("unknown source %s" % self.source)

    def fetch_documents(self):
        raise NotImplementedError("Implement in subclass")

    def clean_document(self, url):
        raise NotImplementedError("Implement in subclass")

    def clean_documents(self):
        queryset = (
            News.objects(
                source=self.source, processing_state=NewsProcessingState.IMPORTED.value
            )
            .limit(1000)
            .only("url")
        )
        for news in queryset:
            self.clean_document(news.url)
