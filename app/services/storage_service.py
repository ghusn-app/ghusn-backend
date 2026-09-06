import os
import uuid
from fastapi import UploadFile

UPLOAD_DIR = "app/uploads/diagnoses"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_diagnosis_image(file: UploadFile) -> str:
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)

    return f"/{file_path}"