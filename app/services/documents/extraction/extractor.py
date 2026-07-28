from app.models.document import Document
from app.services.documents.extraction.pdf_extractor import extract_pdf
from app.services.documents.extraction.models import ExtractionResult


EXTRACTORS = {
    "application/pdf": extract_pdf
}

def extract_document(document: Document,upload_directory:str) -> ExtractionResult:
    try:
        extractor = EXTRACTORS[document.content_type]
    except KeyError:
        raise ValueError(f"Unsupported content type: {document.content_type}")

    return extractor(document.storage_path,upload_directory)

    