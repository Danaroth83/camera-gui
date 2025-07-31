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
        cam.device_property_map.set_value


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


class TisCamera(Camera):
    grabber : ic4.Grabber
    sink: ic4.SnapSink | None
    state: TisCameraState

    def __init__(self): 
        self.grabber = ic4.Grabber()
        self.sink = None

    def open(self):
        first_device_info = ic4.DeviceEnum.devices()[0]
        self.grabber.device_open(first_device_info)
        self.sink = ic4.SnapSink()
        self.grabber.stream_setup(self.sink, setup_option=ic4.StreamSetupOption.ACQUISITION_START)
        
    def close(self):
        self.grabber.stream_stop()
        

