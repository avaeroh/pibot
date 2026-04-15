from independent.detector import Detection, bucket_detections, bucket_for_label, prioritized_buckets, summarize_detections


def test_bucket_for_label_maps_people_and_cat():
    assert bucket_for_label("person") == "people"
    assert bucket_for_label("cat") == "cat"
    assert bucket_for_label("dog") is None


def test_bucket_detections_groups_target_labels():
    detections = [
        Detection(label="person", score=0.91, bbox=(1, 2, 3, 4)),
        Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8)),
        Detection(label="bottle", score=0.77, bbox=(9, 10, 11, 12)),
    ]

    buckets = bucket_detections(detections)

    assert list(buckets.keys()) == ["people", "cat"]
    assert [item.label for item in buckets["people"]] == ["person"]
    assert [item.label for item in buckets["cat"]] == ["cat"]


def test_prioritized_buckets_prefers_cat_then_people():
    buckets = {
        "people": [Detection(label="person", score=0.91, bbox=(1, 2, 3, 4))],
        "cat": [Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8))],
    }

    assert prioritized_buckets(buckets) == ["cat", "people"]


def test_summarize_detections_formats_bucket_summary():
    detections = [
        Detection(label="person", score=0.91, bbox=(1, 2, 3, 4)),
        Detection(label="cat", score=0.88, bbox=(5, 6, 7, 8)),
    ]

    assert summarize_detections(detections) == "cat: cat | people: person"
