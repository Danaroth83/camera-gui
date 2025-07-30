import sys
from dataclasses import dataclass

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5.QtCore import QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from ximea import xiapi

from ximea_visualizer.visualizer import CameraState, init_camera

@dataclass
class Camera:
    cam: xiapi.Camera
    img: xiapi.Image

    @classmethod
    def start(cls):
        cam, img = init_camera()
        return cls(cam=cam, img=img)

    def change_exposure(self, exposure: int):
        self.cam.

    def toggle_bits(self):




class VideoPlayer(QWidget):
    def __init__(
        self,
        state: CameraState,
        cam: xiapi.Camera,
        img: xiapi.Image,
    ):
        super().__init__()
        self.setWindowTitle("XIMEA video Player")
        self.state = state
        self.cam = cam
        self.img = img

        self.label = QLabel("Waiting for image...")
        self.button = QPushButton("Pause")
        self.button.clicked.connect(self.toggle)
        self.running = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)

    def toggle_play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
            self.playButton.setText("Play")
        else:
            self.mediaPlayer.play()
            self.playButton.setText("Pause")

    def update_frame(self):
        if not self.running:
            return
        self.cam.get_image(self.img)
        if image:
            qimg = self.pil2pixmap(self.img)
            self.label.setPixmap(qimg)



def main():
    app = QApplication(sys.argv)
    cam, img = init_camera()


    player = VideoPlayer(cam=cam, img=img, state=state, fps=30)
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()