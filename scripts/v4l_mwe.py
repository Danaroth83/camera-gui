import subprocess
import numpy as np
from colour_demosaicing import demosaicing_CFA_Bayer_bilinear


def capture_bayer_image_in_memory(device="/dev/video2", width=640, height=480, pixfmt="GB16"):
    """Captures one BG16 frame using v4l2-ctl and returns it as a NumPy array."""
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


def bayer_to_rgb(bayer_raw: np.ndarray, demosaic: bool) -> np.ndarray:
    # Normalize 16-bit to float for demosaicing
    if bayer_raw.dtype == np.uint16:
        out = bayer_raw.astype(np.float32) / 65535.0
    else:
        out = bayer_raw.astype(np.float32) / 255.0
    if demosaic:
        out = demosaicing_CFA_Bayer_bilinear(out, pattern="GBRG")
    return out

# === Usage ===
if __name__ == "__main__":
    width, height = 1920, 1200
    bayer = capture_bayer_image_in_memory("/dev/video2", width, height, pixfmt="GB16")
    rgb = bayer_to_rgb(bayer, demosaic=True)
    print(f"Bayer shape: {bayer.shape}")
    print(f"Bayer dtype: {bayer.dtype}")
    print(f"RBG shape: {rgb.shape}")
    print(f"RGB dtype: {rgb.dtype}")