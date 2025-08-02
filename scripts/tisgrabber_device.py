import sys

import gi

gi.require_version("Tcam", "1.0")
gi.require_version("Gst", "1.0")

from gi.repository import Tcam, Gst


def main():
    Gst.init(sys.argv)

    monitor = Gst.DeviceMonitor.new()
    # We are only interested in devices that are in the categories
    # Video and Source and tcam
    monitor.add_filter("Video/Source/tcam")

    for device in monitor.get_devices():
        struc = device.get_properties()

        print(f"model: {struc.get_string("model")}")
        print(f"serial: {struc.get_string("serial")}")
        print(f"type: {struc.get_string("type")}")

if __name__ == "__main__":
    main()