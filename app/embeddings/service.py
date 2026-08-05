from app.embeddings.providers.sentence_transformer import SentenceTransformerProvider


class EmbeddingService:

    def __init__(self, provider: SentenceTransformerProvider):
        self.provider = provider

    @property
    def model_name(self) -> str:
        return self.provider.model_name

    def encode(self, texts: list[str]):
        return self.provider.encode(texts)

    def prepare_passages(self, texts: list[str]) -> list[str]:
        return self.provider.prepare_passages(texts)

    def prepare_query(self, text: str) -> str:
        return self.provider.prepare_query(text)

    def count_tokens(self, text: str) -> int:
        return self.provider.count_tokens(text)

    def encode_tokens(self, text: str) -> list[int]:
        return self.provider.encode_tokens(text)

    def decode_tokens(self, tokens: list[int]) -> str:
        return self.provider.decode_tokens(tokens)