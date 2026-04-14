import base64
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


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


def test_start_libcamera_stream_creates_fifo_and_starts_process(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    popen = Mock(return_value="process")
    mkfifo = Mock()
    monkeypatch.setattr(stream.os.path, "exists", lambda path: False)
    monkeypatch.setattr(stream.os, "mkfifo", mkfifo)
    monkeypatch.setattr(stream.subprocess, "Popen", popen)

    stream.start_libcamera_stream()

    mkfifo.assert_called_once_with(stream.FIFO_PATH)
    popen.assert_called_once_with(
        [
            "libcamera-vid",
            "-t",
            "0",
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
    assert stream.VIDEO_PROCESS == "process"


def test_capture_frames_emits_base64_encoded_jpeg(monkeypatch, reload_module):
    class StreamComplete(Exception):
        pass

    stream = reload_module("camera.stream")
    cap = Mock()
    cap.isOpened.return_value = True
    cap.read.return_value = (True, "frame")
    socketio = SimpleNamespace(emit=Mock(side_effect=StreamComplete))
    monkeypatch.setattr(stream.cv2, "VideoCapture", Mock(return_value=cap))
    monkeypatch.setattr(stream.cv2, "imencode", Mock(return_value=(True, b"jpeg-bytes")))
    monkeypatch.setattr(stream.time, "sleep", lambda *_: None)

    with pytest.raises(StreamComplete):
        stream.capture_frames(socketio)

    cap.grab.assert_called()
    socketio.emit.assert_called_once_with(
        "video_frame",
        {"data": base64.b64encode(b"jpeg-bytes").decode("utf-8")},
        namespace="/",
    )


def test_capture_frames_returns_when_fifo_cannot_be_opened(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    cap = Mock()
    cap.isOpened.return_value = False
    socketio = SimpleNamespace(emit=Mock())
    monkeypatch.setattr(stream.cv2, "VideoCapture", Mock(return_value=cap))

    stream.capture_frames(socketio)

    socketio.emit.assert_not_called()


def test_start_streaming_starts_camera_then_background_thread(monkeypatch, reload_module):
    stream = reload_module("camera.stream")
    start_libcamera_stream = Mock()
    thread = Mock()
    thread_class = Mock(return_value=thread)
    socketio = object()
    monkeypatch.setattr(stream, "start_libcamera_stream", start_libcamera_stream)
    monkeypatch.setattr(stream, "Thread", thread_class)

    stream.start_streaming(socketio)

    start_libcamera_stream.assert_called_once_with()
    thread_class.assert_called_once_with(target=stream.capture_frames, args=(socketio,))
    assert thread.daemon is True
    thread.start.assert_called_once_with()
