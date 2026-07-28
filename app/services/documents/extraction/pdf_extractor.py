from pathlib import Path
from collections import defaultdict
import fitz
from pprint import pprint
from app.services.documents.extraction.models import *


SPACE_WIDTH = 4
Y_TOLERANCE = 2.0





def extract_images(pdf: fitz.Document, upload_directory: str) -> list[ImageBlock]:
    
    if upload_directory=='':  #this block can be removed after testing
        return []
    
    images: list[ImageBlock] = []

    images_directory = Path(upload_directory) / "artifacts" / "images"

    saved_images: dict[int, str] = {}
    image_counter = 1

    for page_number, page in enumerate(pdf, start=1):
        for image in page.get_images(full=True):
            xref = image[0]

            if xref in saved_images:
                image_path = saved_images[xref]

            else:
                extracted = pdf.extract_image(xref)

                extension = extracted["ext"]
                filename = f"image_{image_counter}.{extension}"
                image_path = images_directory / filename

                with image_path.open("wb") as file:
                    file.write(extracted["image"])

                saved_images[xref] = (str(image_path), extension)
                image_path, extension = saved_images[xref]
                image_counter += 1

            images.append(
                ImageBlock(
                    page=page_number,
                    path=str(image_path),
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

        y = round(line["spans"][0]["bbox"][1] / Y_TOLERANCE) * Y_TOLERANCE

        grouped[y].extend(line["spans"])

    normalized_lines: list[dict] = []

    for y in sorted(grouped.keys()):

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
    spans = [build_raw_span(span) for span in line["spans"]]

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

    text = "".join(text_parts).rstrip()

    left = min(span.bbox[0] for span in spans)
    top = min(span.bbox[1] for span in spans)

    return RawLine(
        page=page,
        text=text,
        left=left,
        top=top,
    )
def build_raw_lines(pdf: fitz.Document) -> list[RawLine]:
    raw_lines: list[RawLine] = []

    for page_number, page in enumerate(pdf, start=1):
        page_dict = page.get_text("dict")

        for block in page_dict["blocks"]:

            if block["type"] != 0:
                continue

            normalized_lines = normalize_lines(block)

            for line in normalized_lines:

                raw_line = build_raw_line(
                    page=page_number,
                    line=line,
                )

                if raw_line.text:
                    raw_lines.append(raw_line)

    return raw_lines
def build_document_pages(raw_lines: list[RawLine]) -> list[dict]:
    if not raw_lines:
        return []

    pages: list[dict] = []

    current_page = raw_lines[0].page
    current_lines: list[str] = []

    for line in raw_lines:

        if line.page != current_page:

            pages.append(
                {
                    "page": current_page,
                    "text": "\n".join(current_lines),
                }
            )

            current_page = line.page
            current_lines = []

        current_lines.append(line.text)

    pages.append(
        {
            "page": current_page,
            "text": "\n".join(current_lines),
        }
    )

    return pages


def extract_pdf(file_path: Path, upload_directory: str) -> ExtractionResult:
    with fitz.open(file_path) as pdf:
        raw_lines = build_raw_lines(pdf)
        images = extract_images(pdf, upload_directory)

    return ExtractionResult(
        texts=build_document_pages(raw_lines),
        images=images,
    )


if __name__ == "__main__":
    e=extract_pdf('/home/luser/session_mastery_summary.pdf',"")

    for x in e.texts:
        pprint(x)
