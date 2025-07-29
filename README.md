# Introduction

This code was originally produced for a user-friendly Python interface with the XIMEA camera MQ02HG-IM-SM4x4.

The camera is a mosaic based camera with a 4x4 color filter array pattern operating in the RED/NIR wavelength range.

The provided code allows to:
- Visualize the acquisition;
- Pause the acquisition;
- Switch between a mosaiced and demosaiced visualization;
- Record a sequence of frames.

# Installation instruction


## Prerequisites

For this tutorial, you require a Linux machine running on x86 with `root`
priviledges.

Before installing, you may need to change the security level of your UEFI/BIOS.
Restart your PC and go to the `UEFI/BIOS firmware` installation (typically by pressing Esc, F2, or Del at restart).
In the `UEFI` menu, choose `Secure Boot` and select `Disabled`.

## XIMEA API installation

This software instructions are intended for a Linux x86 machine user.
For Windows/MacOS, please consult the official guide for installing
the XIMEA software package available at:
<https://www.ximea.com/support/wiki/apis/APIs>

Download the software package for Linux available at:
<https://www.ximea.com/software-downloads>

and select `Linux x86 Software Package Beta`.

Unzip it and then browse to the `package` subfolder, and then run
```bash
sudo .\install -cam_usb30
```
if your camera is USB 3.0 based (this is the case for our camera), or
```bash
sudo .\install -pcie
```
if it is based on the PCIE protocol.

Then, restart your PC.


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
  sudo \opt\XIMEA\uninstall
  ```
- Try installing the software package again through a root account
  ```bash
  su -i
  sudo .\install
  ```

## Testing the camera connection

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
python ximea_visualizer/visualization.py
```

where 10000 is the requested exposure time (10 seconds in this case).
From the visualization applet, you can:
- Press P to pause/unpause.
- Press M to switch between mosaiced and demosaiced view and viceversa.
- Press R to start/stop recording frames to data/[timestamp].
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
The folder contains:
- The original measurement design: `cameras_94mm_v2.pdf`
- A 2d draft for lasercuts: `plate_design.pdf`
- Blender 3d renders for the machine: `scaled_holed_plate.blend`
- An STL conversion for 3d printing: `scaled_holed_plate.stl`
- The sliced version for the Flashforge 3d printer: `scaled_holed_plate.gx`

The original design `cameras_94mm_v2.pdf` was made by:
- Kuniaki Uto <uto@wise-sss.titech.ac.jp>


## Developer

Daniele Picone  
Univ. Grenoble Alpes, CNRS, Grenoble INP, GIPSA-lab, 38000 Grenoble, France  
Work mail: [daniele.picone@grenoble-inp.fr](mailto:daniele.picone@grenoble-inp.fr)  
Personal mail: [danaroth83@gmail.com](mailto:danaroth83@gmail.com)  