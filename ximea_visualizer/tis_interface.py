from dataclasses import dataclass
from pathlib import Path

import imagingcontrol4 as ic4
from ximea_visualizer.mock_interface import Camera


@dataclass
class TisCameraState:
    save_folder: Path
    current_exposure: int
    # demosaic: bool = False
    # bit_depth_10bits: bool = False
    # min_exposure: int = XIMEA_MIN_EXPOSURE
    # max_exposure: int = XIMEA_MAX_EXPOSURE
    # filename_stem: str = "frame"
    # save_subfolder: str | None = None

    def sync(self, cam: ic4.Grabber):
        pass


class TisCamera(Camera):
    grabber : ic4.Grabber
    sink: ic4.SnapSink | None
    state: TisCameraState

    def __init__(self): 
        self.grabber = ic4.Grabber()
        self.sink = None
        data_path = Path(__file__).resolve().parents[1] / "data"
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
        self.grabber.device_open(first_device_info)
        self.sink = ic4.SnapSink()
        self.grabber.stream_setup(self.sink, setup_option=ic4.StreamSetupOption.ACQUISITION_START)
        
    def close(self):
        self.grabber.stream_stop()
        
    def set_save_subfolder(self, subfolder: str) -> None:
        self.state.save_subfolder = subfolder
        self.state.save_path.mkdir(parents=False, exist_ok=True)

    def save_folder(self) -> Path:
        return self.state.save_path
    
    def exception_type(self) -> Exception:
        return ic4.Exception