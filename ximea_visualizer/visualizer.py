from pathlib import Path
from functools import partial
from typing import Any
from dataclasses import dataclass
from datetime import datetime


from ximea import xiapi
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


@dataclass
class CameraState:
    save_folder: Path
    paused: bool = False
    demosaic: bool = False
    record: bool = False
    save_subfolder: str | None = None

    @property
    def save_path(self) -> Path | None:
        if self.save_subfolder is None:
            return None
        else:
            return self.save_folder / self.save_subfolder

def demosaic(arr: np.ndarray) -> np.ndarray:
    out = np.empty((arr.shape[0] // 4, arr.shape[1] // 4, 16), dtype=arr.dtype)
    for ii in range(4):
        for jj in range(4):
            out[:, :, jj + 4 * ii] = arr[ii::4, jj::4]
    return out

def demosaic_tiled(arr: np.ndarray):
    bands = arr.transpose(2, 0, 1).reshape(4, 4, arr.shape[0], arr.shape[1])
    return np.block([[bands[i, j] for j in range(4)] for i in range(4)])

def get_images(
    frame: np.ndarray, 
    demosaic_flag: bool,
) -> tuple[np.ndarray, np.ndarray]:
    frame_normalized = np.array(frame, dtype=np.float32) / 255
    if not demosaic_flag:
        return frame_normalized, frame_normalized
    dem = demosaic(arr=frame_normalized)
    tiles = demosaic_tiled(arr=dem)
    return frame_normalized, tiles


def update(
    frame_index: int,
    state: CameraState,
    cam: xiapi.Camera,
    img: xiapi.Image,
    im: Any, 
):
    cam.get_image(img)
    frame = img.get_image_data_numpy()
    frame_normalized, demosaiced = get_images(frame=frame, demosaic_flag=state.demosaic)
    if not state.paused:
        if not state.demosaic:
            im.set_data(frame_normalized)
        else:
            im.set_data(demosaiced)
    if state.record and state.save_path is not None:
        savefile = state.save_path / f"frame_{frame_index}.npy"
        np.save(file=f"{savefile}", arr=frame)
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


def main():
    # Initialize camera
    cam = xiapi.Camera()
    cam.open_device()
    cam.set_exposure(10000)
    cam.start_acquisition()
    img  = xiapi.Image()


    # Initial frame
    fig, ax = plt.subplots()
    cam.get_image(img)
    frame = img.get_image_data_numpy()
    frame_normalized, _ = get_images(frame=frame, demosaic_flag=False)
    ax.set_title("P to pause/unpause, R to start/stop recording, M to switch view")

    im = ax.imshow(frame_normalized, cmap="gray")
    
    data_folder = Path(__file__).resolve().parents[1] / "data"
    data_folder.mkdir(parents=False, exist_ok=True)
    state = CameraState(save_folder=data_folder)

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


if __name__ == "__main__":
    main()
