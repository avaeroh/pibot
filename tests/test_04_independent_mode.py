from independent.detector import Detection, bucket_detections, bucket_for_label, prioritized_buckets, summarize_detections
from independent.service import IndependentModeService


def test_bucket_for_label_maps_people_and_cat():
    assert bucket_for_label("person") == "people"
    assert bucket_for_label("cat") == "cat"
    assert bucket_for_label("dog") is None


def test_bucket_detections_groups_target_labels():
    detections = [
        Detection(label="person", score=0.91, bbox=(1, 2, 3, 4)),
        Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8)),
        Detection(label="bottle", score=0.77, bbox=(9, 10, 11, 12)),
    ]

    buckets = bucket_detections(detections)

    assert list(buckets.keys()) == ["people", "cat"]
    assert [item.label for item in buckets["people"]] == ["person"]
    assert [item.label for item in buckets["cat"]] == ["cat"]


def test_prioritized_buckets_prefers_cat_then_people():
    buckets = {
        "people": [Detection(label="person", score=0.91, bbox=(1, 2, 3, 4))],
        "cat": [Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8))],
    }

    assert prioritized_buckets(buckets) == ["cat", "people"]


def test_summarize_detections_formats_bucket_summary():
    detections = [
        Detection(label="person", score=0.91, bbox=(1, 2, 3, 4)),
        Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8)),
    ]

    assert summarize_detections(detections) == "cat: cat | people: person"


def test_service_builds_stdout_camera_command():
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda bucket: bucket,
        camera_command_resolver=lambda: "rpicam-vid",
    )

    command = service._build_camera_command()

    assert command[0] == "rpicam-vid"
    assert command[-1] == "-"
    assert "--codec" in command
    assert "mjpeg" in command


def test_service_triggers_highest_priority_bucket_once():
    calls = []
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda bucket: calls.append(bucket) or bucket,
        camera_command_resolver=lambda: "rpicam-vid",
        time_fn=lambda: 100.0,
    )

    service._trigger_behaviors(
        {
            "people": [Detection(label="person", score=0.91, bbox=(1, 2, 3, 4))],
            "cat": [Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8))],
        },
        100.0,
    )
    service._behavior_thread.join(timeout=1)

    assert calls == ["cat"]


def test_service_respects_behavior_cooldown():
    calls = []
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda bucket: calls.append(bucket) or bucket,
        camera_command_resolver=lambda: "rpicam-vid",
    )
    service._last_trigger_times["cat"] = 50.0

    service._trigger_behaviors(
        {"cat": [Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8))]},
        52.0,
    )

    assert calls == []
