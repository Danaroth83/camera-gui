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

from camera_visualizer.camera_interface.mock_interface import Camera, \
    CameraEnum, camera
from camera_visualizer.serializer import SaveFormatEnum


@dataclass
class GuiState:
    selected_camera: CameraEnum = CameraEnum.MOCK
    fps: float = 30
    frame_counter: int = 0
    recording: bool = False
    running: bool = False
    paused: bool = False
    estimating_exposure: bool = False
    exposure_tries: int = 0
    recording_format: SaveFormatEnum = SaveFormatEnum.ENVI
    filename_stem: str = "frame"


class VideoPlayer(QWidget):
    camera: Camera


    def __init__(
        self,
        fps: float,
        camera_id: CameraEnum | str = CameraEnum.MOCK,
    ):
        super().__init__()
        self.camera = camera(camera_id=camera_id)
        self.state = GuiState(selected_camera=camera_id, fps=fps)

        self.setWindowTitle("Camera Video Player")
        self.label = QLabel("Waiting for image...")
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.toggle_running)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_pausing)
        
        self.view_button = QPushButton("Toggle view")
        self.view_button.clicked.connect(self.toggle_view)

        # FPS and Exposure Inputs
        self.fps_input = QLineEdit(f"{self.state.fps}")
        self.exposure_input = QLineEdit(f"{self.camera.exposure():d}")
        self.filename_input = QLineEdit(self.state.filename_stem)
        self.exposure_input.setEnabled(False)
        
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

        self.camera_select = QComboBox()
        self.camera_select.addItems([e.value for e in CameraEnum])
        self.camera_select.currentIndexChanged.connect(self.choose_camera)
        self.camera_select.setCurrentText(self.state.selected_camera)
        self.camera_select.setEnabled(True)
        
        self.exposure_button = QPushButton("Estimate Exposure Time")
        self.exposure_button.clicked.connect(self.toggle_exposure)
        
        self.bit_depth_button = QPushButton(f"Toggle bit depth: {self.camera.bit_depth()}")
        self.bit_depth_button.clicked.connect(self.toggle_bit_depth)

        # Layouts
        control_layout = QFormLayout()
        control_layout.addRow("FPS:", self.fps_input)
        control_layout.addRow("Exposure (μs):", self.exposure_input)
        control_layout.addRow("Filename:", self.filename_input)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.camera_select)
        layout.addWidget(self.view_button)
        layout.addWidget(self.bit_depth_button)
        layout.addWidget(self.exposure_button)
        layout.addWidget(self.recording_label)
        layout.addWidget(self.record_button)
        layout.addWidget(self.record_format)
        layout.addLayout(control_layout)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 // self.state.fps))

    def toggle_running(self) -> None:
        if not self.state.running:
            try:
                self.camera = camera(camera_id=self.state.selected_camera)
                self.camera.open()
            except self.camera.exception_type() as e:
                print(e)
                return
            self.camera_select.setEnabled(False)
            self.exposure_input.setEnabled(True)
            self.exposure_input.setText(f"{self.camera.exposure()}")
        else:
            self.camera_select.setEnabled(True)
            self.exposure_input.setEnabled(False)
            self.camera.close()
        self.state.paused = False
        self.pause_button.setText("Pause")
        self.state.running = not self.state.running
        self.play_button.setText("Stop" if self.state.running else "Play")
        
    def toggle_pausing(self) -> None:
        if not self.state.running:
            return
        self.state.paused = not self.state.paused
        self.pause_button.setText("Pause" if not self.state.paused else "Resume")

    def toggle_view(self) -> None:
        if (not self.state.running) or self.state.paused:
            return
        self.camera.toggle_view()
        
    def toggle_bit_depth(self):
        if (not self.state.running) or self.state.paused or self.state.recording:
            return
        self.camera.toggle_bit_depth()
        self.bit_depth_button.setText(f"Toggle bit depth: {self.camera.bit_depth()}")

    def toggle_recording(self):
        if (not self.state.running) or self.state.paused:
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
        if (not self.state.running) or self.state.paused or self.state.estimating_exposure:
            return
        self.state.estimating_exposure = True
        self.state.exposure_tries = 0
        self.exposure_button.setText("Estimating exposure time...")
        self.exposure_input.setEnabled(False)
        self.camera.init_exposure(max_exposure=int(1_000_000 // self.state.fps))

    def set_record_format(self):
        selected_value = self.record_format.currentText()
        self.state.recording_format = SaveFormatEnum(selected_value)

    def choose_camera(self):
        if self.state.running:
            return
        selected_value = self.camera_select.currentText()
        self.state.selected_camera = CameraEnum(selected_value)


    @staticmethod
    def numpy_to_pixmap(arr: np.ndarray):
        arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
        if arr.ndim == 2 or (arr.ndim == 3 and arr.shape[2] == 1):  # Grayscale
            qimg = QImage(
                arr.data, 
                arr.shape[1], 
                arr.shape[0], 
                arr.shape[1], 
                QImage.Format_Grayscale8,
            )
        elif arr.ndim == 3:  # RGB
            arr = arr[..., :3]
            qimg = QImage(
                arr.data, 
                arr.shape[1], 
                arr.shape[0], 
                arr.shape[2] * arr.shape[1], 
                QImage.Format_RGB888,
            )
        else:
            ValueError("Image not displayable")
        return QPixmap.fromImage(qimg.copy())

    def update_frame(self):
        if (not self.state.running) or self.state.paused:
            return
        if self.state.estimating_exposure:
            self.camera.adjust_exposure()
            self.exposure_input.setText(f"{self.camera.exposure()}")
        frame_save, frame_view = self.camera.get_frame(fps=self.state.fps)
        if frame_view is not None:
            pixmap = self.numpy_to_pixmap(arr=frame_view)
            self.label.setPixmap(pixmap)
        if self.state.recording:
            filename = f"frame_{self.state.frame_counter:04d}"
            self.camera.save_frame(
                filename_stem=filename,
                frame=frame_save,
                fmt=self.state.recording_format,
            )
            self.state.frame_counter += 1
        if self.state.estimating_exposure:
            converged = self.camera.check_exposure(frame=frame_save)
            self.state.estimating_exposure = not converged
            self.state.exposure_tries += 1
            if self.state.exposure_tries >=50:
                self.state.estimating_exposure = False
            if not self.state.estimating_exposure:
                self.state.exposure_tries = 0
                self.exposure_input.setEnabled(True)
                self.exposure_button.setText("Estimate Exposure Time")

    def update_fps(self):
        try:
            fps_val = float(self.fps_input.text())
            if fps_val <= 0:
                return
            self.state.fps = fps_val
            self.timer.setInterval(int(1000 // self.state.fps))
        except ValueError:
            pass  # Ignore invalid input

    def update_exposure(self):
        if (not self.state.running) or self.state.paused:
            return
        try:
            exposure_val = int(self.exposure_input.text())
            self.camera.set_exposure(exposure_val)
        except (ValueError, self.camera.exception_type()):
            self.exposure_input.setText(f"{self.camera.exposure()}")

    def update_filename(self):
        try:
            exposure_val = str(self.exposure_input.text())
            self.state.filename_stem = exposure_val
        except ValueError:
            pass


def main():
    app = QApplication(sys.argv)
    try:
        from camera_visualizer.camera_interface.ximea_interface import XimeaCamera
        camera_id = CameraEnum.XIMEA
    except ImportError:
        camera_id = CameraEnum.MOCK
    except Exception as e:
        raise e
    player = VideoPlayer(camera_id=camera_id, fps=30)
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
