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

XIMEA_MOSAIC_R = 4
XIMEA_MOSAIC_C = 4
XIMEA_MIN_EXPOSURE = 100
XIMEA_MAX_EXPOSURE = 499_950
XIMEA_DYNRANGE = 255

@dataclass
class CameraState:
    save_folder: Path
    current_exposure: int
    paused: bool = False
    demosaic: bool = False
    record: bool = False
    estimating_exposure: bool = False
    min_exposure: int = XIMEA_MIN_EXPOSURE
    max_exposure: int = XIMEA_MAX_EXPOSURE
    save_subfolder: str | None = None

    @property
    def save_path(self) -> Path | None:
        if self.save_subfolder is None:
            return None
        else:
            return self.save_folder / self.save_subfolder

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
            out[:, :, jj + XIMEA_MOSAIC_R * ii] = arr[ii::XIMEA_MOSAIC_R, jj::XIMEA_MOSAIC_R]
    return out

def demosaic_tiled(arr: np.ndarray):
    bands = arr.transpose(2, 0, 1)
    bands = bands.reshape(XIMEA_MOSAIC_R, XIMEA_MOSAIC_C, arr.shape[0], arr.shape[1])
    return np.block([
        [bands[i, j] for j in range(XIMEA_MOSAIC_C)] 
        for i in range(XIMEA_MOSAIC_R)
    ])

def get_images(
    frame: np.ndarray, 
    demosaic_flag: bool,
) -> tuple[np.ndarray, np.ndarray]:
    frame_normalized = np.array(frame, dtype=np.float32) / XIMEA_DYNRANGE
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
    saturated = (frame >= XIMEA_DYNRANGE).sum()
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


def update(
    frame_index: int,
    state: CameraState,
    cam: xiapi.Camera,
    img: xiapi.Image,
    im: Any, 
):
    if state.estimating_exposure:
        cam.set_exposure(state.current_exposure)
        print(f"Min: {state.min_exposure}, Max: {state.max_exposure}")
        print(f"Exposure set to {state.current_exposure} us")

    cam.get_image(img)
    frame = img.get_image_data_numpy()
    frame_normalized, demosaiced = get_images(
        frame=frame,
        demosaic_flag=state.demosaic,
    )
    if not state.paused:
        if not state.demosaic:
            im.set_data(frame_normalized)
        else:
            im.set_data(demosaiced)
    if state.record and state.save_path is not None:
        savefile = state.save_path / f"frame_{frame_index}.npy"
        np.save(file=f"{savefile}", arr=frame)

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


def main_run(exposure: int = 10_000):
    # Initialize camera
    cam = xiapi.Camera()
    cam.open_device()
    cam.set_exposure(exposure)
    cam.start_acquisition()
    img  = xiapi.Image()


    # Initial frame
    fig, ax = plt.subplots()
    cam.get_image(img)
    frame = img.get_image_data_numpy()
    frame_normalized, _ = get_images(frame=frame, demosaic_flag=False)
    ax.set_title(
        "P to pause/unpause, R to start/stop recording, M to switch view, E for calibrating exposure time."
    )

    im = ax.imshow(frame_normalized, cmap="gray")
    
    data_folder = Path(__file__).resolve().parents[1] / "data"
    data_folder.mkdir(parents=False, exist_ok=True)
    state = CameraState(save_folder=data_folder, current_exposure=exposure)

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
    args = parser.parse_args()
    main_run(exposure=args.exposure)

if __name__ == "__main__":
    main()
