import os
from dataclasses import dataclass

import cv2

TARGET_BUCKETS = {
    "people": {"person"},
    "cat": {"cat"},
}

BUCKET_PRIORITY = ["cat", "people"]
BOX_COLOR = (50, 180, 255)
TEXT_COLOR = (255, 255, 255)
LABEL_BG_COLOR = (30, 30, 30)


@dataclass(frozen=True)
class Detection:
    label: str
    score: float
    bbox: tuple[int, int, int, int]


def normalize_label(label):
    return (label or "").strip().lower()


def bucket_for_label(label, bucket_map=None):
    normalized_label = normalize_label(label)
    lookup = bucket_map or TARGET_BUCKETS
    for bucket, labels in lookup.items():
        if normalized_label in labels:
            return bucket
    return None


def bucket_detections(detections, bucket_map=None):
    buckets = {}
    for detection in detections:
        bucket = bucket_for_label(detection.label, bucket_map=bucket_map)
        if bucket is None:
            continue
        buckets.setdefault(bucket, []).append(detection)
    return buckets


def prioritized_buckets(buckets):
    return [bucket for bucket in BUCKET_PRIORITY if bucket in buckets]


def summarize_detections(detections):
    buckets = bucket_detections(detections)
    if not buckets:
        return "No target matches"

    parts = []
    for bucket in prioritized_buckets(buckets):
        labels = ", ".join(sorted({detection.label for detection in buckets[bucket]}))
        parts.append(f"{bucket}: {labels}")
    return " | ".join(parts)


def draw_detections(image, detections, summary_text=None):
    for detection in detections:
        x, y, width, height = detection.bbox
        start_point = (x, y)
        end_point = (x + width, y + height)
        cv2.rectangle(image, start_point, end_point, BOX_COLOR, 2)

        label = f"{detection.label} ({detection.score:.2f})"
        text_origin = (x + 4, max(20, y - 8))
        cv2.putText(image, label, text_origin, cv2.FONT_HERSHEY_SIMPLEX, 0.5, BOX_COLOR, 2)

    if summary_text:
        cv2.rectangle(image, (10, 10), (min(image.shape[1] - 10, 630), 40), LABEL_BG_COLOR, -1)
        cv2.putText(image, summary_text, (18, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2)

    return image


class TFLiteObjectDetector:
    def __init__(self, model_path, num_threads=2, enable_edgetpu=False, max_results=5, score_threshold=0.35):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"TFLite model not found at {model_path}")

        try:
            from tflite_support.task import core
            from tflite_support.task import processor
            from tflite_support.task import vision
        except ImportError as exc:
            raise RuntimeError(
                "tflite-support is not installed. Install tflite/requirements.txt for independent mode."
            ) from exc

        base_options = core.BaseOptions(
            file_name=model_path,
            use_coral=enable_edgetpu,
            num_threads=num_threads,
        )
        detection_options = processor.DetectionOptions(
            max_results=max_results,
            score_threshold=score_threshold,
        )
        options = vision.ObjectDetectorOptions(
            base_options=base_options,
            detection_options=detection_options,
        )

        self._vision = vision
        self._detector = vision.ObjectDetector.create_from_options(options)

    def detect(self, image):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_tensor = self._vision.TensorImage.create_from_array(rgb_image)
        detection_result = self._detector.detect(input_tensor)

        detections = []
        for detection in detection_result.detections:
            category = detection.categories[0]
            bbox = detection.bounding_box
            detections.append(
                Detection(
                    label=normalize_label(category.category_name),
                    score=float(category.score),
                    bbox=(bbox.origin_x, bbox.origin_y, bbox.width, bbox.height),
                )
            )

        return detections
