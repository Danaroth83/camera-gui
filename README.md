# Introduction

This code was originally produced for a user-friendly Python interface
for the visualization of cameras through a device independent API.

This code was originally developed for interfacing with:
- the XIMEA camera model MQ02HG-IM-SM4x4-RedNir.
  - A hyperspectral mosaic based camera with a 4x4 color filter array pattern
    operating in the RED/NIR range
- the Imaging Source camera model DFK 23UX236 
  - A compact RGB camera with a Bayer patterned color filter array.
  - 
The code provides a graphical interface in PyQt5 which allows to:
- visualize the data stream;
- pause resume the acquisition;
- switch between different image views (e.g. mosaiced/demosaiced)
- change the bit depth;
- record a sequence of frames;
- change the FPS;
- set and dynamically assess the exposure time.

# Installation instruction


## XIMEA API installation

### Prerequisites

For this tutorial, you require a Linux machine running on x86 with `root`
privileges.

Before installing, you may need to change the security level of your UEFI/BIOS.
Restart your PC and go to the `UEFI/BIOS firmware` installation (typically by pressing Esc, F2, or Del at restart).
In the `UEFI` menu, choose `Secure Boot` and select `Disabled`.

### Introduction

This software instructions are intended for a Linux x86 machine user.  
For Windows/MacOS, please consult the official guide for installing
the XIMEA software package available at:  
<https://www.ximea.com/support/wiki/apis/APIs>

Download the software package for Linux available at:  
<https://www.ximea.com/software-downloads>

and select `Linux x86 Software Package Beta`.

Unzip it and then browse to the `package` subfolder, and then run
```bash
sudo ./install -cam_usb30
```
if your camera is USB 3.0 based (this is the case for our camera), or
```bash
sudo ./install -pcie
```
if it is based on the PCIE protocol.

Then, restart your PC.

### Testing the connection

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

### Testing the camera API

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

However, the USB default transfer rate on LINUX is usually limited by default.
You should be able to change this option by accessing your root account
and typing:

```bash
sudo echo 0 > /sys/module/usbcore/parameters/usbfs_memory_mb
```

## TIS API installation

### Introduction

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
and select the Linux-AMD driver. Once downloaded, install it through `dpkg`
(Note: the filename may be different for you):

```bash
sudo dpkg -i ic4-gentl-driver-v4l2_1.0.0.144_amd64.deb
```

### Testing the camera API

Then install the Imaging Control 4:
```bash
pip install imagingcontrol4
```

and test it with a sample Python code:
```python
import imagingcontrol4 as ic4
ic4.Library.init()
ic4.DeviceEnum.devices()
```

## Script testing

### Prerequisites

This is a simple list of prerequisites for running the Python script.
For Linux you typically require to have a Matplotlib renderer; these intructions should be enough:

```bash
pip install numpy
pip install matplotlib
pip install pyqt5
```

For visualization, you may also need to install this library:
```bash
sudo apt install libxcb-xinerama0
```


From this moment on you should be able to connect the camera through USB to
your machine and type:
```bash
python ximea_visualizer/gui.py
```
A GUI will allow to select the camera model:
- `mock` is a fake camera just to test the graphic interface
- `ximea`: is 


where 10000 is the requested exposure time (10 seconds in this case).
From the visualization applet, you can (while within the scope of the figure):
- Press P to pause/unpause.
- Press M to switch between mosaiced and demosaiced view and viceversa.
- Press B to switch between 10 bits/8 bits acquisition
- Press R to start/stop recording frames to data/[timestamp].
  - Remember to press R again or the acquisitions will continue indefinitely.
  - You can select the savefile name by running the script with the `-n` 
    argument. E.g., to save as `dark` within the save folder:
    ```bash
    python ximea_visualizer/visualization.py -n dark
    ```
- Press E to estimate the exposure time via binary search
  - Keep the camera still while estimating.
  - This is an experimental feature, so it may fail.
  - Press E again to restart the estimation in case of failure.
  - You may want to rerun the script with the estimated exposure time, e.g. 
    for 10000 microseconds:
    ```bash
    python ximea_visualizer/visualization.py -e 10000
    ```
- To exit, just close the visualization applet.

## Plate designs

The repository also contains some 3d designs for a plate to mount a camera
over a standard tripod in the folder `data\plate_design`.
The plate was designed for a combined acquisition of two companion cameras:
- XIMEA model MQ02HG-IM-SM4x4.
- The Imaging Source (TIS) model DFK 23UK236.

The folder contains:
- The original measurement design: `cameras_94mm_v2.pdf`
- A 2d draft for lasercuts: `plate_design.pdf`
- Blender 3d renders for the machine: `scaled_holed_plate.blend`
- An STL conversion for 3d printing: `scaled_holed_plate.stl`
- The sliced version for the Flashforge 3d printer: `scaled_holed_plate.gx`

The design `cameras_94mm_v2.pdf` was originally made by:
- Kuniaki Uto [uto@wise-sss.titech.ac.jp](mailto:uto@wise-sss.titech.ac.jp)


## Developer

Daniele Picone  
Univ. Grenoble Alpes, CNRS, Grenoble INP, GIPSA-lab, 38000 Grenoble, France  
Work mail: [daniele.picone@grenoble-inp.fr](mailto:daniele.picone@grenoble-inp.fr)  
Personal mail: [danaroth83@gmail.com](mailto:danaroth83@gmail.com)  

Mohamad Jouni  
Florais - Filiale UGA, CNRS, Grenoble INP, GIPSA-lab, 38000 Grenoble, France  
Work mail: [mohamad.jouni@grenoble-inp.fr](mailto:mohamad.jouni@grenoble-inp.fr)  
Personal mail: [mhmd.jouni@outlook.fr](mailto:mhmd.jouni@outlook.fr)  
