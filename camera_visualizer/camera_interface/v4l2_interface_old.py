import os
import subprocess

import scipy
import numpy as np

from camera_visualizer.camera_interface.mock_interface import Camera

V4L2_MIN_EXPOSURE_MS = 15
V4L2_MAX_EXPOSURE_MS = 33_333
V4L2_EXPOSURE_INCREMENT = 1

def list_video_devices():
    """Returns a list of /dev/video* devices."""
    return sorted(f"/dev/{d}" for d in os.listdir("/dev") if d.startswith("video"))


def supports_format(device, fmt: str = "BG16"):
    """Checks if a video device supports the BG16 pixel format."""
    try:
        result = subprocess.run(
            ["v4l2-ctl", "--device", device, "--list-formats"],
            capture_output=True, check=True, text=True
        )
        return fmt in result.stdout
    except subprocess.CalledProcessError:
        return False

def find_device(fmt: list[str]):
    """Finds the first /dev/videoX device that supports BG16 format."""
    for dev in list_video_devices():
        for f in fmt:
            if not supports_format(dev, f):
                break
        return dev
    return None

def capture_bayer_image_in_memory(
    device: str | None,
    width: int=640,
    height: int=480,
    pixfmt="GB16",
):
    """Captures one BG16 frame using v4l2-ctl and returns it as a NumPy array."""
    if device is None:
        device = find_device(fmt=[pixfmt])
        if device is None:
            raise ValueError("Device not found")

    cmd = [
        "v4l2-ctl",
        f"--device={device}",
        f"--set-fmt-video=width={width},height={height},pixelformat={pixfmt}",
        "--stream-mmap",
        "--stream-count=1",
        "--stream-to=-"  # <-- stdout
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)
    raw = np.frombuffer(result.stdout, dtype=np.uint16)
    return raw.reshape((height, width))


def demosaic_cfa_bayer_gbrb_bilinear(bayer: np.ndarray):
    f_g = np.array([[0, 1, 0], [1, 4, 1], [0, 1, 0]], dtype=np.float32) / 8
    f_r = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=np.float32) / 16
    out = np.zeros((*bayer.shape[:2], 3))

    # Red
    out[1::2, 0::2, 0] = bayer[1::2, 0::2]
    out[..., 0] = scipy.ndimage.convolve(out[..., 0], f_r)
    # Green
    out[0::2, 0::2, 1] = bayer[0::2, 0::2]
    out[1::2, 1::2, 1] = bayer[1::2, 1::2]
    out[..., 1] = scipy.ndimage.convolve(out[..., 1], f_g)
    # Blue
    out[0::2, 1::2, 2] = bayer[0::2, 1::2]
    out[..., 2] = scipy.ndimage.convolve(out[..., 2], f_r)

    return out


class V4l2Camera(Camera):

    def __init__(
        self,
        device: str | None = None,
        width: int = 640,
        height: int = 480,
        pixel_formats: tuple[str, ...] = ("BG16", "BG8")
    ):
        if device is None:
            device = find_device(fmt=list(pixel_formats))
            if device is None:
                raise ValueError("Device not found")
        else:
            for f in pixel_formats:
                if not supports_format(device, f):
                    raise ValueError(f"Device does not support format {f}")
        self.device = device
        self.width = width
        self.height = height
        self.pixel_formats = pixel_formats

    def open(self) -> None:
        cmd = [
            "v4l2-ctl",
            f"--device={self.device}",
            f"--set-fmt-video=width={self.width},height={self.height},pixelformat={self.pixel_formats[0]}",
            "--stream-mmap",
            "--stream-count=1",
            "--stream-to=-"  # <-- stdout
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)