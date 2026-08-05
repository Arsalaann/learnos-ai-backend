from pathlib import Path

from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


ALLOWED_FILE_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


async def validate_upload(file: UploadFile) -> None:

    extension = Path(file.filename).suffix.lower()

    expected_content_type = ALLOWED_FILE_TYPES.get(extension)

    if expected_content_type is None:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF and DOCX files are allowed.",
        )

    if file.content_type != expected_content_type:
        raise HTTPException(
            status_code=400,
            detail="Invalid content type.",
        )

    # Validate file signature.
    if extension == ".pdf":

        header = await file.read(5)

        if header != b"%PDF-":
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file.",
            )

    elif extension == ".docx":

        header = await file.read(4)

        if header != b"PK\x03\x04":
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX file.",
            )

    await file.seek(0)

    # Validate file size.
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10 MB.",
        )

    await file.seek(0)