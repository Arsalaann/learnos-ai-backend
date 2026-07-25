from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_file(file: UploadFile) -> Path:
    extension = Path(file.filename).suffix
    stored_filename = f"{uuid.uuid4()}{extension}"

    destination = UPLOAD_DIR / stored_filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return destination


def delete_file(path: Path) -> None:
    path.unlink(missing_ok=True)