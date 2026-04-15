from unittest.mock import call


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
