from dataclasses import dataclass
from pydantic import BaseModel, Field

__all__ = [
    "RawSpan",
    "RawLine",
    "RawBlock",
    "ImageBlock",
    "ExtractionResult",
]


@dataclass(slots=True)
class RawSpan:
    text: str
    font: str
    size: float
    bbox: tuple[float, float, float, float]


@dataclass(slots=True)
class RawLine:
    page: int
    text: str
    left: float
    top: float


@dataclass(slots=True)
class RawBlock:
    page: int
    lines: list[RawLine]
    max_font_size: float
    left: float
    right: float
    top: float
    bottom: float


@dataclass(slots=True)
class ImageBlock:
    page: int
    path: str
    format: str


class ExtractionResult(BaseModel):
    texts: list[dict] = Field(default_factory=list)
    images: list[ImageBlock] = Field(default_factory=list)