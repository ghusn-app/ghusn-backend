import random


def analyze_plant_image(image_path: str) -> dict:
    """
    Placeholder مؤقت لحد ما يجهز موديل الذكاء الاصطناعي الحقيقي.
    لاحقاً، تستبدلي محتوى هذه الدالة باستدعاء API/موديل زميلك،
    بشرط ترجع نفس الشكل بالضبط: {"disease_name": str, "confidence_score": float}
    """
    fake_diseases = ["Early Blight", "Late Blight", "Healthy", "Leaf Mold"]
    return {
        "disease_name": random.choice(fake_diseases),
        "confidence_score": round(random.uniform(0.4, 0.98), 2),
    }