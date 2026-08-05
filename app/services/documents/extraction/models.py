from dataclasses import dataclass

from pydantic import BaseModel, Field

__all__ = [
    "ExtractedBlock",
    "ExtractionResult",
    "ImageBlock",
    "RawBlock",
    "RawLine",
    "RawSpan",
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


class ExtractedBlock(BaseModel):
    index: int
    type: str
    text: str
    source_type: str
    source_start: int | None = None
    source_end: int | None = None


@dataclass(slots=True)
class ImageBlock:
    page: int
    path: str
    format: str


class ExtractionResult(BaseModel):
    blocks: list[ExtractedBlock] = Field(default_factory=list)
    images: list[ImageBlock] = Field(default_factory=list)