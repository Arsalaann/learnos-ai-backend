from dataclasses import dataclass
from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@dataclass(slots=True)
class StoredFile:
    filename: str
    storage_path: str


async def save_file(file: UploadFile) -> StoredFile:
    extension = Path(file.filename).suffix
    stored_filename = f"{uuid.uuid4()}{extension}"

    destination = UPLOAD_DIR / stored_filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return StoredFile(filename=stored_filename, storage_path=str(destination))


def delete_file(storage_path: str) -> None:
    Path(storage_path).unlink(missing_ok=True)