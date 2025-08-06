from dataclasses import dataclass
from datetime import datetime
from typing import Type

import numpy as np
from pathlib import Path

from ximea import xiapi

from camera_visualizer.camera_interface.mock_interface import Camera
from camera_visualizer.paths import load_data_path

XIMEA_MOSAIC_R = 4
XIMEA_MOSAIC_C = 4
XIMEA_MIN_EXPOSURE = 7_000
XIMEA_MAX_EXPOSURE = 499_950
XIMEA_EXPOSURE_INCREMENT = 10
XIMEA_FPS_MIN = 1
XIMEA_FPS_MAX = 170
XIMEA_FPS_INCREMENT = 1
XIMEA_DYN_RANGE_10BIT = 1023
XIMEA_DYN_RANGE_8BIT = 255
XIMEA_HEIGHT = 1088
XIMEA_WIDTH = 2048


@dataclass
class CameraState:
    save_folder: Path
    current_exposure: int
    demosaic: bool = False
    bit_depth_10bits: bool = False
    min_exposure: int = XIMEA_MIN_EXPOSURE
    max_exposure: int = XIMEA_MAX_EXPOSURE
    filename_stem: str = "frame"
    save_subfolder: str | None = None

    def sync(self, cam: xiapi.Camera):
        self.current_exposure = cam.get_exposure()
        if cam.get_image_data_bit_depth() == "XI_BPP_10":
            self.bit_depth_10bits = True
        else:
            self.bit_depth_10bits = False

    @property
    def save_path(self) -> Path | None:
        if self.save_subfolder is None:
            return None
        else:
            return self.save_folder / self.save_subfolder

    @property
    def dynamic_range(self):
        return XIMEA_DYN_RANGE_10BIT if self.bit_depth_10bits else XIMEA_DYN_RANGE_8BIT

    @property
    def bit_depth(self):
        return 10 if self.bit_depth_10bits else 8


def demosaic(arr: np.ndarray) -> np.ndarray:
    out = np.empty(
        (
            arr.shape[0] // XIMEA_MOSAIC_R,
            arr.shape[1] // XIMEA_MOSAIC_C,
            XIMEA_MOSAIC_R * XIMEA_MOSAIC_C,
        ),
        dtype=arr.dtype,
    )
    for ii in range(XIMEA_MOSAIC_R):
        for jj in range(XIMEA_MOSAIC_C):
            idx = jj + XIMEA_MOSAIC_C * (XIMEA_MOSAIC_R - 1 - ii)
            out[:, :, idx] = arr[ii::XIMEA_MOSAIC_R, jj::XIMEA_MOSAIC_R]
    return out


def demosaic_tiled(arr: np.ndarray):
    out = []
    for ii in range(XIMEA_MOSAIC_R):
        out_list = []
        for jj in range(XIMEA_MOSAIC_C):
            idx = jj + XIMEA_MOSAIC_C * (XIMEA_MOSAIC_R - 1 - ii)
            out_list.append(arr[:, :, idx])
        out.append(out_list)
    return np.block(out)


def get_envi_header(state: CameraState) -> dict:
    wl = [
        [800, 820, 840, 860],
        [720, 740, 760, 780],
        [655, 660, 680, 700],
        [595, 610, 625, 640],
    ]
    wl_flat = [w for wa in wl for w in wa]
    data_type = 12 if state.bit_depth_10bits else 1
    bit_depth = "10 bits" if state.bit_depth_10bits else "8 bits"
    return {
        'samples': XIMEA_WIDTH,  # width in pixels
        'lines': XIMEA_HEIGHT,  # height in pixels
        'bands': 1,  # raw mosaic has one band
        'interleave': 'bsq',
        'byte order': 0,  # little endian (0)
        'data type': data_type,  # 1 = uint8, 12 = uint16
        'sensor type': 'XIMEA MQ02HG-IM-SM4x4-REDNIR',

        'spatial resolution': '512 x 272 (per band, SNm4x4 REDNIR version)',
        'spectral resolution': '~10-15 nm (collimated)',
        'spectral range': '595-860 nm (SNm4x4 RedNIR version)',
        'bands count': '16 bands',
        'bit depth': bit_depth,
        'pixel pitch': '5.5 μm',
        'imager type': 'CMOS, CMOSIS CMV2000 based',
        'acquisition speed': 'up to 120 hyperspectral cubes/second (USB3.0 limited)',
        'optics': '16/25/35/50 mm lenses, F2.8, C-mount',
        'interface': 'USB3.0 + GPIO + I/O for triggering',
        'power consumption': '1.6 Watt',
        'dimensions': '26 x 26 x 31 mm',
        'weight': '32 g (without optics)',

        'acquisition time': datetime.now().isoformat(),
        'exposure time (ms)': f"{state.current_exposure / 1000:.3f}",
        'description': 'Raw 4x4 mosaic snapshot. Each 4×4 tile encodes 16 spectral bands.',
        'filter array size': '4x4',
        'wavelength units': 'Nanometers',
        'wavelength': wl_flat,
        'note': 'Raw mosaic. Wavelengths are listed in row-major order (left to right, top to bottom).'
    }


