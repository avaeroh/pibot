import json
from unittest.mock import Mock

from independent import behaviors
from independent.config import DEFAULT_RUNTIME_CONFIG
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


def test_independent_config_route_returns_full_config_state(monkeypatch, reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    service = Mock()
    service.get_config_state.return_value = {
        "active_detection_mode": "subjects",
        "bucket_groups": {"subjects": {"label": "Subjects", "buckets": {}}},
        "detection_modes": {"subjects": {"label": "Subjects"}, "gestures": {"label": "Gestures"}},
        "mappings": {"subjects": {"people": "wiggle", "cat": "spin_360"}, "gestures": {"wave": "disabled"}},
        "options": {
            "disabled": {"label": "Disabled"},
            "wiggle": {"label": "Wiggle"},
            "spin_360": {"label": "Spin 360"},
        },
    }
    monkeypatch.setattr(server, "independent_mode_service", service)
    client = server.app.test_client()

    response = client.get("/independent/config")

    assert response.status_code == 200
    assert response.get_json()["active_detection_mode"] == "subjects"
    assert response.get_json()["mappings"]["subjects"]["people"] == "wiggle"


def test_independent_config_route_updates_runtime_config(monkeypatch, reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    service = Mock()
    service.update_runtime_config.return_value = {
        "active_detection_mode": "gestures",
        "bucket_groups": {},
        "detection_modes": {},
        "mappings": {"subjects": {"people": "wiggle", "cat": "spin_360"}, "gestures": {"wave": "disabled"}},
        "options": {},
    }
    monkeypatch.setattr(server, "independent_mode_service", service)
    client = server.app.test_client()

    response = client.post(
        "/independent/config",
        json={
            "active_detection_mode": "gestures",
            "mappings": {"gestures": {"wave": "disabled"}},
        },
    )

    assert response.status_code == 200
    service.update_runtime_config.assert_called_once_with(
        {
            "active_detection_mode": "gestures",
            "mappings": {"gestures": {"wave": "disabled"}},
        }
    )
    assert response.get_json()["active_detection_mode"] == "gestures"


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


def test_service_builds_stdout_camera_command(tmp_path):
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=tmp_path / "gesture-mappings.json",
    )

    command = service._build_camera_command()

    assert command[0] == "rpicam-vid"
    assert command[-1] == "-"
    assert "--codec" in command
    assert "mjpeg" in command


def test_service_bootstraps_default_runtime_config_file(tmp_path):
    config_path = tmp_path / "gesture-mappings.json"

    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=config_path,
    )

    assert service.get_runtime_config() == DEFAULT_RUNTIME_CONFIG
    assert json.loads(config_path.read_text()) == DEFAULT_RUNTIME_CONFIG


def test_service_normalizes_invalid_persisted_runtime_config(tmp_path):
    config_path = tmp_path / "gesture-mappings.json"
    config_path.write_text(
        json.dumps(
            {
                "active_detection_mode": "both",
                "mappings": {
                    "subjects": {"people": "invalid", "cat": "spin_360"},
                    "gestures": {"thumbs_up": "invalid", "open_palm": "spin_360"},
                },
            }
        )
    )

    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=config_path,
    )

    assert service.get_active_detection_mode() == "subjects"
    assert service.get_behavior_config()["subjects"]["people"] == "wiggle"
    assert service.get_behavior_config()["gestures"]["thumbs_up"] == "wiggle"
    assert service.get_behavior_config()["gestures"]["wave"] == "disabled"
    assert json.loads(config_path.read_text()) == service.get_runtime_config()


def test_service_exposes_behavior_options_and_detection_modes(tmp_path):
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=tmp_path / "gesture-mappings.json",
    )

    assert service.get_behavior_options() == {
        "disabled": {"label": "Disabled"},
        "spin_360": {"label": "Spin 360"},
        "wiggle": {"label": "Wiggle"},
    }
    assert service.get_detection_modes() == {
        "subjects": {"label": "Subjects"},
        "gestures": {"label": "Gestures"},
    }


def test_service_returns_mapping_copy_not_live_reference(tmp_path):
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=tmp_path / "gesture-mappings.json",
    )

    snapshot = service.get_behavior_config()
    snapshot["subjects"]["people"] = "disabled"

    assert service.get_behavior_config()["subjects"]["people"] == DEFAULT_RUNTIME_CONFIG["mappings"]["subjects"]["people"]


def test_service_updates_runtime_config_and_persists_changes(tmp_path):
    config_path = tmp_path / "gesture-mappings.json"
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=config_path,
    )

    state = service.update_runtime_config(
        {
            "active_detection_mode": "gestures",
            "mappings": {
                "subjects": {"people": "disabled"},
                "gestures": {"thumbs_up": "spin_360"},
            },
        }
    )

    assert state["active_detection_mode"] == "gestures"
    assert state["mappings"]["subjects"]["people"] == "disabled"
    assert state["mappings"]["gestures"]["thumbs_up"] == "spin_360"
    assert json.loads(config_path.read_text()) == service.get_runtime_config()


