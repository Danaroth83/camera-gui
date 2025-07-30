from pathlib import Path
from functools import partial
from typing import Any
from dataclasses import dataclass
from datetime import datetime
import argparse

from ximea import xiapi
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import spectral

XIMEA_MOSAIC_R = 4
XIMEA_MOSAIC_C = 4
XIMEA_MIN_EXPOSURE = 100
XIMEA_MAX_EXPOSURE = 499_950
XIMEA_DYN_RANGE_10BIT = 1023
XIMEA_DYN_RANGE_8BIT = 255


@dataclass
class CameraState:
    save_folder: Path
    current_exposure: int
    paused: bool = False
    demosaic: bool = False
    record: bool = False
    bit_depth_selector: bool = False
    estimating_exposure: bool = False
    min_exposure: int = XIMEA_MIN_EXPOSURE
    max_exposure: int = XIMEA_MAX_EXPOSURE
    filename_stem: str = "frame"
    bit_depth_max: bool = False
    save_subfolder: str | None = None

    @property
    def save_path(self) -> Path | None:
        if self.save_subfolder is None:
            return None
        else:
            return self.save_folder / self.save_subfolder
    
    @property
    def dynamic_range(self):
        return XIMEA_DYN_RANGE_10BIT if self.bit_depth_max else XIMEA_DYN_RANGE_8BIT

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

def save_frame(
    state: CameraState,
    frame: np.ndarray,
    array_index: int,
    save_folder: Path,
    filename_stem: str,
    format: str = "envi",
):
    if format == "numpy":
        np.save(file=save_folder / f"{filename_stem}_{array_index}.npy", arr=frame)
    elif format == "envi":
        # ---- Metadata ----
        wl = [
            [800, 820, 840, 860],
            [720, 740, 760, 780],
            [655, 660, 680, 700],
            [595, 610, 625, 640],
        ]
        wl_flat = [w for wa in wl for w in wa] 
        data_type = 12 if state.bit_depth_max else 1
        bit_depth = "10 bits" if state.bit_depth_max else "8 bits"
        metadata = {
            'samples': frame.shape[1],  # width in pixels
            'lines': frame.shape[0],    # height in pixels
            'bands': 1,                 # raw mosaic has one band
            'interleave': 'bsq',
            'byte order': 0,            # little endian (0)
            'data type': data_type,      # 1 = uint8, 12 = uint16
            'sensor type': 'XIMEA MQ02HG-IM-SM4x4',

            'spatial resolution': '512 x 272 (per band, SNm4x4 VIS version)',
            'spectral resolution': '~10-15 nm (collimated)',
            'spectral range': '460-620 nm (SNm4x4 VIS version), 595-860 nm (SNm4x4 RedNIR version)',
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
            'description': 'Raw 4x4 mosaic snapshot. Each 4×4 tile encodes 16 spectral bands.',
            'filter array size': '4x4',
            'wavelength units': 'Nanometers',
            'wavelength': wl_flat,
            'note': 'Raw mosaic. Wavelengths are listed in row-major order (left to right, top to bottom).'
        }
        spectral.envi.save_image(
            hdr_file=save_folder / f'{filename_stem}_{array_index}.hdr',
            image=frame,
            dtype=np.uint8,
            ext=".img",
            force=True,
            interleave='bsq',
            metadata=metadata,
        )
    else:
        raise ValueError(f"File format {format} unknown.")

def get_images(
    frame: np.ndarray, 
    demosaic_flag: bool,
    dynamic_range: int,
) -> tuple[np.ndarray, np.ndarray]:
    frame_normalized = np.array(frame, dtype=np.float32) / dynamic_range
    if not demosaic_flag:
        return frame_normalized, frame_normalized
    dem = demosaic(arr=frame_normalized)
    tiles = demosaic_tiled(arr=dem)
    return frame_normalized, tiles


def find_exposure_for_saturation(
    state: CameraState,
    frame: np.ndarray,
    max_saturation: int = 8000,
    tol: int = 1000,  # tolerated difference in number of saturated pixels
) -> bool:
    """
    Binary search for exposure time to keep saturated pixels under max_saturation.
    """

    converged = False
    saturated = (frame >= state.dynamic_range).sum()
    mid_exposure = (state.max_exposure + state.min_exposure) // 2
    if saturated > max_saturation:
        state.max_exposure = mid_exposure - 1
    else:
        state.min_exposure = mid_exposure + 1
    tmp = state.max_exposure - state.min_exposure 
    state.current_exposure = (state.max_exposure + state.min_exposure) // 2 
    if abs(saturated - max_saturation) < tol or abs(tmp) < 10:
        converged = True
    return converged


