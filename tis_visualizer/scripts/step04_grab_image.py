import imagingcontrol4 as ic4
ic4.Library.init()


def check_tis_accepted_pixel_formats():
    grabber = ic4.Grabber()
    grabber.device_open(ic4.DeviceEnum.devices()[0])

    sink = ic4.SnapSink(
        accepted_pixel_formats=[ic4.PixelFormat.Mono8]
    )
    grabber.stream_setup(sink=sink, setup_option=ic4.StreamSetupOption.ACQUISITION_START)

    def toggle_pixel_format(pixel_format):
        try:
            grabber.device_property_map.set_value(ic4.PropId.PIXEL_FORMAT, pixel_format)
            print(f"Pixel Format is set to {pixel_format.name}")
        except ic4.IC4Exception:
            print(f"Cannot set to {pixel_format.name}")

    print(f"Sink pixel format state: {sink.output_image_type.pixel_format.name}")

    toggle_pixel_format(ic4.PixelFormat.BayerGB16)


    print(f"Sink pixel format state: {sink.output_image_type.pixel_format.name}")

    grabber.stream_stop()
    grabber.device_close()


def main():
    # Create a Grabber object
    grabber = ic4.Grabber()

    # Open the first available video capture device
    first_device_info = ic4.DeviceEnum.devices()[0]
    print(first_device_info)

    grabber.device_open(first_device_info)

    a = grabber.device_property_map
    print(a)

    # Configure the device to output images in the Mono8 pixel format
    grabber.device_property_map.set_value(ic4.PropId.PIXEL_FORMAT, ic4.PixelFormat.Mono8)

    # Set the resolution to 640x480
    grabber.device_property_map.set_value(ic4.PropId.WIDTH, 640)
    grabber.device_property_map.set_value(ic4.PropId.HEIGHT, 480)

    # Create a SnapSink. A SnapSink allows grabbing single images (or image sequences) out of a data stream.
    sink = ic4.SnapSink()
    # Setup data stream from the video capture device to the sink and start image acquisition.
    grabber.stream_setup(sink, setup_option=ic4.StreamSetupOption.ACQUISITION_START)

    try:
        # Grab a single image out of the data stream.
        image = sink.snap_single(1000)

        # Print image information.
        print(f"Received an image. ImageType: {image.image_type}")

        # Save the image.
        image.save_as_png("test.png")

    except ic4.IC4Exception as ex:
        print(ex.message)

    # Stop the data stream.
    grabber.stream_stop()


if __name__ == "__main__":
    check_tis_accepted_pixel_formats()
