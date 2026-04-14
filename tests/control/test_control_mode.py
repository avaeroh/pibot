from unittest.mock import Mock, call


def test_import_uses_mock_gpio_when_enabled(reload_module):
    movement_controls = reload_module("utility.movement_controls")

    assert movement_controls.GPIO_AVAILABLE is False


def test_stop_turns_all_motor_pins_off(reload_module):
    movement_controls = reload_module("utility.movement_controls")
    movement_controls.GPIO.reset_mock()

    movement_controls.Stop()

    movement_controls.GPIO.output.assert_called_once_with(
        [
            movement_controls.pinMotorAForwards,
            movement_controls.pinMotorABackwards,
            movement_controls.pinMotorBForwards,
            movement_controls.pinMotorBBackwards,
        ],
        0,
    )


def test_forwards_sets_forward_pins_after_clearing_previous_state(reload_module):
    movement_controls = reload_module("utility.movement_controls")
    movement_controls.GPIO.reset_mock()

    movement_controls.Forwards()

    assert movement_controls.GPIO.output.call_args_list == [
        call(
            [
                movement_controls.pinMotorAForwards,
                movement_controls.pinMotorABackwards,
                movement_controls.pinMotorBForwards,
                movement_controls.pinMotorBBackwards,
            ],
            0,
        ),
        call(
            [
                movement_controls.pinMotorAForwards,
                movement_controls.pinMotorBForwards,
            ],
            1,
        ),
    ]


def test_backwards_sets_reverse_pins_after_clearing_previous_state(reload_module):
    movement_controls = reload_module("utility.movement_controls")
    movement_controls.GPIO.reset_mock()

    movement_controls.Backwards()

    assert movement_controls.GPIO.output.call_args_list == [
        call(
            [
                movement_controls.pinMotorAForwards,
                movement_controls.pinMotorABackwards,
                movement_controls.pinMotorBForwards,
                movement_controls.pinMotorBBackwards,
            ],
            0,
        ),
        call(
            [
                movement_controls.pinMotorABackwards,
                movement_controls.pinMotorBBackwards,
            ],
            1,
        ),
    ]


def test_left_sets_turn_pins_after_clearing_previous_state(reload_module):
    movement_controls = reload_module("utility.movement_controls")
    movement_controls.GPIO.reset_mock()

    movement_controls.Left()

    assert movement_controls.GPIO.output.call_args_list == [
        call(
            [
                movement_controls.pinMotorAForwards,
                movement_controls.pinMotorABackwards,
                movement_controls.pinMotorBForwards,
                movement_controls.pinMotorBBackwards,
            ],
            0,
        ),
        call(
            [
                movement_controls.pinMotorAForwards,
                movement_controls.pinMotorBBackwards,
            ],
            1,
        ),
    ]


def test_right_sets_turn_pins_after_clearing_previous_state(reload_module):
    movement_controls = reload_module("utility.movement_controls")
    movement_controls.GPIO.reset_mock()

    movement_controls.Right()

    assert movement_controls.GPIO.output.call_args_list == [
        call(
            [
                movement_controls.pinMotorAForwards,
                movement_controls.pinMotorABackwards,
                movement_controls.pinMotorBForwards,
                movement_controls.pinMotorBBackwards,
            ],
            0,
        ),
        call(
            [
                movement_controls.pinMotorABackwards,
                movement_controls.pinMotorBForwards,
            ],
            1,
        ),
    ]


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
