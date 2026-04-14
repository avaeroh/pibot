import os
import subprocess
import threading
import time

import cv2
import numpy as np

from camera.stream import get_camera_command, iter_mjpeg_frames
from independent.behaviors import trigger_bucket_behavior
from independent.detector import TFLiteObjectDetector, bucket_detections, draw_detections, prioritized_buckets, summarize_detections
from utility.logger import log

MODEL_PATH = os.getenv("TFLITE_MODEL", "models/efficientdet_lite0.tflite")
ENABLE_EDGE_TPU = os.getenv("TFLITE_ENABLE_EDGETPU", "false").lower() == "true"
CAMERA_WIDTH = int(os.getenv("INDEPENDENT_WIDTH", 640))
CAMERA_HEIGHT = int(os.getenv("INDEPENDENT_HEIGHT", 480))
CAMERA_FPS = int(os.getenv("INDEPENDENT_FPS", 6))
CAMERA_QUALITY = int(os.getenv("INDEPENDENT_QUALITY", 70))
ROTATION = int(os.getenv("LIBCAM_ROTATION", 180))
DETECTION_INTERVAL_SECONDS = float(os.getenv("TFLITE_DETECTION_INTERVAL", 0.4))
BEHAVIOR_COOLDOWN_SECONDS = float(os.getenv("INDEPENDENT_BEHAVIOR_COOLDOWN", 6.0))
JPEG_OUTPUT_QUALITY = int(os.getenv("INDEPENDENT_JPEG_QUALITY", 75))
LOG_LIMIT = 50


class IndependentModeService:
    def __init__(
        self,
        detector_factory=None,
        behavior_runner=trigger_bucket_behavior,
        camera_command_resolver=get_camera_command,
        popen=subprocess.Popen,
        time_fn=time.monotonic,
        sleep_fn=time.sleep,
    ):
        self._detector_factory = detector_factory or self._default_detector_factory
        self._behavior_runner = behavior_runner
        self._camera_command_resolver = camera_command_resolver
        self._popen = popen
        self._time_fn = time_fn
        self._sleep_fn = sleep_fn
        self._detector = None
        self._process = None
        self._worker_thread = None
        self._behavior_thread = None
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._latest_frame = None
        self._event_log = []
        self._last_completed_times = {}
        self._active_behavior_bucket = None
        self._latest_summary = "Waiting for detections"
        self._latest_buckets = {}
        self._worker_error = None
        self._stop_requested = False

    def _default_detector_factory(self):
        return TFLiteObjectDetector(
            model_path=MODEL_PATH,
            num_threads=2,
            enable_edgetpu=ENABLE_EDGE_TPU,
        )

    def _append_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        log(message)
        with self._lock:
            self._event_log.append(entry)
            if len(self._event_log) > LOG_LIMIT:
                self._event_log.pop(0)

    def get_log_entries(self):
        with self._lock:
            return list(self._event_log)

    def get_worker_error(self):
        with self._lock:
            return self._worker_error

    def _get_detector(self):
        if self._detector is None:
            self._detector = self._detector_factory()
        return self._detector

    def _build_camera_command(self):
        camera_command = self._camera_command_resolver()
        return [
            camera_command,
            "-t",
            "0",
            "--codec",
            "mjpeg",
            "--inline",
            "--width",
            str(CAMERA_WIDTH),
            "--height",
            str(CAMERA_HEIGHT),
            "--framerate",
            str(CAMERA_FPS),
            "--quality",
            str(CAMERA_QUALITY),
            "--rotation",
            str(ROTATION),
            "-o",
            "-",
        ]

    def start(self):
        with self._lock:
            if self._worker_thread and self._worker_thread.is_alive():
                return
            self._stop_requested = False
            self._worker_error = None

        self._get_detector()
        command = self._build_camera_command()
        self._worker_thread = threading.Thread(target=self._worker_loop, args=(command,), daemon=True)
        self._worker_thread.start()

    def cleanup(self):
        with self._lock:
            self._stop_requested = True
            self._condition.notify_all()

        if self._process and self._process.poll() is None:
            self._append_log("Stopping independent mode camera process")
            self._process.terminate()
            self._process.wait()
        self._process = None

    def _should_trigger(self, bucket, now):
        last_completed = self._last_completed_times.get(bucket)
        if last_completed is None:
            return True
        return (now - last_completed) >= BEHAVIOR_COOLDOWN_SECONDS

    def _run_behavior(self, bucket):
        try:
            behavior_name = self._behavior_runner(bucket)
            if behavior_name:
                self._append_log(f"Completed behavior for {bucket}: {behavior_name}")
        finally:
            with self._lock:
                self._last_completed_times[bucket] = self._time_fn()
                self._active_behavior_bucket = None

    def _trigger_behaviors(self, buckets, now):
        with self._lock:
            if self._active_behavior_bucket is not None:
                return

        for bucket in prioritized_buckets(buckets):
            if not self._should_trigger(bucket, now):
                continue

            with self._lock:
                if self._active_behavior_bucket is not None:
                    return
                self._active_behavior_bucket = bucket
            self._append_log(f"Matched {bucket}; triggering behavior")
            self._behavior_thread = threading.Thread(target=self._run_behavior, args=(bucket,), daemon=True)
            self._behavior_thread.start()
            break

    def _update_frame(self, frame_bytes, buckets, summary_text):
        with self._condition:
            self._latest_frame = frame_bytes
            self._latest_buckets = buckets
            self._latest_summary = summary_text
            self._condition.notify_all()

    def _worker_loop(self, command):
        try:
            self._append_log(f"Starting independent camera pipeline with {command[0]}")
            self._process = self._popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0,
            )
            if self._process.stdout is None:
                raise RuntimeError("Independent camera process did not provide stdout")

            detector = self._get_detector()
            last_detections = []
            last_detection_time = 0.0

            for frame_bytes in iter_mjpeg_frames(self._process.stdout):
                with self._lock:
                    if self._stop_requested:
                        break

                frame = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                now = self._time_fn()
                if now - last_detection_time >= DETECTION_INTERVAL_SECONDS:
                    last_detections = detector.detect(frame)
                    buckets = bucket_detections(last_detections)
                    summary_text = summarize_detections(last_detections)
                    self._trigger_behaviors(buckets, now)
                    if buckets:
                        self._append_log(f"Detected {summary_text}")
                    last_detection_time = now
                else:
                    buckets = self._latest_buckets
                    summary_text = self._latest_summary

                annotated = draw_detections(frame.copy(), last_detections, summary_text=summary_text)
                success, encoded = cv2.imencode(
                    ".jpg",
                    annotated,
                    [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_OUTPUT_QUALITY],
                )
                if not success:
                    continue

                self._update_frame(encoded.tobytes(), buckets, summary_text)
        except Exception as exc:
            self._append_log(f"Independent mode error: {exc}")
            with self._lock:
                self._worker_error = str(exc)
        finally:
            if self._process and self._process.poll() is None:
                self._process.terminate()
                self._process.wait()
            self._process = None

    def stream_frames(self):
        self.start()

        while True:
            with self._condition:
                if self._worker_error:
                    raise RuntimeError(self._worker_error)

                if self._latest_frame is None:
                    self._condition.wait(timeout=1.0)
                    if self._worker_error:
                        raise RuntimeError(self._worker_error)
                    frame = self._latest_frame
                else:
                    frame = self._latest_frame

            if frame is None:
                self._sleep_fn(0.1)
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame
                + b"\r\n"
            )
            self._sleep_fn(max(0.01, 1 / max(CAMERA_FPS, 1)))


independent_mode_service = IndependentModeService()
