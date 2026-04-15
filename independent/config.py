import json
from copy import deepcopy
from pathlib import Path


DETECTION_MODES = {
    "subjects": {"label": "Subjects"},
    "gestures": {"label": "Gestures"},
}

BUCKET_GROUPS = {
    "subjects": {
        "label": "Subjects",
        "buckets": {
            "people": {"label": "People"},
            "cat": {"label": "Cat"},
        },
    },
    "gestures": {
        "label": "Gestures",
        "buckets": {
            "thumbs_up": {"label": "Thumbs Up"},
            "open_palm": {"label": "Open Palm"},
            "wave": {"label": "Wave"},
        },
    },
}

DEFAULT_BEHAVIOR_MAPPINGS = {
    "subjects": {
        "people": "wiggle",
        "cat": "spin_360",
    },
    "gestures": {
        "thumbs_up": "wiggle",
        "open_palm": "spin_360",
        "wave": "disabled",
    },
}

DEFAULT_RUNTIME_CONFIG = {
    "active_detection_mode": "subjects",
    "mappings": deepcopy(DEFAULT_BEHAVIOR_MAPPINGS),
}


def default_runtime_config():
    return deepcopy(DEFAULT_RUNTIME_CONFIG)


def get_config_path(config_path=None):
    if config_path is not None:
        return Path(config_path)
    return Path("config") / "gesture-mappings.json"


def normalize_runtime_config(raw_config, available_behaviors):
    config = raw_config if isinstance(raw_config, dict) else {}
    active_detection_mode = config.get("active_detection_mode")
    if active_detection_mode not in DETECTION_MODES:
        active_detection_mode = DEFAULT_RUNTIME_CONFIG["active_detection_mode"]

    raw_mappings = config.get("mappings")
    if not isinstance(raw_mappings, dict):
        raw_mappings = {}

    normalized_mappings = {}
    for group_key, group_meta in BUCKET_GROUPS.items():
        raw_group = raw_mappings.get(group_key)
        if not isinstance(raw_group, dict):
            raw_group = {}

        normalized_group = {}
        for bucket_key in group_meta["buckets"]:
            default_behavior = DEFAULT_BEHAVIOR_MAPPINGS[group_key][bucket_key]
            behavior_key = raw_group.get(bucket_key, default_behavior)
            if behavior_key not in available_behaviors:
                behavior_key = default_behavior
            normalized_group[bucket_key] = behavior_key
        normalized_mappings[group_key] = normalized_group

    return {
        "active_detection_mode": active_detection_mode,
        "mappings": normalized_mappings,
    }


def load_runtime_config(config_path, available_behaviors):
    path = get_config_path(config_path)
    if not path.exists():
        return default_runtime_config(), False

    try:
        raw_config = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default_runtime_config(), True

    normalized = normalize_runtime_config(raw_config, available_behaviors)
    return normalized, normalized != raw_config


def save_runtime_config(config_path, config):
    path = get_config_path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
