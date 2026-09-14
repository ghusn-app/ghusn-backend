import uuid

from supabase import create_client
from app.config import settings


_supabase_client = None


def _get_client():
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SECRET_KEY
        )

    return _supabase_client


def save_diagnosis_image(
    image_bytes: bytes,
    original_filename: str,
    content_type: str,
    farmer_id: int
) -> str:
    """
    ترفع صورة التشخيص الناجح فقط إلى Supabase Storage
    وترجع Public URL دائم للصورة.
    """

    client = _get_client()

    # استخراج امتداد الصورة
    file_extension = original_filename.rsplit(".", 1)[-1].lower()

    # إنشاء اسم فريد
    unique_filename = f"{uuid.uuid4()}.{file_extension}"

    # تنظيم الصور حسب المزارع
    storage_path = (
        f"farmers/{farmer_id}/diagnoses/{unique_filename}"
    )

    # رفع الصورة
    client.storage.from_(
        settings.SUPABASE_BUCKET
    ).upload(
        path=storage_path,
        file=image_bytes,
        file_options={
            "content-type": content_type,
            "upsert": "false",
        }
    )

    # بما أن Bucket Public
    public_url = (
        client.storage
        .from_(settings.SUPABASE_BUCKET)
        .get_public_url(storage_path)
    )

    return public_url