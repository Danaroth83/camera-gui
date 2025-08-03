# XIMEA API installation

## Prerequisites

For this tutorial, you require a Linux machine running on x86 with `root`
privileges.

Before installing, you may need to change the security level of your UEFI/BIOS.
Restart your PC and go to the `UEFI/BIOS firmware` installation (typically by 
pressing Esc, F2, or Del at restart).
In the `UEFI` menu, choose `Secure Boot` and select `Disabled`.

## Introduction

This software instructions are intended for a Linux x86 machine user.  
For Windows/MacOS, please consult the official guide for installing
the XIMEA software package available at:  
<https://www.ximea.com/support/wiki/apis/APIs>

- Download the software package for Linux available at:  
  <https://www.ximea.com/software-downloads>
- Select: 
  - `Linux x86 Software Package Beta` if you are on a x86 system 
    (typical for laptops).
  - `Linux ARM Software Package Beta` if you are on an ARM system
    (e.g. a Jetson board).
- Unzip it and then browse to the `package` subfolder, and then run:
  - If your camera works through USB (that is the case for our camera)
  ```bash
  sudo ./install
  ```
  - If your camera is PCIE-based:
  ```bash
  sudo ./install -pcie
  ```
  
- IMPORTANT NOTE FOR USB CAMERAS:
  - The USB default transfer rate on LINUX is usually limited by default.
    You should be able to change this option by accessing your root account
    (`sudo -i`) and typing:
    ```bash
    sudo echo 0 > /sys/module/usbcore/parameters/usbfs_memory_mb
    ```

- Restart your PC.

## Testing the connection

You should first show if the camera is recognized by the USB port:
```bash
lsusb
```
and it should list your XIMEA camera in the list.

Additionally, and more importantly, you should check if the messages
are properly listened by your machine from the camera.
```bash
sudo dmesg | grep -i ximea
```
and see a message like this one:
```
[    0.826118] usb 4-1: Manufacturer: XIMEA
```

To test if the API has been installed then run (with Python installed on your machine):
```bash
python -c "import ximea; print(ximea.__version__)"
```
If this has not worked, please try:
- Uninstalling your XIMEA software package
  ```bash
  sudo /opt/XIMEA/uninstall
  ```
- Try installing the software package again through a root account
  ```bash
  su -i
  sudo ./install
  ```

## Testing the camera API

The ximea API provides some simplified script to test the connection;
it should look something like this:
```python
from ximea import xiapi

cam = xiapi.Camera()
cam.open_device()
cam.set_exposure(10_000)
img = xiapi.Image()


cam.start_acquisition()
cam.get_image(img)
...
cam.stop_acquisition()
cam.close_device()

```
