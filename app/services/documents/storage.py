from dataclasses import dataclass
from pathlib import Path
import shutil
import uuid

from fastapi import UploadFile


UPLOAD_DIR = Path("uploads")


# uploads/
# └── users/
#     └── {user_id}/
#         └── {upload_id}/
#             ├── source/
#             │   └── <uploaded file>
#             ├── artifacts/
#             │   ├── images/
#             │   ├── tables/
#             │   └── code/
#             └── temp/


@dataclass(slots=True)
class StoredFile:
    storage_path: str
    upload_directory: str


async def save_file(file: UploadFile, user_id: int) -> StoredFile:
    upload_id = str(uuid.uuid4())

    upload_directory = UPLOAD_DIR / "users" / str(user_id) / upload_id

    source_directory = upload_directory / "source"
    artifacts_directory = upload_directory / "artifacts"

    (artifacts_directory / "images").mkdir(parents=True, exist_ok=True)
    (artifacts_directory / "tables").mkdir(exist_ok=True)
    (artifacts_directory / "code").mkdir(exist_ok=True)
    (upload_directory / "temp").mkdir(exist_ok=True)
    source_directory.mkdir(exist_ok=True)

    destination = source_directory / file.filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return StoredFile(
        storage_path=str(destination),
        upload_directory=str(upload_directory),
    )


def delete_upload(upload_directory: str) -> None:
    shutil.rmtree(upload_directory, ignore_errors=True)