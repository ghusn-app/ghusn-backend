import requests
from app.config import settings


def analyze_plant_image(image_path: str) -> dict:
    """
    يستدعي خدمة الذكاء الاصطناعي المستضافة (ghusn-ai) عبر HTTP،
    ويرجع النتيجة بنفس الشكل المتوقع من باقي الكود.
    """
    with open(image_path.lstrip("/"), "rb") as image_file:
        files = {"file": image_file}
        response = requests.post(
            f"{settings.AI_SERVICE_URL}/predict",
            files=files,
            timeout=30,
        )
    response.raise_for_status()
    result = response.json()

    return {
        "disease_name": result["predicted_class"],
        "confidence_score": result["confidence"],
    }