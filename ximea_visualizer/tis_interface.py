

from ximea_visualizer.mock_interface import Camera

<<<<<<< HEAD

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


=======
>>>>>>> 739332a8026cf4380f14b4881ecbf033cd842a6e
class TisCamera(Camera):

    def open():
        