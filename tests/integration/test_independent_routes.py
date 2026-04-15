from unittest.mock import Mock


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
    service.stream_frames.assert_called_once_with()


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
