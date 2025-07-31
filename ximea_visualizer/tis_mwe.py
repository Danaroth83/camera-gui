import imagingcontrol4 as ic4


def main():
    ic4.Library.init()
    print(ic4.DeviceEnum.devices())



if __name__ == "__main__":
    main()