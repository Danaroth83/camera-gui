import subprocess
import numpy as np

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

def demosaic_bilinear_gbrg(bayer: np.ndarray) -> np.ndarray:
    """
    Perform manual bilinear interpolation for a GBRG Bayer pattern.
    Input: 2D bayer image (uint8 or uint16)
    Output: 3D RGB image (uint8)
    """
    h, w = bayer.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)

    # Green channel (on GBRG it's on (even, even) and (odd, odd))
    rgb[0::2, 0::2, 1] = bayer[0::2, 0::2]  # even rows, even cols
    rgb[1::2, 1::2, 1] = bayer[1::2, 1::2]  # odd rows, odd cols
    rgb[0::2, 1::2, 1] = (bayer[0::2, 0:-2:2] + bayer[0::2, 2::2]) / 2  # horizontal interp
    rgb[1::2, 0::2, 1] = (bayer[0:-2:2, 0::2] + bayer[2::2, 0::2]) / 2  # vertical interp

    # Red channel (at (odd, even))
    rgb[1::2, 0::2, 0] = bayer[1::2, 0::2]
    rgb[1::2, 1::2, 0] = (bayer[1::2, 0:-2:2] + bayer[1::2, 2::2]) / 2  # horizontal
    rgb[0::2, 0::2, 0] = (bayer[0:-2:2, 0::2] + bayer[2::2, 0::2]) / 2  # vertical
    rgb[0::2, 1::2, 0] = (
        bayer[0:-2:2, 0:-2:2] + bayer[0:-2:2, 2::2] +
        bayer[2::2, 0:-2:2] + bayer[2::2, 2::2]
    ) / 4  # diagonal

    # Blue channel (at (even, odd))
    rgb[0::2, 1::2, 2] = bayer[0::2, 1::2]
    rgb[0::2, 0::2, 2] = (bayer[0::2, 1:-1:2] + bayer[0::2, 3::2]) / 2  # horizontal
    rgb[1::2, 1::2, 2] = (bayer[0:-2:2, 1::2] + bayer[2::2, 1::2]) / 2  # vertical
    rgb[1::2, 0::2, 2] = (
        bayer[0:-2:2, 1:-1:2] + bayer[0:-2:2, 3::2] +
        bayer[2::2, 1:-1:2] + bayer[2::2, 3::2]
    ) / 4  # diagonal

    return rgb


def bayer_to_rgb(bayer_raw: np.ndarray, demosaic: bool) -> np.ndarray:
    # Normalize 16-bit to float for demosaicing
    if bayer_raw.dtype == np.uint16:
        out = bayer_raw.astype(np.float32) / 65535.0
    else:
        out = bayer_raw.astype(np.float32) / 255.0
    if demosaic:
        out = demosaic_bilinear_gbrg(out)
    return out

# === Usage ===
if __name__ == "__main__":
    width, height = 640, 480
    bayer = capture_bayer_image_in_memory("/dev/video2", width, height, pixfmt="GB16")
    rgb = bayer_to_rgb(bayer, demosaic=True)
    print(f"Bayer shape: {bayer.shape}")
    print(f"Bayer dtype: {bayer.dtype}")
    print(f"RBG shape: {rgb.shape}")
    print(f"RGB dtype: {rgb.dtype}")