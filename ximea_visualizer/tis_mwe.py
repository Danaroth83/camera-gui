import imagingcontrol4 as ic4


def main():
    ic4.Library.init()
    # Open the first available video capture device
    
    grabber = ic4.Grabber()
    first_device_info = ic4.DeviceEnum.devices()[0]
    grabber.device_open(first_device_info)

    



if __name__ == "__main__":
    main()