from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from enum import Enum

import numpy as np
from ximea_visualizer.serializer import save_frame, SaveFormatEnum


class Camera(ABC):

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def toggle_bit_depth(self) -> None:
        ...

    @abstractmethod
    def bit_depth(self) -> int:
        ...

    @abstractmethod
    def get_frame(self) -> tuple[np.ndarray, np.ndarray]:
        ...

    @abstractmethod
    def shape(self) -> tuple[int, int]:
        ...

    @abstractmethod
    def exposure(self) -> int:
        ...

    @abstractmethod
    def set_exposure(self, exposure: int) -> bool:
        ...

    @abstractmethod
    def init_exposure(self) -> None:
        ...

    @abstractmethod
    def adjust_exposure(self) -> None:
        ...

    @abstractmethod
    def check_exposure(self, frame: np.ndarray) -> bool:
        ...

    @abstractmethod
    def toggle_view(self) -> None:
        ...

    @abstractmethod
    def get_envi_options(self) -> None:
        ...

    @abstractmethod
    def set_save_subfolder(self, subfolder: str) -> None:
        ...

    @abstractmethod
    def save_folder(self) -> Path:
        ...

    @abstractmethod
    def exception_type(self) -> Exception:
        ...

    def save_frame(
        self,
        frame: np.ndarray,
        filename_stem: str,
        fmt: SaveFormatEnum
    ) -> None:
        save_frame(
            frame=frame,
            save_folder=self.save_folder(),
            filename_stem=filename_stem,
            envi_options=self.get_envi_options(),
            fmt=fmt,
        )


class MockCamera(Camera):

    def __init__(self):
        self._shape = [480, 640]
        self._exposure = 10_000
        self._exposure_max = 500_000
        self._exposure_min = 100
        self._bit_depth = 8
        self._counter = 0
        self._toggle_view = 0
        data_path = Path(__file__).resolve().parents[1] / "data/mock"
        data_path.mkdir(parents=True, exist_ok=True)
        self._save_folder = data_path
        self._subfolder = None

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def toggle_bit_depth(self):
        self._bit_depth = 8 if self._bit_depth == 16 else 16

    def toggle_view(self):
        self._toggle_view = 0 if self._toggle_view == 1 else 1

    def bit_depth(self) -> int:
        return self._bit_depth

    def shape(self):
        return self._shape

    def exposure(self):
        return self._exposure

    def set_exposure(self, exposure: int) -> bool:
        if exposure >= self._exposure_max or exposure <= self._exposure_min:
            return False
        self._exposure = exposure
        return True

    def init_exposure(self) -> None:
        self._exposure_max = 500_000
        self._exposure_min = 100

    def adjust_exposure(self) -> None:
        self._exposure = (self._exposure_min + self._exposure_max) // 2

    def check_exposure(self, frame: np.ndarray) -> bool:
        if self._exposure > 10000:
            self._exposure_max = self._exposure - 1
        else:
            self._exposure_min = self._exposure + 1
        if 8000 <= self.exposure() <= 12000:
            self._exposure_max = 500_000
            self._exposure_min = 100
            return True
        else:
            return False

    def get_frame(self) -> tuple[np.ndarray, np.ndarray]:
        """Returns a (H, W) grayscale float32 NumPy array in [0, 1]"""
        img = np.zeros(self.shape(), dtype=np.float32)
        if self._toggle_view == 0:
            x = (self._counter % self.shape()[1])
            img[:, x:x + 5] = 1.0  # moving white bar
        else:
            y = (self._counter % self.shape()[0])
            img[y:y + 5, :] = 1.0
        self._counter += 1
        return img, img

    def get_envi_options(self) -> dict:
        return {
            'samples': self._shape[1],
            'lines': self._shape[0],
            'bands': 1,
            'interleave': 'bsq',
            'byte order': 0,
            'data type': 4,
            'acquisition time': datetime.now().isoformat(),
        }

    def set_save_subfolder(self, subfolder: str) -> None:
        self._subfolder = subfolder
        self.save_folder().mkdir(parents=False, exist_ok=True)

    def save_folder(self):
        if self._subfolder is None:
            return self._save_folder
        return self._save_folder / self._subfolder
    
    def exception_type(self):
        return Exception


class CameraEnum(str, Enum):
    MOCK = "mock"
    XIMEA = "ximea"
    TIS = "tis"


def camera(camera_id: CameraEnum | str) -> Camera:
    
    if camera_id == CameraEnum.MOCK:
        return MockCamera()
    elif camera_id == CameraEnum.XIMEA:
        from ximea_visualizer.ximea_interface import XimeaCamera
        return XimeaCamera()
    elif camera_id == CameraEnum.TIS:
        from ximea_visualizer.ximea_interface import TisCamera
        return TisCamera()
    else:
        raise ValueError(f"Camera f{camera_id} not known.")