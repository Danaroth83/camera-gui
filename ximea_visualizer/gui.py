import sys
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QLineEdit,
    QFormLayout,
    QComboBox,
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap

from ximea_visualizer.mock_interface import Camera, MockCamera
from ximea_visualizer.serializer import SaveFormatEnum


@dataclass
class GuiState:
    fps: float = 30
    frame_counter: int = 0
    recording: bool = False
    running: bool = False
    estimating_exposure: bool = False
    recording_format: SaveFormatEnum = SaveFormatEnum.ENVI
    filename_stem: str = "frame"


class VideoPlayer(QWidget):
    def __init__(
        self,
        camera: Camera,
        fps: float,
    ):
        super().__init__()
        self.camera = camera
        self.state = GuiState(fps=fps)

        self.setWindowTitle("XIMEA video Player")
        self.label = QLabel("Waiting for image...")
        self.button = QPushButton("Play")
        self.button.clicked.connect(self.toggle)
        self.view_button = QPushButton("Toggle view")
        self.view_button.clicked.connect(self.camera.toggle_view)

        # FPS and Exposure Inputs
        self.fps_input = QLineEdit("30")
        self.exposure_input = QLineEdit(str(self.camera.exposure()))
        self.filename_input = QLineEdit(self.state.filename_stem)

        self.fps_input.editingFinished.connect(self.update_fps)
        self.exposure_input.editingFinished.connect(self.update_exposure)

        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        self.recording_label = QLabel("")
        self.recording_label.setStyleSheet("color: red; font-weight: bold")

        self.record_format = QComboBox()
        self.record_format.addItems([e.value for e in SaveFormatEnum])
        self.record_format.currentIndexChanged.connect(self.set_record_format)
        self.record_format.setCurrentText(self.state.recording_format)

        # Layouts
        control_layout = QFormLayout()
        control_layout.addRow("FPS:", self.fps_input)
        control_layout.addRow("Exposure (μs):", self.exposure_input)
        control_layout.addRow("Filename:", self.filename_input)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.view_button)
        layout.addWidget(self.recording_label)
        layout.addWidget(self.record_button)
        layout.addWidget(self.record_format)
        layout.addLayout(control_layout)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 // self.state.fps)

    def toggle(self):
        self.state.running = not self.state.running
        self.button.setText("Resume" if not self.state.running else "Pause")

    def toggle_recording(self):
        if not self.state.running:
            return
        self.state.recording = not self.state.recording
        if self.state.recording:
            self.record_format.setEnabled(False)
            self.filename_input.setEnabled(False)
            self.state.frame_counter = 0
            self.record_button.setText("Stop Recording")
            self.recording_label.setText("RECORDING")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.camera.set_save_subfolder(subfolder=timestamp)
        else:
            self.record_format.setEnabled(True)
            self.filename_input.setEnabled(True)
            self.record_button.setText("Start Recording")
            self.recording_label.setText("")

    def toggle_exposure(self):
        self.state.estimating_exposure = True
        self.camera.init_exposure()

    def set_record_format(self, index):
        selected_value = self.record_format.currentText()
        self.state.recording_format = SaveFormatEnum(selected_value)

    @staticmethod
    def numpy_to_pixmap(arr: np.ndarray):
        """Convert a (H, W) float32 NumPy array in [0, 1] to QPixmap"""
        arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
        h, w = arr.shape
        qimg = QImage(arr.data, w, h, w, QImage.Format_Grayscale8)
        return QPixmap.fromImage(qimg.copy())

    def update_frame(self):
        if not self.state.running:
            return
        if self.state.estimating_exposure:
            self.camera.adjust_exposure()
        frame_save, frame_view = self.camera.get_frame()
        if frame_view is not None:
            pixmap = self.numpy_to_pixmap(arr=frame_view)
            self.label.setPixmap(pixmap)
        if self.state.recording:
            filename = f"frame_{self.state.frame_counter:04d}.png"
            self.camera.save_frame(
                filename_stem=filename,
                frame=frame_save,
                fmt=self.state.recording_format,
            )
            self.state.frame_counter += 1
        if self.state.estimating_exposure:
            self.state.estimating_exposure = self.camera.check_exposure(
                frame=frame_save,
            )

    def update_fps(self):
        try:
            fps_val = float(self.fps_input.text())
            if fps_val <= 0:
                return
            self.state.fps = fps_val
            self.timer.setInterval(1000 // self.state.fps)
        except ValueError:
            pass  # Ignore invalid input

    def update_exposure(self):
        try:
            exposure_val = int(self.exposure_input.text())
            if exposure_val > 0:
                self.camera.set_exposure(exposure_val)
        except ValueError:
            pass

    def update_filename(self):
        try:
            exposure_val = str(self.exposure_input.text())
            self.state.filename_stem = exposure_val
        except ValueError:
            pass


def main():
    app = QApplication(sys.argv)
    try:
        from ximea_visualizer.ximea_interface import XimeaCamera
        camera = XimeaCamera()
    except ImportError:
        camera = MockCamera()
    except Exception as e:
        raise e
    player = VideoPlayer(camera=camera, fps=30)
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()