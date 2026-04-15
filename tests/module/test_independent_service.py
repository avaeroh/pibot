import json
from unittest.mock import Mock

from independent.config import DEFAULT_RUNTIME_CONFIG
from independent.detector import Detection
from independent.service import IndependentModeService


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


def test_service_start_does_not_eagerly_initialize_detector(tmp_path):
    created_threads = []

    class DummyThread:
        def __init__(self, target=None, args=None, daemon=None):
            self.target = target
            self.args = args or ()
            self.daemon = daemon
            self.started = False
            created_threads.append(self)

        def start(self):
            self.started = True

        def is_alive(self):
            return self.started

    service = IndependentModeService(
        detector_factory=lambda: (_ for _ in ()).throw(AssertionError("detector should not be created on start")),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=tmp_path / "gesture-mappings.json",
    )

    import independent.service as service_module
    original_thread_class = service_module.threading.Thread
    service_module.threading.Thread = DummyThread
    try:
        service.start()
    finally:
        service_module.threading.Thread = original_thread_class

    assert created_threads
    assert created_threads[0].started is True


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
    assert service.get_behavior_config()["gestures"]["open_palm"] == "spin_360"
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
                "gestures": {"open_palm": "invalid_behavior"},
                "unknown": {"bucket": "wiggle"},
            },
        }
    )

    assert state["active_detection_mode"] == "subjects"
    assert state["mappings"]["subjects"]["people"] == "wiggle"
    assert state["mappings"]["gestures"]["open_palm"] == "spin_360"


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
    assert state["visible_bucket_group"] == "subjects"


def test_service_visible_bucket_group_tracks_active_detection_mode(tmp_path):
    service = IndependentModeService(
        detector_factory=lambda: object(),
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=tmp_path / "gesture-mappings.json",
    )

    initial_state = service.get_config_state()
    updated_state = service.update_runtime_config({"active_detection_mode": "gestures"})

    assert initial_state["visible_bucket_group"] == "subjects"
    assert updated_state["visible_bucket_group"] == "gestures"


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


def test_service_detect_gestures_uses_recognizer_output(tmp_path):
    recognizer = Mock()
    recognizer.detect.return_value = [
        Detection(label="thumbs_up", score=1.0, bbox=(1, 2, 3, 4)),
        Detection(label="open_palm", score=1.0, bbox=(5, 6, 7, 8)),
    ]
    service = IndependentModeService(
        detector_factory=lambda: object(),
        gesture_recognizer_factory=lambda: recognizer,
        behavior_runner=lambda behavior_key: behavior_key,
        camera_command_resolver=lambda: "rpicam-vid",
        config_path=tmp_path / "gesture-mappings.json",
    )

    detections, buckets, summary = service._detect_gestures(Mock())

    assert [detection.label for detection in detections] == ["thumbs_up", "open_palm"]
    assert list(buckets.keys()) == ["thumbs_up", "open_palm"]
    assert summary == "thumbs_up: thumbs up | open_palm: open palm"


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
