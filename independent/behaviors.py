import os
import time

from utility.movement_controls import Backwards, Forwards, Left, Right, Stop

SPIN_360_SECONDS = float(os.getenv("SPIN_360_SECONDS", 0.95))
WIGGLE_TURN_SECONDS = float(os.getenv("WIGGLE_TURN_SECONDS", 0.12))
WIGGLE_MOVE_SECONDS = float(os.getenv("WIGGLE_MOVE_SECONDS", 0.15))


def run_timed_motion(motion, duration):
    motion()
    time.sleep(duration)
    Stop()


def spin_360():
    run_timed_motion(Right, SPIN_360_SECONDS)


def wiggle():
    # Best-effort "hello" wiggle that returns close to the starting heading and position.
    run_timed_motion(Left, WIGGLE_TURN_SECONDS)
    run_timed_motion(Right, WIGGLE_TURN_SECONDS * 2)
    run_timed_motion(Left, WIGGLE_TURN_SECONDS)
    run_timed_motion(Forwards, WIGGLE_MOVE_SECONDS)
    run_timed_motion(Backwards, WIGGLE_MOVE_SECONDS)
    Stop()


AVAILABLE_BEHAVIORS = {
    "none": ("No Action", None),
    "spin_360": ("Spin 360", spin_360),
    "wiggle": ("Wiggle", wiggle),
}


DEFAULT_BUCKET_BEHAVIORS = {
    "cat": "spin_360",
    "people": "wiggle",
}


def trigger_behavior(behavior_key):
    behavior = AVAILABLE_BEHAVIORS.get(behavior_key)
    if behavior is None:
        return None

    behavior_name, handler = behavior
    if handler is None:
        return behavior_name

    handler()
    return behavior_name
