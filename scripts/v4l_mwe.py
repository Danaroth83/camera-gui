import argparse
import subprocess
import os

import numpy as np
import scipy


def list_video_devices():
    """Returns a list of /dev/video* devices."""
    return sorted(f"/dev/{d}" for d in os.listdir("/dev") if d.startswith("video"))

def supports_bg16(device):
    """Checks if a video device supports the BG16 pixel format."""
    try:
        result = subprocess.run(
            ["v4l2-ctl", "--device", device, "--list-formats"],
            capture_output=True, check=True, text=True
        )
        return "BG16" in result.stdout
    except subprocess.CalledProcessError:
        return False

def find_bg16_device():
    """Finds the first /dev/videoX device that supports BG16 format."""
    for dev in list_video_devices():
        if supports_bg16(dev):
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
        device = find_bg16_device()
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

def bayer_to_rgb(bayer_raw: np.ndarray, demosaic: bool) -> np.ndarray:
    # Normalize 16-bit to float for demosaicing
    if bayer_raw.dtype == np.uint16:
        out = bayer_raw.astype(np.float32) / 65535.0
    else:
        out = bayer_raw.astype(np.float32) / 255.0
    if demosaic:
        out = demosaic_cfa_bayer_gbrb_bilinear(out)
    return out.astype(np.float32)

# === Usage ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(
        description="Camera visualizer with optional window resize.")
    parser.add_argument('--width', '-W', type=int, default=1920,
                        help='Window width')
    parser.add_argument('--height', '-H', type=int, default=1200,
                        help='Window height')
    args = parser.parse_args()

    width, height = args.width, args.height
    bayer = capture_bayer_image_in_memory("/dev/video2", width, height, pixfmt="GB16")
    # bayer = (np.random.randn(width, height) * 65535).astype(np.uint16)
    rgb = bayer_to_rgb(bayer, demosaic=True)
    print(f"Bayer shape: {bayer.shape}")
    print(f"Bayer dtype: {bayer.dtype}")
    print(f"RBG shape: {rgb.shape}")
    print(f"RGB dtype: {rgb.dtype}")