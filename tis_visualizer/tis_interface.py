from dataclasses import dataclass
from pathlib import Path

import imagingcontrol4 as ic4

from ximea_visualizer.paths import load_project_dir

ic4.Library.init()

import numpy as np

from ximea_visualizer.mock_interface import Camera

TIS_HEIGHT = 1920
TIS_WIDTH = 1200
TIS_DEFAULT_PIXEL_FORMAT = ic4.PixelFormat.Mono8

# bit_depth_map = {
#     ic4.PixelFormat.Mono8: 8,
# }

@dataclass
class TisCameraState:
    save_folder: Path
    current_exposure: int
    save_subfolder: str | None = None
    timeout_ms: int = 1000

    @property
    def save_path(self) -> Path:
        if self.save_subfolder is None:
            return self.save_folder
        else:
            return self.save_folder / self.save_subfolder


class TisCamera(Camera):
    grabber: ic4.Grabber
    sink: ic4.SnapSink | None
    state: TisCameraState

    def __init__(self):
        self.grabber = ic4.Grabber(dev=None)
        self.sink = None
        data_path = load_project_dir() / "data"
        data_path.mkdir(parents=False, exist_ok=True)
        data_path = data_path / "tis"
        data_path.mkdir(parents=False, exist_ok=True)
        state = TisCameraState(
            save_folder=data_path,
            current_exposure=10_000,
        )
        self.state = state

    def open(self):
        first_device_info = ic4.DeviceEnum.devices()[0]
        self.grabber.device_open(dev=first_device_info)
        self.sink = ic4.SnapSink()
        self.grabber.stream_setup(
            sink=self.sink,
            setup_option=ic4.StreamSetupOption.ACQUISITION_START,
        )

    def close(self):
        self.grabber.stream_stop()

    def shape(self) -> tuple[int, int]:
        pass

    def bit_depth(self) -> int:
        pass

    def toggle_bit_depth(self) -> None:
        pass

    def get_frame(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns a numpy frame and its view.
        """
        print(
            f"Sink: {self.sink}\n"
            f"\tType: {self.sink.type}\n"
            f"\tOutput image type: {self.sink.output_image_type}"
        )

        image_buffer = self.sink.snap_single(timeout_ms=self.state.timeout_ms)
        print(f"Received an image. ImageType: {image_buffer.image_type}")

        frame_np = image_buffer.numpy_wrap()
        print(
            f"Frame NumPy: {frame_np.shape}\n"
            f"\tType: {type(frame_np)}\n"
            f"\tData Type: {frame_np.dtype}"
        )

        return frame_np, frame_np

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
    cam = TisCamera()

    cam.open()

    frame, frame_view = cam.get_frame()

    cam.close()


if __name__ == "__main__":
    main()