def test_service_ignores_invalid_runtime_config_updates(tmp_path):
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=tmp_path / "gesture-mappings.json",
    )

    state = service.update_runtime_config(
        {
            "active_detection_mode": "invalid",
            "mappings": {
                "subjects": {"people": "invalid_behavior"},
                "gestures": {"wave": "invalid_behavior"},
                "unknown": {"bucket": "wiggle"},
            },
        }
    )

    assert state["active_detection_mode"] == "subjects"
    assert state["mappings"]["subjects"]["people"] == "wiggle"
    assert state["mappings"]["gestures"]["wave"] == "disabled"


def test_service_get_config_state_contains_groups_modes_and_options(tmp_path):
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=tmp_path / "gesture-mappings.json",
    )

    state = service.get_config_state()

    assert state["active_detection_mode"] == "subjects"
    assert "subjects" in state["bucket_groups"]
    assert "gestures" in state["bucket_groups"]
    assert "disabled" in state["options"]
    assert "subjects" in state["detection_modes"]


def test_trigger_behavior_returns_label_for_disabled():
    assert behaviors.trigger_behavior("disabled") == "Disabled"


def test_trigger_behavior_runs_selected_handler(monkeypatch):
    called = []
    monkeypatch.setattr(behaviors, "wiggle", lambda: called.append("wiggle"))
    monkeypatch.setitem(
        behaviors.AVAILABLE_BEHAVIORS,
        "wiggle",
        ("Wiggle", behaviors.wiggle),
    )

    label = behaviors.trigger_behavior("wiggle")

    assert label == "Wiggle"
    assert called == ["wiggle"]


def test_service_triggers_highest_priority_subject_bucket_once(tmp_path):
    calls = []
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: calls.append(behavior_key) or behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        time_fn=lambda: 100.0,
        config_path=tmp_path / "gesture-mappings.json",
    )

    service._trigger_behaviors(
        {
            "people": [Detection(label="person", score=0.91, bbox=(1, 2, 3, 4))],
            "cat": [Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8))],
        },
        100.0,
    )
    service._behavior_thread.join(timeout=1)

    assert calls == ["wiggle"]


def test_service_uses_updated_subject_mapping_for_next_detection(tmp_path):
    calls = []
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: calls.append(behavior_key) or behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        time_fn=lambda: 100.0,
        config_path=tmp_path / "gesture-mappings.json",
    )
    service.update_runtime_config({"mappings": {"subjects": {"people": "spin_360"}}})

    service._trigger_behaviors(
        {"people": [Detection(label="person", score=0.91, bbox=(1, 2, 3, 4))]},
        100.0,
    )
    service._behavior_thread.join(timeout=1)

    assert calls == ["spin_360"]


def test_service_can_trigger_gesture_mapping_when_gesture_mode_is_active(tmp_path):
    calls = []
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: calls.append(behavior_key) or behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        time_fn=lambda: 100.0,
        config_path=tmp_path / "gesture-mappings.json",
    )
    service.update_runtime_config(
        {
            "active_detection_mode": "gestures",
            "mappings": {"gestures": {"thumbs_up": "spin_360"}},
        }
    )

    service._trigger_behaviors({"thumbs_up": [object()]}, 100.0)
    service._behavior_thread.join(timeout=1)

    assert calls == ["spin_360"]


def test_service_respects_behavior_cooldown(tmp_path):
    calls = []
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: calls.append(behavior_key) or behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=tmp_path / "gesture-mappings.json",
    )
    service._last_completed_times["cat"] = 50.0

    service._trigger_behaviors(
        {"cat": [Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8))]},
        52.0,
    )

    assert calls == []


def test_service_does_not_queue_new_behavior_while_one_is_running(tmp_path):
    calls = []

    def behavior_runner(behavior_key):
        calls.append(behavior_key)

    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=behavior_runner,
        camera_command_resolver=lambda: "rpicam-vid",
        time_fn=lambda: 100.0,
        config_path=tmp_path / "gesture-mappings.json",
    )
    service._active_behavior_bucket = "people"
    service._behavior_thread = Mock()
    service._behavior_thread.is_alive.return_value = True

    service._trigger_behaviors(
        {"cat": [Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8))]},
        100.0,
    )

    assert calls == []


def test_service_cooldown_starts_after_behavior_completion(tmp_path):
    timeline = [100.0, 103.0]
    calls = []

    def time_fn():
        return timeline.pop(0)

    def behavior_runner(behavior_key):
        calls.append(behavior_key)
        time_fn()
        return behavior_key

    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=behavior_runner,
        camera_command_resolver=lambda: "rpicam-vid",
        time_fn=time_fn,
        config_path=tmp_path / "gesture-mappings.json",
    )

    service._trigger_behaviors(
        {"people": [Detection(label="person", score=0.91, bbox=(1, 2, 3, 4))]},
        100.0,
    )
    service._behavior_thread.join(timeout=1)

    assert calls == ["wiggle"]
    assert service._last_completed_times["people"] == 103.0


def test_service_skips_bucket_when_behavior_is_disabled(tmp_path):
    calls = []
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: calls.append(behavior_key) or behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        time_fn=lambda: 100.0,
        config_path=tmp_path / "gesture-mappings.json",
    )
    service.update_runtime_config({"mappings": {"subjects": {"people": "disabled"}}})

    service._trigger_behaviors(
        {"people": [Detection(label="person", score=0.91, bbox=(1, 2, 3, 4))]},
        100.0,
    )

    assert calls == []
