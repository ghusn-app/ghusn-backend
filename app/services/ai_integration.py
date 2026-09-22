from gradio_client import Client, handle_file

_client = None


def _get_client() -> Client:
    global _client

    if _client is None:
        _client = Client("Hala18/Ghusn-API")

    return _client


def analyze_plant_image(image_path: str) -> dict:
    client = _get_client()

    result = client.predict(
        image=handle_file(image_path),
        api_name="/predict_disease",
    )

    disease_name = result[0]
    confidence_score = float(result[1])

    # صورة ضبابية
    if confidence_score == 0.0 and "ضبابية" in disease_name:
        return {
            "status": "blurry",
            "message": disease_name,
            "disease_name": None,
            "confidence_score": 0.0,
            "is_confident": False,
        }

    # تشخيص منخفض الثقة
    if "التشخيص غير مؤكد" in disease_name:
        return {
            "status": "low_confidence",
            "message": disease_name,
            "disease_name": None,
            "confidence_score": confidence_score,
            "is_confident": False,
        }

    # تشخيص ناجح
    return {
        "status": "success",
        "message": None,
        "disease_name": disease_name,
        "confidence_score": confidence_score,
        "is_confident": True,
    }