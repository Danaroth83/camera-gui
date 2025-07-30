from pathlib import Path
from enum import Enum

import spectral
import numpy as np


class SaveFormatEnum(str, Enum):
    NUMPY = "numpy"
    ENVI = "envi"


def save_frame(
    frame: np.ndarray,
    save_folder: Path,
    filename_stem: str,
    envi_options: dict | None = None,
    fmt: SaveFormatEnum | str = SaveFormatEnum.NUMPY,
) -> None:
    if not isinstance(fmt, SaveFormatEnum):
        fmt = SaveFormatEnum(fmt)
    if fmt == SaveFormatEnum.NUMPY:
        np.save(file=save_folder / f"{filename_stem}.npy", arr=frame)
    elif fmt == SaveFormatEnum.ENVI:
        if envi_options is None:
            raise ValueError("Impossible to save to ENVI")
        metadata = envi_options
        spectral.envi.save_image(
            hdr_file=save_folder / f'{filename_stem}.hdr',
            image=frame,
            dtype=np.uint8,
            ext=".img",
            force=True,
            interleave='bsq',
            metadata=metadata,
        )
    else:
        raise ValueError(f"File format {fmt} unknown.")