def get_images(
    frame: np.ndarray,
    demosaic_flag: bool,
    dynamic_range: int,
) -> np.ndarray:
    frame_normalized = np.array(frame, dtype=np.float32) / dynamic_range
    if not demosaic_flag:
        return frame_normalized
    dem = demosaic(arr=frame_normalized)
    tiles = demosaic_tiled(arr=dem)
    return tiles


def get_frame(
    cam: xiapi.Camera,
    img: xiapi.Image,
    state: CameraState,
) -> tuple[np.ndarray, np.ndarray]:
    cam.get_image(img)
    frame = img.get_image_data_numpy()
    frame_view = get_images(
        frame=frame,
        demosaic_flag=state.demosaic,
        dynamic_range=state.dynamic_range,
    )
    return frame, frame_view


def find_exposure_for_saturation(
    state: CameraState,
    frame: np.ndarray,
) -> bool:
    """
    Binary search for exposure time to keep saturated pixels under max_saturation.
    """
    # Amount of allowed saturated pixels
    max_saturation = 1000 if state.bit_depth_10bits else 8000
    # Tolerated difference in number of saturated pixels
    tol = 250 if state.bit_depth_10bits else 2000

    converged = False
    saturated = (frame >= state.dynamic_range).sum()
    if saturated > max_saturation:
        state.max_exposure = state.current_exposure - 1
    else:
        state.min_exposure = state.current_exposure + 1
    tmp = state.max_exposure - state.min_exposure
    mid_exposure = int((state.max_exposure + state.min_exposure) // 2)

    if (
        abs(saturated - max_saturation) < tol 
        or abs(tmp) < 10
        or abs(state.current_exposure - mid_exposure) <= 2 * XIMEA_EXPOSURE_INCREMENT
    ):
        converged = True
    return converged


def switch_bit_depth(
    cam: xiapi.Camera,
    state: CameraState,
) -> None:
    if state.bit_depth_10bits:
        cam.set_imgdataformat("XI_MONO8")
        cam.set_image_data_bit_depth("XI_BPP_8")
        state.bit_depth_10bits = False
        print("Changed to 8 bits")
    else:
        cam.set_imgdataformat("XI_MONO16")
        cam.set_image_data_bit_depth("XI_BPP_10")
        state.bit_depth_10bits = True
        print("Changed to 10 bits")


class XimeaCamera(Camera):
    cam: xiapi.Camera
    img: xiapi.Image
    state: CameraState

    def __init__(self):
        self.cam = xiapi.Camera()
        self.img = None
        data_path = load_data_path()
        data_path.mkdir(parents=False, exist_ok=True)
        data_path = data_path / "ximea"
        data_path.mkdir(parents=False, exist_ok=True)
        state = CameraState(
            save_folder=data_path,
            current_exposure=10_000,
        )
        self.state = state

    def open(self):
        self.cam.open_device()
        self.cam.start_acquisition()
        self.img = xiapi.Image()
        self.state.sync(cam=self.cam)

    def close(self):
        self.cam.stop_acquisition()
        self.cam.close_device()

    def toggle_bit_depth(self):
        switch_bit_depth(cam=self.cam, state=self.state)

    def bit_depth(self) -> int:
        return self.state.bit_depth

    def get_frame(self, fps: float) -> tuple[np.ndarray, np.ndarray]:
        if self.img is None:
            raise ValueError("Camera was not opened. Run self.open() before this operation.")
        return get_frame(
            cam=self.cam,
            img=self.img,
            state=self.state,
        )

    def shape(self) -> tuple[int, int]:
        return XIMEA_HEIGHT, XIMEA_WIDTH

    def exposure(self) -> int:
        return int(self.state.current_exposure)

    def exposure_range(self) -> tuple[int, int, int]:
        return XIMEA_MIN_EXPOSURE, XIMEA_MAX_EXPOSURE, XIMEA_EXPOSURE_INCREMENT

    def fps_range(self) -> tuple[int, int, int]:
        return XIMEA_FPS_MIN, XIMEA_FPS_MAX, XIMEA_FPS_INCREMENT

    def set_exposure(self, exposure: int) -> bool:
        if abs(self.state.current_exposure - exposure) <= XIMEA_EXPOSURE_INCREMENT:
            return False
        if exposure <= XIMEA_MIN_EXPOSURE or exposure >= XIMEA_MAX_EXPOSURE:
            return False
        try:
            self.cam.set_exposure(exposure)
        except xiapi.Xi_error:
            return False
        self.state.current_exposure = exposure
        return True

    def init_exposure(self, max_exposure: int) -> None:
        self.state.max_exposure = min(XIMEA_MAX_EXPOSURE, max_exposure)
        self.state.min_exposure = XIMEA_MIN_EXPOSURE

    def adjust_exposure(self) -> int:
        return int((self.state.max_exposure + self.state.min_exposure) // 2)

    def check_exposure(self, frame: np.ndarray) -> bool:
        return find_exposure_for_saturation(
            state=self.state,
            frame=frame,
        )

    def set_save_subfolder(self, subfolder: str) -> None:
        self.state.save_subfolder = subfolder
        self.state.save_path.mkdir(parents=False, exist_ok=True)

    def save_folder(self) -> Path:
        return self.state.save_path

    def toggle_view(self):
        self.state.demosaic = not self.state.demosaic

    def exception_type(self) -> Type[Exception]:
        return xiapi.Xi_error

    def get_envi_options(self) -> dict:
        return get_envi_header(state=self.state)
 