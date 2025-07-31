from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import imagingcontrol4 as ic4
from PyQt6.QtCore.QProcess import state

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

PIXEL_FORMAT_TO_ENVI_FORMAT = {
    ic4.PixelFormat.Mono8: 1,
    ic4.PixelFormat.BayerGB8: 1,
    ic4.PixelFormat.BayerGB16: 12,
}


@dataclass
class TisCameraState:
    save_folder: Path
    current_exposure: int
    pixel_format: ic4.PixelFormat = ic4.PixelFormat.BayerGB16
    demosaic: bool = False
    save_subfolder: str | None = None

    @property
    def save_path(self) -> Path | None:
        if self.save_subfolder is None:
            return None
        else:
            return self.save_folder / self.save_subfolder

    def bit_depth(self) -> int:
        bit_depth = PIXEL_FORMAT_TO_BIT_DEPTH_MAP[self.pixel_format]
        return bit_depth


def get_envi_header(state: TisCameraState) -> dict:
    wl = [  # GB (Green-Blue) config
        [550, 450],
        [650, 550],
    ]
    wl_flat = [w for wa in wl for w in wa]
    envi_data_type = PIXEL_FORMAT_TO_ENVI_FORMAT[state.pixel_format]
    bit_depth = f"{state.bit_depth()} bits"
    return {
        'samples': TIS_WIDTH,  # width in pixels
        'lines': TIS_HEIGHT,  # height in pixels
        'bands': 1,  # raw mosaic has one band
        'interleave': 'bsq',
        'byte order': 0,  # little endian (0)
        'data type': envi_data_type,  # 1 = uint8, 12 = uint16
        'sensor type': 'The Imaging Source DFK 23UX236',

        'spatial resolution': '1920 x 1200',
        'spectral range': '450-650 nm',
        'bands count': '3 bands',
        'bit depth': bit_depth,
        # 'pixel pitch': '5.5 μm',
        # 'imager type': 'CMOS, CMOSIS CMV2000 based',
        # 'acquisition speed': 'up to 120 hyperspectral cubes/second (USB3.0 limited)',
        # 'optics': '16/25/35/50 mm lenses, F2.8, C-mount',
        'interface': 'USB3.0 + GPIO + I/O for triggering',
        # 'power consumption': '1.6 Watt',
        # 'dimensions': '26 x 26 x 31 mm',
        # 'weight': '32 g (without optics)',

        'acquisition time': datetime.now().isoformat(),
        'description': 'Bayer mosaic image snapshot.',
        'filter array size': '2x2',
        'wavelength units': 'Nanometers',
        'wavelength': wl_flat,
        'note': 'Raw mosaic. Wavelengths are listed in row-major order (left to right, top to bottom).'
    }


class TisCamera(Camera):
    grabber: ic4.Grabber
    sink: ic4.SnapSink | None
    state: TisCameraState

    def __init__(self, pixel_format: ic4.PixelFormat = TIS_DEFAULT_PIXEL_FORMAT):
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

    def _get_frame_view(
            self,
            frame: np.ndarray,
    ) -> np.ndarray:
        frame_normalized = frame.astype(np.float32) / (2 ** self.bit_depth() - 1)
        frame_view = np.mean(frame_normalized, axis=-2)
        return frame_view

    def get_frame(self, timeout_ms: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Returns a numpy frame and its view.
        """
        image_buffer = self.sink.snap_single(timeout_ms=timeout_ms)
        frame = image_buffer.numpy_wrap()
        frame_view = self._get_frame_view(
            frame=frame,
        )
        return frame, frame_view

    def get_envi_options(self) -> dict:
        return get_envi_header(state=self.state)

    def set_save_subfolder(self, subfolder: str) -> None:
        self.state.save_subfolder = subfolder
        self.state.save_path.mkdir(parents=False, exist_ok=True)

    def save_folder(self) -> Path:
        return self.state.save_path

    def exception_type(self) -> Exception:
        return ic4.IC4Exception

    def exposure(self) -> int:
        return self.state.current_exposure

    def set_exposure(self, exposure: int) -> bool:
        self.state.current_exposure = exposure
        return True

    def init_exposure(self, max_exposure: int) -> None:
        pass

    def adjust_exposure(self) -> None:
        pass

    def check_exposure(self, frame: np.ndarray) -> bool:
        pass

    def toggle_view(self) -> None:
        self.state.demosaic = not self.state.demosaic


def main():
    cam = TisCamera(pixel_format=ic4.PixelFormat.BayerGB16)

    cam.open()

    frame, frame_view = cam.get_frame()
    print(f"frame type: {frame.dtype}, max: {frame.max()}")
    print(f"frame_view type: {frame_view.dtype}, max: {frame_view.max()}")

    cam.close()


if __name__ == "__main__":
    main()
