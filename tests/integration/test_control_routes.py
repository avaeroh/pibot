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


def test_control_route_serves_control_page(reload_modules):
    _, server = reload_modules("control.app_instance", "control.server")
    client = server.app.test_client()

    response = client.get("/control")

    assert response.status_code == 200
    assert b"Pibot Movement Controls" in response.data


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


def test_socket_connect_logs_client_connection(monkeypatch, reload_modules):
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
