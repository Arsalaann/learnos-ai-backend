from app.services.documents.extraction.pdf_extractor import extract_pdf
from app.services.documents.extraction.models import ExtractionResult


EXTRACTORS = {
    "application/pdf": extract_pdf
}

def extract_document(content_type:str,storage_path: str,upload_directory:str) -> ExtractionResult:
    extractor = EXTRACTORS.get(content_type)
    if extractor is None:
        raise ValueError(f"Unsupported content type: {content_type}")
    return extractor(storage_path, upload_directory)

    