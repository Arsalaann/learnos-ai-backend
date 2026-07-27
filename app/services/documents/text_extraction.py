from pathlib import Path

import fitz

from app.services.documents.processing_models import ExtractedPage


def extract_text_pages(file_path: Path) -> list[ExtractedPage]:
    extracted_pages: list[ExtractedPage] = []

    with fitz.open(file_path) as pdf:
        for index, page in enumerate(pdf):
            extracted_pages.append(
                ExtractedPage(
                    page_number=index + 1,
                    text=page.get_text(),
                )
            )

    return extracted_pages