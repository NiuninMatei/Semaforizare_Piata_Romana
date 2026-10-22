"""Citirea fluxului HLS al camerei Webcam România (sau a unui fișier video local).

Fluxul HLS (.m3u8) este o listă de segmente .ts de 6 s; OpenCV îl citește prin FFmpeg. Un segment
sosește dintr-odată și se decodează în ~2 s, apoi cititorul așteaptă următorul segment: fără tampon,
imaginea ar „alerga” 2 s și ar sta 4 s, iar cadrele analizate ar fi neuniforme în timp. De aceea
cititorul (fir separat) pune cadrele, eșantionate la `target_fps` după marcajul de timp al fluxului,
într-un tampon în memorie, iar `frames()` le redă uniform, cu o întârziere fixă (`delay`, implicit
8 s = un segment + marjă). Nu se stochează nimic pe disc (principiul minimizării datelor,
GDPR art. 5 alin. (1) lit. c); tamponul ține doar câteva secunde de cadre.
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque

import cv2

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")


class FrameSource:
    """Sursă de cadre cu reconectare automată.

    - pentru URL-uri (stream live) se citește continuu și se redă uniform, cu întârzierea
      `delay`, la frecvența cerută (`target_fps`);
    - pentru fișiere se livrează cadrele în ordine, eșantionate la `target_fps`.
    """

    def __init__(self, source: str, target_fps: float = 6.0, delay: float = 8.0):
        self.source = source
        self.is_live = source.startswith(("http://", "https://", "rtsp://"))
        self.target_fps = target_fps
        self.delay = delay
        self._cap = None
        self._lock = threading.Lock()
        # (marcaj de timp al fluxului în s, cadru); limita protejează memoria dacă redarea rămâne în urmă
        self._buf: deque = deque(maxlen=int(target_fps * (delay + 6)) + 1)
        self._epoch = 0          # crește la fiecare reconectare (marcajele de timp o iau de la capăt)
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
            with self._lock:
                self._buf.clear()
                self._epoch += 1
            n, last_kept = 0, -1e9
            while not self._stop.is_set():
                ok, frame = self._cap.read()
                if not ok:
                    self.connected = False
                    self.reconnects += 1
                    break
                n += 1
                pts = self._cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0 or n / self.native_fps
                if pts - last_kept < 0.9 / self.target_fps and pts >= last_kept:
                    continue            # eșantionare la target_fps pe ceasul fluxului
                last_kept = pts
                with self._lock:
                    self._buf.append((pts, frame))

    # ------------------------------------------------------------------ public
    def frames(self):
        """Generator de (timestamp_sec, cadru)."""
        if self.is_live:
            offset, epoch = None, -1      # ora de redare = marcajul fluxului + offset
            while not self._stop.is_set():
                now = time.time()
                frame = None
                with self._lock:
                    if self._buf:
                        newest = self._buf[-1][0]
                        # ancorarea pe cel mai nou cadru (la pornire, după reconectare, dacă fluxul a stat
                        # sau dacă sosește dintr-odată o restanță de segmente): redăm de la marginea live
                        # cu întârzierea `delay`, iar restanța mai veche se sare
                        if (self._epoch != epoch or newest + offset < now - 3.0
                                or newest + offset > now + self.delay + 7.0):
                            epoch, offset = self._epoch, now + self.delay - newest
                    if offset is not None:
                        # cel mai recent cadru a cărui oră de redare a venit; cele mai vechi se aruncă
                        while self._buf and self._buf[0][0] + offset <= now:
                            frame = self._buf.popleft()[1]
                if frame is None:
                    time.sleep(0.01)
                    continue
                yield now, frame
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
