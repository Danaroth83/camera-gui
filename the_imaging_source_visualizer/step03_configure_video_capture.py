import imagingcontrol4 as ic4


def main():
    # Initialize library
    ic4.Library.init()

    # Create a Grabber object
    grabber = ic4.Grabber()

    # Open the first available video capture device
    first_device_info = ic4.DeviceEnum.devices()[0]
    grabber.device_open(first_device_info)

    # # Configure the device to output images in the Mono8 pixel format
    # grabber.device_property_map.set_value(ic4.PropId.PIXEL_FORMAT, ic4.PixelFormat.Mono8)
    #
    # # Set the resolution to 640x480
    # grabber.device_property_map.set_value(ic4.PropId.WIDTH, ic4.PropId.WIDTH_MAX)
    # grabber.device_property_map.set_value(ic4.PropId.HEIGHT, 480)

    # Set the origin of the ROI to the top-left corner of the sensor
    grabber.device_property_map.set_value(ic4.PropId.OFFSET_AUTO_CENTER, "Off")
    grabber.device_property_map.set_value(ic4.PropId.OFFSET_X, 0)
    grabber.device_property_map.set_value(ic4.PropId.OFFSET_Y, 0)

    # Configure the exposure time to 5ms (5000µs)
    grabber.device_property_map.set_value(ic4.PropId.EXPOSURE_AUTO, "Off")
    grabber.device_property_map.set_value(ic4.PropId.EXPOSURE_TIME, 5000.0)

    # Enable GainAuto
    grabber.device_property_map.set_value(ic4.PropId.GAIN_AUTO, "Continuous")


if __name__ == "__main__":
    main()
