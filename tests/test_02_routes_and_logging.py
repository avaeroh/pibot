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
    start_streaming = Mock()
    monkeypatch.setattr(server, "start_streaming", start_streaming)

    server.handle_connect()

    start_streaming.assert_called_once_with(server.socketio)
