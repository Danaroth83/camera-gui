import imagingcontrol4 as ic4
from ximea_visualizer.mock_interface import Camera


TIS_HEIGHT = 1920
TIS_WIDTH = 1200


class TisCamera(Camera):
    def __init__(
            self,
            device_idx: int = 0,
    ):
        self.camera = ic4.DeviceEnum.devices()[device_idx]

    def open(self):
        # Create a Grabber object
        grabber = ic4.Grabber()
        # Open the first available video capture device
        device_info =
        grabber.device_open(first_device_info)


def main():
    pass


if __name__ == "__main__":
    main()
