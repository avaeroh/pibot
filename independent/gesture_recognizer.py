from dataclasses import dataclass

import cv2

from independent.detector import Detection

GESTURE_BUCKETS = {
    "thumbs_up": {"thumbs_up"},
    "open_palm": {"open_palm"},
}

THUMB_TIP = 4
THUMB_IP = 3
THUMB_MCP = 2
INDEX_TIP = 8
INDEX_PIP = 6
MIDDLE_TIP = 12
MIDDLE_PIP = 10
RING_TIP = 16
RING_PIP = 14
PINKY_TIP = 20
PINKY_PIP = 18


@dataclass(frozen=True)
class HandDetection:
    label: str
    bbox: tuple[int, int, int, int]


def _finger_is_extended(landmarks, tip_index, pip_index):
    return landmarks[tip_index].y < landmarks[pip_index].y


def _thumb_is_extended(landmarks, handedness_label):
    thumb_tip = landmarks[THUMB_TIP]
    thumb_ip = landmarks[THUMB_IP]
    thumb_mcp = landmarks[THUMB_MCP]
    horizontal_extended = thumb_tip.x > thumb_ip.x if handedness_label == "Left" else thumb_tip.x < thumb_ip.x
    vertical_upright = thumb_tip.y < thumb_ip.y < thumb_mcp.y
    return horizontal_extended and vertical_upright


def classify_hand_gesture(landmarks, handedness_label):
    thumb_extended = _thumb_is_extended(landmarks, handedness_label)
    index_extended = _finger_is_extended(landmarks, INDEX_TIP, INDEX_PIP)
    middle_extended = _finger_is_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP)
    ring_extended = _finger_is_extended(landmarks, RING_TIP, RING_PIP)
    pinky_extended = _finger_is_extended(landmarks, PINKY_TIP, PINKY_PIP)

    if thumb_extended and not any([index_extended, middle_extended, ring_extended, pinky_extended]):
        return "thumbs_up"

    if thumb_extended and all([index_extended, middle_extended, ring_extended, pinky_extended]):
        return "open_palm"

    return None


def bucket_gesture_detections(detections):
    buckets = {}
    for detection in detections:
        bucket = detection.label if detection.label in GESTURE_BUCKETS else None
        if bucket is None:
            continue
        buckets.setdefault(bucket, []).append(detection)
    return buckets


def summarize_gesture_detections(detections):
    buckets = bucket_gesture_detections(detections)
    if not buckets:
        return "No gesture matches"
    return " | ".join(f"{bucket}: {bucket.replace('_', ' ')}" for bucket in buckets)


class MediaPipeGestureRecognizer:
    def __init__(self, hands_factory=None):
        if hands_factory is None:
            try:
                import mediapipe as mp
            except ImportError as exc:
                raise RuntimeError(
                    "mediapipe is not installed. Install tflite/requirements.txt for gesture mode."
                ) from exc

            hands_factory = lambda: mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )

        self._hands = hands_factory()

    def detect(self, image):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = self._hands.process(rgb_image)
        if not result.multi_hand_landmarks or not result.multi_handedness:
            return []

        image_height, image_width = image.shape[:2]
        detections = []
        for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            handedness_label = handedness.classification[0].label
            label = classify_hand_gesture(hand_landmarks.landmark, handedness_label)
            if label is None:
                continue

            x_values = [landmark.x for landmark in hand_landmarks.landmark]
            y_values = [landmark.y for landmark in hand_landmarks.landmark]
            min_x = max(0, int(min(x_values) * image_width))
            min_y = max(0, int(min(y_values) * image_height))
            max_x = min(image_width, int(max(x_values) * image_width))
            max_y = min(image_height, int(max(y_values) * image_height))
            detections.append(
                Detection(
                    label=label,
                    score=1.0,
                    bbox=(min_x, min_y, max(1, max_x - min_x), max(1, max_y - min_y)),
                )
            )

        return detections
