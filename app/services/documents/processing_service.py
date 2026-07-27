from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.document import DocumentText
from app.services.documents.text_extraction import extract_text_pages


def process_document(document: Document, db: Session) -> None:
    try:
        extracted_pages = extract_text_pages(document.storage_path)

        content = {
            "pages": [
                {
                    "page": page.page_number,
                    "text": page.text,
                }
                for page in extracted_pages
            ]
        }

        document_content = DocumentText(document_id=document.id,content=content,)
        db.add(document_content)
        document.status = DocumentStatus.COMPLETED
        db.commit()
    except Exception:
        db.rollback()
        document.status = DocumentStatus.FAILED
        db.commit()