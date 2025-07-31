import imagingcontrol4 as ic4

ic4.Library.init()
devices_list = ic4.DeviceEnum.devices()
print(devices_list)