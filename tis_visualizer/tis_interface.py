from dataclasses import dataclass
from pathlib import Path

import imagingcontrol4 as ic4

from ximea_visualizer.paths import load_project_dir

ic4.Library.init()

import numpy as np

from ximea_visualizer.mock_interface import Camera

TIS_HEIGHT = 1200
TIS_WIDTH = 1920
TIS_DEFAULT_PIXEL_FORMAT = ic4.PixelFormat.BayerGB16

TIS_ACCEPTED_PIXEL_FORMATS = [
    ic4.PixelFormat.Mono8,
    ic4.PixelFormat.BayerGB8,
    ic4.PixelFormat.BayerGB16,
]

PIXEL_FORMAT_TO_BIT_DEPTH_MAP = {
    ic4.PixelFormat.Mono8: 8,
    ic4.PixelFormat.BayerGB8: 8,
    ic4.PixelFormat.BayerGB16: 16,
}

PIXEL_FORMAT_TO_SHAPE = {
    ic4.PixelFormat.Mono8: (TIS_HEIGHT, TIS_WIDTH, 1),
    ic4.PixelFormat.BayerGB8: (TIS_HEIGHT, TIS_WIDTH, 1),
    ic4.PixelFormat.BayerGB16: (TIS_HEIGHT, TIS_WIDTH, 1),
}

@dataclass
class TisCameraState:
    save_folder: Path
    current_exposure: int
    pixel_format: ic4.PixelFormat = ic4.PixelFormat.BayerGB16
    save_subfolder: str | None = None
    timeout_ms: int = 1000

    @property
    def save_path(self) -> Path:
        if self.save_subfolder is None:
            return self.save_folder
        else:
            return self.save_folder / self.save_subfolder

    def bit_depth(self) -> int:
        bit_depth = PIXEL_FORMAT_TO_BIT_DEPTH_MAP[self.pixel_format]
        return bit_depth


class TisCamera(Camera):
    grabber: ic4.Grabber
    sink: ic4.SnapSink | None
    state: TisCameraState

    def __init__(self, pixel_format: ic4.PixelFormat):
        self.grabber = ic4.Grabber(dev=None)
        self.sink = None
        data_path = load_project_dir() / "data"
        data_path.mkdir(parents=False, exist_ok=True)
        data_path = data_path / "tis"
        data_path.mkdir(parents=False, exist_ok=True)
        state = TisCameraState(
            save_folder=data_path,
            current_exposure=10_000,
            pixel_format=pixel_format,
        )
        self.state = state

    def open(self):
        first_device_info = ic4.DeviceEnum.devices()[0]
        self.grabber.device_open(dev=first_device_info)
        self.sink = ic4.SnapSink(
            accepted_pixel_formats=[
                self.state.pixel_format,
            ]
        )
        self.grabber.stream_setup(
            sink=self.sink,
            setup_option=ic4.StreamSetupOption.ACQUISITION_START,
        )

    def close(self):
        self.grabber.stream_stop()
        self.grabber.device_close()

    def shape(self) -> tuple[int, int]:
        return TIS_HEIGHT, TIS_WIDTH

    def bit_depth(self) -> int:
        return self.state.bit_depth()

    def toggle_bit_depth(self) -> None:
        pass

    def get_frame(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns a numpy frame and its view.
        """
        image_buffer = self.sink.snap_single(timeout_ms=self.state.timeout_ms)
        frame_np = image_buffer.numpy_wrap()
        frame_normalized = frame_np / (2 ** self.bit_depth() - 1)
        return frame_normalized, frame_normalized

    def get_envi_options(self) -> None:
        pass

    def set_save_subfolder(self, subfolder: str) -> None:
        self.state.save_subfolder = subfolder
        self.state.save_path.mkdir(parents=False, exist_ok=True)

    def save_folder(self) -> Path:
        return self.state.save_path

    def exception_type(self) -> Exception:
        return ic4.IC4Exception

    def exposure(self) -> int:
        pass

    def set_exposure(self, exposure: int) -> bool:
        pass

    def init_exposure(self) -> None:
        pass

    def adjust_exposure(self) -> None:
        pass

    def check_exposure(self, frame: np.ndarray) -> bool:
        pass

    def toggle_view(self) -> None:
        pass


def main():
    cam = TisCamera(pixel_format=ic4.PixelFormat.BayerGB16)

    cam.open()

    frame, frame_view = cam.get_frame()
    print(f"frame type: {frame.dtype}, max: {frame.max()}")
    print(f"frame_view type: {frame_view.dtype}, max: {frame_view.max()}")

    cam.close()


if __name__ == "__main__":
    main()
