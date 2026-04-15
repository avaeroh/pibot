from independent import behaviors


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
