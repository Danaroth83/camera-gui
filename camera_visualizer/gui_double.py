import sys

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QApplication

from camera_visualizer.gui import VideoPlayer
from camera_visualizer.camera_interface.mock_interface import CameraEnum


class DoubleVideoPlayer(QWidget):

    def __init__(
        self,
        fps_a: int = 30,
        fps_b: int = 30,
        camera_a: CameraEnum = CameraEnum.MOCK,
        camera_b: CameraEnum = CameraEnum.MOCK,
    ):
        super().__init__()
        self.player_a = VideoPlayer(fps=fps_a, camera_id=camera_a)
        self.player_b = VideoPlayer(fps=fps_b, camera_id=camera_b)
        layout = QHBoxLayout()

        layout.addWidget(self.player_a)
        layout.addWidget(self.player_b)
        self.setLayout(layout)



def main():
    app = QApplication(sys.argv)
    try:
        from camera_visualizer.camera_interface.ximea_interface import XimeaCamera
        camera_a = CameraEnum.XIMEA
    except ImportError:
        camera_a = CameraEnum.MOCK
    except Exception as e:
        raise e
    try:
        from camera_visualizer.camera_interface.tis_interface import TisCamera
        camera_b = CameraEnum.TIS
    except ImportError:
        camera_b = CameraEnum.MOCK
    except Exception as e:
        raise e
    player = DoubleVideoPlayer(camera_a=camera_a, camera_b=camera_b)
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()