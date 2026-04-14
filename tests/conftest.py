import importlib
import sys

import pytest


@pytest.fixture(autouse=True)
def mock_gpio_env(monkeypatch):
    monkeypatch.setenv("MOCK_GPIO", "true")
    monkeypatch.setenv("BUTTON_DELAY", "0")


@pytest.fixture
def reload_module():
    def _reload(module_name):
        sys.modules.pop(module_name, None)
        return importlib.import_module(module_name)

    return _reload


@pytest.fixture
def reload_modules():
    def _reload(*module_names):
        for module_name in module_names:
            sys.modules.pop(module_name, None)
        return [importlib.import_module(module_name) for module_name in module_names]

    return _reload
