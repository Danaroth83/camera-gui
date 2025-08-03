# Introduction

This code was originally produced for a user-friendly Python interface
for the visualization of cameras through a device independent API.

The code provides a graphical interface in PyQt5 which allows to:
- visualize the data stream;
- pause resume the acquisition;
- switch between different image views (e.g. mosaiced/demosaiced)
- change the bit depth;
- record a sequence of frames;
- change the FPS;
- set and dynamically assess the exposure time.


This code was originally developed for interfacing with:
- the XIMEA camera model MQ02HG-IM-SM4x4-REDNIR.
  - A hyperspectral mosaic based camera with a 4x4 color filter array pattern
    operating in the RED/NIR range
- the Imaging Source camera model DFK 23UX236 
  - A compact RGB camera with a Bayer patterned color filter array.

In the acquisition campaign performed in Japan in the July/August 2025 period,
the cameras were mounted on a robot model JetArm Track T1, and placed on a 
tripod over its mechanical arm.  
The 3d designs for accomodating for the cameras over the tripod are shared
in the `data\plate_design` folder.


# Installation instruction

## GUI

### Prerequisites

The script was tested on a Linux machine running Ubuntu 22.04.5 LTS using 
Wayland as windowing system.

You can install the provided package as a library by going to the root folder
of the cloned repository and typing:
```bash
pip install pip --upgrade
pip install .
```

For visualization, you may also need to install this library:
```bash
sudo apt install libxcb-xinerama0
```

### Testing the GUI

From this moment on you should be able to connect the camera through USB to
your machine and type:
```bash
python camera_visualizer/gui.py
```

You can also run two camera feeds at the same time by running:
```bash
python camera_visualizer/gui_double.py
```

If the dependencies internally, you can run the script directly without
installing the library by typing:
```bash
python -m camera_visualizer.gui
```

### GUI instructions

To start a camera acquisition:

- Select the proper FPS (Note: the camera may change the value internally).
- Select the camera model:
  - `mock` is a fake camera just to test the graphic interface;
  - `ximea` is the XIMEA camera model MQ02HG-IM-SM4x4-REDNIR;
  - `tis` is the Imaging Source camera model DFK 23UX236.
  Note: Even if no camera API is installed, the `mock` camera will showcase
  the functionalities of the GUI.
- Press the `Start` button.


For setting the exposure time, either:
- Click the button `Estimate exposure time`
- Change the exposure time in the box `Exposure time (us)`

For saving video frames:
- Type the save format;
- Type the filename;
- Press the `Record` button;
- Press the `Stop recording` button to stop the recording. 
Files will be saved in `data/[camera_name]/[filename]_[timestamp]` and with a 
sequential index.

To exit, just close the visualization applet.


## XIMEA API installation

### Prerequisites

For this tutorial, you require a Linux machine running on x86 with `root`
privileges.

Before installing, you may need to change the security level of your UEFI/BIOS.
Restart your PC and go to the `UEFI/BIOS firmware` installation (typically by 
pressing Esc, F2, or Del at restart).
In the `UEFI` menu, choose `Secure Boot` and select `Disabled`.

### Introduction

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

### Testing the camera connection

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

The design `cameras_94mm_v2.pdf` designed by:
- Kuniaki Uto [uto@wise-sss.titech.ac.jp](mailto:uto@wise-sss.titech.ac.jp)


## Developers

Daniele Picone  
Univ. Grenoble Alpes, CNRS, Grenoble INP, GIPSA-lab, 38000 Grenoble, France  
Work mail: [daniele.picone@grenoble-inp.fr](mailto:daniele.picone@grenoble-inp.fr)  
Personal mail: [danaroth83@gmail.com](mailto:danaroth83@gmail.com)  

Mohamad Jouni  
Florais - Filiale UGA, CNRS, Grenoble INP, GIPSA-lab, 38000 Grenoble, France  
Work mail: [mohamad.jouni@grenoble-inp.fr](mailto:mohamad.jouni@grenoble-inp.fr)  
Personal mail: [mhmd.jouni@outlook.fr](mailto:mhmd.jouni@outlook.fr)  
