from collections import defaultdict
from pathlib import Path
from pprint import pprint

import fitz

from app.services.documents.constants import SPACE_WIDTH, Y_TOLERANCE
from app.services.documents.extraction.models import *


def extract_images(pdf: fitz.Document, upload_directory: str) -> list[ImageBlock]:

    if not upload_directory:
        return []

    images_directory = Path(upload_directory) / "artifacts" / "images"
    images_directory.mkdir(parents=True, exist_ok=True)

    images: list[ImageBlock] = []

    saved_images: dict[int, tuple[str, str]] = {}
    image_counter = 1

    for page_number, page in enumerate(pdf, start=1):

        for image in page.get_images(full=True):

            xref = image[0]

            if xref in saved_images:
                image_path, extension = saved_images[xref]

            else:
                extracted = pdf.extract_image(xref)

                extension = extracted["ext"]
                filename = f"image_{image_counter}.{extension}"
                image_path = images_directory / filename

                with image_path.open("wb") as file:
                    file.write(extracted["image"])

                image_path = str(image_path)

                saved_images[xref] = (
                    image_path,
                    extension,
                )

                image_counter += 1

            images.append(
                ImageBlock(
                    page=page_number,
                    path=image_path,
                    format=extension,
                )
            )

    return images


def build_raw_span(span: dict) -> RawSpan:

    return RawSpan(
        text=span["text"],
        font=span["font"],
        size=span["size"],
        bbox=span["bbox"],
    )


def normalize_lines(block: dict) -> list[dict]:

    grouped: dict[float, list[dict]] = defaultdict(list)

    for line in block["lines"]:

        if not line["spans"]:
            continue

        y = round(
            line["spans"][0]["bbox"][1] / Y_TOLERANCE
        ) * Y_TOLERANCE

        grouped[y].extend(line["spans"])

    normalized_lines: list[dict] = []

    for y in sorted(grouped):

        spans = sorted(
            grouped[y],
            key=lambda span: span["bbox"][0],
        )

        normalized_lines.append(
            {
                "spans": spans,
            }
        )

    return normalized_lines


def build_raw_line(page: int, line: dict) -> RawLine:

    spans = [
        build_raw_span(span)
        for span in line["spans"]
    ]

    if not spans:
        raise ValueError("Line contains no spans.")

    text_parts: list[str] = []
    previous_right: float | None = None

    for span in spans:

        if previous_right is not None:

            gap = span.bbox[0] - previous_right

            if gap > SPACE_WIDTH:
                text_parts.append(
                    " " * int(gap // SPACE_WIDTH)
                )

        text_parts.append(span.text)

        previous_right = span.bbox[2]

    text = "".join(text_parts).strip()

    left = min(
        span.bbox[0]
        for span in spans
    )

    top = min(
        span.bbox[1]
        for span in spans
    )

    return RawLine(
        page=page,
        text=text,
        left=left,
        top=top,
    )


def build_raw_blocks(pdf: fitz.Document) -> list[RawBlock]:

    raw_blocks: list[RawBlock] = []

    for page_number, page in enumerate(pdf, start=1):

        page_dict = page.get_text("dict")

        for block in page_dict["blocks"]:

            if block["type"] != 0:
                continue

            normalized_lines = normalize_lines(block)

            raw_lines: list[RawLine] = []

            for line in normalized_lines:

                raw_line = build_raw_line(
                    page=page_number,
                    line=line,
                )

                if raw_line.text:
                    raw_lines.append(raw_line)

            if not raw_lines:
                continue

            spans = [
                build_raw_span(span)
                for line in normalized_lines
                for span in line["spans"]
            ]

            if not spans:
                continue

            raw_blocks.append(
                RawBlock(
                    page=page_number,
                    lines=raw_lines,
                    max_font_size=max(
                        span.size
                        for span in spans
                    ),
                    left=min(
                        span.bbox[0]
                        for span in spans
                    ),
                    right=max(
                        span.bbox[2]
                        for span in spans
                    ),
                    top=min(
                        span.bbox[1]
                        for span in spans
                    ),
                    bottom=max(
                        span.bbox[3]
                        for span in spans
                    ),
                )
            )

    return raw_blocks





def classify_block(
    block: RawBlock,
    body_font_size: float,
) -> str:

    text = " ".join(
        line.text
        for line in block.lines
    ).strip()

    if not text:
        return "unknown"

    if block.max_font_size > body_font_size * 1.25:
        return "heading"

    return "paragraph"





def estimate_body_font_size(
    blocks: list[RawBlock],
) -> float:

    if not blocks:
        return 0.0

    font_sizes = [
        block.max_font_size
        for block in blocks
    ]

    font_sizes.sort()

    return font_sizes[len(font_sizes) // 2]






def build_extracted_blocks(
    raw_blocks: list[RawBlock],
) -> list[ExtractedBlock]:

    if not raw_blocks:
        return []

    extracted_blocks: list[ExtractedBlock] = []

    current_page = raw_blocks[0].page
    page_blocks: list[RawBlock] = []

    pages: list[list[RawBlock]] = []

    for block in raw_blocks:

        if block.page != current_page:

            pages.append(page_blocks)

            current_page = block.page
            page_blocks = []

        page_blocks.append(block)

    if page_blocks:
        pages.append(page_blocks)

    index = 0

    for page_blocks in pages:

        body_font_size = estimate_body_font_size(
            page_blocks
        )

        for block in page_blocks:

            text = "\n".join(
                line.text
                for line in block.lines
            ).strip()

            if not text:
                continue

            block_type = classify_block(
                block,
                body_font_size,
            )

            extracted_blocks.append(
                ExtractedBlock(
                    index=index,
                    type=block_type,
                    text=text,
                    source_type="page",
                    source_start=block.page,
                    source_end=block.page,
                )
            )

            index += 1

    return extracted_blocks






def extract_pdf(
    file_path: Path,
    upload_directory: str,
) -> ExtractionResult:

    with fitz.open(file_path) as pdf:

        raw_blocks = build_raw_blocks(pdf)

        images = extract_images(
            pdf,
            upload_directory,
        )

    return ExtractionResult(
        blocks=build_extracted_blocks(
            raw_blocks
        ),
        images=images,
    )
    
    
    
if __name__ == "__main__":
    e=extract_pdf('/home/luser/session_mastery_summary.pdf',"")

    for x in e.texts:
        pprint(x)
