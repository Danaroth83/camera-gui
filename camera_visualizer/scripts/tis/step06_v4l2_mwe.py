import numpy as np

from tis_visualizer.v4l2_interface import V4L2Camera

cam = V4L2Camera()
cam.open()

try:
    for i in range(10):
        frame, _ = cam.get_frame()
        np.save(file="frame", arr=frame)

        print(f"{cam.bit_depth()}: {frame.shape} {frame.dtype} max={frame.max():.4f}")
        # cam.toggle_bit_depth()  # switch to 16-bit

finally:
    cam.close()
