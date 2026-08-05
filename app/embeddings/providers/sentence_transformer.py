from sentence_transformers import SentenceTransformer


class SentenceTransformerProvider:

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name,local_files_only=True)

    def encode(self, texts: list[str]):
        return self.model.encode(
            texts,
            normalize_embeddings=True,
        )

    def prepare_passages(self, texts: list[str]) -> list[str]:
        return [f"passage: {text}" for text in texts]

    def prepare_query(self, text: str) -> str:
        return f"query: {text}"

    def count_tokens(self, text: str) -> int:
        encoded = self.model.tokenizer(
            text,
            add_special_tokens=True,
            truncation=False,
        )

        return len(encoded["input_ids"])

    def encode_tokens(self, text: str) -> list[int]:
        return self.model.tokenizer.encode(
            text,
            add_special_tokens=True,
        )

    def decode_tokens(self, tokens: list[int]) -> str:
        return self.model.tokenizer.decode(
            tokens,
            skip_special_tokens=True,
        )