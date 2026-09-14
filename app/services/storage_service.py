import os
import uuid
from fastapi import UploadFile
from supabase import create_client
from app.config import settings

UPLOAD_DIR = "app/uploads/diagnoses"
os.makedirs(UPLOAD_DIR, exist_ok=True)

_supabase_client = None


def _get_client():
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
    return _supabase_client


def save_diagnosis_image(file: UploadFile) -> str:
    """
    ترفع الصورة لـSupabase Storage وترجع رابط عام دائم لها.
    """
    client = _get_client()

    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"

    file_bytes = file.file.read()
    client.storage.from_(settings.SUPABASE_BUCKET).upload(
        unique_filename, file_bytes, {"content-type": file.content_type}
    )

    public_url = client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(unique_filename)
    return public_url

