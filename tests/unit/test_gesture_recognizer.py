from types import SimpleNamespace

from independent.gesture_recognizer import (
    classify_hand_gesture,
    summarize_gesture_detections,
    bucket_gesture_detections,
)
from independent.detector import Detection


def _landmarks(overrides):
    points = [SimpleNamespace(x=0.5, y=0.5) for _ in range(21)]
    for index, (x_value, y_value) in overrides.items():
        points[index] = SimpleNamespace(x=x_value, y=y_value)
    return points


def test_classify_hand_gesture_detects_thumbs_up():
    landmarks = _landmarks(
        {
            4: (0.2, 0.2),
            3: (0.3, 0.3),
            2: (0.4, 0.5),
            8: (0.5, 0.7),
            6: (0.5, 0.6),
            12: (0.55, 0.7),
            10: (0.55, 0.6),
            16: (0.6, 0.7),
            14: (0.6, 0.6),
            20: (0.65, 0.7),
            18: (0.65, 0.6),
        }
    )

    assert classify_hand_gesture(landmarks, "Right") == "thumbs_up"


def test_classify_hand_gesture_detects_open_palm():
    landmarks = _landmarks(
        {
            4: (0.7, 0.2),
            3: (0.6, 0.3),
            2: (0.5, 0.5),
            8: (0.45, 0.2),
            6: (0.45, 0.4),
            12: (0.5, 0.2),
            10: (0.5, 0.4),
            16: (0.55, 0.2),
            14: (0.55, 0.4),
            20: (0.6, 0.2),
            18: (0.6, 0.4),
        }
    )

    assert classify_hand_gesture(landmarks, "Left") == "open_palm"


def test_classify_hand_gesture_returns_none_for_unknown_pose():
    landmarks = _landmarks(
        {
            4: (0.5, 0.5),
            3: (0.5, 0.45),
            2: (0.5, 0.4),
            8: (0.45, 0.55),
            6: (0.45, 0.5),
        }
    )

    assert classify_hand_gesture(landmarks, "Right") is None


def test_bucket_and_summary_for_gesture_detections():
    detections = [
        Detection(label="thumbs_up", score=1.0, bbox=(1, 2, 3, 4)),
        Detection(label="open_palm", score=1.0, bbox=(5, 6, 7, 8)),
    ]

    buckets = bucket_gesture_detections(detections)

    assert list(buckets.keys()) == ["thumbs_up", "open_palm"]
    assert summarize_gesture_detections(detections) == "thumbs_up: thumbs up | open_palm: open palm"
