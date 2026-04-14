from unittest.mock import Mock


def test_logs_endpoint_returns_recent_entries(reload_modules):
    logger_module, server = reload_modules("utility.logger", "control.server")
    logger_module.log_buffer.clear()

    client = server.app.test_client()

    logger_module.log("first entry")
    logger_module.log("second entry")

    response = client.get("/logs")

    assert response.status_code == 200
    assert response.get_json()[-2:] == logger_module.log_buffer[-2:]


def test_root_route_serves_control_page(reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    client = server.app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Pibot Movement Controls" in response.data


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


def test_log_buffer_keeps_only_latest_fifty_entries(reload_module):
    logger_module = reload_module("utility.logger")
    logger_module.log_buffer.clear()

    for index in range(55):
        logger_module.log(f"entry {index}")

    assert len(logger_module.log_buffer) == 50
    assert "entry 0" not in logger_module.log_buffer[0]
    assert "entry 5" in logger_module.log_buffer[0]
    assert "entry 54" in logger_module.log_buffer[-1]


def test_forwards_route_calls_movement_control(monkeypatch, reload_modules):
    _, server, routes = reload_modules("control.app_instance", "control.server", "control.movement_routes")
    client = server.app.test_client()
    forwards = Mock()
    monkeypatch.setattr(routes, "Forwards", forwards)

    response = client.post("/forwards")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Moving forwards"}
    forwards.assert_called_once_with()


def test_backwards_route_calls_movement_control(monkeypatch, reload_modules):
    _, server, routes = reload_modules("control.app_instance", "control.server", "control.movement_routes")
    client = server.app.test_client()
    backwards = Mock()
    monkeypatch.setattr(routes, "Backwards", backwards)

    response = client.post("/backwards")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Moving backwards"}
    backwards.assert_called_once_with()


def test_left_route_calls_movement_control(monkeypatch, reload_modules):
    _, server, routes = reload_modules("control.app_instance", "control.server", "control.movement_routes")
    client = server.app.test_client()
    left = Mock()
    monkeypatch.setattr(routes, "Left", left)

    response = client.post("/left")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Turning left"}
    left.assert_called_once_with()


def test_right_route_calls_movement_control(monkeypatch, reload_modules):
    _, server, routes = reload_modules("control.app_instance", "control.server", "control.movement_routes")
    client = server.app.test_client()
    right = Mock()
    monkeypatch.setattr(routes, "Right", right)

    response = client.post("/right")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Turning right"}
    right.assert_called_once_with()


def test_stop_route_calls_movement_control(monkeypatch, reload_modules):
    _, server, routes = reload_modules("control.app_instance", "control.server", "control.movement_routes")
    client = server.app.test_client()
    stop = Mock()
    monkeypatch.setattr(routes, "Stop", stop)

    response = client.post("/stop")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Stopped"}
    stop.assert_called_once_with()


def test_socket_connect_starts_streaming(monkeypatch, reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    log = Mock()
    monkeypatch.setattr(server, "log", log)

    server.handle_connect()

    log.assert_called_once_with("Client connected")


def test_move_start_event_calls_matching_movement_control(monkeypatch, reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    forwards = Mock()
    monkeypatch.setattr(server, "Forwards", forwards)

    response = server.handle_move_start({"direction": "forwards"})

    forwards.assert_called_once_with()
    assert response == {"status": "ok", "message": "Moving forwards"}


def test_move_start_event_rejects_unknown_direction(reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")

    response = server.handle_move_start({"direction": "spin"})

    assert response == {"status": "error", "message": "Unknown direction"}


def test_stop_event_calls_stop_control(monkeypatch, reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    stop = Mock()
    monkeypatch.setattr(server, "Stop", stop)

    response = server.handle_stop()

    stop.assert_called_once_with()
    assert response == {"status": "ok", "message": "Stopped"}


def test_disconnect_stops_robot(monkeypatch, reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    stop = Mock()
    monkeypatch.setattr(server, "Stop", stop)

    server.handle_disconnect()

    stop.assert_called_once_with()


def test_video_feed_route_returns_mjpeg_response(monkeypatch, reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    generator = iter([b"--frame\r\nContent-Type: image/jpeg\r\n\r\nframe\r\n"])
    monkeypatch.setattr(server, "generate_mjpeg_stream", Mock(return_value=generator))

    response = server.video_feed()

    assert response.mimetype == "multipart/x-mixed-replace"
    assert response.headers["Content-Type"] == "multipart/x-mixed-replace; boundary=frame"


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
