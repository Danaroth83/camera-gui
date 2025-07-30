import sys
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

import numpy as np

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, \
    QVBoxLayout, QLineEdit, QFormLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtGui import QImage, QPixmap

from ximea_visualizer.mock_interface import Camera, MockCamera


class VideoPlayer(QWidget):
    def __init__(
        self,
        camera: Camera,
        fps: int,
    ):
        super().__init__()
        self.camera = camera

        self.setWindowTitle("XIMEA video Player")
        self.label = QLabel("Waiting for image...")
        self.button = QPushButton("Pause")
        self.button.clicked.connect(self.toggle)
        self.view_button = QPushButton("Toggle view")
        self.view_button.clicked.connect(self.camera.toggle_view)
        self.running = False

        # FPS and Exposure Inputs
        self.fps_input = QLineEdit("30")
        self.exposure_input = QLineEdit(str(self.camera.exposure()))

        self.fps_input.editingFinished.connect(self.update_fps)
        self.exposure_input.editingFinished.connect(self.update_exposure)

        # Layouts
        control_layout = QFormLayout()
        control_layout.addRow("FPS:", self.fps_input)
        control_layout.addRow("Exposure (μs):", self.exposure_input)


        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.view_button)
        layout.addLayout(control_layout)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / fps))

    def toggle(self):
        self.running = not self.running
        self.button.setText("Resume" if not self.running else "Pause")

    def toggle_recording(self):
        self.recording = not self.recording
        if self.recording:
            self.frame_counter = 0
            self.record_button.setText("Stop Recording")
            self.recording_label.setText("RECORDING")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.camera.set_save_subfolder(subfolder=timestamp)
        else:
            self.record_button.setText("Start Recording")
            self.recording_label.setText("")

    def numpy_to_pixmap(self, arr: np.ndarray):
        """Convert a (H, W) float32 NumPy array in [0, 1] to QPixmap"""
        arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
        h, w = arr.shape
        qimg = QImage(arr.data, w, h, w, QImage.Format_Grayscale8)
        return QPixmap.fromImage(qimg.copy())

    def update_frame(self):
        if not self.running:
            return
        frame_save, frame_view = self.camera.get_frame()
        if frame_view is not None:
            pixmap = self.numpy_to_pixmap(frame_view)
            self.label.setPixmap(pixmap)
        if self.recording:
            filename = f"frame_{self.frame_counter:04d}.png"
            self.camera.save_frame(
                filename_stem=filename,
                frame=frame_save,
                fmt="numpy",
            )
            self.frame_counter += 1

    def update_fps(self):
        try:
            fps_val = float(self.fps_input.text())
            if fps_val <= 0:
                return
            self.fps = fps_val
            self.timer.setInterval(int(1000 / self.fps))
        except ValueError:
            pass  # Ignore invalid input

    def update_exposure(self):
        try:
            exposure_val = int(self.exposure_input.text())
            if exposure_val > 0:
                self.camera.set_exposure(exposure_val)
        except ValueError:
            pass



def main():
    app = QApplication(sys.argv)
    camera = MockCamera()
    player = VideoPlayer(camera=camera, fps=30)
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()