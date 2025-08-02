import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import numpy as np

FPS = 30
WIDTH = 640
HEIGHT = 480
USE_16BIT = True
# PIXEL_FORMAT = "Y16" if USE_16BIT else "GRAY8"
PIXEL_FORMAT = "GB16" if USE_16BIT else "GBRG"
BAYER_PATTERN = 'GB'  # For GBRG / GB16

def demosaic_bilinear_gbrg(bayer: np.ndarray) -> np.ndarray:
    """
    Perform manual bilinear interpolation for a GBRG Bayer pattern.
    Input: 2D bayer image (uint8 or uint16)
    Output: 3D RGB image (uint8)
    """
    h, w = bayer.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)

    # Green channel (on GBRG it's on (even,odd) and (odd,even))
    rgb[0::2, 1::2, 1] = bayer[0::2, 1::2]  # even rows, odd cols
    rgb[1::2, 0::2, 1] = bayer[1::2, 0::2]  # odd rows, even cols
    rgb[0::2, 0::2, 1] = (bayer[0::2, 1:-1:2] + bayer[0::2, 0:-2:2]) / 2  # interpolate horizontally
    rgb[1::2, 1::2, 1] = (bayer[0:-2:2, 1::2] + bayer[2::2, 1::2]) / 2    # interpolate vertically

    # Red channel (at (even, even))
    rgb[0::2, 0::2, 0] = bayer[0::2, 0::2]
    rgb[0::2, 1::2, 0] = (bayer[0::2, 0:-2:2] + bayer[0::2, 2::2]) / 2
    rgb[1::2, 0::2, 0] = (bayer[0:-2:2, 0::2] + bayer[2::2, 0::2]) / 2
    rgb[1::2, 1::2, 0] = (bayer[0:-2:2, 0:-2:2] + bayer[0:-2:2, 2::2] + bayer[2::2, 0:-2:2] + bayer[2::2, 2::2]) / 4

    # Blue channel (at (odd, odd))
    rgb[1::2, 1::2, 2] = bayer[1::2, 1::2]
    rgb[0::2, 1::2, 2] = (bayer[1::2, 1::2] + bayer[1::2, 1::2]) / 2
    rgb[1::2, 0::2, 2] = (bayer[1::2, 1::2] + bayer[1::2, 1::2]) / 2
    rgb[0::2, 0::2, 2] = (bayer[1::2, 1::2] + bayer[1::2, 1::2] + bayer[1::2, 1::2] + bayer[1::2, 1::2]) / 4

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


def main():
    Gst.init(None)

    # Create a pipeline that gets 1 frame from the camera
    pipeline_str = (
        f"tcambin name=source ! "
        f"video/x-raw,format={PIXEL_FORMAT},width={WIDTH},height={HEIGHT},framerate={FPS:d}/1 ! "
        f"appsink name=sink emit-signals=true max-buffers=1 drop=true"
    )

    pipeline = Gst.parse_launch(pipeline_str)
    appsink = pipeline.get_by_name("sink")

    def pull_frame():
        sample = appsink.emit("pull-sample")
        buf = sample.get_buffer()
        caps = sample.get_caps()
        width = caps.get_structure(0).get_value("width")
        height = caps.get_structure(0).get_value("height")

        # Map and extract raw data
        result, mapinfo = buf.map(Gst.MapFlags.READ)
        if not result:
            return None
        raw = mapinfo.data
        dtype = np.uint16 if USE_16BIT else np.uint8
        arr = np.frombuffer(raw, dtype=dtype).reshape((height, width))
        buf.unmap(mapinfo)
        return arr

    # Start and grab one frame
    pipeline.set_state(Gst.State.PLAYING)
    GLib.MainContext().iteration(False)  # Let GStreamer initialize

    frame = pull_frame()
    pipeline.set_state(Gst.State.NULL)

    print("Frame shape:", frame.shape, "dtype:", frame.dtype)
    rgb = bayer_to_rgb(frame, demosaic=True)
    print("RGB shape:", rgb.shape, "dtype:", rgb.dtype)

if __name__ == "__main__":
    main()