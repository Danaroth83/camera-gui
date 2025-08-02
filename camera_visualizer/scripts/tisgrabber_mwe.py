import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import numpy as np
from skimage.color import demosaicing_CFA_Bayer_bilinear

FPS = 30
WIDTH = 640
HEIGHT = 480
USE_16BIT = True
# PIXEL_FORMAT = "Y16" if USE_16BIT else "GRAY8"
PIXEL_FORMAT = "GB16" if USE_16BIT else "GBRG"
BAYER_PATTERN = 'GB'  # For GBRG / GB16


def bayer_to_rgb(bayer_raw: np.ndarray) -> np.ndarray:
    # Normalize 16-bit to float for demosaicing
    if bayer_raw.dtype == np.uint16:
        bayer_float = bayer_raw.astype(np.float32) / 65535.0
    else:
        bayer_float = bayer_raw.astype(np.float32) / 255.0

    rgb = demosaicing_CFA_Bayer_bilinear(bayer_float, pattern=f'{BAYER_PATTERN}RG')
    return np.clip(rgb * 255, 0, 255).astype(np.uint8)


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


if __name__ == "__main__":
    main()