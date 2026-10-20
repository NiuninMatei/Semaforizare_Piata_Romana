"""Citirea fluxului HLS al camerei Webcam România (sau a unui fișier video local).

Fluxul HLS (.m3u8) este o listă de segmente .ts de ~6 s; OpenCV îl citește prin FFmpeg.
Cititorul rulează pe un fir separat și păstrează doar ultimul cadru (nu se stochează nimic
pe disc – principiul minimizării datelor, GDPR art. 5 alin. (1) lit. c).
"""
from __future__ import annotations

import os
import threading
import time

import cv2

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")


class FrameSource:
    """Sursă de cadre cu reconectare automată.

    - pentru URL-uri (stream live) se citește continuu și se livrează ultimul cadru
      la frecvența cerută (`target_fps`);
    - pentru fișiere se livrează cadrele în ordine, eșantionate la `target_fps`.
    """

    def __init__(self, source: str, target_fps: float = 6.0):
        self.source = source
        self.is_live = source.startswith(("http://", "https://", "rtsp://"))
        self.target_fps = target_fps
        self._cap = None
        self._lock = threading.Lock()
        self._frame = None
        self._frame_time = 0.0
        self._stop = threading.Event()
        self.native_fps = 0.0
        self.reconnects = 0
        self.connected = False
        if self.is_live:
            os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", f"user_agent;{UA}")
            self._thread = threading.Thread(target=self._reader, daemon=True)
            self._thread.start()
        else:
            self._open()

    # ------------------------------------------------------------------ intern
    def _open(self) -> bool:
        if self._cap is not None:
            self._cap.release()
        self._cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
        ok = self._cap.isOpened()
        self.connected = ok
        if ok:
            self.native_fps = self._cap.get(cv2.CAP_PROP_FPS) or 18.0
        return ok

    def _reader(self) -> None:
        backoff = 1.0
        while not self._stop.is_set():
            if not self._open():
                self.reconnects += 1
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                continue
            backoff = 1.0
            while not self._stop.is_set():
                ok, frame = self._cap.read()
                if not ok:
                    self.connected = False
                    self.reconnects += 1
                    break
                with self._lock:
                    self._frame = frame
                    self._frame_time = time.time()

    # ------------------------------------------------------------------ public
    def frames(self):
        """Generator de (timestamp_sec, cadru)."""
        if self.is_live:
            period = 1.0 / self.target_fps
            last_t = 0.0
            while not self._stop.is_set():
                with self._lock:
                    frame, ft = self._frame, self._frame_time
                if frame is None or ft == last_t:
                    time.sleep(0.01)
                    continue
                last_t = ft
                yield ft, frame
                # respectă frecvența țintă (procesarea însăși poate fi mai lentă)
                time.sleep(max(0.0, period - (time.time() - ft)))
        else:
            step = max(1, round((self.native_fps or 18.0) / self.target_fps))
            idx = 0
            while True:
                ok, frame = self._cap.read()
                if not ok:
                    return
                if idx % step == 0:
                    yield idx / (self.native_fps or 18.0), frame
                idx += 1

    def snapshot(self, timeout: float = 30.0):
        """Un singur cadru (pentru calibrarea zonelor)."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            for _, f in self.frames():
                return f
            time.sleep(0.5)
        return None

    def close(self) -> None:
        self._stop.set()
        if self._cap is not None:
            self._cap.release()
