"""
Image Classification Utility — ResNet50 Classifier
===================================================

Modul ini bertanggung jawab memuat model CNN ResNet50 hasil training
dan melakukan inferensi terhadap gambar lembar jawaban / dokumen.
"""

import os
import json
import numpy as np
from typing import Dict, Any, Union, Optional
from PIL import Image

# Global cache untuk model agar tidak load berulang kali pada setiap request
_MODEL_CACHE = None
_CLASS_NAMES_CACHE = None


def get_model_and_classes(model_path: Optional[str] = None, output_dir: Optional[str] = None):
    """
    Memuat model dan class mapping (dengan lazy-loading singleton).
    """
    global _MODEL_CACHE, _CLASS_NAMES_CACHE

    if _MODEL_CACHE is not None and _CLASS_NAMES_CACHE is not None:
        return _MODEL_CACHE, _CLASS_NAMES_CACHE

    base_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if output_dir is None:
        output_dir = os.path.join(base_backend_dir, "model_output")

    if model_path is None:
        model_path = os.path.join(output_dir, "best_model.keras")
        if not os.path.exists(model_path):
            model_path = os.path.join(output_dir, "final_model.keras")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model klasifikasi belum ditemukan di: {model_path}. Silakan jalankan train_model.py terlebih dahulu.")

    # Load class names
    indices_path = os.path.join(output_dir, "class_indices.json")
    if os.path.exists(indices_path):
        with open(indices_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        class_names = {int(v): k for k, v in mapping.items()}
    else:
        class_names = {0: "terpilih", 1: "tidak_terpilih"}

    import tensorflow as tf
    model = tf.keras.models.load_model(model_path)

    _MODEL_CACHE = model
    _CLASS_NAMES_CACHE = class_names
    return _MODEL_CACHE, _CLASS_NAMES_CACHE


def classify_image(
    image_input: Union[str, Image.Image, Any],
    target_size: tuple = (224, 224),
    model_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Melakukan klasifikasi gambar menggunakan model ResNet50.

    Args:
        image_input : File path (str), PIL.Image, atau FileStorage dari Flask.
        target_size : Ukuran input model (default: 224x224).
        model_path  : Path khusus ke file model .keras (opsional).

    Returns:
        Dict: {
            "prediction": "terpilih" | "tidak_terpilih",
            "class_id": int (0 / 1),
            "confidence": float (0.0 - 1.0),
            "probability_raw": float
        }
    """
    from tensorflow.keras.applications.resnet50 import preprocess_input

    model, class_names = get_model_and_classes(model_path=model_path)

    # Preprocessing Image ke PIL Image
    if isinstance(image_input, str):
        img = Image.open(image_input)
    elif isinstance(image_input, Image.Image):
        img = image_input
    elif hasattr(image_input, 'read'):  # FileStorage / stream
        img = Image.open(image_input)
    else:
        raise ValueError(f"Tipe input gambar tidak didukung: {type(image_input)}")

    # Pastikan format RGB dan resize
    img = img.convert("RGB").resize(target_size)
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)  # Shape (1, 224, 224, 3)
    img_array = preprocess_input(img_array)

    # Prediksi menggunakan model
    raw_pred = model.predict(img_array, verbose=0)
    prob = float(raw_pred[0][0])

    class_id = 1 if prob >= 0.5 else 0
    pred_label = class_names.get(class_id, f"Class_{class_id}")
    confidence = prob if class_id == 1 else (1.0 - prob)

    return {
        "prediction": pred_label,
        "class_id": class_id,
        "confidence": round(confidence, 4),
        "probability_raw": round(prob, 4)
    }


def predict_batch_crops(
    crop_images: list,
    target_size: tuple = (224, 224),
    model_path: Optional[str] = None
) -> list:
    """
    Melakukan prediksi batch untuk sekelompok crop gambar sekaligus.
    Lebih efisien daripada classify_image berulang karena model.predict
    dijalankan hanya sekali untuk seluruh batch.

    Args:
        crop_images : List gambar (PIL.Image, numpy array BGR, atau path string).
        target_size : Ukuran input model (default: 224x224).
        model_path  : Path khusus ke file model .keras (opsional).

    Returns:
        List dict per gambar:
        [{"prediction": str, "class_id": int, "confidence": float, "probability_raw": float}, ...]
    """
    from tensorflow.keras.applications.resnet50 import preprocess_input

    if not crop_images:
        return []

    model, class_names = get_model_and_classes(model_path=model_path)

    batch_arrays = []
    for item in crop_images:
        if isinstance(item, str):
            pil_img = Image.open(item)
        elif isinstance(item, Image.Image):
            pil_img = item
        elif isinstance(item, np.ndarray):
            # OpenCV BGR -> PIL RGB
            import cv2
            rgb = cv2.cvtColor(item, cv2.COLOR_BGR2RGB) if len(item.shape) == 3 else item
            pil_img = Image.fromarray(rgb)
        else:
            raise ValueError(f"Tipe item tidak didukung: {type(item)}")

        pil_img = pil_img.convert("RGB").resize(target_size)
        arr = np.array(pil_img, dtype=np.float32)
        batch_arrays.append(arr)

    batch = np.stack(batch_arrays, axis=0)  # (N, H, W, 3)
    batch = preprocess_input(batch)

    raw_preds = model.predict(batch, verbose=0)  # (N, 1)

    results = []
    for prob_raw in raw_preds:
        prob = float(prob_raw[0])
        class_id = 1 if prob >= 0.5 else 0
        pred_label = class_names.get(class_id, f"Class_{class_id}")
        confidence = prob if class_id == 1 else (1.0 - prob)
        results.append({
            "prediction": pred_label,
            "class_id": class_id,
            "confidence": round(confidence, 4),
            "probability_raw": round(prob, 4)
        })

    return results
