import imagingcontrol4 as ic4

from camera_visualizer.camera_interface.ic4_interface import Ic4Camera, Ic4CameraState

TIS_EXPOSURE_TIMES = [
    ic4.PropId.EXPOSURE_AUTO,
    ic4.PropId.EXPOSURE_AUTO_HIGHLIGHT_REDUCTION,
    ic4.PropId.EXPOSURE_AUTO_LOWER_LIMIT,
    ic4.PropId.EXPOSURE_AUTO_REFERENCE,
    ic4.PropId.EXPOSURE_AUTO_UPPER_LIMIT,
    ic4.PropId.EXPOSURE_AUTO_UPPER_LIMIT_AUTO,
    ic4.PropId.EXPOSURE_TIME,
]


def print_exposure_time(grabber: ic4.Grabber, exp_time_property: str):
    try:
        exp_time = grabber.device_property_map.get_value_float(property_name=exp_time_property)
        print(f"[FLOAT] {exp_time_property}: {exp_time}")
    except ic4.IC4Exception:
        try:
            exp_time = grabber.device_property_map.get_value_int(property_name=exp_time_property)
            print(f"[INT] {exp_time_property}: {exp_time}")
        except ic4.IC4Exception:
            print(f"Cannot get the value of '{exp_time_property}' as float or int.")


def main():
    cam = Ic4Camera()
    cam.open()
    print(f"Cam State ExpTime Before set_exposure: {cam.state.current_exposure}")
    for exp_time_property in TIS_EXPOSURE_TIMES:
        print_exposure_time(grabber=cam.grabber, exp_time_property=exp_time_property)
    print()

    exposure_time_ms = 100  # 10 fps at best
    cam.set_exposure(exposure_time_ms)
    print(f"Cam State ExpTime After set_exposure: {cam.state.current_exposure}")
    for exp_time_property in TIS_EXPOSURE_TIMES:
        print_exposure_time(grabber=cam.grabber, exp_time_property=exp_time_property)
    print()

    exposure_time_ms = 900  # 10 fps at best
    cam.set_exposure(exposure_time_ms)
    print(f"Cam State ExpTime After set_exposure: {cam.state.current_exposure}")
    for exp_time_property in TIS_EXPOSURE_TIMES:
        print_exposure_time(grabber=cam.grabber, exp_time_property=exp_time_property)
    print()

    cam.close()

if __name__ == "__main__":
    main()
