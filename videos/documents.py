from elasticsearch_dsl import Document, Text


class VideoDocument(Document):
    title = Text()
    description = Text()

    class Index:
        name = 'video_index'
