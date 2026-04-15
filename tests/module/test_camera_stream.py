from io import BytesIO
from unittest.mock import Mock


def test_get_camera_command_prefers_rpicam_vid(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    monkeypatch.setattr(
        stream,
        "which",
        lambda command: "/usr/bin/rpicam-vid" if command == "rpicam-vid" else None,
    )

    assert stream.get_camera_command() == "rpicam-vid"


def test_get_camera_command_falls_back_to_libcamera_vid(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    monkeypatch.setattr(
        stream,
        "which",
        lambda command: "/usr/bin/libcamera-vid" if command == "libcamera-vid" else None,
    )

    assert stream.get_camera_command() == "libcamera-vid"


def test_get_camera_command_raises_when_no_camera_binary_exists(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    monkeypatch.setattr(stream, "which", lambda _: None)

    try:
        stream.get_camera_command()
    except FileNotFoundError as exc:
        assert "No supported camera command found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError when no camera binary exists")


def test_cleanup_camera_terminates_process_and_removes_fifo(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    process = Mock()
    process.poll.return_value = None
    stream.VIDEO_PROCESS = process
    monkeypatch.setattr(stream.os.path, "exists", lambda path: path == stream.FIFO_PATH)
    removed_paths = []
    monkeypatch.setattr(stream.os, "remove", removed_paths.append)

    stream.cleanup_camera()

    process.terminate.assert_called_once_with()
    process.wait.assert_called_once_with()
    assert removed_paths == [stream.FIFO_PATH]
    assert stream.VIDEO_PROCESS is None


def test_start_libcamera_stream_creates_fifo_and_starts_process(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    process = Mock()
    process.poll.return_value = None
    popen = Mock(return_value=process)
    mkfifo = Mock()
    monkeypatch.setattr(stream.os.path, "exists", lambda path: False)
    monkeypatch.setattr(stream.os, "mkfifo", mkfifo)
    monkeypatch.setattr(stream.subprocess, "Popen", popen)
    monkeypatch.setattr(stream, "get_camera_command", lambda: "rpicam-vid")

    stream.start_libcamera_stream()

    mkfifo.assert_called_once_with(stream.FIFO_PATH)
    popen.assert_called_once_with(
        [
            "rpicam-vid",
            "-t",
            "0",
            "--codec",
            "mjpeg",
            "--inline",
            "--width",
            str(stream.WIDTH),
            "--height",
            str(stream.HEIGHT),
            "--framerate",
            str(stream.FPS),
            "--quality",
            str(stream.QUALITY),
            "--rotation",
            str(stream.ROTATION),
            "-o",
            stream.FIFO_PATH,
        ]
    )
    assert stream.VIDEO_PROCESS is process


def test_start_libcamera_stream_reuses_existing_running_process(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    process = Mock()
    process.poll.return_value = None
    stream.VIDEO_PROCESS = process
    mkfifo = Mock()
    popen = Mock()
    monkeypatch.setattr(stream.os, "mkfifo", mkfifo)
    monkeypatch.setattr(stream.subprocess, "Popen", popen)

    stream.start_libcamera_stream()

    mkfifo.assert_not_called()
    popen.assert_not_called()


def test_iter_mjpeg_frames_extracts_complete_jpegs(reload_module):
    stream = reload_module("camera.stream")
    payload = (
        b"noise"
        + stream.JPEG_START
        + b"frame-one"
        + stream.JPEG_END
        + b"more-noise"
        + stream.JPEG_START
        + b"frame-two"
        + stream.JPEG_END
    )

    frames = list(stream.iter_mjpeg_frames(BytesIO(payload), chunk_size=5))

    assert frames == [
        stream.JPEG_START + b"frame-one" + stream.JPEG_END,
        stream.JPEG_START + b"frame-two" + stream.JPEG_END,
    ]


def test_generate_mjpeg_stream_wraps_frames_for_http_response(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    start_libcamera_stream = Mock()
    monkeypatch.setattr(stream, "start_libcamera_stream", start_libcamera_stream)
    monkeypatch.setattr(
        "builtins.open",
        Mock(return_value=BytesIO(stream.JPEG_START + b"frame" + stream.JPEG_END)),
    )

    chunk = next(stream.generate_mjpeg_stream())

    start_libcamera_stream.assert_called_once_with()
    assert chunk.startswith(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n")
    assert chunk.endswith(b"\r\n")
