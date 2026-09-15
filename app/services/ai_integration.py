from gradio_client import Client, handle_file

_client = None


def _get_client() -> Client:
    """
    ينشئ اتصال Gradio Client مرة وحدة بس، ويعيد استخدامه بكل استدعاء لاحق
    (إنشاء Client جديد بكل طلب مكلف وبطيء، أفضل نحتفظ بنسخة واحدة).
    """
    global _client
    if _client is None:
        _client = Client("Hala18/Ghusn-API")
    return _client


def analyze_plant_image(image_path: str) -> dict:
    """
    يستدعي موديل الذكاء الاصطناعي المستضاف على Hugging Face عبر Gradio Client،
    ويرجع النتيجة بالشكل الموحد المستخدم بباقي الكود.
    """
    client = _get_client()

    result = client.predict(
        image=handle_file(image_path),
        api_name="/predict_disease",
    )

    print("===== AI RESULT =====")
    print("image_path:", image_path)
    print("result:", result)
    print("=====================")

    

    disease_name = result[0]
    confidence_score = float(result[1])

    return {
        "disease_name": disease_name,
        "confidence_score": confidence_score,
        "is_confident": confidence_score >= 0.70,
    }
   # return {
    #    "disease_name": result["predicted_class"],
    #    "confidence_score": result["confidence"],
    #    "is_confident": result["is_confident"],
    #}