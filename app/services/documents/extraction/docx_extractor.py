from pathlib import Path

from docx import Document as DocxDocument
from docx.document import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.services.documents.extraction.models import (
    ExtractedBlock,
    ExtractionResult,
    ImageBlock,
)


def iter_block_items(document: Document):
    body = document.element.body

    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def extract_images(
    document: Document,
    upload_directory: str,
) -> list[ImageBlock]:

    if not upload_directory:
        return []

    images_directory = Path(upload_directory) / "artifacts" / "images"
    images_directory.mkdir(parents=True, exist_ok=True)

    images: list[ImageBlock] = []
    saved_images: dict[str, tuple[str, str]] = {}
    image_counter = 1

    for relationship in document.part.rels.values():

        if relationship.reltype != (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
        ):
            continue

        image_part = relationship.target_part
        image_key = str(image_part.partname)

        if image_key in saved_images:
            image_path, extension = saved_images[image_key]

        else:
            extension = image_part.content_type.split("/")[-1]

            filename = f"image_{image_counter}.{extension}"
            image_path = images_directory / filename

            with image_path.open("wb") as file:
                file.write(image_part.blob)

            image_path = str(image_path)

            saved_images[image_key] = (
                image_path,
                extension,
            )

            image_counter += 1

        images.append(
            ImageBlock(
                page=0,
                path=image_path,
                format=extension,
            )
        )

    return images


def extract_table_text(table: Table) -> str:
    rows: list[str] = []

    for row in table.rows:
        cells = [
            cell.text.strip()
            for cell in row.cells
        ]

        rows.append(" | ".join(cells))

    return "\n".join(rows)


def extract_docx(
    file_path: Path,
    upload_directory: str,
) -> ExtractionResult:

    document = DocxDocument(file_path)

    blocks: list[ExtractedBlock] = []

    for index, block in enumerate(iter_block_items(document)):

        if isinstance(block, Paragraph):

            text = block.text.strip()

            if not text:
                continue

            block_type = (
                "heading"
                if block.style.name.startswith("Heading")
                else "paragraph"
            )

        elif isinstance(block, Table):

            text = extract_table_text(block).strip()

            if not text:
                continue

            block_type = "table"

        else:
            continue

        blocks.append(
            ExtractedBlock(
                index=index,
                type=block_type,
                text=text,
                source_type="block",
                source_start=index,
                source_end=index,
            )
        )

    images = extract_images(
        document=document,
        upload_directory=upload_directory,
    )

    return ExtractionResult(
        blocks=blocks,
        images=images,
    )