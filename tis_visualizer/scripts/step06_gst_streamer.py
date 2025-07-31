import sys
import time

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst


def on_message(bus, message, loop=None):
    if message.type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print("Error:", err.message)
        print("Debug info:", debug)
        if loop:
            loop.quit()
    elif message.type == Gst.MessageType.EOS:
        print("End-Of-Stream reached.")
        if loop:
            loop.quit()


def main():
    Gst.init(sys.argv)

    # Replace with your actual video device
    device_path = "/dev/video3"

    pipeline_description = f"v4l2src device={device_path} ! videoconvert ! autovideosink sync=false"

    print("Launching pipeline:", pipeline_description)
    pipeline = Gst.parse_launch(pipeline_description)

    # Attach bus to handle errors
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", on_message)

    # Set the pipeline to PLAYING
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set pipeline to PLAYING state.")
        return

    print("Streaming... Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    main()
