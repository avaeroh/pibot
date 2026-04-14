from unittest.mock import Mock

from independent.detector import Detection, bucket_detections, bucket_for_label, prioritized_buckets, summarize_detections
from independent.service import IndependentModeService


def test_root_route_serves_independent_page_when_mode_is_set(monkeypatch, reload_modules):
    monkeypatch.setenv("PIBOT_MODE", "independent")
    _, server = reload_modules("control.app_instance", "control.server")
    client = server.app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Pibot Independent Mode" in response.data


def test_independent_route_serves_independent_page(reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    client = server.app.test_client()

    response = client.get("/independent")

    assert response.status_code == 200
    assert b"Pibot Independent Mode" in response.data


def test_independent_video_feed_route_returns_mjpeg_response(monkeypatch, reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    generator = iter([b"--frame\r\nContent-Type: image/jpeg\r\n\r\nframe\r\n"])
    service = Mock()
    service.stream_frames.return_value = generator
    monkeypatch.setattr(server, "independent_mode_service", service)

    response = server.independent_video_feed()

    assert response.mimetype == "multipart/x-mixed-replace"
    assert response.headers["Content-Type"] == "multipart/x-mixed-replace; boundary=frame"


def test_independent_logs_route_returns_service_logs(monkeypatch, reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    service = Mock()
    service.get_log_entries.return_value = ["[12:00:00] Detected people: person"]
    monkeypatch.setattr(server, "independent_mode_service", service)
    client = server.app.test_client()

    response = client.get("/independent/logs")

    assert response.status_code == 200
    assert response.get_json() == ["[12:00:00] Detected people: person"]


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
    service._last_completed_times["cat"] = 50.0

    service._trigger_behaviors(
        {"cat": [Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8))]},
        52.0,
    )

    assert calls == []


def test_service_does_not_queue_new_behavior_while_one_is_running():
    calls = []

    def behavior_runner(bucket):
        calls.append(bucket)

    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=behavior_runner,
        camera_command_resolver=lambda: "rpicam-vid",
        time_fn=lambda: 100.0,
    )
    service._active_behavior_bucket = "people"
    service._behavior_thread = Mock()
    service._behavior_thread.is_alive.return_value = True

    service._trigger_behaviors(
        {"cat": [Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8))]},
        100.0,
    )

    assert calls == []


def test_service_cooldown_starts_after_behavior_completion():
    timeline = [100.0, 103.0]
    calls = []

    def time_fn():
        return timeline.pop(0)

    def behavior_runner(bucket):
        calls.append(bucket)
        time_fn()
        return bucket

    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=behavior_runner,
        camera_command_resolver=lambda: "rpicam-vid",
        time_fn=time_fn,
    )

    service._trigger_behaviors(
        {"people": [Detection(label="person", score=0.91, bbox=(1, 2, 3, 4))]},
        100.0,
    )
    service._behavior_thread.join(timeout=1)

    assert calls == ["people"]
    assert service._last_completed_times["people"] == 103.0
