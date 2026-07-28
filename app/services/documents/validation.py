from pathlib import Path

from fastapi import HTTPException, UploadFile


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def validate_upload(file: UploadFile) -> None:
    # 1. Validate extension
    if Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    # 2. Validate MIME type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Invalid content type.",
        )

    # 3. Validate file signature (magic bytes)
    header = await file.read(5)

    if header != b"%PDF-":
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file.",
        )

    # Reset pointer after reading header
    await file.seek(0)

    # 4. Validate file size
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10 MB.",
        )

    # Reset pointer again so StorageService can save the file
    await file.seek(0)