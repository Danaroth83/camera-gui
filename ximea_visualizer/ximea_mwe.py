from pathlib import Path

from ximea import xiapi
import numpy as np
import matplotlib.pyplot as plt


def main():
    output_folder = Path(__file__).resolve().parents[2] / "data"
    output_folder.mkdir(parents=False, exist_ok=True)

    #create instance for first connected camera
    cam = xiapi.Camera()

    #start communication
    #to open specific device, use:
    #cam.open_device_by_SN('41305651')
    #(open by serial number)
    print('Opening first camera...')
    cam.open_device()
    print(cam.get_imgdataformat())
    cam.set_imgdataformat("XI_MONO16")
    cam.set_image_data_bit_depth("XI_BPP_10")

    #settings
    cam.set_exposure(10000)
    print('Exposure was set to %i us' %cam.get_exposure())

    #create instance of Image to store image data and metadata
    img = xiapi.Image()

    #start data acquisition
    print('Starting data acquisition...')
    cam.start_acquisition()

    for i in range(10):
        #get data and pass them from camera to img
        cam.get_image(img)
        print(f"Min exposure: {cam.get_exposure_minimum()}")
        print(f"Max exposure: {cam.get_exposure_maximum()}")
        print(f"Exposure increment: {cam.get_exposure_increment()}")

        #get raw data from camera
        #for Python2.x function returns string
        #for Python3.x function returns bytes
        data_raw = img.get_image_data_raw()

        #transform data to list
        data = list(data_raw)

        a = img.get_image_data_numpy()
        out = np.empty((a.shape[0] // 4, a.shape[1] // 4, 16), dtype=a.dtype)
        for ii in range(4):
            for jj in range(4):
                out[:, :, jj + 4 * ii] = a[ii::4, jj::4]
        np.save(output_folder / f"image_{i}.npy", arr=a)
        np.save(output_folder / f"demosaic_{i}.npy", arr=out)

        print(f"Max value {a.max()}")

        a_normalized = np.array(a, dtype=np.float32) / (2 ** 10 - 1)
        out_normalized = np.empty((a.shape[0] // 4, a.shape[1] // 4, 16), dtype=a_normalized.dtype)
        for ii in range(4):
            for jj in range(4):
                out_normalized[:, :, jj + 4 * ii] = a_normalized[ii::4, jj::4]
        np.save(output_folder / f"image_normalized_{i}.npy", arr=a_normalized)
        np.save(output_folder / f"demosaic_normalized_{i}.npy", arr=out_normalized)

        rgb = [12, 8, 4]
        fig, ax = plt.subplots(1, 2)
        ax[0].imshow(a_normalized)
        ax[1].imshow(out_normalized[..., rgb])
        fig.savefig(output_folder / f"figure_{i}.png")
        plt.close()

        #print image data and metadata
        print(f"Image type {type(img)}")
        print('Image number: ' + str(i))
        print('Image width (pixels):  ' + str(img.width))
        print('Image height (pixels): ' + str(img.height))
        print('First 10 pixels: ' + str(data[:10]))
        print('\n')

    #stop data acquisition
    print('Stopping acquisition...')
    cam.stop_acquisition()

    #stop communication
    cam.close_device()

    print('Done.')


if __name__ == "__main__":
    main()

