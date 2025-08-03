# TIS API installation

## Introduction

The camera The Imaging Source (TIS) model DFK 23UX236 reached end of life service.
First, test if the camera is discoverable through USB3:
```bash
lsusb
```
and you should get a message such as:
```
Bus 004 Device 003: ID 199e:841a The Imaging Source Europe GmbH DFK 23UX236
```

The camera is non-Genicam (V4L2), so you need to go to this page:  
<https://www.theimagingsource.com/en-us/support/download/ic4gentlprodv4l2-1.0.0.144/>
and select:
- the Linux-AMD driver (the most common in commercial laptops). 
- the Linux-ARM driver (in case you are running it on an ARM device, e.g. a 
  Jetson board).
Once downloaded, install it (Note: the filename may be different for you):

```bash
sudo dpkg -i ic4-gentl-driver-v4l2_1.0.0.144_amd64.deb
```

You may optionally want to install `tiscamera`:
```bash
git clone https://github.com/TheImagingSource/tiscamera.git
cd tiscamera
sudo ./scripts/dependency-magager install
mkdir build
cd build
sudo cmake ..
sudo make -j2
sudo cmake --install build
```

## Testing the camera connection

You can test if the camera is recongized through V4L2 (Video for Linux 2)
- Install the v4l2 utility:
  ```bash
  sudo apt-get install v4l-utils
  ```
- List existing devices:
  ```bash
  v4l2-ctl --list-devices
  ```
- List the available formats for a specific data flow:
  ```bash
  v4l2-ctl --device /dev/video0 --list-formats-ext
  ```
- Then run the selected format through `ffplay` (once you install `ffmpeg`):
  ```bash
  ffplay -i /dev/video0 -pixel_format y16 -video_size 640x480
  ```
- Be sure that the pixel format and video size are compatible with the request
  for your camera.

## Testing the camera API

Then install the Imaging Control 4:
```bash
pip install imagingcontrol4
```

and test it with a sample Python code:
```python
import imagingcontrol4 as ic4
ic4.Library.init()
print(ic4.DeviceEnum.devices())
```