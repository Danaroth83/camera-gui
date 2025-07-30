from functools import partial
from typing import Any
from datetime import datetime
import argparse

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from ximea_visualizer.mock_interface import MockCamera, Camera
from ximea_visualizer.serializer import SaveFormatEnum


class VisualizerState:
    paused: bool = False
    record: bool = False
    bit_depth_selector: bool = False
    estimating_exposure: bool = False
    demosaic: bool = False


def on_key(event, state: VisualizerState, camera: Camera):
    if event.key == "p":
        state.paused = not state.paused
        print("Paused" if state.paused else "Resumed")
    if event.key == "m":
        camera.toggle_view()
        state.demosaic = False if state.demosaic else True
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
            camera.set_save_subfolder(subfolder=timestamp)
            print("Recording")
        else:
            print("Stopped recording")
    if event.key == "e":
        camera.init_exposure()
        state.estimating_exposure = True


def update(
    frame_index: int,
    state: VisualizerState,
    camera: Camera,
    filename_stem: str,
    im: Any, 
):
    if state.bit_depth_selector:
        camera.toggle_bit_depth()
        print("Switched bit depth")
        state.bit_depth_selector = False
    if state.estimating_exposure:
        camera.adjust_exposure()
        print(f"Exposure set to {camera.exposure()} us")

    frame_save, frame_view = camera.get_frame()

    if not state.paused:
        im.set_data(frame_view)
    if state.record and camera.save_folder().exists():
        camera.save_frame(
            frame=frame_save,
            filename_stem=f"{filename_stem}_{frame_index}",
            fmt=SaveFormatEnum.ENVI,
        )
    if state.estimating_exposure:
        converged = camera.check_exposure(frame=frame_save)
        state.estimating_exposure = not converged
    return [im]


def main_run(
    exposure: int = 10_000,
    filename_stem: str = "frame",    
):
    try:
        from ximea_visualizer.ximea_interface import XimeaCamera
        camera = XimeaCamera()
    except ImportError:
        camera = MockCamera()
    except Exception as e:
        raise e

    camera.open(exposure=exposure)
    camera.toggle_bit_depth()
    frame, frame_normalized = camera.get_frame()
    fig, ax = plt.subplots()
    ax.set_title(
        "P to pause/unpause, R to start/stop recording, M to switch view,\n"+
        "E for calibrating exposure time, B to change bit depth."
    )
    im = ax.imshow(frame_normalized, cmap="gray")

    state = VisualizerState()

    update_fn = partial(update, state=state, camera=camera, filename_stem=filename_stem, im=im)
    ani = FuncAnimation(
        fig,
        update_fn,
        interval=30,
        blit=True,
        cache_frame_data=False,
    )
    
    on_key_update = partial(on_key, state=state, camera=camera)
    fig.canvas.mpl_connect('key_press_event', on_key_update)

    try:
        plt.show()
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        camera.close()


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