def switch_bit_depth(
    cam: xiapi.Camera,
    state: CameraState,
) -> None:
    if state.bit_depth_max:
        cam.set_imgdataformat("XI_MONO8")
        cam.set_image_data_bit_depth("XI_BPP_8")
        state.bit_depth_max = False
        print("Changed to 8 bits")
    else:
        cam.set_imgdataformat("XI_MONO16")
        cam.set_image_data_bit_depth("XI_BPP_10")
        state.bit_depth_max = True
        print("Changed to 10 bits")

def update(
    frame_index: int,
    state: CameraState,
    cam: xiapi.Camera,
    img: xiapi.Image,
    im: Any, 
):
    if state.bit_depth_selector:
        switch_bit_depth(cam=cam, state=state)
        state.bit_depth_selector = False
    if state.estimating_exposure:
        cam.set_exposure(state.current_exposure)
        print(f"Min: {state.min_exposure}, Max: {state.max_exposure}")
        print(f"Exposure set to {state.current_exposure} us")

    cam.get_image(img)
    frame = img.get_image_data_numpy()
    frame_normalized, demosaiced = get_images(
        frame=frame,
        demosaic_flag=state.demosaic,
        dynamic_range=state.dynamic_range,
    )
    if not state.paused:
        if not state.demosaic:
            im.set_data(frame_normalized)
        else:
            im.set_data(demosaiced)
    if state.record and state.save_path is not None:
        save_frame(
            state=state,
            frame=frame,
            array_index=frame_index,
            filename_stem=state.filename_stem,
            save_folder=state.save_path,
        )
    if state.estimating_exposure:
        converged = find_exposure_for_saturation(
            state=state,
            frame=frame,
        )
        state.estimating_exposure = not converged
    return [im]


def on_key(event, state: CameraState):
    if event.key == "p":
        state.paused = not state.paused
        print("Paused" if state.paused else "Resumed")
    if event.key == "m":
        state.demosaic = not state.demosaic
        if state.demosaic:
            print("Switched to demosaic view.")
        else:
            print("Switched to raw view.")
    if event.key == "b":
        state.bit_depth_selector = True
    if event.key == "r":
        state.record = not state.record
        if state.record:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            state.save_subfolder = timestamp
            state.save_path.mkdir(parents=False, exist_ok=True)
            print("Recording")
        else:
            print("Stopped recording")
    if event.key == "e":
        state.min_exposure = XIMEA_MIN_EXPOSURE
        state.max_exposure = XIMEA_MAX_EXPOSURE
        state.current_exposure = (state.max_exposure + state.min_exposure) // 2
        state.estimating_exposure = True


def init_camera(
    exposure: int = 10_000,
) -> tuple[xiapi.Camera, xiapi.Image]:
    # Initialize camera
    cam = xiapi.Camera()
    cam.open_device()
    cam.set_exposure(exposure)
    cam.start_acquisition()
    img  = xiapi.Image()
    return cam, img


def main_run(
    exposure: int = 10_000,
    filename_stem: str = "frame",    
):
    cam, img = init_camera(exposure=exposure)

    # Setting initial state
    data_folder = Path(__file__).resolve().parents[1] / "data"
    data_folder.mkdir(parents=False, exist_ok=True)
    state = CameraState(
        save_folder=data_folder, 
        current_exposure=exposure,
        filename_stem=filename_stem,
    )

    # Initial frame
    switch_bit_depth(cam=cam, state=state)
    cam.get_image(img)
    fig, ax = plt.subplots()
    frame = img.get_image_data_numpy()
    frame_normalized, _ = get_images(frame=frame, demosaic_flag=False, dynamic_range=state.dynamic_range)
    ax.set_title(
        "P to pause/unpause, R to start/stop recording, M to switch view,\n"+
        "E for calibrating exposure time, B to change bit depth."
    )
    im = ax.imshow(frame_normalized, cmap="gray")


    update_fn = partial(update, cam=cam, img=img, im=im, state=state)
    ani = FuncAnimation(fig, update_fn, interval=30, blit=True)
    
    on_key_update = partial(on_key, state=state)
    fig.canvas.mpl_connect('key_press_event', on_key_update)

    try:
        plt.show()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        cam.stop_acquisition()
        cam.close_device()


def main():
    parser = argparse.ArgumentParser(description="Setting up exposure time")
    parser.add_argument(
        "-e",
        "--exposure",
        type=int,
        default=10000,
        help="Choose the exposure time in microseconds.",
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default="frame",
        help="Choose the savefile name.",
    )
    args = parser.parse_args()
    main_run(
        exposure=args.exposure,
        filename_stem=args.name,    
    )

if __name__ == "__main__":
    main()
