from dataclasses import dataclass

@dataclass(slots=True)
class ExtractedPage:
    page_number: int
    text: str