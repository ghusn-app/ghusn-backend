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

    # الصورة ضبابية
    if confidence_score == 0.0 and "ضبابية" in disease_name:
        return {
            "status": "blurry",
            "message": disease_name,
            "disease_name": None,
            "confidence_score": 0.0,
            "is_confident": False,
        }

    return {
        "status": "success",
        "message": None,
        "disease_name": disease_name,
        "confidence_score": confidence_score,
        "is_confident": confidence_score >= 0.85,
    }