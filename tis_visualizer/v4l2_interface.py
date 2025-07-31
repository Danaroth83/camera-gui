# v4l2_camera.py (updated)

import numpy as np
from pathlib import Path
from gi.repository import Gst
from enum import Enum

from ximea_visualizer.mock_interface import Camera


class SaveFormatEnum(Enum):
    PNG = 'png'
    TIFF = 'tiff'


class V4L2Camera(Camera):
    def __init__(self, device='/dev/video3', width=1920, height=1200):
        Gst.init(None)
        self.device = device
        self._width = width
        self._height = height
        self._bit_depth = 8  # Default to 8-bit
        self._pipeline = None
        self._appsink = None
        self._frame_count = 0

    def open(self):
        if self._bit_depth == 8:
            raw_format = "GRAY8"
        elif self._bit_depth == 16:
            raw_format = "GRAY16_LE"
        else:
            raise ValueError(f"Unsupported bit depth: {self._bit_depth}")

        pipeline_desc = f"""
            v4l2src device={self.device} !
            video/x-raw,format={raw_format},width={self._width},height={self._height} !
            videoconvert !
            video/x-raw,format=RGB !
            appsink name=sink emit-signals=false sync=false max-buffers=1 drop=true
        """
        self._pipeline = Gst.parse_launch(pipeline_desc)
        self._appsink = self._pipeline.get_by_name('sink')
        self._pipeline.set_state(Gst.State.PLAYING)

    def close(self):
        if self._pipeline:
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
            self._appsink = None

    def get_frame(self):
        sample = self._appsink.emit('pull-sample')
        if not sample:
            raise RuntimeError("Failed to pull frame from appsink")

        buf = sample.get_buffer()
        caps = sample.get_caps()
        width = caps.get_structure(0).get_value('width')
        height = caps.get_structure(0).get_value('height')

        success, map_info = buf.map(Gst.MapFlags.READ)
        if not success:
            raise RuntimeError("Failed to map buffer")

        try:
            frame = np.frombuffer(map_info.data, dtype=np.uint8)
            frame = frame.reshape((height, width, 3))
            frame = frame.astype(np.float32)
            if self._bit_depth == 8:
                frame /= 255.0
            else:
                frame /= 65535.0  # if you later support real RGB16
        finally:
            buf.unmap(map_info)

        self._frame_count += 1
        return frame, None

    def shape(self):
        return (self._height, self._width)

    def bit_depth(self) -> int:
        return self._bit_depth

    def toggle_bit_depth(self):
        self._bit_depth = 16 if self._bit_depth == 8 else 8
        self.close()
        self.open()

    def exposure(self) -> int:
        raise NotImplementedError()

    def set_exposure(self, exposure: int) -> bool:
        raise NotImplementedError()

    def init_exposure(self):
        pass

    def adjust_exposure(self):
        pass

    def check_exposure(self, frame: np.ndarray) -> bool:
        return True

    def toggle_view(self):
        pass

    def get_envi_options(self):
        return None

    def set_save_subfolder(self, subfolder: str):
        pass

    def save_folder(self) -> Path:
        return Path(".")

    def exception_type(self):
        return RuntimeError
